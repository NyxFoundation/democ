#!/usr/bin/env python3
"""Run Gum's upstream demo in a real PTY and save its ANSI output for offline replay."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import termios
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'templates/library/source-ui/gum'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=SOURCE / 'recording.json')
    args = parser.parse_args()
    work = ROOT / 'out/template-library/web-sources/gum-capture'
    binary = work.parent / 'bin/gum'
    work.mkdir(parents=True, exist_ok=True)
    if not binary.exists():
        binary.parent.mkdir(exist_ok=True)
        subprocess.run(['go', 'install', 'github.com/charmbracelet/gum@v0.17.0'],
                       env={**os.environ, 'GOBIN': str(binary.parent)}, check=True)
    original = (SOURCE / 'demo.sh').read_text()
    script = work / 'demo.sh'
    script.write_text(original.replace('#!/bin/bash', '#!/usr/bin/env bash', 1))
    script.chmod(0o755)
    pid, master = pty.fork()
    if pid == 0:
        os.chdir(work)
        env = {**os.environ, 'PATH': str(binary.parent) + ':' + os.environ['PATH'],
               'TERM': 'xterm-256color', 'COLORTERM': 'truecolor', 'CLICOLOR_FORCE': '1',
               'PS1': '\x1b[38;5;63m> \x1b[0m', 'PS2': '', 'HISTFILE': '/dev/null',
               'COLORFGBG': '15;0', 'GUM_INPUT_SHOW_HELP': 'false',
               'GUM_WRITE_SHOW_HELP': 'false', 'GUM_WRITE_PROMPT': '│ ',
               'GUM_INPUT_CURSOR_FOREGROUND': '#00c4a7',
               'GUM_WRITE_CURSOR_FOREGROUND': '#00c4a7'}
        env.pop('NO_COLOR', None)
        os.execvpe('bash', ['bash', '--noprofile', '--norc', '-i'], env)
    fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', 24, 80, 0, 0))
    inputs = [(i * .05 + .08, c) for i, c in enumerate('./demo.sh')]
    inputs += [(.55, '\r')]
    inputs += [(1.42 + i * .05, c) for i, c in enumerate('Walter')]
    inputs += [(2.10, '\r')]
    inputs += [(4.28 + i * .05, c) for i, c in enumerate('Nope, sorry!')]
    inputs += [(5.4, '\x1b\r'), (5.6, '\x1b\r')]
    events = []
    start = time.monotonic()
    try:
        while time.monotonic() - start < 6.05:
            elapsed = time.monotonic() - start
            while inputs and inputs[0][0] <= elapsed:
                _, value = inputs.pop(0)
                os.write(master, value.encode())
            if select.select([master], [], [], .005)[0]:
                data = os.read(master, 65536)
                events.append([round(time.monotonic() - start, 4), data.decode('utf-8', errors='replace')])
                # Answer the same capability/color probes that a terminal answers.
                if b'\x1b]11;?' in data:
                    os.write(master, b'\x1b]11;rgb:1616/1616/1616\x1b\\')
                if b'\x1b]10;?' in data:
                    os.write(master, b'\x1b]10;rgb:dddd/dddd/dddd\x1b\\')
                if b'\x1b[6n' in data:
                    os.write(master, b'\x1b[1;1R')
                if b'\x1b[c' in data:
                    os.write(master, b'\x1b[?1;2c')
    finally:
        os.killpg(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        os.close(master)
    joined = ''.join(data for _, data in events)
    record = {'version': 'gum v0.17.0', 'source': 'https://github.com/charmbracelet/gum/blob/main/examples/demo.sh',
              'source_sha256': hashlib.sha256(original.encode()).hexdigest(),
              'columns': 80, 'rows': 24, 'duration': 6.05, 'events': events}
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2))
    if not all(word in joined for word in ['Hello', 'Welcome', 'secret']):
        raise RuntimeError('Gum did not complete the expected demo states; inspect ' + str(args.output))
    print(f'Captured {len(events)} real PTY events: {args.output}')


if __name__ == '__main__':
    main()
