#!/usr/bin/env python3
"""カードの文字を Kdenlive のタイトルクリップにする。

焼き込んだ mp4 だと Kdenlive の中で文字を直せない。タイトルクリップにすれば
ダブルクリックで打ち替えられる。代わりに、文字数から保持時間を決める仕組みと
入らないときの自動縮小はエンジン側の機能なので効かなくなる。

できるのは画面に重なっているだけの文字だけ。UI の中の文字（コード・ファイルタブ・
ブラウザの中身）は画面そのものなので、外には出せない。

位置は絶対指定しかないので、文字幅を測って中央に置く。測るのは PIL で、
melt の実測と 0.6% しか違わない（704px に対して約 700px）。

font-weight は Qt6 の尺度（1〜1000）。昔の 0〜99 のつもりで 75 と書くと
Thin に近い細さで出る。太字は 700。
"""

from __future__ import annotations

import html
import re
from xml.sax.saxutils import escape

FONT = "Noto Sans CJK JP"
# 1 行の中で色が変わると項目が分かれる。項目ごとに左の余白が入るので、
# そのぶん詰めないと境目だけ字間が広く見える（実測 10px、通常の字間は 3〜5px）
RUN_KERN = 6
FONT_FILE = "/run/current-system/sw/share/fonts/opentype/noto-cjk/NotoSansCJK-VF.otf.ttc"
_cache: dict = {}


def _font(size: int):
    if size not in _cache:
        from PIL import ImageFont
        _cache[size] = ImageFont.truetype(FONT_FILE, size)
    return _cache[size]


_warned = False


def width_of(s: str, size: int) -> float:
    global _warned
    try:
        return _font(size).getlength(s)
    except Exception as e:
        # フォントが読めない機械では、全角 1em・半角 0.5em で当てる。
        # 中央寄せが甘くなるので、黙って落ちないよう一度だけ言う
        if not _warned:
            print(f"  （文字幅を概算で出している: {e}）")
            _warned = True
        return sum(1.0 if ord(c) > 0x2E80 else 0.5 for c in s) * size


def rgba(hexcolor: str, alpha: int = 255) -> str:
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "%d,%d,%d,%d" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def runs(line: str, fg: str, accent: str):
    """1 行を、色の変わるところで区切る。<em> が accent 色になる。"""
    out = []
    for part in re.split(r"(<em>.*?</em>|<b>.*?</b>)", line):
        if not part:
            continue
        m = re.match(r"<(em|b)>(.*?)</\1>", part, re.S)
        txt = m.group(2) if m else part
        txt = html.unescape(re.sub(r"<[^>]+>", "", txt))
        if txt:
            out.append((txt, accent if m else fg))
    return out


def build(text: str, *, frames: int, width=1600, height=1000,
          size=52, weight=700, fg="#eef3fb", accent="#5fd7d7", bg="#05070d",
          max_width_ratio=0.78, line_ratio=1.42) -> str:
    """カードの text（HTML）から kdenlivetitle の XML を作る。"""
    lines = [l for l in re.split(r"<br\s*/?>", text or "")]
    laid = [runs(l, fg, accent) for l in lines]

    # 入る大きさまで落とす。エンジンの autofit と同じ考え方
    limit = width * max_width_ratio
    while size > 24 and any(sum(width_of(t, size) for t, _ in ln) > limit for ln in laid):
        size -= 2

    lh = size * line_ratio
    top = (height - lh * len(laid)) / 2
    items, z = [], 0
    for i, ln in enumerate(laid):
        total = sum(width_of(t, size) for t, _ in ln) - RUN_KERN * (len(ln) - 1)
        x = (width - total) / 2
        y = top + lh * i
        for txt, color in ln:
            items.append(
                f'  <item z-index="{z}" type="QGraphicsTextItem">\n'
                f'   <position x="{x:.0f}" y="{y:.0f}">'
                f'<transform>1,0,0,0,1,0,0,0,1</transform></position>\n'
                f'   <content font-color="{rgba(color)}" font-pixel-size="{size}"'
                f' font-weight="{weight}" font="{FONT}" font-italic="0" font-underline="0"'
                f'>{escape(txt)}</content>\n'
                f'  </item>')
            x += width_of(txt, size) - RUN_KERN
            z += 1

    return (f'<kdenlivetitle width="{width}" height="{height}" out="{frames - 1}"'
            f' LC_NUMERIC="C" duration="{frames}">\n'
            + "\n".join(items) + "\n"
            f' <startviewport rect="0,0,{width},{height}"/>\n'
            f' <endviewport rect="0,0,{width},{height}"/>\n'
            f' <background color="{rgba(bg)}"/>\n'
            f'</kdenlivetitle>\n')
