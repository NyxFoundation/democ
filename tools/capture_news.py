#!/usr/bin/env python3
"""Cache real public newsroom screenshots and a clearly identified source reel."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'templates/library/newsroom/sources.yaml'


def ensure_images(out=None):
    out = Path(out or ROOT / 'out/template-library')
    folder = out / 'assets/newsroom'
    folder.mkdir(parents=True, exist_ok=True)
    sources = yaml.safe_load(SOURCES.read_text())['sources']
    paths = [folder / (source['id']+'.png') for source in sources]
    missing = [(source, path) for source, path in zip(sources, paths)
               if not path.exists() or not path.with_suffix('.json').exists()]
    if missing:
        from browser import launch_chromium
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = launch_chromium(p, headless=True)
            for source, path in missing:
                page = browser.new_page(viewport={'width':1360, 'height':980}, device_scale_factor=1)
                response = page.goto(source['url'], wait_until='domcontentloaded', timeout=60000)
                if response and response.status >= 400:
                    raise RuntimeError(f'{source["url"]}: HTTP {response.status}')
                page.evaluate('document.fonts.ready')
                page.wait_for_timeout(1600)
                # Reject optional cookies when a public page offers that choice.
                for label in ['Reject all', 'Reject All', 'Deny all cookies', 'Do not allow cookies', 'Only necessary cookies', 'Decline']:
                    button = page.get_by_role('button', name=label, exact=True)
                    if button.count() and button.first.is_visible():
                        button.first.click(timeout=3000)
                        break
                page.screenshot(path=str(path), animations='disabled')
                meta = {**source, 'title':page.title(), 'captured_at':datetime.now(timezone.utc).isoformat(),
                        'width':1360, 'height':980, 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'rights':'Publisher-owned source screenshot; local visual study. Not an endorsement.'}
                path.with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
                print('captured', source['id'], meta['title'], flush=True)
                page.close()
            browser.close()
    for path in paths:
        meta = json.loads(path.with_suffix('.json').read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
            raise ValueError(f'Screenshot checksum mismatch: {path}')
    return [p.resolve() for p in paths]


def reference_movie(out):
    out = Path(out)
    images = ensure_images(out)
    folder = out / 'assets/newsroom'
    target = folder / 'source-reel.mp4'
    signature = hashlib.sha256(b''.join(p.read_bytes() for p in images)).hexdigest()
    stamp = target.with_suffix('.json')
    if not target.exists() or not stamp.exists() or json.loads(stamp.read_text())['signature'] != signature:
        listing = folder / 'frames.txt'
        listing.write_text(''.join(f"file '{p}'\nduration 0.8\n" for p in images) + f"file '{images[-1]}'\n")
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),
                        '-vf','scale=960:600:force_original_aspect_ratio=decrease,pad=960:600:(ow-iw)/2:(oh-ih)/2:color=0x101116,fps=25',
                        '-t','4.8','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],check=True)
        stamp.write_text(json.dumps({'signature':signature, 'kind':'Screenshot source reel, not a publisher-made animation',
                                      'sources':[json.loads(p.with_suffix('.json').read_text()) for p in images]},indent=2))
    return target.resolve()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'out/template-library')
    args=parser.parse_args()
    print(reference_movie(args.out))
