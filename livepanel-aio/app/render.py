"""Fastfetch command helper: render cached values without probing the system."""
import argparse
import json
import os
import unicodedata
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box
from common import theme

def clean(value):
    return ' '.join(''.join(c for c in str(value) if unicodedata.category(c) not in ('Cc','Cf','Cs') or c in '\n\t').split())

def card(entries, color, label_width=None):
    t=theme(); c=t['colors']
    labels=Table(box=box.ROUNDED,show_header=False,expand=True,padding=(0,1),
                 style=f"on {c['label']}",border_style=f"{c['border']} on {c['label']}")
    labels.add_column(no_wrap=True,overflow='ellipsis',style=f"{color} on {c['label']}")
    values=Table(box=box.ROUNDED,show_header=False,expand=True,padding=(0,1),
                 style=f"on {c['value']}",border_style=f"{c['border']} on {c['value']}")
    values.add_column(no_wrap=True,overflow='ellipsis',style=f"{c['text']} on {c['value']}")
    for label,value in entries:
        labels.add_row(Text(clean(label)))
        values.add_row(Text(clean(value)))
    grid=Table.grid(expand=True,padding=0)
    grid.add_column(width=(label_width or t['label_width'])+4)
    grid.add_column(ratio=1)
    grid.add_row(labels,values)
    return grid

def build(mode, groups, data, width):
    c=theme()['colors']
    if mode=='rows':
        entries=[]
        for name in groups:
            if name=='playing': entries.append(('Playing',data.get('playing','Nothing playing')))
            elif name in ('weather','forecast'):
                if not data.get('weather_enabled',True):continue
                entries.append((data.get(name+'_label',name.title()),data.get(name,'Loading…')))
            else: entries.append((name,data.get(name,'—')))
        if data.get('weather_note'):entries.append(('Weather status',data['weather_note']))
        if not entries:return Text('')
        lw=min(max(Text(clean(x[0])).cell_len for x in entries), max(8,width//3-4))
        return card(entries,c['cyan'],lw)
    cards=[]
    for spec,color in zip(groups,[c['green'],c['mint'],c['cyan']]*10):
        entries=[]
        for token in spec.split(','):
            label,sep,key=token.partition('=')
            if not sep:key=label
            entries.append((label,data.get(key,'—')))
        cards.append(card(entries,color))
    if width<95:
        from rich.console import Group
        return Group(*cards)
    grid=Table.grid(expand=True,padding=(0,theme()['group_gap']))
    for _ in cards:grid.add_column(ratio=1)
    grid.add_row(*cards)
    return grid

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['columns','rows']);p.add_argument('groups',nargs='+');a=p.parse_args()
    data=json.loads(Path(os.environ['LIVEPANEL_SNAPSHOT']).read_text())
    width=int(os.environ.get('LIVEPANEL_WIDTH','120'))
    console=Console(width=width,height=100,force_terminal=True,color_system='truecolor',highlight=False, no_color=False)
    console.print(build(a.mode,a.groups,data,width))
if __name__=='__main__':main()
