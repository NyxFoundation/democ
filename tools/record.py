#!/usr/bin/env python3
"""組み上がった HTML を MP4 に録る。

素のスクリーン録画と違い、HTML は毎回まったく同じ絵を出す。文言を一つ直して録り
直しても、尺もタイミングも前回と揃う。録画で踏んだ穴が二つあり、どちらもここで
塞いである。

1. wait_for_timeout で待つとレンダラが休み、setTimeout が詰まって映像がスローに
   なる。200ms ごとに evaluate で突いて起こし続ける。
2. 録画中の進みは実行のたびに数秒ぶれる。秒数で止めると末尾が切れたり黒が残るので、
   エンジンが立てる body[data-done] を見てから --hold 秒だけ録って止める。

既定はシーンごとに 1 本ずつ録る。1 本に繋げて録ると「7 番目だけ 3D 版に差し替える」
が切り貼りになるし、文言を直したときに全部録り直すことになる。分けておけば
タイムラインがクリップの並びになって、人が開いたときに触れるものになる。

  uv run --with playwright python tools/record.py out/screens/nyxis.html \
      --out out/screens/nyxis            # → 00-数字.mp4 … と index.json
  uv run --with playwright python tools/record.py out/screens/nyxis.html \
      --one --out out/screens/nyxis.mp4  # 全部つなげて 1 本
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium          # noqa: E402

DONE = "() => document.body.dataset.done === '1'"
SAFE = re.compile(r"[^\w.\-ぁ-んァ-ヶ一-龠々ー]+")


def _encode(webm, out, settle):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(settle), "-i", webm,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-movflags", "+faststart", out], check=True)


def _seconds(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 3)
    except ValueError:
        return 0.0


def _run(html, out, scene, hold, maxs, settle, width, height):
    """1 本録る。scene が None なら全部つなげて。"""
    tmp = tempfile.mkdtemp(prefix="rec_")
    errors = []
    with sync_playwright() as p:
        b = launch_chromium(p)
        ctx = b.new_context(viewport={"width": width, "height": height},
                            record_video_dir=tmp,
                            record_video_size={"width": width, "height": height})
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(f"file://{html}?rec=1")
        if scene is not None:
            pg.wait_for_timeout(400)
            pg.evaluate("(i) => D.playScene(i)", scene)
        t0 = time.time()
        seen = None
        while time.time() - t0 < maxs:
            if seen is None and pg.evaluate(DONE):
                seen = time.time()
            if seen and time.time() - seen >= hold:
                break
            pg.evaluate("1")                   # レンダラを起こし続ける
            pg.wait_for_timeout(200)
        ctx.close()
        b.close()
    webm = max(glob.glob(os.path.join(tmp, "*.webm")), key=os.path.getmtime)
    _encode(webm, out, settle)
    shutil.rmtree(tmp, ignore_errors=True)
    if errors:
        print("JS errors:", *errors, sep="\n  ", file=sys.stderr)
    return out


def scene_list(html, width, height):
    """名前とハッシュ。ハッシュは build.py が埋めたもの。"""
    with sync_playwright() as p:
        b = launch_chromium(p)
        pg = b.new_context(viewport={"width": width, "height": height}).new_page()
        pg.goto(f"file://{html}?rec=1")
        pg.wait_for_timeout(400)
        out = pg.evaluate("""() => ({
          engine: D.spec.engine || '',
          scenes: D.spec.scenes.map((s, i) => ({
            name: s.name || (i + ' ' + s.type), hash: s.hash || '' })) })""")
        b.close()
    return out


def record_scenes(html, outdir, hold=0.35, maxs=180, settle=0.8, width=1600, height=1000):
    html = os.path.abspath(html)
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)
    info = scene_list(html, width, height)
    engine, names = info["engine"], info["scenes"]

    # 前回の録画を読んで、中身が変わっていないシーンはそのまま使う
    prev = {}
    old = os.path.join(outdir, "index.json")
    if os.path.exists(old):
        try:
            o = json.load(open(old, encoding="utf-8"))
            if o.get("engine") == engine:
                prev = {s["i"]: s for s in o.get("scenes", [])}
        except Exception:
            pass

    index = []
    kept = 0
    for i, sc in enumerate(names):
        name, h = sc["name"], sc["hash"]
        fn = "%02d-%s.mp4" % (i, SAFE.sub("_", name).strip("_") or str(i))
        path = os.path.join(outdir, fn)
        old_s = prev.get(i)
        if old_s and old_s.get("hash") == h and old_s.get("file") == fn \
                and os.path.exists(path):
            index.append(old_s)
            kept += 1
            print("  %2d %-10s %6.2fs  （変更なし）" % (i, name, old_s["seconds"]))
            continue
        _run(html, path, i, hold, maxs, settle, width, height)
        secs = _seconds(path)
        index.append({"i": i, "name": name, "file": fn, "seconds": secs, "hash": h})
        print("  %2d %-10s %6.2fs  %s" % (i, name, secs, fn))
    meta = {"page": os.path.basename(html), "fps": 25, "engine": engine, "scenes": index}
    with open(os.path.join(outdir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("%d シーン（%d 本は据え置き）/ 合計 %.1fs → %s"
          % (len(index), kept, sum(s["seconds"] for s in index), outdir))
    return outdir


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out", required=True, help="シーンごとなら書き出し先ディレクトリ")
    ap.add_argument("--one", action="store_true", help="全部つなげて 1 本にする")
    ap.add_argument("--scene", type=int, default=None, help="1 場面だけ録る")
    ap.add_argument("--hold", type=float, default=None, help="終端を映す秒数")
    ap.add_argument("--max", type=float, default=300)
    ap.add_argument("--settle", type=float, default=0.8, help="頭を落とす秒数")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1000)
    a = ap.parse_args()
    if a.one or a.scene is not None:
        hold = a.hold if a.hold is not None else (2.6 if a.one else 0.35)
        _run(os.path.abspath(a.html), os.path.abspath(a.out), a.scene,
             hold, a.max, a.settle, a.width, a.height)
        print("wrote", a.out)
    else:
        record_scenes(a.html, a.out, a.hold if a.hold is not None else 0.35,
                      a.max, a.settle, a.width, a.height)
