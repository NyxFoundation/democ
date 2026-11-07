#!/usr/bin/env python3
"""demos/<name>.yaml を 1 枚の HTML に組み立てる。

人が触るのは YAML だけ。文言も、コードも、保持時間の方針もそこにある。
エンジンとシーンの型は engine/ にあり、使ったシーンの CSS と JS だけが埋め込まれる。

  python3 tools/build.py demos/nyxis/nyxis.yaml -o out/nyxis/page.html
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml                                     # noqa: E402
from highlight import highlight, lines as hl_lines, plain_of  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "engine"


# --- 小さな部品 -------------------------------------------------------------
class SpecError(SystemExit):
    pass


def require(s, *keys):
    missing = [k for k in keys if s.get(k) in (None, "", [], {})]
    if missing:
        raise SpecError(f"{s.get('name') or s['type']}: {', '.join(missing)} が要る"
                        f"（書き方は docs/scenes.md）")


def tab_html(name, icon=None):
    """ファイル名のタブ。注釈を置く代わりに、画面自身に名前を言わせる。"""
    if not name:
        return ""
    return (f'<div class="ftab"><i class="{icon or ""}"></i>{name}'
            f'<span class="x">×</span></div><div class="frule"></div>')


def key_html(s):
    """{{x}} を「変わったところ」として差す。URL の一文字など。"""
    return re.sub(r"\{\{(.+?)\}\}", r'<b class="key">\1</b>', str(s or ""))


def code_of(d, key="code"):
    """コードのブロックを色付きの行の列にして、保持時間用の素のテキストも返す。"""
    src = d.get(key)
    rows = hl_lines(src, d.get("lang"))
    return rows, plain_of(src)


def wrap_range(rows, spec, span_id):
    """行範囲 "1-3" を 1 つの span で包む。飛ばす側と着地する側の目印になる。"""
    if not spec:
        return rows
    a, _, b = str(spec).partition("-")
    a = int(a); b = int(b or a)
    rows = list(rows)
    rows[a - 1] = f'<span id="{span_id}">' + rows[a - 1]
    rows[b - 1] = rows[b - 1] + "</span>"
    return rows


# --- シーンごとの変換 -------------------------------------------------------
def build_card(s):
    s["tabHtml"] = tab_html(s.pop("tab", None), s.pop("icon", None))
    if s.get("code"):
        s["codeHtml"], _ = code_of(s)
    s.pop("code", None)


def build_browser(s):
    s["urlHtml"] = key_html(s.pop("url", ""))
    s["crumbHtml"] = key_html(s.pop("crumb", ""))
    ch = s.get("change")
    if ch:
        ch["urlHtml"] = key_html(ch.pop("url", ""))
        ch["crumbHtml"] = key_html(ch.pop("crumb", ""))


def build_code(s):
    s["tabHtml"] = tab_html(s.pop("tab", None), s.pop("icon", None))
    out = []
    require(s, "lines")
    for raw in str(s.pop("lines")).split("\n"):
        if not raw.strip():
            if out:
                out.append({"gap": True})
            continue
        m = re.match(r"^\s*(\d+)[ \t](.*)$", raw)
        if not m:
            raise SystemExit(f"code の行は「行番号 スペース コード」で書く: {raw!r}")
        n, body = int(m.group(1)), m.group(2)
        out.append({"n": n, "html": highlight(body, s.get("lang")), "plain": plain_of(body)})
    while out and out[-1].get("gap"):
        out.pop()
    s["lines"] = out


def build_split(s):
    require(s, "left", "right")
    for side, span in (("left", "spFly"), ("right", "spLand")):
        d = s[side]
        d["tabHtml"] = tab_html(d.pop("tab", None), d.pop("icon", None))
        rows, pl = code_of(d)
        d["codeHtml"] = wrap_range(rows, d.pop("fly", None) or d.pop("land", None), span)
        d["plain"] = pl
        d.pop("code", None)


def build_tree(s):
    require(s, "root", "levels")
    if s.get("error"):
        s["errorHtml"] = highlight(s["error"], "sh")
        s["errorPlain"] = plain_of(s.pop("error"))
    if s.get("done"):
        s["doneHtml"] = highlight(s["done"], "sh")
        s["donePlain"] = plain_of(s.pop("done"))
    for o in s.get("inspect", []):
        o["needHtml"] = highlight(o["need"], s.get("lang"))
        o["needPlain"] = plain_of(o.pop("need"))
        o["hasHtml"] = highlight(o["has"], s.get("lang"))
        o.pop("has", None)
    s["inspectLabels"] = s.pop("inspect_labels", None)


def build_terminal(s):
    require(s, "lines")
    s.setdefault("lang", "sh")
    if "gap_ms" in s:
        s["gapMs"] = s.pop("gap_ms")
    s["codeHtml"], _ = code_of(s, "lines")
    s.pop("lines", None)
    side = s.get("side")
    if side:
        side["tabHtml"] = tab_html(side.pop("tab", None), side.pop("icon", None))
        side["codeHtml"], _ = code_of(side)
        side.pop("code", None)


BUILDERS = {"card": build_card, "browser": build_browser, "code": build_code,
            "split": build_split, "tree": build_tree, "terminal": build_terminal}


# --- 組み立て ---------------------------------------------------------------
def assemble(spec_path: Path, out_path: Path) -> Path:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    scenes = spec.get("scenes") or []
    if not scenes:
        raise SystemExit(f"{spec_path} に scenes がない")

    used = []
    for i, s in enumerate(scenes):
        t = s.get("type")
        if t not in BUILDERS:
            raise SystemExit(f"知らないシーン種別: {t!r}（使えるのは {', '.join(BUILDERS)}）")
        if t not in used:
            used.append(t)
        try:
            BUILDERS[t](s)
        except SpecError:
            raise
        except Exception as e:
            raise SystemExit(f"scenes[{i}] ({s.get('name') or t}): {e}") from e
        s["_next"] = scenes[i + 1]["type"] if i + 1 < len(scenes) else None
        s["_prev"] = scenes[i - 1]["type"] if i else None

    css = [(ENGINE / "engine.css").read_text(encoding="utf-8")]
    js = [(ENGINE / "engine.js").read_text(encoding="utf-8")]
    for t in used:
        css.append((ENGINE / "scenes" / f"{t}.css").read_text(encoding="utf-8"))
        js.append((ENGINE / "scenes" / f"{t}.js").read_text(encoding="utf-8"))

    # 文言を一つ直したときに、そのシーンだけ録り直せるようにする。
    # エンジンが変わったら全部が変わったものとして扱う。
    eng = hashlib.sha1("".join(css + js).encode("utf-8")).hexdigest()[:12]
    spec["engine"] = eng
    for sc in scenes:
        sc["hash"] = hashlib.sha1(
            json.dumps(sc, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:12]

    title = spec.get("title", spec_path.stem)
    doc = f"""<!doctype html>
<html lang="ja"><meta charset="utf-8">
<title>{title}</title>
<!-- 生成物。直すのは {spec_path.relative_to(ROOT) if spec_path.is_relative_to(ROOT) else spec_path} の方。 -->
<style>
{chr(10).join(css)}
</style>
<body>
<div class="controls">
  <div>{title} · <span id="tick">00.0s</span></div>
  <div class="steps" id="steps"></div>
</div>
<div class="stage-wrap"><div class="stage" id="stage">
  <div class="grid"></div>
  <div id="scenes"></div>
</div></div>
<script>
{chr(10).join(js)}
</script>
<script>
const DEMO = {json.dumps(spec, ensure_ascii=False, indent=1)};
D.boot(DEMO);
</script>
</body></html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    print(f"{out_path}  {len(scenes)} scenes / {len(doc) // 1024} KB  [{' '.join(used)}]")
    return out_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    sp = Path(a.spec).resolve()
    assemble(sp, Path(a.out).resolve() if a.out else ROOT / "out" / sp.stem / "page.html")
