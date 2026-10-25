"""Configuration and Fastfetch compilation. No shell evaluation of config values."""
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import json5

ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(os.environ.get('LIVEPANEL_CONFIG_DIR', Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'livepanel-aio')).expanduser()
DEFAULT = ROOT/'config'

def read_json(path):
    with Path(path).open() as f:
        return json5.load(f, allow_duplicate_keys=False)

def path_for(name):
    p = CONFIG/name
    return p if p.exists() else DEFAULT/name

def settings():
    with path_for('settings.toml').open('rb') as f:
        c = tomllib.load(f)
    if c['shell'] not in ('fish', 'bash', 'zsh'):
        raise ValueError('shell must be fish, bash or zsh')
    if not 1 <= c['refresh_seconds'] <= 60:
        raise ValueError('refresh_seconds must be between 1 and 60')
    if c['height'] != 'auto' and (type(c['height']) is not int or c['height'] < 5):
        raise ValueError('height must be "auto" or an integer of at least 5')
    if c['weather']['units'] not in ('metric','imperial'):
        raise ValueError('weather.units must be metric or imperial')
    interval = c['weather']['refresh_seconds']
    if interval != 0 and interval < 60:
        raise ValueError('weather refresh must be 0 or at least 60 seconds')
    return c

def theme():
    c = read_json(path_for('theme.jsonc'))
    for key,value in {**c['colors'], 'divider':c['divider']}.items():
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
            raise ValueError(f'theme color {key} must be #RRGGBB')
    return c

def resolved(value, base=CONFIG):
    p = Path(os.path.expandvars(value)).expanduser()
    return p if p.is_absolute() else base/p

def atomic_json(path, value):
    p = Path(path); tmp = p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False))
    os.replace(tmp,p)

def bg(hex_color):
    return '\033[48;2;'+';'.join(str(int(hex_color[i:i+2],16)) for i in (1,3,5))+'m'

def compile_fetch(source, destination, *, dynamic=False):
    """Pass native Fastfetch options through; expand only opt-in @theme.name tokens."""
    c = copy.deepcopy(read_json(source))
    t = theme(); colors=t['colors']
    tokens={**colors, 'label_bg':bg(colors['label']), 'value_bg':bg(colors['value'])}
    def expand(obj):
        if isinstance(obj,str):
            return re.sub(r'@theme\.([a-z_]+)', lambda m:tokens[m[1]], obj)
        if isinstance(obj,list): return [expand(x) for x in obj]
        if isinstance(obj,dict): return {k:expand(v) for k,v in obj.items()}
        return obj
    c=expand(c)
    logo=c.get('logo',{})
    # Image graphics are supported in the static pane, not the repeatedly repainted pane.
    if dynamic and isinstance(logo,dict) and logo.get('type') in ('kitty','kitty-direct','kitty-icat','sixel','iterm','raw'):
        raise ValueError('Use an ASCII logo or no logo in dynamic.jsonc; put image logos in static.jsonc')
    if isinstance(logo,dict) and logo.get('source','').startswith('@logos/'):
        p=CONFIG/'logos'/logo['source'][7:]
        if not p.exists(): p=ROOT/'logos'/logo['source'][7:]
        if not p.exists(): raise ValueError(f'Logo not found: {p}')
        mode=logo.get('type','auto')
        if mode=='auto':
            terminal=os.environ.get('LIVEPANEL_TERMINAL','')
            mode='kitty-icat' if p.suffix.lower() not in ('.txt','.asc','.ascii') and terminal in ('ghostty','kitty') and shutil.which('kitten') else 'file'
        if mode=='file' and p.suffix.lower() in ('.svg','.png','.jpg','.jpeg','.webp','.gif'):
            p=CONFIG/'logos/live-panel.txt'
            if not p.exists(): p=ROOT/'logos/live-panel.txt'
        elif p.suffix.lower()=='.svg':
            converter=shutil.which('rsvg-convert')
            if not converter: raise ValueError('SVG image mode needs rsvg-convert; use logo.type="file" for ASCII')
            rendered=Path(destination).with_suffix('.logo.png')
            subprocess.run([converter,'-w','640','-o',str(rendered),str(p)],check=True,timeout=10)
            p=rendered
        if mode=='file':
            logo.pop('width',None);logo.pop('height',None)
        logo.update(source=str(p),type=mode)
    atomic_json(destination,c)
    return destination

def compile_prompt(destination):
    # Template uses Starship palette names: external Starship configs work unchanged.
    text=path_for('prompt.toml').read_text()
    colors=theme()['colors']
    if '[palettes.livepanel]' not in text and 'palette = "livepanel"' in text:
        text+='\n[palettes.livepanel]\n'+''.join(f'{k} = "{v}"\n' for k,v in colors.items())
    tomllib.loads(text)
    Path(destination).write_text(text)
