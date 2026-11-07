#!/usr/bin/env python3
"""同じ並びを Kdenlive の方言で書き出す。

Kdenlive は素の MLT を開かない。「Project corrupted. Clip producerN with invalid Id」
と言って止まる。要るのは三つ。

1. 素材は <producer> ではなく <chain>。中身は resource だけでよく、残りは
   Kdenlive が開くときに埋める
2. その chain を main_bin プレイリストに並べる。ここがプロジェクトビンの実体
3. トラックは「2 つの playlist を持つ tractor」。さらにその全部を束ねる
   シーケンス tractor があり、最後に final_tractor が居る

melt に渡すのは out/edit.mlt のほう。こちらは人が開くためだけのもの。
"""

from __future__ import annotations

import uuid as _uuid
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

NS = _uuid.UUID("6f1f4f4e-0000-4000-8000-000000000001")


def tc(frames: int, fps: int) -> str:
    """Kdenlive が書くのと同じ HH:MM:SS.mmm 形式。"""
    ms = round(frames * 1000 / fps)
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def _prop(parent, name, value=None):
    e = ET.SubElement(parent, "property", {"name": name})
    if value is not None:
        e.text = str(value)
    return e


def _fade(entry, kind: str, frames: int, fps: int, n: int):
    """Kdenlive がフェードのつまみとして読み戻す形。"""
    f = ET.SubElement(entry, "filter", {
        "id": f"fade{n}", "in": tc(0, fps), "out": tc(max(frames - 1, 0), fps)})
    _prop(f, "start", 1)
    _prop(f, "level", 1)
    _prop(f, "mlt_service", "brightness")
    _prop(f, "kdenlive_id", f"fade_{kind}_black")
    _prop(f, "alpha", "0=0;-1=1" if kind == "from" else "0=1;-1=0")


