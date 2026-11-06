#!/usr/bin/env python3
"""画面素材の HTML を MP4 に録る。

素のスクリーン録画と違い、HTML は毎回まったく同じ絵を出す。だから編集を直しても
録り直しがただで、タイムラインの尺が崩れない。録画で踏んだ穴が二つあり、どちらも
ここで塞いである。

1. wait_for_timeout で放置するとレンダラが休み、setTimeout が詰まって映像がスローになる。
   200ms ごとに evaluate で突いて起こし続ける。
2. 録画中の進みは実行のたびに数秒ぶれる。秒数で止めると末尾が切れたり黒が残るので、
   終端マーカー（--until の文字列が --marker の要素に出ること）を見てから
   --hold 秒だけ録って止める。

  uv run --with playwright python tools/record.py assets/screens/foo.html \
      --out out/screens/foo.mp4 --until NyxFoundation
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile, time

from playwright.sync_api import sync_playwright


def launch_chromium(p, **kw):
    """Playwright の同梱ブラウザが無い機械（NixOS など）でも起動する。"""
    env = os.environ.get("DEMO_CHROMIUM")
    err = None
    if not env:
        try:
            return p.chromium.launch(**kw)
        except Exception as e:
            err = e
    names = ("chromium", "chromium-browser", "google-chrome-stable", "google-chrome")
    cands = ([env] if env else []) + [c for c in map(shutil.which, names) if c]
    cands += sorted(glob.glob("/nix/store/*-chromium-*/bin/chromium"), reverse=True)
    for exe in cands:
        try:
            b = p.chromium.launch(executable_path=exe, **kw)
            print(f"[demo] chromium: {exe}")
            return b
        except Exception as e:
            err = e
    raise SystemExit(f"chromium を起動できない ({err})。"
                     " playwright install chromium するか DEMO_CHROMIUM を指す。")


ap = argparse.ArgumentParser()
ap.add_argument("html")
ap.add_argument("--out", default=None)
ap.add_argument("--until", default="NyxFoundation", help="終端マーカーの文字列")
ap.add_argument("--marker", default="#tcT", help="終端マーカーを探す要素")
ap.add_argument("--hold", type=float, default=2.8, help="終端カードを映す秒数")
ap.add_argument("--max", type=float, default=300, help="保険の打ち切り秒数")
ap.add_argument("--settle", type=float, default=0.8, help="頭を落とす秒数")
ap.add_argument("--width", type=int, default=1600)
ap.add_argument("--height", type=int, default=1000)
a = ap.parse_args()

html = os.path.abspath(a.html)
out = os.path.abspath(a.out or os.path.splitext(html)[0] + ".mp4")
os.makedirs(os.path.dirname(out), exist_ok=True)
tmp = tempfile.mkdtemp(prefix="rec_")
probe = ("() => (document.querySelector(%r)?.textContent || '').includes(%r)"
         % (a.marker, a.until)).replace("'", '"', 4)

with sync_playwright() as p:
    b = launch_chromium(p)
    ctx = b.new_context(viewport={"width": a.width, "height": a.height},
                        record_video_dir=tmp,
                        record_video_size={"width": a.width, "height": a.height})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(f"file://{html}?rec=1")
    t0 = time.time()
    seen = None
    while time.time() - t0 < a.max:
        if seen is None and pg.evaluate(probe):
            seen = time.time()
        if seen and time.time() - seen >= a.hold:
            break
        pg.evaluate("1")                       # レンダラを起こし続ける
        pg.wait_for_timeout(200)
    print("終端まで %.1fs" % ((seen - t0) if seen else -1))
    ctx.close()
    b.close()
    if errors:
        print("JS errors:", *errors, sep="\n  ", file=sys.stderr)

webm = max(glob.glob(os.path.join(tmp, "*.webm")), key=os.path.getmtime)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a.settle), "-i", webm,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                "-movflags", "+faststart", out], check=True)
shutil.rmtree(tmp, ignore_errors=True)
print("wrote", out)
