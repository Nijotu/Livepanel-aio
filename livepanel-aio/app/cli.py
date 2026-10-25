#!/usr/bin/env python3
"""Livepanel AIO: one entry point, independent of the legacy installation."""
import argparse
import asyncio
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from rich.cells import cell_len
from common import ROOT, CONFIG, path_for, settings, theme, resolved, atomic_json, compile_fetch, compile_prompt

ANSI = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

def tmux(socket, *args, check=True):
    r=subprocess.run(['tmux','-L',socket,*args],text=True,capture_output=True,timeout=5)
    if check and r.returncode: raise RuntimeError(r.stderr.strip() or 'tmux failed')
    return r.stdout.strip()

def terminal_name():
    term=os.environ.get('TERM_PROGRAM','').lower()
    if 'ghostty' in term or os.environ.get('GHOSTTY_RESOURCES_DIR'):return 'ghostty'
    if os.environ.get('KITTY_WINDOW_ID'):return 'kitty'
    return term

def environment(run):
    os.environ.update(LIVEPANEL='1', LIVEPANEL_APP=str(ROOT/'app'),
                      LIVEPANEL_PYTHON=sys.executable, LIVEPANEL_SNAPSHOT=str(run/'snapshot.json'),
                      LIVEPANEL_RUN=str(run), STARSHIP_CONFIG=str(run/'prompt.toml'))
    os.environ['PATH']=str(ROOT/'bin')+os.pathsep+os.environ.get('PATH','')

def prepare(run, custom=None):
    environment(run)
    source=resolved(custom or settings()['static_config'])
    if not source.exists() and not custom:source=path_for(settings()['static_config'])
    compile_fetch(source,run/'static.jsonc')
    compile_fetch(path_for('dynamic.jsonc'),run/'dynamic.jsonc',dynamic=True)
    compile_prompt(run/'prompt.toml')

def shell_start(run):
    for _ in range(100):
        if (run/'session.json').exists():break
        time.sleep(.05)
    meta=json.loads((run/'session.json').read_text()); socket=meta['socket']
    environment(run)
    # Wait for a real client, so image placement has terminal pixel geometry.
    for _ in range(100):
        if tmux(socket,'list-clients','-F','#{client_tty}',check=False):break
        time.sleep(.05)
    shell=meta['shell']
    fastfetch=shutil.which('fastfetch')
    if shell=='fish':
        script='''function fish_greeting; end
clear
command fastfetch --config "$LIVEPANEL_RUN/static.jsonc"
command starship init fish | source
'''
        os.execvp('fish',['fish','-i','-C',script])
    if shell=='bash':
        script=run/'bashrc'
        script.write_text('''[ ! -f "$HOME/.bashrc" ] || source "$HOME/.bashrc"
clear
command fastfetch --config "$LIVEPANEL_RUN/static.jsonc"
eval "$(command starship init bash)"
''')
        os.execvp('bash',['bash','--rcfile',str(script),'-i'])
    # Load the normal zsh config before initializing this session's prompt.
    old=os.environ.get('ZDOTDIR',str(Path.home()))
    script=run/'.zshrc'
    script.write_text('ZDOTDIR='+shlex.quote(old)+'\n'+'''[[ ! -f "$ZDOTDIR/.zshrc" ]] || source "$ZDOTDIR/.zshrc"
clear
command fastfetch --config "$LIVEPANEL_RUN/static.jsonc"
eval "$(command starship init zsh)"
''')
    os.environ['ZDOTDIR']=str(run)
    os.execvp('zsh',['zsh','-i'])

def frame_height(frame, width):
    return sum(max(1,math.ceil(cell_len(ANSI.sub('',line))/max(width,1))) for line in frame.rstrip('\n').split('\n'))

async def panel(run):
    from collector import Dashboard
    import sources
    meta=json.loads((run/'session.json').read_text());socket=meta['socket']
    environment(run)
    d=Dashboard();d.start()
    stop=asyncio.Event();loop=asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGUSR1,d.refresh_weather.set)
    for sig in (signal.SIGTERM,signal.SIGHUP,signal.SIGINT):loop.add_signal_handler(sig,stop.set)
    print('\033[?25l\033[2J',end='',flush=True)
    last_height=None
    try:
        while not stop.is_set():
            panes=await asyncio.to_thread(tmux,socket,'list-panes','-F','#{pane_id}',check=False)
            if meta['bottom'] not in panes.splitlines():break
            size=shutil.get_terminal_size((120,40))
            os.environ['LIVEPANEL_WIDTH']=str(size.columns)
            atomic_json(run/'snapshot.json',d.snapshot())
            result=await sources.run('fastfetch','--config',str(run/'dynamic.jsonc'),timeout=8)
            frame=result.stdout.rstrip('\n') if result.code==0 else 'Livepanel config error: '+result.error
            if not frame:frame='No dynamic modules configured.'
            # Measure actual output, including custom modules, not a hardcoded pane height.
            total=await asyncio.to_thread(tmux,socket,'display-message','-p','#{window_height}',check=False)
            window_height=int(total) if total.isdigit() else size.lines+10
            desired=meta['height']
            if desired=='auto':desired=frame_height(frame,size.columns)+1
            desired=max(5,min(int(desired),max(5,window_height-9)))
            if desired!=last_height:
                await asyncio.to_thread(tmux,socket,'resize-pane','-t',os.environ['TMUX_PANE'],'-y',str(desired),check=False)
                last_height=desired
            lines=frame.splitlines()
            if len(lines)>desired:
                lines=lines[:desired-1]+['\033[0mPanel clipped: enlarge the terminal or zoom with Ctrl+b z.']
            sys.stdout.write('\033[H'+'\n'.join(lines)+'\033[0m\033[J');sys.stdout.flush()
            try:await asyncio.wait_for(stop.wait(),settings()['refresh_seconds'])
            except asyncio.TimeoutError:pass
    finally:
        await d.close()
        sys.stdout.write('\033[0m\033[?25h');sys.stdout.flush()
        # Only this app's isolated server; never affect the user's other tmux sessions.
        await asyncio.to_thread(tmux,socket,'kill-server',check=False)
        shutil.rmtree(run,ignore_errors=True)

