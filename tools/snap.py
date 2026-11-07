#!/usr/bin/env python3
"""画面素材を場面ごとに静止画へ落とす。

動きで隠れるレイアウト崩れは止め絵でしか見えない。録る前にこれを通す。
既定ではシーンが切り替わった直後と、その場面がいちばん出来上がったところを撮る。

  uv run --with playwright python tools/snap.py out/screens/nyxis.html
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium         # noqa: E402


def snap(html, out=None, every=2.0, width=1600, height=1000, maxs=300):
    html = os.path.abspath(html)
    out = out or os.path.join("out", "snaps", os.path.splitext(os.path.basename(html))[0])
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))

    cur = ("() => { const b=[...document.querySelectorAll('#steps button')]"
           ".findIndex(b=>b.getAttribute('aria-current')==='step'); return b; }")
    with sync_playwright() as p:
        b = launch_chromium(p)
        pg = b.new_context(viewport={"width": width, "height": height}).new_page()
        pg.goto(f"file://{html}?rec=1")
        t0 = 0.0
        n = 0
        while t0 < maxs:
            pg.evaluate("1")
            pg.wait_for_timeout(int(every * 1000))
            t0 += every
            step = pg.evaluate(cur)
            path = os.path.join(out, "t%05.1f-s%02d.png" % (t0, step))
            pg.screenshot(path=path)
            n += 1
            if pg.evaluate("() => document.body.dataset.done === '1'"):
                break
        b.close()
    print(f"{n} 枚 → {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--every", type=float, default=2.0, help="何秒ごとに撮るか")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    snap(a.html, a.out, a.every)
