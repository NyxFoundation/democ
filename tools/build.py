#!/usr/bin/env python3
"""out/<デモ>/<デモ>.yaml を 1 枚の HTML に組み立てる。

人が触るのは YAML だけ。文言も、コードも、保持時間の方針もそこにある。
エンジンとシーンの型は engine/ にあり、使ったシーンの CSS と JS だけが埋め込まれる。

  python3 tools/build.py out/nyxis/nyxis.yaml -o out/nyxis/build/page.html
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
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


def build_incident(s):
    for field in ("code", "missing"):
        if s.get(field):
            s[field + "Html"] = hl_lines(s.pop(field), s.get("lang", "js"))


def build_policy(s):
    for field in ("code", "schema", "invalid"):
        if s.get(field):
            s[field + "Html"] = hl_lines(s.pop(field), "cedar")


def build_motion(s):
    presets = {"auto-layout", "spatial-carousel", "cursor-zoom"}
    if s.get("preset") not in presets:
        raise SpecError(f"motion: preset は {', '.join(sorted(presets))} のいずれか")
    duration = s.setdefault("duration", 6)
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise SpecError("motion: duration は正の秒数")
    if "labels" in s:
        count = 3 if s["preset"] == "auto-layout" else 7
        if not isinstance(s["labels"], list) or len(s["labels"]) != count:
            raise SpecError(f"motion: labels は {count} 個の配列")
    if "colors" in s and (not isinstance(s["colors"], list) or len(s["colors"]) != 7 or
                          not all(re.fullmatch(r"#[0-9a-fA-F]{6}", str(c)) for c in s["colors"])):
        raise SpecError("motion: colors は7個の #RRGGBB の配列")
    if "turns" in s and (not isinstance(s["turns"], (int, float)) or not math.isfinite(s["turns"])):
        raise SpecError("motion: turns は有限の回転数")
    if "rows" in s:
        rows = s["rows"]
        if not isinstance(rows, list) or len(rows) != 6 or any(
                not isinstance(row, list) or len(row) != 5 for row in rows):
            raise SpecError("motion: rows は見出しを含め6行5列")
        try:
            valid = all(math.isfinite(float(row[4])) for row in rows[1:])
        except (ValueError, TypeError):
            valid = False
        if not valid:
            raise SpecError("motion: rows の最終列は数値")


def editorial_font(s):
    from library_assets import acquire_assets
    path = acquire_assets(['inter-variable'], ROOT / 'out/template-library')['inter-variable']
    s['font_data'] = 'data:font/woff2;base64,' + base64.b64encode(path.read_bytes()).decode()
    s['font_license'] = (ROOT / 'templates/library/newsroom/Inter-OFL.txt').read_text()


def build_typography(s):
    if s.get('preset') not in {'type-punch', 'type-flight', 'type-morph'}:
        raise SpecError('typography: preset は type-punch / type-flight / type-morph')
    duration = s.setdefault('duration', 5.6)
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise SpecError('typography: duration は正の秒数')
    field = 'words' if s['preset'] == 'type-punch' else 'lines'
    limit = 12 if field == 'words' else 3
    if not isinstance(s.get(field), list) or not 1 <= len(s[field]) <= limit or not all(
            isinstance(word, str) and word.strip() for word in s[field]):
        raise SpecError(f'typography: {field} は1〜{limit}個の空でない文字列')
    if 'font_size' in s and (not isinstance(s['font_size'], (int, float)) or
                             not math.isfinite(s['font_size']) or s['font_size'] <= 0):
        raise SpecError('typography: font_size は正の数')
    editorial_font(s)


def build_press(s):
    if s.get('preset') not in {'press-cascade', 'press-wall'}:
        raise SpecError('press: preset は press-cascade / press-wall')
    duration = s.setdefault('duration', 6.8)
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise SpecError('press: duration は正の秒数')
    paths = s.pop('images', None)
    if paths is None:
        from capture_news import ensure_images
        paths = ensure_images()
    if not isinstance(paths, list) or not 1 <= len(paths) <= 64:
        raise SpecError('press: images は1〜64個の画像パス')
    s['image_data'] = []
    for path in paths:
        image = Path(path)
        mime = {'.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.webp':'image/webp'}.get(image.suffix.lower())
        if not mime:
            raise SpecError('press: PNG / JPEG / WebP を指定')
        s['image_data'].append('data:'+mime+';base64,'+base64.b64encode(image.read_bytes()).decode())
    metric = s.setdefault('metric', {'value':12800000, 'label':'DEMO IMPRESSIONS'})
    if not isinstance(metric, dict) or not isinstance(metric.get('value'), (int, float)) or not math.isfinite(metric['value']) or metric['value'] < 0 or not isinstance(metric.get('label'), str):
        raise SpecError('press: metric に非負の value と文字列 label が要る')
    editorial_font(s)


def build_study(s):
    if s.get('preset') not in {'terminal-flow', 'code-diff', 'network-globe', 'market-chart'}:
        raise SpecError('study: 知らない preset')
    duration = s.setdefault('duration', 4.8)
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise SpecError('study: duration は正の秒数')
    if s['preset'] == 'network-globe':
        from library_assets import acquire_assets
        defaults = {'texture': 'earth-nasa-day', 'clouds': 'earth-clouds-8k',
                    'night': 'earth-nasa-night', 'water': 'earth-nasa-water'}
        embedded = {'texture': 'earth_map', 'clouds': 'earth_cloud_map',
                    'night': 'earth_night_map', 'water': 'earth_water_map'}
        missing = {kind: name for kind, name in defaults.items()
                   if not s.get(kind+'_path') and not s.get(embedded[kind])}
        if missing:
            paths = acquire_assets(missing.values(), ROOT / 'out/template-library')
            s.update({kind+'_path': str(paths[name]) for kind, name in missing.items()})
    for key, field in [('texture_path', 'earth_map'), ('clouds_path', 'earth_cloud_map'),
                       ('night_path', 'earth_night_map'), ('water_path', 'earth_water_map')]:
        if not s.get(key):
            continue
        image = Path(s.pop(key))
        if s['preset'] == 'network-globe':
            import subprocess
            compact = image.with_name(image.stem + '-web-4k.jpg')
            if not compact.exists() or compact.stat().st_mtime < image.stat().st_mtime:
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(image),
                                '-vf', 'scale=4096:-2:flags=lanczos', '-q:v', '3',
                                '-threads', '2', str(compact)], check=True)
            image = compact
        mime = 'image/png' if image.suffix.lower() == '.png' else 'image/jpeg'
        s[field] = 'data:' + mime + ';base64,' + base64.b64encode(image.read_bytes()).decode()


BUILDERS = {"card": build_card, "browser": build_browser, "code": build_code,
            "split": build_split, "tree": build_tree, "terminal": build_terminal,
            "incident": build_incident, "policy": build_policy, "kernel": lambda s: None,
            "motion": build_motion, "study": build_study,
            "typography": build_typography, "press": build_press}


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
    if any(s['type'] == 'study' and s.get('preset') in
           {'terminal-flow', 'code-diff', 'market-chart', 'network-globe'} for s in scenes):
        from source_ui import assets as source_ui_assets
        upstream_css, upstream_js = source_ui_assets()
        css.extend([upstream_css, (ENGINE / 'scenes/source-ui.css').read_text()])
        js = [upstream_js, *js, (ENGINE / 'scenes/source-ui.js').read_text()]
        if any(s.get('preset')=='network-globe' for s in scenes):
            css.append((ENGINE/'scenes/network-globe.css').read_text())
            js.append((ENGINE/'scenes/network-globe.js').read_text())

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
    assemble(sp, Path(a.out).resolve() if a.out
             else ROOT / "out" / sp.stem / "build" / "page.html")
