"""Run with the app venv: python -m unittest discover -s tests -v."""
import asyncio
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import common,render,sources
from cli import frame_height,ANSI
from collector import Dashboard
from rich.console import Console
from rich.cells import cell_len

class Core(unittest.TestCase):
    def test_auto_text_logo_in_image_capable_terminal(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'logos').mkdir()
            for suffix in ('.txt','.asc','.ascii'):
                logo=root/'logos'/('custom'+suffix);logo.write_text('custom logo')
                source=root/'source.json';dest=root/'compiled.json'
                source.write_text(json.dumps({'logo':{'type':'auto','source':'@logos/'+logo.name,'width':36,'height':13}}))
                with patch.object(common,'CONFIG',root), patch.dict(os.environ,{'LIVEPANEL_TERMINAL':'ghostty'}), patch.object(common.shutil,'which',return_value='/mock/kitten'):
                    common.compile_fetch(source,dest)
                result=json.loads(dest.read_text())['logo']
                self.assertEqual(result['type'],'file')
                self.assertEqual(result['source'],str(logo))
                self.assertNotIn('width',result);self.assertNotIn('height',result)
    def test_image_fallback_uses_configured_text_logo(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'logos').mkdir()
            (root/'logos/custom.svg').write_text('<svg/>')
            fallback=root/'logos/live-panel.txt';fallback.write_text('user fallback')
            source=root/'source.json';dest=root/'compiled.json'
            source.write_text(json.dumps({'logo':{'type':'file','source':'@logos/custom.svg','width':36}}))
            with patch.object(common,'CONFIG',root):common.compile_fetch(source,dest)
            self.assertEqual(json.loads(dest.read_text())['logo']['source'],str(fallback))
    def test_boxes_fit_wide_and_narrow_terminals(self):
        data={'time':'12:34:56','uptime':'10d 12h 34m 56s','cpu':'100% · 85°C','memory':'32/64 GiB (50%)','date':'2026-10-18'}
        for width in (80,120,209):
            out=io.StringIO();console=Console(file=out,width=width,height=100,force_terminal=True,color_system='truecolor',no_color=False)
            console.print(render.build('columns',['Time=time,Uptime=uptime','CPU=cpu,RAM=memory','Date=date'],data,width))
            value=out.getvalue()
            self.assertIn('48;2;43;43;69',value)
            self.assertIn('48;2;56;59;78',value)
            self.assertTrue(all(cell_len(ANSI.sub('',line))<=width for line in value.splitlines()))
            self.assertIn('╰',value)
    def test_untrusted_metadata_does_not_execute_terminal_controls(self):
        cleaned=render.clean('\x1b]52;c;payload\x07\ntrack\rtitle\x00')
        self.assertNotIn('\x1b',cleaned);self.assertNotIn('\x07',cleaned);self.assertNotIn('\n',cleaned)
    def test_native_config_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.json';dest=Path(d)/'dest.json'
            data={'logo':{'type':'none'},'modules':[{'type':'cpu','format':'{name}'}]}
            source.write_text(json.dumps(data));common.compile_fetch(source,dest)
            self.assertEqual(data,json.loads(dest.read_text()))
    def test_dynamic_rejects_persistent_image_mode(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.json';source.write_text('{"logo":{"type":"kitty-direct"}}')
            with self.assertRaises(ValueError):common.compile_fetch(source,Path(d)/'out',dynamic=True)
    def test_shared_theme_expands(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'out';common.compile_fetch(common.DEFAULT/'static.jsonc',dest)
            value=dest.read_text();self.assertNotIn('@theme.',value);self.assertIn('16D84D',value)
            common.compile_prompt(Path(d)/'prompt');self.assertIn('[palettes.livepanel]',(Path(d)/'prompt').read_text())
    def test_height_counts_wide_unicode_cells(self):
        self.assertEqual(frame_height('\x1b[31mabcd\x1b[0m\n界界界',4),3)
    def test_weather_headings_are_separate_from_values(self):
        d=Dashboard();d.weather_parts=['Weather in London: 12 °C - Humidity: 90%','London forecast: Sun: 12/8 °C']
        data=d.snapshot();self.assertEqual(data['weather_label'],'Weather in London');self.assertEqual(data['weather'],'12 °C - Humidity: 90%')
        self.assertEqual(data['forecast'],'Sun: 12/8 °C')
    def test_missing_media_tool_is_explained(self):
        async def fake(*args,**kwargs):return sources.Result(code=127)
        async def scenario():
            d=Dashboard()
            with patch.object(sources,'run',fake):await d.music_update()
            self.assertEqual(d.snapshot()['playing'],'playerctl unavailable')
        asyncio.run(scenario())
    def test_tuptime_parsing(self):
        self.assertEqual(sources.parse_tuptime('System uptime: 1,234.5 seconds'),1234)
        self.assertIsNone(sources.parse_tuptime('unavailable'))
        self.assertEqual(sources.parse_tuptime('System uptime: 99.24% = 123456.78'),123456)
        self.assertEqual(sources.parse_tuptime('System uptime: 100.0% = 86400 seconds'),86400)
        self.assertEqual(sources.parse_tuptime('System uptime: 0.0% = 0'),0)
        self.assertIsNone(sources.parse_tuptime('System uptime: 99.24%'))
        self.assertIsNone(sources.parse_tuptime('System uptime: 99.24% = 1d 22h 04m 44s'))
    def test_process_count_reaches_snapshot(self):
        async def scenario():
            d=Dashboard()
            with patch('collector.psutil.pids',return_value=[1,2,3,4]):
                await d.fast_metrics()
            self.assertEqual(d.snapshot()['processes'],'4')
        asyncio.run(scenario())
    def test_odometer_baseline_and_failure(self):
        async def scenario():
            d=Dashboard();d.birth=1
            d.config['odometer']['baseline_seconds']=3600
            async def success(*args,**kwargs):return sources.Result(stdout='System uptime: 95.0% = 7200')
            async def failure(*args,**kwargs):return sources.Result(stdout='System uptime: 95.0% = 7200',code=1)
            with patch.object(sources,'run',success),patch.object(sources,'uptime_seconds',return_value=100):
                await d.odometer()
                self.assertEqual(d.snapshot()['odometer'],'3 h')
            with patch.object(sources,'run',failure):await d.odometer()
            self.assertIsNone(d.anchor)
            self.assertEqual(d.snapshot()['odometer'],'tuptime unavailable')
            self.assertEqual(d.snapshot()['average'],'—')
        asyncio.run(scenario())
if __name__=='__main__':unittest.main()
