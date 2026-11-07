#!/usr/bin/env python3
"""MLT XML を組み立てる。

ここが AI の作業面。素材（画面録画・Blender の書き出し・静止画）を並べ、
フェードや重ねを決めて `.mlt` を吐く。GUI は人が確かめて直すために開くもので、
GUI で作った構成をここへ書き戻す運転はしない。

    make timeline        out/edit.mlt を書く
    make preview         melt で再生して確かめる
    make render          out/demo.mp4 へ描画
    make open            Kdenlive で開いて人が直す

MLT を選ぶ理由は、Kdenlive と Shotcut が同じ XML を開くから。AI が書いた構成を
そのまま人が GUI で手直しできるし、手直し後の .mlt をまた melt で描画できる。
"""

from __future__ import annotations

import json
import shutil
import sys
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kdenlive                                  # noqa: E402


def probe_duration(path: Path) -> float:
    """素材の尺を秒で返す。ffprobe が無ければ 0 を返し、呼び出し側に尺を書かせる。"""
    if not shutil.which("ffprobe"):
        return 0.0
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


@dataclass
class Clip:
    """1 トラック上の 1 区間。service が blank なら空き。"""
    resource: Path | None
    start: float = 0.0            # 素材の中の開始位置（秒）
    length: float = 0.0           # 使う長さ（秒）
    fade_in: float = 0.0
    fade_out: float = 0.0
    service: str = "avformat"     # avformat / qimage / color / blank
    properties: dict = field(default_factory=dict)


class Timeline:
    def __init__(self, width=1600, height=1000, fps=25, tracks=2):
        self.width, self.height, self.fps = width, height, fps
        self.tracks: list[list[Clip]] = [[] for _ in range(tracks)]

    # --- 素材を置く -----------------------------------------------------
    def _resolve(self, resource) -> Path:
        path = Path(resource)
        if not path.is_absolute():
            path = ROOT / path
        if not path.exists():
            raise FileNotFoundError(f"素材がない: {path}  （make screens / make 3d は通したか）")
        return path

    def video(self, resource, *, track=0, start=0.0, length=None,
              fade_in=0.0, fade_out=0.0) -> "Timeline":
        path = self._resolve(resource)
        if length is None:
            length = max(probe_duration(path) - start, 0.0)
            if not length:
                raise ValueError(f"{path.name} の尺を測れない。length= を書く")
        self.tracks[track].append(
            Clip(path, start, length, fade_in, fade_out, "avformat"))
        return self

    def image(self, resource, *, seconds, track=0, fade_in=0.0, fade_out=0.0) -> "Timeline":
        self.tracks[track].append(
            Clip(self._resolve(resource), 0.0, seconds, fade_in, fade_out, "qimage"))
        return self

    def color(self, value, *, seconds, track=0, fade_in=0.0, fade_out=0.0) -> "Timeline":
        """value は MLT の色表記。黒は '#ff000000'（先頭 2 桁がアルファ）。"""
        self.tracks[track].append(
            Clip(None, 0.0, seconds, fade_in, fade_out, "color", {"resource": value}))
        return self

    def gap(self, seconds, *, track=0) -> "Timeline":
        self.tracks[track].append(Clip(None, 0.0, seconds, service="blank"))
        return self

    # --- 書き出し -------------------------------------------------------
    def _f(self, seconds: float) -> int:
        """秒 → フレーム番号。位置に使う。"""
        return int(round(seconds * self.fps))

    def _len(self, seconds: float) -> int:
        """秒 → フレーム数。長さに使うので 0 にはしない。"""
        return max(self._f(seconds), 1)

    def _fade(self, prod, in_f: int, frames: int,
              fade_in: float, fade_out: float, tag: str):
        """brightness の level を動かす。Kdenlive はこれをフェードとして読み戻す。

        filter に in/out を必ず付ける。付けないと素材の全長にかかり、2 点しかない
        level アニメが折り返して、真ん中がずっと暗いまま描画される。
        """
        for kind, sec in (("in", fade_in), ("out", fade_out)):
            if not sec:
                continue
            n = min(self._len(sec), frames)
            if kind == "in":
                lo, hi, level = in_f, in_f + n - 1, f"0=0;{n - 1}=1"
            else:
                lo, hi, level = in_f + frames - n, in_f + frames - 1, f"0=1;{n - 1}=0"
            filt = ET.SubElement(prod, "filter", {
                "id": f"filter_{tag}_{kind}", "in": str(lo), "out": str(hi)})
            ET.SubElement(filt, "property", {"name": "mlt_service"}).text = "brightness"
            ET.SubElement(filt, "property", {"name": "level"}).text = level

    def write(self, path) -> Path:
        path = Path(path)
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)

        mlt = ET.Element("mlt", {
            "LC_NUMERIC": "C", "version": "7.0.0",
            "title": path.stem, "producer": "main_tractor",
        })
        dar = Fraction(self.width, self.height)
        ET.SubElement(mlt, "profile", {
            "description": f"{self.width}x{self.height} {self.fps}fps",
            "width": str(self.width), "height": str(self.height),
            "progressive": "1",
            "sample_aspect_num": "1", "sample_aspect_den": "1",
            "display_aspect_num": str(dar.numerator),
            "display_aspect_den": str(dar.denominator),
            "frame_rate_num": str(self.fps), "frame_rate_den": "1",
            # colorspace は書かない。書くと素材の色域へ変換がかかり、
            # full-range で録った画面素材が目に見えて暗くなる
        })

        total, n = 0, 0
        playlists: list[tuple[str, list]] = []

        for ti, clips in enumerate(self.tracks):
            entries = []
            for clip in clips:
                frames = self._len(clip.length)
                if clip.service == "blank":
                    entries.append((None, frames, 0))
                    continue

                pid = f"producer{n}"
                n += 1
                in_f = self._f(clip.start)
                prod = ET.SubElement(mlt, "producer", {
                    "id": pid, "in": str(in_f), "out": str(in_f + frames - 1)})

                def prop(k, v):
                    ET.SubElement(prod, "property", {"name": k}).text = str(v)

                if clip.service == "avformat":
                    # avformat-novalidate にしない。素材を調べないので尺が 1 フレームになる
                    prop("mlt_service", "avformat")
                    prop("resource", clip.resource)
                elif clip.service == "qimage":
                    prop("mlt_service", "qimage")
                    prop("resource", clip.resource)
                    prop("length", frames)
                elif clip.service == "color":
                    prop("mlt_service", "color")
                    prop("length", frames)
                for k, v in clip.properties.items():
                    prop(k, v)

                self._fade(prod, in_f, frames, clip.fade_in, clip.fade_out, pid)
                entries.append((pid, frames, in_f))

            playlists.append((f"playlist{ti}", entries))
            total = max(total, sum(e[1] for e in entries))

        for pl_id, entries in playlists:
            pl = ET.SubElement(mlt, "playlist", {"id": pl_id})
            for pid, frames, in_f in entries:
                if pid is None:
                    ET.SubElement(pl, "blank", {"length": str(frames)})
                else:
                    ET.SubElement(pl, "entry", {
                        "producer": pid, "in": str(in_f),
                        "out": str(in_f + frames - 1)})

        tractor = ET.SubElement(mlt, "tractor", {
            "id": "main_tractor", "in": "0", "out": str(max(total - 1, 0))})
        for pl_id, _ in playlists:
            ET.SubElement(tractor, "track", {"producer": pl_id})
        # 上のトラックを下へ重ねる合成。これが無いと一番下のトラックしか見えない
        for i in range(1, len(playlists)):
            tr = ET.SubElement(tractor, "transition", {"id": f"transition{i}"})
            for k, v in (("a_track", "0"), ("b_track", str(i)),
                         ("mlt_service", "frei0r.cairoblend"),
                         ("always_active", "1"), ("disable", "0")):
                ET.SubElement(tr, "property", {"name": k}).text = v

        ET.indent(mlt, space="  ")
        doc = b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(mlt, encoding="utf-8")
        # 中身が同じなら書かない。毎回書くと melt が毎回描き直すことになる
        if path.exists() and path.read_bytes() == doc:
            print(f"{path.relative_to(ROOT)}  変更なし / {total / self.fps:.1f}s")
            return path
        path.write_bytes(doc)
        print(f"{path.relative_to(ROOT)}  {total} frames / {total / self.fps:.1f}s")
        return path


