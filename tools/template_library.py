#!/usr/bin/env python3
"""Collect public reference excerpts and render original, reusable motion studies."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'templates/library'


def run(command, **kwargs):
    subprocess.run(list(map(str, command)), check=True, **kwargs)


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))


def read_catalog():
    entries = yaml.safe_load((LIBRARY / 'catalog.yaml').read_text())['templates']
    seen = set()
    for item in entries:
        name = item['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or name in seen:
            raise ValueError(f'Invalid or duplicate template id: {name}')
        if item['renderer'] not in ('html', 'blender') or item['duration'] <= 0:
            raise ValueError(f'Invalid renderer/duration: {name}')
        ref = item['reference']
        if not 0 <= ref['start'] < ref['end']:
            raise ValueError(f'Invalid reference timecode: {name}')
        seen.add(name)
    return entries


def collect(item, args):
    """Fetch only the selected time range; metadata records the actual local artifact."""
    ref = item['reference']
    target = args.out / 'references' / (item['id'] + '.mp4')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not args.force:
        print(f'keep {target}')
        return
    source = str(args.source.resolve()) if args.source else ref['asset']
    temporary = target.with_suffix('.partial.mp4')
    try:
        run(['ffmpeg', '-y', '-loglevel', 'error', '-threads', '4',
             '-ss', ref['start'], '-i', source, '-t', ref['end'] - ref['start'],
             '-an', '-vf', 'fps=25,scale=960:600:force_original_aspect_ratio=decrease,'
             'pad=960:600:(ow-iw)/2:(oh-ih)/2:color=0x101116,setsar=1',
             '-c:v', 'libx264', '-threads', '4', '-preset', 'fast', '-crf', '20',
             '-pix_fmt', 'yuv420p', '-movflags', '+faststart', temporary])
        info = probe(temporary)
        duration = float(info['format']['duration'])
        if duration < ref['end'] - ref['start'] - .15:
            raise ValueError(f'{item["id"]}: source ended early ({duration}s)')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    metadata = {
        'reference': ref, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
        'input': source, 'duration': duration,
        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
        'use': 'Local reference excerpt; source rights are not transferred.',
    }
    target.with_suffix('.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f'collected {target}')


def scene(item):
    return {**item.get('parameters', {}), 'type': item.get('scene_type', 'motion'),
            'name': item['title'], 'preset': item['id'], 'duration': item['duration']}


def render_html(item, args, work, frames):
    from build import assemble
    from browser import launch_chromium
    from playwright.sync_api import sync_playwright

    spec = work / 'scene.yaml'
    spec.write_text(yaml.safe_dump({'title': item['title'], 'transition': {'duration': .2},
                                   'scenes': [scene(item)]}, allow_unicode=True))
    pagefile = assemble(spec, work / 'page.html')
    with sync_playwright() as playwright:
        browser = launch_chromium(playwright, headless=True)
        page = browser.new_page(viewport={'width': args.width, 'height': args.height},
                                device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(pagefile.as_uri() + '?rec=1&autoplay=0')
        page.evaluate("document.querySelector('.sc').style.transition='none'")
        page.evaluate('()=>{const s=DEMO.scenes[0];D.Scenes[s.type].drawAt(s,0);D.cls(s.type,"on");}')
        page.evaluate('()=>D.Scenes[DEMO.scenes[0].type].ready||Promise.resolve()')
        page.evaluate('document.fonts.ready')
        count = max(2, round(item['duration'] * args.fps))
        for frame in range(count):
            page.evaluate('(t)=>{const s=DEMO.scenes[0];D.Scenes[s.type].drawAt(s,t);D.cls(s.type,"on");}',
                          frame / args.fps)
            page.screenshot(path=str(frames / f'f{frame+1:04d}.png'))
        browser.close()
        if errors:
            raise RuntimeError('\n'.join(errors))


def render(item, args):
    args = argparse.Namespace(**vars(args))
    args.engine = args.engine or item.get('engine', 'cycles')
    args.samples = args.samples or item.get('samples', 48)
    work = args.out / 'build' / item['id']
    frames = work / 'frames'
    frames.mkdir(parents=True, exist_ok=True)
    target = args.out / 'renders' / (item['id'] + '.mp4')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not args.force:
        print(f'keep {target}; --force to regenerate')
        return
    # A shorter new render must never pick up stale tail frames.
    for old in frames.glob('f*.png'):
        old.unlink()
    from library_assets import acquire_assets
    parameters = dict(item.get('parameters', {}))
    assets = acquire_assets(item.get('assets', []), args.out)
    parameters['asset_sources'] = [json.loads(path.with_suffix(path.suffix + '.json').read_text())
                                   for path in assets.values()]
    for kind in ('model', 'hdri', 'texture', 'terrain', 'clouds'):
        key = kind + '_asset'
        if key in parameters:
            parameters[kind + '_path'] = str(assets[parameters[key]])
    if item['renderer'] == 'html':
        render_html(dict(item, parameters=parameters), args, work, frames)
    else:
        if not shutil.which('blender'):
            raise SystemExit('blender is required; enter nix develop .#full first')
        config = work / 'parameters.json'
        config.write_text(json.dumps(parameters))
        with (work / 'blender.log').open('w') as log:
            run(['blender', '-b', '-t', args.threads, '-P', LIBRARY / 'hardware.py', '--',
                 '--preset', item['id'], '--out', frames, '--config', config,
                 '--duration', item['duration'], '--fps', args.fps,
                 '--width', args.width, '--height', args.height, '--samples', args.samples,
                 '--engine', args.engine],
                stdout=log, stderr=subprocess.STDOUT)
    encode_render(item, args, frames, target)
    print(f'rendered {target}', flush=True)


def encode_render(item, args, frames, target):
    temporary = target.with_suffix('.partial.mp4')
    expected_frames = max(2, round(item['duration'] * args.fps))
    actual_frames = len(list(frames.glob('f[0-9][0-9][0-9][0-9].png')))
    if actual_frames != expected_frames:
        raise ValueError(f'{item["id"]}: expected {expected_frames} frames, got {actual_frames}')
    try:
        run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', args.fps,
             '-i', frames / 'f%04d.png', '-filter_complex',
             f'color=c=black:s={args.width}x{args.height}:r={args.fps},format=rgba[bg];'
             '[bg][0:v]overlay=shortest=1:format=auto:alpha=straight,format=yuv420p[v]',
             '-map', '[v]', '-an', '-c:v', 'libx264', '-threads', '4',
             '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
             '-movflags', '+faststart', temporary])
        duration = float(probe(temporary)['format']['duration'])
        if abs(duration - expected_frames / args.fps) > 1 / args.fps:
            raise ValueError(f'{item["id"]}: render duration mismatch: {duration}s')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    finish_render(item, args, target)


def finish_render(item, args, target):
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', item['duration'] * .82,
         '-i', target, '-frames:v', '1', '-pix_fmt', 'yuvj420p', target.with_suffix('.jpg')])
    metadata = {'rendered_at': datetime.now(timezone.utc).isoformat(),
                'width': args.width, 'height': args.height, 'fps': args.fps,
                'samples': args.samples if item['renderer'] == 'blender' else None,
                'render_engine': args.engine if item['renderer'] == 'blender' else 'Chromium',
                'template': item,
                'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    if item.get('assets'):
        from library_assets import REGISTRY
        registry = yaml.safe_load(REGISTRY.read_text())['assets']
        metadata['assets'] = []
        for name in item['assets']:
            asset = target.parent.parent / 'assets' / registry[name]['filename']
            metadata['assets'].append(json.loads(asset.with_suffix(asset.suffix + '.json').read_text()))
    target.with_suffix('.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))


def gallery(entries, args):
    args.out.mkdir(parents=True, exist_ok=True)
    data = []
    for item in entries:
        if not all((args.out / folder / f'{item["id"]}.mp4').exists()
                   for folder in ('references', 'renders')):
            continue
        entry = dict(item)
        entry['reference_clip'] = (f'references/{item["id"]}.mp4'
                                   if (args.out/'references'/f'{item["id"]}.mp4').exists() else None)
        entry['render_clip'] = (f'renders/{item["id"]}.mp4'
                                if (args.out/'renders'/f'{item["id"]}.mp4').exists() else None)
        source = f'build/{item["id"]}/' + (
            f'{item["id"]}.blend' if item['renderer'] == 'blender' else 'page.html')
        entry['project_file'] = source if (args.out / source).exists() else None
        data.append(entry)
    serialized = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    html = (LIBRARY / 'gallery.html').read_text().replace('__CATALOG_JSON__', serialized)
    target = args.out / 'index.html'
    target.write_text(html)
    print(target)


def verify(item, args):
    """Check the artifacts themselves: full duration, hash, codec and decode."""
    for role in ('references', 'renders'):
        path = args.out / role / (item['id'] + '.mp4')
        metadata = json.loads(path.with_suffix('.json').read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['sha256']:
            raise ValueError(f'{path}: checksum mismatch')
        info = probe(path)
        video = next(stream for stream in info['streams'] if stream['codec_type'] == 'video')
        expected = (item['duration'] if role == 'renders' else
                    item['reference']['end'] - item['reference']['start'])
        actual = float(info['format']['duration'])
        if abs(actual - expected) > .1:
            raise ValueError(f'{path}: expected {expected}s, got {actual}s')
        if role == 'renders':
            expected_frames = max(2, round(item['duration'] * metadata['fps']))
            if int(video['nb_frames']) != expected_frames:
                raise ValueError(f'{path}: expected {expected_frames} frames, got {video["nb_frames"]}')
            if (video['width'], video['height']) != (metadata['width'], metadata['height']):
                raise ValueError(f'{path}: dimensions do not match render settings')
        run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'null', '-'],
            stdout=subprocess.DEVNULL)
    if item['renderer'] == 'blender':
        project = args.out / 'build' / item['id'] / (item['id'] + '.blend')
        if not project.exists():
            raise ValueError(f'{project}: missing editable project')
    print(f'verified {item["id"]}: reference + reproduction', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list', 'collect', 'render', 'catalog', 'verify', 'all'])
    parser.add_argument('--id', action='append', help='Template id; repeatable. Default: all.')
    parser.add_argument('--out', type=Path, default=ROOT/'out/template-library')
    parser.add_argument('--source', type=Path, help='Local source override (collect, one id only)')
    parser.add_argument('--force', action='store_true', help='Regenerate existing artifacts')
    parser.add_argument('--width', type=int, default=960)
    parser.add_argument('--height', type=int, default=600)
    parser.add_argument('--fps', type=int, default=25)
    parser.add_argument('--samples', type=int, default=None)
    parser.add_argument('--engine', choices=['cycles', 'eevee'], default=None)
    parser.add_argument('--threads', type=int, default=8)
    args = parser.parse_args()
    if min(args.width, args.height, args.fps, args.samples if args.samples is not None else 48, args.threads) < 1:
        parser.error('Render settings must be positive')
    if args.width % 2 or args.height % 2:
        parser.error('H.264 dimensions must be even')
    if args.width * 10 != args.height * 16:
        parser.error('Templates use a 16:10 stage (e.g. 960x600 or 1600x1000)')
    args.out = args.out.resolve()
    entries = read_catalog()
    if args.id and set(args.id) - {t['id'] for t in entries}:
        parser.error('Unknown template id')
    selected = [t for t in entries if not args.id or t['id'] in args.id]
    if args.source and (len(selected) != 1 or args.command != 'collect'):
        parser.error('--source requires collect --id <one id>')
    if args.command == 'list':
        for item in selected:
            print(f'{item["id"]:20} {item["renderer"]:7} {item["duration"]:4.1f}s '
                  f'{item["reference"]["brand"]} — {item["title"]}')
    for item in selected:
        if args.command in ('collect', 'all'):
            collect(item, args)
        if args.command in ('render', 'all'):
            render(item, args)
        if args.command == 'verify':
            verify(item, args)
    if args.command in ('catalog', 'all'):
        gallery(entries, args)


if __name__ == '__main__':
    main()