def launch(args):
    config=settings()
    shell=args.shell or config['shell']
    needed=['tmux','fastfetch','starship',shell]
    missing=[name for name in needed if not shutil.which(name)]
    if missing:raise ValueError('Missing '+', '.join(missing)+'. Run bash install.sh first.')
    if os.environ.get('TMUX'):raise ValueError('Start Livepanel outside tmux (open a fresh terminal window).')
    if not sys.stdin.isatty():raise ValueError('Run Livepanel in an interactive terminal.')
    size=shutil.get_terminal_size((120,40))
    if size.lines<20:raise ValueError('Make the terminal at least 20 rows tall.')
    base=Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'livepanel-aio/sessions'
    base.mkdir(parents=True,exist_ok=True,mode=0o700)
    run=Path(tempfile.mkdtemp(prefix='session-',dir=base))
    os.environ['LIVEPANEL_TERMINAL']=terminal_name()
    socket='livepanel-aio-'+secrets.token_hex(8)
    height=args.height or config['height']
    try:
        prepare(run,args.fastfetch)
        if os.environ['LIVEPANEL_TERMINAL'] in ('ghostty', 'kitty') and shutil.which('kitten'):
            try:
                subprocess.run(['kitten','icat','--clear-all'], timeout=3, stderr=subprocess.DEVNULL)
            except (OSError,subprocess.TimeoutExpired):
                pass
        command=[sys.executable,str(ROOT/'app/cli.py'),'_shell','--run',str(run)]
        bottom=tmux(socket,'-f',str(ROOT/'tmux.conf'),'new-session','-d','-P','-F','#{pane_id}',
                    '-s','livepanel','-x',str(size.columns),'-y',str(size.lines),'-c',os.getcwd(),*command)
        atomic_json(run/'session.json',dict(socket=socket,bottom=bottom,shell=shell,height=height))
        tmux(socket,'set-option','-g','mouse','on' if config['mouse'] else 'off')
        color=theme()['divider']
        for option in ('pane-border-style','pane-active-border-style'):
            tmux(socket,'set-option','-g',option,'fg='+color)
        top=tmux(socket,'split-window','-d','-v','-b','-l',str(min(14,size.lines-9)),
                 '-P','-F','#{pane_id}','-t',bottom,sys.executable,str(ROOT/'app/cli.py'),'_panel','--run',str(run))
        tmux(socket,'select-pane','-t',bottom)
        pid=tmux(socket,'display-message','-p','-t',top,'#{pane_pid}')
        if not pid.isdigit():raise RuntimeError('Could not identify dashboard process')
        tmux(socket,'bind-key','w','run-shell','kill -USR1 '+pid)
        tmux(socket,'bind-key','z','resize-pane','-Z','-t',bottom)
        os.execvp('tmux',['tmux','-L',socket,'attach-session','-t','livepanel'])
    except BaseException:
        tmux(socket,'kill-server',check=False)
        shutil.rmtree(run,ignore_errors=True)
        raise

def main():
    p=argparse.ArgumentParser(description='Livepanel AIO: live panels, static fetch and Starship in one setup.')
    p.add_argument('action',nargs='?',default='start',choices=['start','fetch','doctor','config','_shell','_panel'])
    p.add_argument('--height',type=int,help='Override automatic top-pane height')
    p.add_argument('--shell',choices=['fish','bash','zsh'])
    p.add_argument('--fastfetch',help='Use an external Fastfetch config for the static pane')
    p.add_argument('--run',type=Path,help=argparse.SUPPRESS)
    a=p.parse_args()
    os.environ['PATH']=str(ROOT/'bin')+os.pathsep+os.environ.get('PATH','')
    try:
        if a.action=='_shell':shell_start(a.run)
        elif a.action=='_panel':asyncio.run(panel(a.run))
        elif a.action=='config':print(CONFIG)
        elif a.action=='doctor':
            settings();theme()
            for name in ('python3','tmux','fastfetch','starship',settings()['shell'],'ansiweather','playerctl','tuptime','rsvg-convert','kitten'):
                print(f'{name:15} {shutil.which(name) or "not found"}')
            with tempfile.TemporaryDirectory() as temp:
                run=Path(temp);os.environ['LIVEPANEL_TERMINAL']=terminal_name();prepare(run,a.fastfetch)
            print('Configs parsed successfully. Run inside a terminal to test rendering.')
        elif a.action=='fetch':
            with tempfile.TemporaryDirectory() as temp:
                run=Path(temp);os.environ['LIVEPANEL_TERMINAL']=terminal_name();prepare(run,a.fastfetch)
                return subprocess.call(['fastfetch','--config',str(run/'static.jsonc')])
        else:
            if a.height is not None and a.height<5:raise ValueError('--height must be at least 5')
            launch(a)
    except (ValueError,OSError,RuntimeError,KeyError,subprocess.SubprocessError) as e:
        print('Livepanel: '+str(e),file=sys.stderr);return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
