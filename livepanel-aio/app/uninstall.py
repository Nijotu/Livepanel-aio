import argparse,json,re,shutil
from pathlib import Path
p=argparse.ArgumentParser(description='Remove Livepanel AIO; keep configs unless --purge-config is specified.')
p.add_argument('--purge-config',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parent.parent
manifest=root/'install-manifest.json'
if not manifest.exists():raise SystemExit('Run uninstall.sh from the installed app directory, not the downloaded source.')
m=json.loads(manifest.read_text())
if a.purge_config and Path(m['config']).name!='livepanel-aio':
 raise SystemExit('Custom config path: remove it manually if desired.')
launcher=Path(m['launcher'])
if launcher.exists() and '# Livepanel AIO managed launcher' in launcher.read_text():launcher.unlink()
for name in m['integration']:
 f=Path(name)
 if not f.exists():continue
 text=f.read_text()
 if f.name=='livepanel-aio.fish' and text.startswith('# Livepanel AIO autostart'):f.unlink()
 else:f.write_text(re.sub(r'\n# BEGIN LIVEPANEL AIO\n.*?# END LIVEPANEL AIO\n','\n',text,flags=re.S))
if a.purge_config:
 config=Path(m['config'])
 if config.name!='livepanel-aio':raise SystemExit('Custom config path: remove it manually if desired.')
 shutil.rmtree(config,ignore_errors=True)
# Font kept: other terminal sessions may still be configured to use it.
shutil.rmtree(root)
print('Removed Livepanel AIO. System dependencies and the installed font were kept.')
