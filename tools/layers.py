#!/usr/bin/env python3
"""画面素材を、部品ごとの透過 PNG に切り出す。

1 枚の絵にしてしまうと、あとは全体をスライドさせることしかできない。部品ごとに
分けておくと Z 方向にずらせるので、視差が出て、片方だけにピントを置けて、
別々に動かせる。3D で合成するときに効いてくるのはここ。

  uv run --with playwright --with pyyaml python tools/layers.py layers/split.yaml

仕様（layers/<名前>.yaml）:
  page:   組み上がった HTML
  scene:  demos の何番目のシーンか
  out:    書き出し先
  clear:  透明にするために背景を消すセレクタ
  layers: - name / select / at（シーン開始からの秒）/ js（撮る前に流す JS）
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser import launch_chromium          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# 透過で撮るための下ごしらえ。元に戻せるよう、消すのではなく隠す
PREP = """(sels) => {
  window.__saved = [];
  const hit = new Set();
  sels.forEach(s => document.querySelectorAll(s).forEach(e => hit.add(e)));
  [document.documentElement, document.body, ...hit].forEach(e => {
    window.__saved.push([e, e.style.background, e.style.boxShadow, e.style.visibility]);
    e.style.background = 'transparent';
    e.style.boxShadow = 'none';
  });
  document.querySelectorAll('.grid').forEach(e => {
    window.__saved.push([e, e.style.background, e.style.boxShadow, e.style.visibility]);
    e.style.visibility = 'hidden';
  });
}"""
UNPREP = """() => {
  (window.__saved || []).forEach(([e, bg, sh, vis]) => {
    e.style.background = bg; e.style.boxShadow = sh; e.style.visibility = vis;
  });
  window.__saved = [];
}"""


def export(spec_path: Path):
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    page = ROOT / spec["page"]
    out = ROOT / spec["out"]
    out.mkdir(parents=True, exist_ok=True)
    clear = spec.get("clear", [".sc", ".stage", ".stage-wrap"])
    idx = spec["scene"]

    with sync_playwright() as p:
        b = launch_chromium(p)
        # scale を上げると板のテクスチャが細かくなる。カメラが寄ったときに
        # 文字がにじまない。layers.json は CSS px のままなので配置は変わらない
        pg = b.new_context(viewport={"width": spec.get("width", 1600),
                                     "height": spec.get("height", 1000)},
                           device_scale_factor=spec.get("scale", 1)).new_page()
        pg.goto(f"file://{page}?rec=1")
        pg.wait_for_timeout(600)

        written = []
        for L in spec["layers"]:
            # 毎回まっさらに戻してから、そのレイヤーの状態を js で作る。
            # 再生させて秒で狙うとシーンの hold を変えた途端に別の絵が撮れてしまう。
            pg.evaluate("""(a) => {
              D.clear();
              document.getElementById('stage').className = 'stage';
              Object.values(D.Scenes).forEach(s => s.reset && s.reset());
              delete document.body.dataset.done;
              window.s = DEMO.scenes[a.i];
              if (a.play) D.Scenes[window.s.type].play(window.s);
            }""", {"i": idx, "play": bool(L.get("play"))})
            if L.get("play"):
                t0 = time.time()
                while time.time() - t0 < float(L.get("at", 0)):
                    pg.evaluate("1")
                    pg.wait_for_timeout(60)
            if L.get("js"):
                pg.evaluate("() => { " + L["js"] + " }")
            pg.wait_for_timeout(int(L.get("settle", 260)))

            pg.evaluate(PREP, clear)
            pg.wait_for_timeout(80)
            el = pg.query_selector(L["select"])
            if el is None:
                raise SystemExit(f"{L['name']}: {L['select']} が見つからない")
            path = out / f"{L['name']}.png"
            el.screenshot(path=str(path), omit_background=True)
            box = el.bounding_box()
            written.append({"name": L["name"], "file": path.name,
                            "x": round(box["x"], 1), "y": round(box["y"], 1),
                            "w": round(box["width"], 1), "h": round(box["height"], 1)})
            print(f"  {L['name']:<8} {box['width']:>6.0f}x{box['height']:<6.0f} @ "
                  f"{box['x']:>6.0f},{box['y']:<6.0f}")
            pg.evaluate(UNPREP)
        b.close()

    # 画面の中のどこにあったかを残す。Blender 側はこれを見て板を並べる
    (out / "layers.json").write_text(
        json.dumps({"stage": [spec.get("width", 1600), spec.get("height", 1000)],
                    "layers": written}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(written)} 枚 → {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    a = ap.parse_args()
    export(Path(a.spec).resolve())
