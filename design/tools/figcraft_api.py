#!/usr/bin/env python3
"""Build the editable G6 proposal using FigCraft's real command API.

Uses FigCraft's task-lived, headless CLI MCP server for exact native edits.
Live prototype verification is a separate owned GUI session.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLORS = {
    'canvas': '#F7F8FA', 'surface': '#FFFFFF', 'ink': '#202939',
    'secondary': '#586476', 'border': '#DBE1EA', 'controlBorder': '#8491A5', 'action': '#315DF5',
    'subtle': '#EEF2FF', 'success': '#246344', 'successSurface': '#EDF8F0',
    'warning': '#80510B', 'warningSurface': '#FFF4DC',
    'error': '#A83138', 'errorSurface': '#FCECEE', 'focus': '#2453DB',
}



class HeadlessSession:
    """Adapt the documented run_command tool to the builder's engine calls."""
    def __enter__(self):
        (ROOT/'.work').mkdir(exist_ok=True)
        self.log = (ROOT/'.work'/'figcraft-headless.log').open('w')
        self.p = subprocess.Popen(['figcraft-cli', 'mcp'], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=self.log, text=True)
        self.counter = 0
        self.rpc('initialize', {'protocolVersion':'2024-11-05', 'capabilities':{},
                               'clientInfo':{'name':'G6-design-builder','version':'1'}})
        self.p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n')
        self.p.stdin.flush()
        return self

    def rpc(self, method, params):
        self.counter += 1
        self.p.stdin.write(json.dumps({'jsonrpc':'2.0','id':self.counter,
                                      'method':method,'params':params})+'\n')
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError('FigCraft CLI closed; inspect design/.work/figcraft-headless.log')
            result = json.loads(line)
            if result.get('id') == self.counter:
                if 'error' in result:
                    raise RuntimeError(result['error'])
                return result['result']

    def call(self, method, params):
        assert method == 'engine.execute'
        result = self.rpc('tools/call', {'name':'run_command','arguments':params})
        if result.get('isError'):
            raise RuntimeError(result)
        return json.loads(next(c['text'] for c in result['content'] if c['type']=='text'))

    def __exit__(self, *_):
        self.p.stdin.close()
        self.p.terminate()
        self.p.wait(timeout=5)
        self.log.close()


class Builder:
    def __init__(self, session):
        self.s = session
        self.frames, self.links, self.nav, self.variables, self.buttons = {}, [], [], {}, {}

    def cmd(self, command, **params):
        return self.s.call('engine.execute', {'command': command, 'params': params})

    def set(self, node, **props):
        self.cmd('node.set', ids=[node], props=props)

    def layer(self, parent, x, y, w, h, fill='surface', name='Panel', radius=0, stroke=None, kind='frame'):
        props = {'fill': COLORS.get(fill, fill), 'cornerRadius': radius}
        if stroke:
            props.update(stroke=COLORS.get(stroke, stroke), strokeWeight=1)
        node = self.cmd('node.create', type=kind, parent=parent, x=x, y=y,
                        width=w, height=h, name=name, props=props, select=False)['id']
        if fill in self.variables:
            self.cmd('variable.bind', ids=[node], field='fill', variable=self.variables[fill])
        return node

    def text(self, parent, x, y, w, content, size=16, color='ink', align='right', height=36, bold=False):
        # Keep Latin identifiers and time ranges readable within Arabic runs.
        display = re.sub(r'[A-Za-z0-9]+(?:[ :/._–-][A-Za-z0-9]+)*',
                         lambda m: '\u2066'+m.group(0)+'\u2069', content)
        node = self.cmd('node.create', type='text', parent=parent, x=x, y=y,
                        width=w, height=height, text=display, name=content.replace('\n', ' ')[:70],
                        props={'fontFamily': 'Noto Sans Arabic', 'fontStyle': 'Bold' if bold else 'Regular',
                               'fontSize': size, 'textAlign': align, 'textAutoResize': 'none',
                               'lineHeight': size * 1.65, 'fill': COLORS.get(color, color)}, select=False)['id']
        # Text creation measures the default font first; apply the final fixed box explicitly.
        self.set(node, width=w, height=height, textAutoResize='none')
        if color in self.variables:
            self.cmd('variable.bind', ids=[node], field='fill', variable=self.variables[color])
        return node

    def chip(self, parent, x, y, label, state='subtle', w=112):
        fg = {'warningSurface': 'warning', 'errorSurface': 'error'}.get(state, 'action')
        n = self.layer(parent, x, y, w, 32, state, name='Status / ' + label, radius=6)
        self.text(n, 6, 2, w-12, label, 12, fg, 'center', 28)
        return n

    def button(self, parent, x, y, label, dest=None, variant='primary'):
        n = self.cmd('instance.create', component=self.buttons[variant], parent=parent, x=x, y=y)['id']
        self.cmd('instance.setProperties', ids=[n], properties={'Label': label})
        self.set(n, name='Action / ' + label)
        if dest:
            self.links.append((n, dest, label))
        return n

    def card(self, parent, x, y, w, h, title=None):
        n = self.layer(parent, x, y, w, h, name=title or 'Card', radius=12, stroke='border')
        if title:
            self.text(n, 20, 16, w-40, title, 18, bold=True)
        return n

    def field(self, parent, x, y, w, label, value):
        self.text(parent, x, y, w, label, 13, 'secondary', height=28)
        n = self.layer(parent, x, y+32, w, 48, radius=8, stroke='border', name='Field / ' + label)
        self.text(n, 12, 7, w-24, value, 15, height=34)
        return n

    def notice(self, parent, y, label, detail, state='warningSurface', x=32, w=1132):
        n = self.layer(parent, x, y, w, 88, state, name='Notice / ' + label, radius=8)
        color = 'error' if state == 'errorSurface' else 'warning' if state == 'warningSurface' else 'action'
        self.text(n, 20, 9, w-40, label, 16, color, bold=True)
        self.text(n, 20, 42, w-40, detail, 13, color)
        return n

    def table(self, parent, x, y, columns, rows, rowheight=64):
        """columns are (label, width) in RTL reading order."""
        width = sum(c[1] for c in columns)
        n = self.layer(parent, x, y, width, 48+len(rows)*rowheight,
                       name='Table / ' + columns[0][0], stroke='border', radius=8)
        self.layer(n, 0, 0, width, 48, 'subtle', name='Table header')
        edge = width
        for label, cw in columns:
            edge -= cw
            self.text(n, edge+12, 7, cw-24, label, 13, 'secondary', height=34, bold=True)
        for ri, row in enumerate(rows):
            top = 48+ri*rowheight
            if ri % 2:
                self.layer(n, 1, top, width-2, rowheight, 'canvas', name='Alternating row')
            edge = width
            for value, (_, cw) in zip(row, columns):
                edge -= cw
                self.text(n, edge+12, top+12, cw-24, value, 14, height=rowheight-12)
        return n
