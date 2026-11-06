# demo-creator

デモ動画を、録画ではなくビルドで作るための置き場。画面は HTML、3D は Blender の
スクリプト、編集は MLT XML。どれもテキストなので AI が直接書けて、直したら
`make` で同じものが出てくる。GUI は人が確かめて手直しするために開く。

```
make            素材 → タイムライン → out/demo.mp4
make screens    assets/screens/*.html を録り直す
make snaps      止め絵で確認する（動きで隠れる崩れはこれでしか見えない）
make 3d         assets/3d/*.py を Blender で焼く
make preview    melt で再生する
make open       Kdenlive で out/edit.mlt を開く
make shell      devShell に入る
```

`melt` が PATH に無ければ Makefile が `nix develop` を噛ませるので、素の端末から
`make` を叩いて構わない。

## なぜ画面収録ではないのか

HTML は毎回まったく同じ絵を出す。文言を一つ直して録り直しても、尺もタイミングも
前回と揃う。画面収録だと一箇所の手直しに全部の録り直しが付いてきて、タイムライン
側の尺が崩れる。完成が近づいて細部を詰める段階ほど、この差が効いてくる。

録画で踏んだ穴は `tools/record.py` に二つ塞いである。Playwright の
`wait_for_timeout` で待つとレンダラが休んで `setTimeout` が詰まり、映像が
スローモーションになる。それと、録画中の進みは実行のたびに数秒ぶれるので、秒数で
止めると末尾が切れるか黒が残る。前者は 200ms ごとに `evaluate` で突いて起こし、
後者は終端マーカーが出たのを見てから `--hold` 秒だけ録って止めている。

## なぜ MLT XML なのか

Kdenlive と Shotcut が同じ `.mlt` を開く。`edit/timeline.py` が書いた構成を人が
GUI で手直しでき、手直しした `.mlt` をまた `melt` で描画できる。AI が書ける編集
フォーマットで、人の手が入る余地が残っているものは他にない。

書き戻しは運転に入れていない。GUI で直したものを `timeline.py` へ反映する経路を
作ると、どちらが正本か分からなくなる。GUI での手直しは最終調整として扱う。

## 構成

| 場所 | 中身 |
|---|---|
| `assets/screens/*.html` | 画面素材。自分で再生する 1 枚の HTML |
| `assets/3d/*.py` | Blender を headless で回すスクリプト |
| `edit/timeline.py` | タイムライン。ここが AI の作業面 |
| `tools/record.py` | HTML → MP4 |
| `tools/snap.py` | HTML → 止め絵 |
| `out/` | 生成物。git には入れない |

`assets/screens/nyxis-hero.html` が最初の一本。作り方と、画面に出す数字の出典は
`docs/nyxis-hero.md` にある。

## 踏んだ穴

MLT を手書きすると最初に当たるものを二つ。どちらも `edit/timeline.py` の
コメントに残してある。

`avformat-novalidate` を使わない。Kdenlive が書く `.mlt` に出てくるので真似したく
なるが、これは素材を調べない指定で、`length` を併せて書かないと尺が 1 フレームに
なる。エラーは出ず、1 フレームだけの動画が静かに出てくる。

`profile` に `colorspace` を書かない。書くと素材の色域へ変換がかかる。画面素材は
full-range で録れているので、709 を宣言した時点で目に見えて暗くなる。これもエラー
は出ない。

フェードの `<filter>` には `in` / `out` を必ず付ける。付けないと素材の全長に
かかり、2 点しかない `level` のアニメーションが折り返して、真ん中がずっと暗いまま
描画される。

## 環境

NixOS 向けの `flake.nix` を置いてある。`nix develop` で mlt・ffmpeg・Blender・
Kdenlive・Shotcut・FreeCAD が揃う。Python の録画まわりは `uv run --with playwright`
で都度解決するので、shell には入れていない。

このディレクトリが親リポジトリで未追跡のまま flake を評価できるよう、Makefile は
`path:` スキームで flake を指している。
