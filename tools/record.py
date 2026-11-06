#!/usr/bin/env python3
"""画面素材の HTML を MP4 に録る。

素のスクリーン録画と違い、HTML は毎回まったく同じ絵を出す。だから文言を一つ直して
録り直しても、尺もタイミングも前回と揃う。録画で踏んだ穴が二つあり、どちらもここで
塞いである。

1. wait_for_timeout で放置するとレンダラが休み、setTimeout が詰まって映像がスローに
   なる。200ms ごとに evaluate で突いて起こし続ける。
2. 録画中の進みは実行のたびに数秒ぶれる。秒数で止めると末尾が切れたり黒が残るので、
   エンジンが最後のシーンを終えたときに立てる body[data-done] を見てから --hold 秒
   だけ録って止める。

  uv run --with playwright python tools/record.py out/screens/foo.html \
      --out out/screens/foo.mp4
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium          # noqa: E402

DONE = "() => document.body.dataset.done === '1'"


def record(html, out=None, hold=2.6, maxs=300, settle=0.8, width=1600, height=1000):
    html = os.path.abspath(html)
    out = os.path.abspath(out or os.path.splitext(html)[0] + ".mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="rec_")

    with sync_playwright() as p:
        b = launch_chromium(p)
        ctx = b.new_context(viewport={"width": width, "height": height},
                            record_video_dir=tmp,
                            record_video_size={"width": width, "height": height})
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(f"file://{html}?rec=1")
        t0 = time.time()
        seen = None
        while time.time() - t0 < maxs:
            if seen is None and pg.evaluate(DONE):
                seen = time.time()
            if seen and time.time() - seen >= hold:
                break
            pg.evaluate("1")                   # レンダラを起こし続ける
            pg.wait_for_timeout(200)
        print("終端まで %.1fs" % ((seen - t0) if seen else -1))
        ctx.close()
        b.close()
        if errors:
            print("JS errors:", *errors, sep="\n  ", file=sys.stderr)

    webm = max(glob.glob(os.path.join(tmp, "*.webm")), key=os.path.getmtime)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(settle), "-i", webm,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-movflags", "+faststart", out], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print("wrote", out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out", default=None)
    ap.add_argument("--hold", type=float, default=2.6, help="終端カードを映す秒数")
    ap.add_argument("--max", type=float, default=300, help="保険の打ち切り秒数")
    ap.add_argument("--settle", type=float, default=0.8, help="頭を落とす秒数")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1000)
    a = ap.parse_args()
    record(a.html, a.out, a.hold, a.max, a.settle, a.width, a.height)
