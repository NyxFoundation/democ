#!/usr/bin/env python3
"""画面素材を一定間隔で静止画に落とす。

動きで隠れるレイアウト崩れは止め絵でしか見えない。録る前にこれを通す。

  uv run --with playwright python tools/snap.py assets/screens/foo.html --every 4
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
from record import launch_chromium          # noqa: E402  起動の面倒は一箇所に置く

ap = argparse.ArgumentParser()
ap.add_argument("html")
ap.add_argument("--every", type=float, default=4.0, help="何秒ごとに撮るか")
ap.add_argument("--count", type=int, default=30)
ap.add_argument("--out", default=None)
ap.add_argument("--width", type=int, default=1600)
ap.add_argument("--height", type=int, default=1000)
a = ap.parse_args()

html = os.path.abspath(a.html)
out = a.out or os.path.join("out", "snaps", os.path.splitext(os.path.basename(html))[0])
os.makedirs(out, exist_ok=True)

with sync_playwright() as p:
    b = launch_chromium(p)
    pg = b.new_context(viewport={"width": a.width, "height": a.height}).new_page()
    pg.goto(f"file://{html}?rec=1")
    for i in range(a.count):
        pg.wait_for_timeout(int(a.every * 1000))
        pg.evaluate("1")
        path = os.path.join(out, "t%03d.png" % int(i * a.every))
        pg.screenshot(path=path)
        print(path)
    b.close()
