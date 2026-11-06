"""コードに色を付ける。

YAML には素のコードを書いてもらい、色はここで付ける。手で <span> を書かせると
文言を直すのが苦行になるし、同じ語が場所によって違う色になる。

書ける印は 2 つだけ。
  {{ここ}}   赤く差す（間違いを指さすとき）
  <<ここ>>   黄色い注記（ターミナルの「← 冒頭のあれ」など）
"""

import html
import re

MARK, NOTE = "\x01", "\x02"

KW = {
    "js": """const let var function return if else await async new class extends import from
             export default throw try catch finally for of in typeof delete void yield
             null undefined true false this""".split(),
    "ts": """const let var function return if else await async new class extends implements
             interface type import from export default throw try catch for of in typeof
             null undefined true false this readonly""".split(),
    "lean": """def theorem lemma structure inductive instance class where match with fun do
               let have show from by exact intro apply simp rw cases induction return pure
               if then else universe namespace end open section variable abbrev deriving
               example axiom partial mutual""".split(),
    "cedar": """permit forbid when unless principal action resource context in is like has
                if then else true false entity namespace type""".split(),
    "json": "true false null".split(),
}
TYP = {
    "js": "String Number Boolean Array Object JSON Promise Date Math Error".split(),
    "ts": "String Number Boolean Array Object JSON Promise Date Math Error".split(),
    "lean": "Nat Int String Bool List Option Prop Type Array Unit IO Except".split(),
    "cedar": "String Long Bool Set Record".split(),
}
COMMENT = {"js": r"//[^\n]*", "ts": r"//[^\n]*", "lean": r"--[^\n]*",
           "cedar": r"//[^\n]*", "json": None}
STRING = r"""'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`"""

CLS = {"comment": "c", "string": "s", "kw": "k", "typ": "t", "func": "f", "num": "n"}
_cache: dict = {}


def _pattern(lang):
    if lang in _cache:
        return _cache[lang]
    parts = []
    if COMMENT.get(lang):
        parts.append(f"(?P<comment>{COMMENT[lang]})")
    parts.append(f"(?P<string>{STRING})")
    if KW.get(lang):
        parts.append(r"(?P<kw>\b(?:%s)\b)" % "|".join(KW[lang]))
    if TYP.get(lang):
        parts.append(r"(?P<typ>\b(?:%s)\b)" % "|".join(TYP[lang]))
    parts.append(r"(?P<func>\b[A-Za-z_][\w.]*(?=\())")
    parts.append(r"(?P<num>\b\d+(?:\.\d+)?\b)")
    _cache[lang] = re.compile("|".join(parts))
    return _cache[lang]


def _sh(src: str) -> str:
    """シェルは語ではなく行の形で読む。プロンプトと終了コードが見えればよい。"""
    src = re.sub(r"(?m)^(\s*)(\$|➜|#)(?= )", r'\1<span class="tk-p">\2</span>', src)
    src = re.sub(r"('(?:[^'\\\n]|\\.)*')", r'<span class="tk-q">\1</span>', src)
    src = re.sub(r"\b(2\d\d)\b", r'<span class="tk-g">\1</span>', src)
    src = re.sub(r"\b([45]\d\d)\b", r'<span class="tk-e">\1</span>', src)
    src = re.sub(r"(·[^\n<]*)", r'<span class="tk-d">\1</span>', src)
    src = re.sub(r"(?m)^(\s*)(✓)", r'\1<span class="tk-g">\2</span>', src)
    src = re.sub(r"(?m)^(\s*)(error:|exit \d+)", r'\1<span class="tk-e">\2</span>', src)
    return src


def highlight(src: str, lang: str | None) -> str:
    """素のコード 1 行ないし複数行を、色付きの HTML にする。"""
    if src is None:
        return ""
    src = str(src)
    marks, notes = [], []

    def grab(m, store, sentinel):
        store.append(m.group(1))
        return sentinel + str(len(store) - 1) + sentinel

    src = re.sub(r"\{\{(.+?)\}\}", lambda m: grab(m, marks, MARK), src, flags=re.S)
    src = re.sub(r"<<(.+?)>>", lambda m: grab(m, notes, NOTE), src, flags=re.S)
    src = html.escape(src, quote=False)

    if lang == "sh":
        src = _sh(src)
    elif lang and (lang in KW or lang in COMMENT):
        def sub(m):
            for name, val in m.groupdict().items():
                if val is not None:
                    return f'<span class="tk-{CLS[name]}">{val}</span>'
            return m.group(0)
        src = _pattern(lang).sub(sub, src)

    src = re.sub(MARK + r"(\d+)" + MARK,
                 lambda m: "<mark>" + html.escape(marks[int(m.group(1))], quote=False) + "</mark>", src)
    src = re.sub(NOTE + r"(\d+)" + NOTE,
                 lambda m: '<span class="tk-a">' + html.escape(notes[int(m.group(1))], quote=False) + "</span>", src)
    return src


def plain_of(src) -> str:
    """保持時間を測るための素のテキスト。印とタグを落として数える。"""
    s = re.sub(r"\{\{(.+?)\}\}", r"\1", str(src or ""), flags=re.S)
    s = re.sub(r"<<(.+?)>>", r"\1", s, flags=re.S)
    return s


def lines(block: str, lang: str | None) -> list[str]:
    """ブロックスカラーを 1 行ずつ色付けして返す。末尾の空行は落とす。"""
    out = [highlight(l, lang) for l in str(block or "").split("\n")]
    while out and not out[-1].strip():
        out.pop()
    return out
