#!/usr/bin/env python3
"""Export small animated README previews and the matching showcase MP4 files."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import re
from pathlib import Path
import shutil
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/demos'


def export(item):
    name = item['id']
    source = ROOT / 'out/template-library/renders' / (name + '.mp4')
    if not source.is_file():
        raise FileNotFoundError(f'{source}: render this template first')
    metadata = json.loads(source.with_suffix('.json').read_text())
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != metadata['sha256']:
        raise ValueError(f'Unverified source movie: {name}')
    preview = OUTPUT / (name + '.gif')
    temporary = preview.with_suffix('.partial.gif')
    try:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source), '-filter_complex',
                        'fps=12,scale=480:300:flags=lanczos,split[a][b];'
                        '[a]palettegen=max_colors=192:stats_mode=diff[p];'
                        '[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle',
                        '-threads', '2', '-loop', '0', str(temporary)], check=True)
        temporary.replace(preview)
    finally:
        temporary.unlink(missing_ok=True)
    shutil.copy2(source, OUTPUT / source.name)
    print(f'{name}: {preview.stat().st_size // 1024} KiB preview', flush=True)
    return {'id': name, 'title': item['title'], 'reference': item['reference']['page'],
            'movie_sha256': digest, 'preview_sha256': hashlib.sha256(preview.read_bytes()).hexdigest()}


def table(items):
    def cell(item):
        name = item['id']
        title = html.escape(item['reference']['brand'])
        code = ('templates/library/quality_scenes.py' if name in {
                    'rim-reveal', 'drone-orbit', 'humanoid-articulation', 'orbital-earth', 'terrain-flyover'} else
                'templates/library/hardware.py' if item['renderer'] == 'blender' else
                'engine/scenes/network-globe.js' if name == 'network-globe' else
                'engine/scenes/source-ui.js' if name in {'terminal-flow','code-diff','market-chart'} else
                'engine/scenes/typography.js' if item.get('scene_type') == 'typography' else
                'engine/scenes/press.js' if item.get('scene_type') == 'press' else
                'engine/scenes/study.js' if item.get('scene_type') == 'study' else
                'engine/scenes/motion.js')
        return (f'**{title}**<br>[<img src="docs/demos/{name}.gif" width="180" '
                f'alt="{html.escape(item["title"], quote=True)}">]'
                f'(docs/demos/{name}.mp4)<br>[MP4](docs/demos/{name}.mp4) · [実装]({code})')
    columns = 4
    rows = ['| ' + ' | '.join([''] * columns) + ' |',
            '| ' + ' | '.join([':---'] * columns) + ' |']
    for n in range(0, len(items), columns):
        cells = [cell(item) for item in items[n:n+columns]]
        rows.append('| ' + ' | '.join(cells + [''] * (columns-len(cells))) + ' |')
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', action='append', help='Only refresh these previews; repeatable')
    args = parser.parse_args()
    items = yaml.safe_load((ROOT / 'templates/library/catalog.yaml').read_text())['templates']
    if args.id and set(args.id) - {i['id'] for i in items}:
        parser.error('Unknown template id')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    selected = [i for i in items if not args.id or i['id'] in args.id]
    with ThreadPoolExecutor(max_workers=2) as pool:
        updates = list(pool.map(export, selected))
    manifest = OUTPUT / 'manifest.json'
    previous = {r['id']: r for r in json.loads(manifest.read_text())} if manifest.exists() else {}
    previous.update({r['id']: r for r in updates})
    manifest.write_text(json.dumps([previous[i['id']] for i in items if i['id'] in previous],
                                   ensure_ascii=False, indent=2) + '\n')
    readme = ROOT / 'README.md'
    start, end = '<!-- demos:start -->', '<!-- demos:end -->'
    before, rest = readme.read_text().split(start, 1)
    _, after = rest.split(end, 1)
    content = before + start + '\n\n' + table(items) + '\n\n' + end + after
    content = re.sub(r'Demos-\d+-', f'Demos-{len(items)}-', content)
    content = re.sub(r'再構成した\d+本', f'再構成した{len(items)}本', content)
    content = re.sub(r'ニュース演出の\d+本', f'ニュース演出の{len(items)}本', content)
    readme.write_text(content)


if __name__ == '__main__':
    main()
