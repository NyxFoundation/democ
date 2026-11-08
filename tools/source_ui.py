"""Build pinned upstream UI libraries into an offline, self-contained demo page."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'templates/library/source-ui'


def assets():
    inputs = sorted(p for p in SOURCE.rglob('*') if p.is_file() and 'node_modules' not in p.parts)
    digest = hashlib.sha256(b''.join(str(p.relative_to(SOURCE)).encode() + p.read_bytes()
                                     for p in inputs)).hexdigest()
    work = ROOT / 'out/source-ui'
    work.mkdir(parents=True, exist_ok=True)
    stamp = work / 'signature'
    bundle = work / 'upstream.js'
    worker = work / 'editor.worker.js'
    if not stamp.exists() or stamp.read_text() != digest or not bundle.exists() or not worker.exists():
        lock = hashlib.sha256((SOURCE / 'package-lock.json').read_bytes()).hexdigest()
        installed = work / 'installed.signature'
        if not installed.exists() or installed.read_text() != lock or not (SOURCE / 'node_modules/.package-lock.json').is_file():
            subprocess.run(['npm', 'ci', '--prefix', str(SOURCE), '--ignore-scripts'], check=True)
            installed.write_text(lock)
        subprocess.run([str(SOURCE / 'node_modules/.bin/esbuild'), str(SOURCE / 'entry.js'),
                        '--bundle', '--format=iife', '--minify', '--legal-comments=inline',
                        '--log-override:duplicate-object-key=silent',
                        '--loader:.ttf=dataurl', '--outfile=' + str(bundle)], check=True)
        subprocess.run([str(SOURCE / 'node_modules/.bin/esbuild'),
                        str(SOURCE / 'node_modules/monaco-editor/esm/vs/editor/editor.worker.js'),
                        '--bundle', '--format=iife', '--minify', '--legal-comments=inline',
                        '--outfile=' + str(worker)], check=True)
        stamp.write_text(digest)
    from library_assets import acquire_assets
    font = acquire_assets(['jetbrains-mono'], ROOT / 'out/template-library')['jetbrains-mono']
    face = '@font-face{font-family:"JetBrains Mono";font-style:normal;font-weight:400;src:url(data:font/woff2;base64,' + base64.b64encode(font.read_bytes()).decode() + ') format("woff2");}'
    css = face + (work / 'upstream.css').read_text() + '\n' + (SOURCE / 'vscode/chat.css').read_text()
    # </script> inside vendored strings must not terminate an embedded HTML script.
    worker_code = json.dumps(worker.read_text()).replace('</script', '<\\/script')
    js = ('globalThis.MonacoEnvironment={getWorker:()=>new Worker(URL.createObjectURL('
          'new Blob([' + worker_code + '],{type:"application/javascript"})))};\n')
    js += bundle.read_text().replace('</script', '<\\/script')
    notices = list(SOURCE.glob('**/LICENSE.txt'))
    notices = [p for p in notices if 'node_modules' not in p.parts]
    notices.append(SOURCE / 'font-OFL.txt')
    for name in ['monaco-editor', '@xterm/xterm', '@vscode/codicons', 'lightweight-charts',
                 '@primer/primitives', 'chroma-js', 'dompurify', 'marked', 'fancy-canvas']:
        notices.extend(p for p in (SOURCE / 'node_modules' / name).glob('LICENSE*') if p.is_file())
        notices.extend(p for p in (SOURCE / 'node_modules' / name).glob('NOTICE*') if p.is_file())
    notices.extend((SOURCE / 'node_modules/monaco-editor').glob('ThirdPartyNotices.txt'))
    js += '\n/* Upstream notices retained with this offline copy.\n' + '\n'.join(
        p.read_text().replace('*/', '* /') for p in notices) + '\n*/'
    return css, js
