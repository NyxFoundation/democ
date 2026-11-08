#!/usr/bin/env python3
"""Acquire CC0 source assets, inspect them in Blender and build a local asset shelf."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
from urllib.parse import quote
from zipfile import ZipFile

import yaml
from library_assets import REGISTRY, acquire_assets

ROOT = REGISTRY.parents[2]


def unpack_material(path):
    """Keep the original archive and unpack maps beside it for direct Blender use."""
    destination = path.with_suffix('')
    with ZipFile(path) as archive:
        for member in archive.infolist():
            target = destination / member.filename
            if (not target.resolve().is_relative_to(destination.resolve()) or
                    (member.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError(f'Unsafe archive member: {member.filename}')
        if archive.testzip():
            raise ValueError(f'Corrupt material archive: {path}')
        archive.extractall(destination)
    hashes = {str(p.relative_to(destination)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in destination.rglob('*') if p.is_file()}
    path.with_suffix('.unpacked.json').write_text(json.dumps(hashes, indent=2))


def inspect_model(name, asset, args, registry):
    work = args.out / 'materials' / name
    preview = work / 'frames/review-0001.png'
    if preview.exists() and (work / 'asset-inspect.blend').exists() and not args.force:
        return
    paths = acquire_assets([name, 'studio-small-05'], args.out)
    work.mkdir(parents=True, exist_ok=True)
    config = {'model_path': str(paths[name]), 'hdri_path': str(paths['studio-small-05']),
              'hdri_strength': .25,
              'asset_sources': {key: registry[key] for key in paths}}
    config.update(asset.get('inspection', {}))
    config_path = work / 'config.json'
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2))
    with (work / 'render.log').open('w') as log:
        subprocess.run(['blender', '-b', '-t', str(args.threads), '-P',
                        str(ROOT / 'templates/library/hardware.py'), '--',
                        '--preset', 'asset-inspect', '--out', str(work / 'frames'),
                        '--engine', 'cycles', '--samples', str(args.samples),
                        '--config', str(config_path), '--frames', '1'],
                       check=True, stdout=log, stderr=subprocess.STDOUT)
    print(f'inspected {name}', flush=True)


def gallery(registry, args):
    shelf = args.out / 'materials'
    shelf.mkdir(parents=True, exist_ok=True)
    cards = {'reviewed': [], 'secondary': []}
    extras = []
    escape = html.escape
    for name, asset in registry.items():
        if asset.get('license') != 'CC0':
            continue
        source = args.out / 'assets' / asset['filename']
        if not source.is_file():
            continue
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if asset.get('sha256') and digest != asset['sha256']:
            raise ValueError(f'Asset checksum mismatch: {name}')
        title = escape(asset.get('title', name))
        original = '../assets/' + quote(asset['filename'])
        links = (f'<a href="{escape(asset["page"], quote=True)}">配布元</a>'
                 f'<a href="{original}">元ファイル</a>')
        if asset['role'] != 'model':
            if asset['role'] == 'pbr-material':
                projects = sorted(source.with_suffix('').glob('*.blend'))
                if projects:
                    project = '../assets/' + quote(str(projects[0].relative_to(args.out / 'assets')))
                    links += f'<a href="{project}">Blender</a>'
            extras.append(f'<li><span>{title}</span><nav>{links}</nav></li>')
            continue
        folder = shelf / name
        if not (folder / 'frames/review-0001.png').is_file() or not (folder / 'asset-inspect.blend').is_file():
            continue
        section = 'secondary' if asset.get('quality_status') == 'secondary' else 'reviewed'
        cards[section].append(
            f'<article><img src="{name}/frames/review-0001.png" alt="{title}" loading="lazy">'
            f'<div><h2>{title}</h2><nav>{links}'
            f'<a href="{name}/asset-inspect.blend">Blender</a></nav></div></article>')
    template = (ROOT / 'templates/library/materials.html').read_text()
    for marker, value in {'__REVIEWED__': ''.join(cards['reviewed']),
                          '__SECONDARY__': ''.join(cards['secondary']),
                          '__EXTRAS__': ''.join(extras)}.items():
        template = template.replace(marker, value)
    (shelf / 'index.html').write_text(template)
    print(shelf / 'index.html')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'fetch', 'inspect', 'catalog', 'all'])
    parser.add_argument('--id', action='append', help='CC0 asset id; repeatable. Default: all CC0 assets.')
    parser.add_argument('--out', type=Path, default=ROOT / 'out/template-library')
    parser.add_argument('--force', action='store_true', help='Repeat Blender inspection')
    parser.add_argument('--threads', type=int, default=8)
    parser.add_argument('--samples', type=int, default=24)
    args = parser.parse_args()
    args.out = args.out.resolve()
    if min(args.threads, args.samples) < 1:
        parser.error('Threads and samples must be positive')
    registry = yaml.safe_load(REGISTRY.read_text())['assets']
    free = {name: asset for name, asset in registry.items() if asset.get('license') == 'CC0'}
    if args.id and set(args.id) - free.keys():
        parser.error('Unknown CC0 asset id')
    selected = {name: asset for name, asset in free.items() if not args.id or name in args.id}
    if args.command == 'list':
        for name, asset in selected.items():
            print(f'{name:35} {asset["role"]:12} {asset.get("quality_status", "")}')
    if args.command in ('fetch', 'all'):
        paths = acquire_assets(selected, args.out)
        for name, path in paths.items():
            if selected[name]['role'] == 'pbr-material' and path.suffix == '.zip':
                unpack_material(path)
        print(f'cached {len(paths)} CC0 assets with dependency maps and SHA-256 records')
    if args.command in ('inspect', 'all'):
        for name, asset in selected.items():
            if asset['role'] == 'model':
                inspect_model(name, asset, args, registry)
    if args.command in ('catalog', 'all'):
        gallery(registry, args)


if __name__ == '__main__':
    main()