# ---------------------------------------------------------------------------
# ここから下が構成。素材を並べ、フェードや重ねを決める。
#
# シーンは 1 つ 1 クリップ。1 本に繋げて録ると「7 番目だけ 3D 版に差し替える」が
# 切り貼りになるし、文言を直したときに全部録り直すことになる。
# ---------------------------------------------------------------------------
def shots(demo: str) -> dict:
    """3D カットがどのシーンを置き換えるかは layers/<デモ>/<ショット>.yaml が宣言する。"""
    import yaml
    out = {}
    for p in sorted((ROOT / "layers" / demo).glob("*.yaml")):
        spec = yaml.safe_load(p.read_text(encoding="utf-8"))
        mp4 = ROOT / "out" / demo / "3d" / f"{p.stem}.mp4"
        if mp4.exists() and "scene" in spec:
            out[spec["scene"]] = mp4
    return out


def build(demo: str) -> Path:
    fps = 25
    base = ROOT / "out" / demo
    index = base / "screens" / "index.json"
    if not index.exists():
        raise SystemExit(f"{index} がない。make screens を先に通す")

    tl = Timeline(width=1600, height=1000, fps=fps, tracks=2)
    sub = shots(demo)
    clips = []
    for s in json.loads(index.read_text(encoding="utf-8"))["scenes"]:
        three = sub.get(s["i"])
        clips.append((three or index.parent / s["file"], s["name"], three is not None))

    last = len(clips) - 1
    kd = []
    for i, (path, name, is3d) in enumerate(clips):
        # 見た目の違うカットの前後だけ短く溶かす。同じ絵の続きは切りっぱなし
        prev3d = i > 0 and clips[i - 1][2]
        next3d = i < last and clips[i + 1][2]
        fi = 0.4 if i == 0 else (0.25 if is3d or prev3d else 0.0)
        fo = 0.8 if i == last else (0.25 if is3d or next3d else 0.0)
        tl.video(path, track=0, fade_in=fi, fade_out=fo)
        kd.append({"path": path, "name": name, "in": 0,
                   "frames": max(int(round(probe_duration(path) * fps)), 1),
                   "fade_in": int(round(fi * fps)), "fade_out": int(round(fo * fps))})
        print("  %2d %-10s %s%s" % (i, name, path.name, "   ← 3D" if is3d else ""))

    out = tl.write(base / "edit.mlt")
    # melt に渡すのは .mlt。人が開くのは .kdenlive のほう（素の MLT は開けない）
    kdenlive.write(base / "edit.kdenlive", kd, width=1600, height=1000, fps=fps, name=demo)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("demo", nargs="?", default=None)
    a = ap.parse_args()
    names = [a.demo] if a.demo else [p.stem for p in sorted((ROOT / "demos").glob("*.yaml"))]
    for n in names:
        build(n)