def write(path, clips, *, width=1600, height=1000, fps=25, name="demo") -> Path:
    """clips = [{path, name, frames, in, fade_in, fade_out}]（フレーム単位）"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    uid = "{%s}" % _uuid.uuid5(NS, name)
    total = sum(c["frames"] for c in clips)

    mlt = ET.Element("mlt", {"LC_NUMERIC": "C", "version": "7.0.0", "producer": "main_bin"})
    dar = Fraction(width, height)
    ET.SubElement(mlt, "profile", {
        "colorspace": "709", "description": f"{width}x{height}, {fps} fps",
        "display_aspect_den": str(dar.denominator), "display_aspect_num": str(dar.numerator),
        "frame_rate_den": "1", "frame_rate_num": str(fps),
        "height": str(height), "width": str(width), "progressive": "1",
        "sample_aspect_den": "1", "sample_aspect_num": "1"})

    # 一番下に敷く黒
    black = ET.SubElement(mlt, "producer", {
        "id": "black_track_producer", "in": tc(0, fps), "out": tc(total, fps)})
    _prop(black, "length", 2147483647)
    _prop(black, "eof", "continue")
    _prop(black, "resource", "black")
    _prop(black, "aspect_ratio", 1)
    _prop(black, "mlt_service", "color")
    _prop(black, "kdenlive:playlistid", "black_track")
    _prop(black, "mlt_image_format", "rgba")
    _prop(black, "set.test_audio", 0)

    # ビンの素材。同じファイルは 1 つにまとめる。
    # タイトルは <chain> ではなく <producer>。Kdenlive はこれをタイトルクリップとして
    # 開くので、ダブルクリックで文字を打ち替えられる。
    chains, order = {}, []
    for n, c in enumerate(clips):
        if c.get("title"):
            pid = f"title{n}"
            c["_ref"] = pid
            order.append(pid)
            pr = ET.SubElement(mlt, "producer", {
                "id": pid, "in": tc(0, fps), "out": tc(c["frames"] - 1, fps)})
            _prop(pr, "mlt_service", "kdenlivetitle")
            _prop(pr, "length", c["frames"])
            _prop(pr, "kdenlive:clipname", c["name"])
            _prop(pr, "xmldata", c["title"])
            continue
        src = str(Path(c["path"]).resolve())
        if src not in chains:
            cid = f"chain{len(chains)}"
            chains[src] = cid
            order.append(cid)
            ch = ET.SubElement(mlt, "chain", {"id": cid})
            _prop(ch, "resource", src)
        c["_ref"] = chains[src]

    # 映像トラック。tractor が playlist を 2 本持つのが Kdenlive の形
    pl = ET.SubElement(mlt, "playlist", {"id": "playlist_v0"})
    for i, c in enumerate(clips):
        inf = c.get("in", 0)
        entry = ET.SubElement(pl, "entry", {
            "producer": c["_ref"],
            "in": tc(inf, fps), "out": tc(inf + c["frames"] - 1, fps)})
        if c.get("fade_in"):
            _fade(entry, "from", c["fade_in"], fps, i * 2)
        if c.get("fade_out"):
            _fade(entry, "to", c["fade_out"], fps, i * 2 + 1)
    ET.SubElement(mlt, "playlist", {"id": "playlist_v1"})

    # 音のトラックは空でも置く。無いと Kdenlive が落ち着かない
    ET.SubElement(mlt, "playlist", {"id": "playlist_a0"})
    ET.SubElement(mlt, "playlist", {"id": "playlist_a1"})
    ta = ET.SubElement(mlt, "tractor", {"id": "tractor_audio"})
    _prop(ta, "kdenlive:audio_track", 1)
    for p in ("playlist_a0", "playlist_a1"):
        ET.SubElement(ta, "track", {"producer": p, "hide": "video"})
    tv = ET.SubElement(mlt, "tractor", {"id": "tractor_video"})
    for p in ("playlist_v0", "playlist_v1"):
        ET.SubElement(tv, "track", {"producer": p, "hide": "audio"})

    # シーケンス。トラックは下（音）から上（映像）の順に積む
    seq = ET.SubElement(mlt, "tractor", {"id": uid, "in": tc(0, fps), "out": tc(total, fps)})
    for k, v in (("kdenlive:uuid", uid), ("kdenlive:clipname", name),
                 ("kdenlive:sequenceproperties.hasAudio", 1),
                 ("kdenlive:sequenceproperties.hasVideo", 1),
                 ("kdenlive:sequenceproperties.activeTrack", 2),
                 ("kdenlive:sequenceproperties.tracksCount", 2),
                 ("kdenlive:sequenceproperties.documentuuid", uid),
                 ("kdenlive:sequenceproperties.audioTarget", 1),
                 ("kdenlive:sequenceproperties.videoTarget", 2),
                 ("kdenlive:duration", tc(total, fps)),
                 ("kdenlive:maxduration", total),
                 ("kdenlive:producer_type", 17), ("kdenlive:id", 3),
                 ("kdenlive:clip_type", 0)):
        _prop(seq, k, v)
    ET.SubElement(seq, "track", {"producer": "black_track_producer"})
    mix = ET.SubElement(seq, "transition", {"id": "transition_mix"})
    for k, v in (("a_track", 0), ("b_track", 1), ("mlt_service", "mix"),
                 ("kdenlive_id", "mix"), ("internal_added", 237),
                 ("always_active", 1), ("accepts_blanks", 1), ("sum", 1)):
        _prop(mix, k, v)
    bl = ET.SubElement(seq, "transition", {"id": "transition_blend"})
    for k, v in (("a_track", 0), ("b_track", 2), ("compositing", 0), ("distort", 0),
                 ("rotate_center", 0), ("mlt_service", "qtblend"),
                 ("kdenlive_id", "qtblend"), ("internal_added", 237), ("always_active", 1)):
        _prop(bl, k, v)
    ET.SubElement(seq, "track", {"producer": "tractor_audio"})
    ET.SubElement(seq, "track", {"producer": "tractor_video"})

    # プロジェクトビン
    binp = ET.SubElement(mlt, "playlist", {"id": "main_bin"})
    for k, v in (("kdenlive:docproperties.decimalPoint", "."),
                 ("kdenlive:docproperties.uuid", uid),
                 ("kdenlive:docproperties.version", "1.1"),
                 ("kdenlive:docproperties.profile", f"{width}x{height}"),
                 ("kdenlive:docproperties.opensequences", uid),
                 ("kdenlive:docproperties.activetimeline", uid),
                 ("kdenlive:sequenceFolder", 2),
                 ("kdenlive:folder.-1.2", "Sequences"),
                 ("xml_retain", 1)):
        _prop(binp, k, v)
    ET.SubElement(binp, "entry", {"producer": uid, "in": tc(0, fps), "out": tc(0, fps)})
    for cid in order:
        ET.SubElement(binp, "entry", {"producer": cid, "in": tc(0, fps), "out": tc(0, fps)})

    final = ET.SubElement(mlt, "tractor", {
        "id": "final_tractor", "in": tc(0, fps), "out": tc(total, fps)})
    _prop(final, "kdenlive:projectTractor", 1)
    ET.SubElement(final, "track", {"producer": uid, "in": tc(0, fps), "out": tc(total, fps)})

    ET.indent(mlt, space="  ")
    doc = b"<?xml version='1.0' encoding='utf-8'?>\n" + ET.tostring(mlt, encoding="utf-8")
    if not (path.exists() and path.read_bytes() == doc):
        path.write_bytes(doc)
    print(f"{path.name}  {len(clips)} クリップ / {total / fps:.1f}s  （Kdenlive 用）")
    return path
