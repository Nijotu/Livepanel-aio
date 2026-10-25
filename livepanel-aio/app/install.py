"""Transactional user-local installation; preserve configs and legacy Livepanel."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
import urllib.request


def download(url,path):
    with urllib.request.urlopen(url,timeout=60) as response,Path(path).open('wb') as f:
        shutil.copyfileobj(response,f)

def unpack(archive,dest):
    with tarfile.open(archive) as tar:
        base=Path(dest).resolve()
        for m in tar.getmembers():
            if m.issym() or m.islnk() or not (base/m.name).resolve().is_relative_to(base):
                raise ValueError('Unsafe downloaded archive member: '+m.name)
        tar.extractall(dest,filter='data')

def backup(path,stamp):
    if path.exists():shutil.copy2(path,path.with_name(path.name+'.bak-'+stamp))

def main():
    env=os.environ;src=Path(env['LIVEPANEL_INSTALL_SOURCE']);app=Path(env['LIVEPANEL_INSTALL_APP'])
    config=Path(env['LIVEPANEL_CONFIG_DIR']).expanduser().absolute();bindir=Path(env['LIVEPANEL_BIN_DIR']).expanduser().absolute()
    shell=env['LIVEPANEL_INSTALL_SHELL'];stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    old_manifest = json.loads((app/'install-manifest.json').read_text()) if (app/'install-manifest.json').exists() else {}
    existing_settings = (config/'settings.toml').exists()
    app.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.livepanel-aio-install-',dir=app.parent))
    try:
        for directory in ('app','config','logos','fonts','docs'):
            shutil.copytree(src/directory,stage/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in ('requirements.txt','tmux.conf','LICENSE','README.md','install.sh','uninstall.sh'):
            shutil.copy2(src/name,stage/name)
        (stage/'bin').mkdir()
        # Keep previously downloaded helper tools on upgrade.
        if (app/'bin').is_dir():shutil.copytree(app/'bin',stage/'bin',dirs_exist_ok=True)
        os.environ['PATH']=str(stage/'bin')+os.pathsep+env.get('PATH','')
        tools=('tmux',shell,'playerctl','jq','bc','curl','fc-cache','rsvg-convert')
        missing=[x for x in tools if not shutil.which(x)]
        if missing:raise RuntimeError('Missing dependencies: '+', '.join(missing)+'. Install them or rerun without --no-deps.')
        if env['LIVEPANEL_INSTALL_DEPS']=='1':
            if not shutil.which('starship'):
                script=stage/'starship-install.sh';download('https://starship.rs/install.sh',script)
                subprocess.run(['sh',str(script),'--yes','--bin-dir',str(stage/'bin')],check=True)
                script.unlink()
            if not shutil.which('fastfetch'):
                arch={'x86_64':'amd64','aarch64':'aarch64'}.get(os.uname().machine)
                if not arch:raise RuntimeError('Install Fastfetch for your CPU architecture and rerun.')
                archive=stage/'fastfetch.tar.gz'
                download(f'https://github.com/fastfetch-cli/fastfetch/releases/download/2.70.0/fastfetch-linux-{arch}.tar.gz',archive)
                dest=stage/'download';dest.mkdir();unpack(archive,dest)
                binaries=[p for p in dest.rglob('fastfetch') if p.is_file()]
                if len(binaries)!=1:raise RuntimeError('Unexpected Fastfetch release archive layout')
                shutil.copy2(binaries[0],stage/'bin/fastfetch');archive.unlink();shutil.rmtree(dest)
            if not shutil.which('ansiweather'):
                download('https://raw.githubusercontent.com/fcambus/ansiweather/1.19.0/ansiweather',stage/'bin/ansiweather')
                (stage/'bin/ansiweather').chmod(0o755)
                download('https://raw.githubusercontent.com/fcambus/ansiweather/1.19.0/LICENSE',stage/'bin/ANSIWEATHER-LICENSE')
        for name in ('fastfetch','starship','ansiweather'):
            if not shutil.which(name):raise RuntimeError('Missing '+name+'. Rerun without --no-deps or install it first.')
        # Build in staging. Venv is relocated below; only its Python executable is used.
        subprocess.run(['python3','-m','venv',str(stage/'.venv')],check=True)
        py=stage/'.venv/bin/python'
        subprocess.run([str(py),'-m','pip','install','-r',str(stage/'requirements.txt')],check=True)
        subprocess.run([str(py),'-m','compileall','-q',str(stage/'app')],check=True)
        # All downloads and validation succeeded before changing the installed app.
        previous=app.with_name(app.name+'.bak-'+stamp)
        if app.exists():app.rename(previous)
        try:stage.rename(app)
        except BaseException:
            if previous.exists():previous.rename(app)
            raise
        config.mkdir(parents=True,exist_ok=True)
        for path in (app/'config').iterdir():
            dest=config/path.name
            if dest.exists():shutil.copy2(path,dest.with_name(dest.name+'.example'))
            else:shutil.copy2(path,dest)
        logos=config/'logos';logos.mkdir(exist_ok=True)
        for path in (app/'logos').iterdir():
            if not (logos/path.name).exists():shutil.copy2(path,logos/path.name)
        settings=config/'settings.toml'
        # First-install options; upgrades preserve existing settings.
        if not existing_settings:
            text=settings.read_text().replace('shell = "fish"','shell = '+json.dumps(shell))
            location=env['LIVEPANEL_INSTALL_LOCATION']
            if location:text=text.replace('location = "London,GB"','location = '+json.dumps(location))
            settings.write_text(text)
        bindir.mkdir(parents=True,exist_ok=True)
        launcher=bindir/'livepanel-aio'
        backup(launcher,stamp)
        launcher.write_text('#!/bin/sh\n# Livepanel AIO managed launcher\nexport LIVEPANEL_CONFIG_DIR='+shlex.quote(str(config))+'\nexec '+shlex.quote(str(app/'.venv/bin/python'))+' '+shlex.quote(str(app/'app/cli.py'))+' "$@"\n')
        launcher.chmod(0o755)
        font_path=old_manifest.get('font')
        if env['LIVEPANEL_INSTALL_FONT']=='1':
            font_dir=Path(env.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'fonts/livepanel-aio'
            font_dir.mkdir(parents=True,exist_ok=True)
            font_path=font_dir/'DroidCachyNerd-Regular.otf'
            backup(font_path,stamp);shutil.copy2(app/'fonts/DroidCachyNerd-Regular.otf',font_path)
            subprocess.run(['fc-cache','-f',str(font_dir)],check=True)
        shell = tomllib.loads(settings.read_text())['shell']
        integration=list(old_manifest.get('integration', []))
        if env['LIVEPANEL_INSTALL_AUTOSTART']=='1':
            if shell=='fish':
                rc=Path(env.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'fish/conf.d/livepanel-aio.fish'
                text='''# Livepanel AIO autostart
if status is-interactive; and not set -q TMUX; and not set -q LIVEPANEL; and not set -q SSH_CONNECTION
    %s
end
''' % shlex.quote(str(launcher))
                rc.parent.mkdir(parents=True,exist_ok=True);backup(rc,stamp);rc.write_text(text);integration.append(str(rc)) if str(rc) not in integration else None
            else:
                rc=Path.home()/'.bashrc' if shell=='bash' else Path(env.get('ZDOTDIR', str(Path.home())))/'.zshrc'
                rc.parent.mkdir(parents=True,exist_ok=True)
                original=rc.read_text() if rc.exists() else ''
                if '# BEGIN LIVEPANEL AIO' not in original:
                    backup(rc,stamp)
                    rc.write_text(original+'\n# BEGIN LIVEPANEL AIO\nif [[ $- == *i* && -z ${TMUX-} && -z ${LIVEPANEL-} && -z ${SSH_CONNECTION-} ]]; then\n    '+shlex.quote(str(launcher))+'\nfi\n# END LIVEPANEL AIO\n')
                integration.append(str(rc)) if str(rc) not in integration else None
        manifest={'app':str(app),'config':str(config),'launcher':str(launcher),'font':str(font_path) if font_path else None,'integration':integration}
        (app/'install-manifest.json').write_text(json.dumps(manifest,indent=2))
        print('\nInstalled. Run: '+str(launcher))
        print('Choose "DroidSansMono Cachy Nerd Font" in your terminal font settings.')
        print('Your legacy Livepanel, fff and global Starship configuration were not changed.')
        if not shutil.which('tuptime'):print('Odometer: install tuptime to track lifetime uptime; other panels work without it.')
    finally:
        if stage.exists():shutil.rmtree(stage)
if __name__=='__main__':main()
