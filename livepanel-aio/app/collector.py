#!/usr/bin/env python3
"""Read-only dashboard; tmux owns the shell below this pane."""
import asyncio
import datetime as dt
from pathlib import Path
import time
from common import settings, path_for, CONFIG
import os

import psutil
from rich.text import Text
import sources as s

CYAN = "\033[38;2;31;191;212m"


class Dashboard:
    def __init__(self, interval=0):
        self.config = settings()
        self.interval = self.config["weather"]["refresh_seconds"]
        self.stop = asyncio.Event()
        self.refresh_weather = asyncio.Event()
        self.weather = Text("Loading ANSIWeather…", style="#1FBFD4")
        self.weather_note = ""
        self.weather_parts = None
        self.birth = 0
        self.anchor = None
        self.odo = self.average = "—"
        self.cpu = "…"
        self.gpu = "…"
        self.vram = "—"
        self.temp = "…"
        self.memory = "…"
        self.swap = "…"
        self.down = self.up = "0 B/s"
        self.ip = "…"
        self.processes = "…"
        self.music = "Checking music…"
        self.progress = ""
        self.previous_net = None
        self.tasks = []

    async def repeat(self, fn, delay):
        while not self.stop.is_set():
            try:
                await fn()
            except (OSError, ValueError, IndexError):
                pass
            try:
                await asyncio.wait_for(self.stop.wait(), delay)
            except asyncio.TimeoutError:
                pass

    async def fast_metrics(self):
        self.processes = str(len(psutil.pids()))
        self.cpu = f"{psutil.cpu_percent():.0f}% · {self.temp}"
        mem, swap = psutil.virtual_memory(), psutil.swap_memory()
        self.memory = f"{mem.used / 2**30:.1f}/{mem.total / 2**30:.1f} GiB ({mem.percent:.0f}%)"
        self.swap = f"{swap.used / 2**30:.1f}/{swap.total / 2**30:.1f} GiB"
        counters = psutil.net_io_counters(pernic=True)
        names = s.default_interfaces() or [n for n in counters if n != "lo" and not n.startswith(("veth", "docker", "br-"))]
        current = {n: counters[n] for n in names if n in counters}
        now = time.monotonic()
        down = up = 0
        if self.previous_net:
            old, at = self.previous_net
            for name in current.keys() & old.keys():
                down += max(0, current[name].bytes_recv - old[name].bytes_recv) / max(.01, now-at)
                up += max(0, current[name].bytes_sent - old[name].bytes_sent) / max(.01, now-at)
        self.previous_net = current, now
        self.down, self.up = s.rate(down), s.rate(up)
        ips = s.local_ips()
        self.ip = ips[0].split(": ",1)[-1] if ips else "offline"

    async def hardware(self):
        self.temp = await asyncio.to_thread(s.cpu_temperature)
        r = await s.run("nvidia-smi", "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits", timeout=3)
        names, values = s.parse_nvidia(r.stdout) if not r.code else ([], [])
        if not values:
            names, values = await asyncio.to_thread(s.amd_gpus)
        if values:
            bits = values[0].split(" • ")
            self.gpu = " · ".join(bits[:2])
            self.vram = bits[2].replace(" VRAM", "") if len(bits)>2 else "—"
        else:
            self.gpu = "readings unavailable"

    async def odometer(self):
        if self.birth == 0:
            birth = (await s.run("stat", "-c", "%W", "/")).stdout.strip()
            self.birth = int(birth) if birth.isdigit() else -1
        baseline = self.config["odometer"]["baseline_seconds"]
        r = await s.run("tuptime", "-sn", c_locale=True)
        tracked = s.parse_tuptime(r.stdout) if r.code == 0 else None
        if tracked is not None:
            self.anchor = int(baseline) + tracked, s.uptime_seconds()
        else:
            self.anchor = None
            self.odo = "tuptime unavailable"
            self.average = "—"

    async def music_update(self):
        players = await s.run("playerctl", "--list-all", timeout=2)
        names = players.stdout.splitlines()
        preferred = self.config["media"]["player"]
        if preferred:
            names = [n for n in names if n == preferred or n.startswith(preferred + ".")]
        if players.code or not names:
            self.music = "Nothing playing" if players.code != 127 else "playerctl unavailable"
            self.progress = ""
            return
        statuses = await asyncio.gather(*(s.run("playerctl", "-p", n, "status", timeout=2) for n in names))
        candidates = [(n,r.stdout.strip()) for n,r in zip(names,statuses) if not r.code]
        if not candidates:
            self.music, self.progress = "Nothing playing", ""
            return
        name, status = next((p for p in candidates if p[1]=="Playing"), candidates[0])
        prefix = ("playerctl", "-p", name)
        meta, pos, total = await asyncio.gather(
            s.run(*prefix,"metadata","--format","{{artist}} — {{title}}",timeout=2),
            s.run(*prefix,"position",timeout=2), s.run(*prefix,"metadata","mpris:length",timeout=2))
        self.music = f"{meta.stdout.strip() or name}" + (" [paused]" if status=="Paused" else "")
        try:
            p,t = max(0,int(float(pos.stdout))), max(0,int(float(total.stdout)/1_000_000))
            self.progress = f"{p//60}:{p%60:02d} / {t//60}:{t%60:02d}"
        except ValueError:
            self.progress = ""

    async def weather_loop(self):
        w = self.config['weather']
        if not w['enabled']:
            return
        os.environ['ANSIWEATHERRC'] = str(path_for('ansiweather.conf'))
        command = ['ansiweather', '-l', w['location'], '-u', w['units'], '-s', 'true', '-a', 'false']
        while not self.stop.is_set():
            self.refresh_weather.clear()
            results = []
            for args in (command, command + ["-f", "3"]):
                results.append(await s.run(*args,timeout=40))
            if any(r.code for r in results):
                self.weather_note = "Weather unavailable / last reading retained · Ctrl+b w retries"
                if self.weather.plain == "Loading ANSIWeather…":
                    self.weather = Text("ANSIWeather unavailable",style="#1FBFD4")
            else:
                self.weather = Text.from_ansi(CYAN + "".join(r.stdout for r in results) + "\033[0m")
                self.weather.rstrip()
                self.weather_parts = [Text.from_ansi(r.stdout).plain.strip() for r in results]
                self.weather_note = ""
            try:
                await asyncio.wait_for(self.refresh_weather.wait(), self.interval or None)
            except asyncio.TimeoutError:
                pass

    def snapshot(self):
        now = time.time()
        age = max(0, int((now-self.birth)//86400)) if self.birth > 0 else None
        if self.anchor:
            total = self.anchor[0] + max(0, s.uptime_seconds()-self.anchor[1])
            self.odo = f"{int(total)//3600:,} h"
            if self.birth > 0 and now > self.birth:
                avg = int(total*86400/(now-self.birth))
                self.average = f"{avg//3600}h {avg%3600//60}m/day"
        location = self.config['weather']['location'].split(',')[0]
        data = {name: getattr(self, name) for name in
                ('cpu','gpu','memory','vram','swap','down','up','ip','processes','average','weather_note')}
        data.update(time=dt.datetime.now().strftime('%H:%M:%S'),
                    date=dt.datetime.now().strftime('%Y-%m-%d'), uptime=s.duration(s.uptime_seconds()),
                    age=f'{age} days' if age is not None else 'unavailable', odometer=self.odo,
                    playing=self.music + ('  ·  '+self.progress if self.progress else ''),
                    weather_enabled=self.config['weather']['enabled'], weather_hint='forecast below',
                    weather_label=f'Weather in {location}', forecast_label=f'{location} forecast',
                    weather=self.weather.plain, forecast='Loading…')
        if self.weather_parts:
            for key,output in zip(('weather','forecast'),self.weather_parts):
                heading,sep,value=' '.join(output.splitlines()).partition(': ')
                data[key]=value if sep else output
                if sep:data[key+'_label']=heading
        return data

    def start(self):
        psutil.cpu_percent()
        self.tasks = [asyncio.create_task(self.repeat(fn, delay)) for fn, delay in
                      ((self.fast_metrics,1),(self.hardware,2),(self.odometer,60),(self.music_update,1))]
        self.tasks.append(asyncio.create_task(self.weather_loop()))

    async def close(self):
        self.stop.set()
        for task in self.tasks: task.cancel()
        await asyncio.gather(*self.tasks,return_exceptions=True)
