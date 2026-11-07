# demo-creator

デモ動画を、録画ではなくビルドで作るための置き場。画面は HTML、3D は Blender の
スクリプト、編集は MLT XML。どれもテキストなので AI が直接書けて、直したら `make`
で同じものが出てくる。GUI は人が確かめて手直しするために開く。

デモ 1 本は `demos/<名前>.yaml` 1 ファイル。場面の型は `engine/scenes/` にあり、
YAML が決めるのは中身だけ。文言を変えれば、画面に出ている時間も文字数から付いてくる。

```
make edit N=nyxis    組んでブラウザで開く。文言を詰めるときはここから
make watch N=nyxis   保存するたびに組み直す。ブラウザは F5
make                 demos/*.yaml → 録画 → タイムライン → out/demo.mp4
make html            HTML だけ組む
make screens         組んで録り直す
make snaps           止め絵で確かめる
make layers          画面を部品ごとの透過 PNG に切り出す
make 3d              その部品を Blender で 3D に置いて撮る（.blend も出る）
make preview         melt で再生する
make open            Kdenlive で out/edit.mlt を開く
make new NAME=foo    templates/starter.yaml から新しいデモを作る
```

`melt` が PATH に無ければ Makefile が `nix develop` を噛ませるので、素の端末から
`make` を叩いて構わない。生成物は全部 `out/` に入り、git には入らない。

## 文言を直す

```sh
make watch N=nyxis       # 別の端末で開いておく
make edit  N=nyxis       # ブラウザが開く
```

あとは `demos/nyxis.yaml` を書き換えて保存するだけ。`watch` が組み直すので、ブラウザ
で F5 を押すと入れ替わる。組み直しは 0.3 秒。`watch` を使わないなら保存のたびに
`make html` を叩く。

開いた画面では数字キーで場面を飛べて、`r` で頭から再生される。14 場面目だけ見たい
ときは `13` を押す。よければ `make` で録り直して書き出す。

引数の一覧は [docs/scenes.md](docs/scenes.md)。文章には `<em>`（accent 色）`<b>`
`<s>`（灰色）`<br>` が書ける。コードは素のまま書けば `lang` から色が付き、
`{{ここ}}` が赤い差し、`<<ここ>>` が黄色い注記になる。

保持時間は `lead + 文字数 / cps` を上下で挟んで決まる。長い文を書けば自動的に長く
出るので、短くしたいときは秒ではなく文を削る。秒で固定したい場面だけ `hold:` を書く。
全体の速さを変えるなら先頭の `reading.cps` を動かす。

## なぜ画面収録ではないのか

HTML は毎回まったく同じ絵を出す。文言を一つ直して録り直しても、尺もタイミングも
前回と揃う。画面収録だと一箇所の手直しに全部の録り直しが付いてきて、タイムライン側
の尺が崩れる。完成が近づいて細部を詰める段階ほど、この差が効いてくる。

録画で踏んだ穴は `tools/record.py` に二つ塞いである。Playwright の
`wait_for_timeout` で待つとレンダラが休んで `setTimeout` が詰まり、映像がスロー
モーションになる。それと、録画中の進みは実行のたびに数秒ぶれるので、秒数で止めると
末尾が切れるか黒が残る。前者は 200ms ごとに `evaluate` で突いて起こし、後者は
エンジンが最後の場面を終えたときに立てる `body[data-done]` を見て止めている。

## なぜ MLT XML なのか

Kdenlive と Shotcut が同じ `.mlt` を開く。`edit/timeline.py` が書いた構成を人が GUI
で手直しでき、手直しした `.mlt` をまた `melt` で描画できる。AI が書ける編集
フォーマットで、人の手が入る余地が残っているものは他にない。

書き戻しは運転に入れていない。GUI で直したものを `timeline.py` へ反映する経路を作ると
どちらが正本か分からなくなる。GUI での手直しは最終調整として扱う。

## 構成

| 場所 | 中身 |
|---|---|
| `demos/*.yaml` | デモ 1 本。人が触るのはここだけ |
| `demos/*.md` | そのデモの注記。数字の出典、言い切りの線引き |
| `templates/` | 新しいデモの雛形 |
| `engine/engine.{css,js}` | ステージと再生の土台 |
| `engine/scenes/*.{css,js}` | 場面の型。増やすときはここに足す |
| `layers/*.yaml` | 画面をどう部品に切るか |
| `assets/3d/*.py` | 切った部品を 3D に置く Blender スクリプト |
| `assets/snippets/` | 使い回すコード片 |
| `tools/build.py` | YAML → 1 枚の HTML |
| `tools/record.py` `snap.py` | HTML → MP4 / 止め絵 |
| `edit/timeline.py` | 素材を並べて `.mlt` を書く |
| `out/` | 生成物。git には入れない |

## HTML のままにしないもの

画面そのものを映す場面——ブラウザ UI、コードエディタ、ターミナル——は HTML が正しい
素材で、3D で作り直すと遅いうえに嘘くさくなる。一方で HTML が原理的に出せないものが
四つある。モーションブラー、被写界深度、実光源が縁を拾う反射、フレームの正確さ。
「安っぽく見える」の正体はだいたいこれで、幾何の精度ではない。

そこで、UI はモデリングせず、部品ごとの透過 PNG に切り出して Blender の空間に板と
して並べる。文言を直したらレイヤーを撮り直すだけで、`.blend` の中のアニメーションは
そのまま生きる。手順は [docs/layers-and-3d.md](docs/layers-and-3d.md)。

クリエイタに渡すのは mp4 ではなく `.blend`。開けば板・カメラ・ライト・キーが全部
そこにあって、続きが作れる。

## 場面の型

いまあるのは 6 つ。足りなければ `engine/scenes/` に増やす（手順は
[docs/scenes.md](docs/scenes.md) の末尾）。

`card` は全画面の文字と数字。`browser` は事故を起こしているウェブアプリ。`code` は
レビューが見ている画面で、良い行と悪い行と「書かれなかった行」を出し分ける。`split`
は左に書いたものが箱になって飛び、空中で表記を変えて右の一部に着地する。`tree` は
依存の木を伸ばし、節を一つ開いて型の照合を見せてから残りに広げる。`terminal` は
出てくる成果物を実際に叩いて見せる。

## 踏んだ穴

MLT を手書きすると最初に当たるものが三つ。どれもエラーが出ないので、気づくまでが長い。
`edit/timeline.py` のコメントに同じことが書いてある。

`avformat-novalidate` を使わない。Kdenlive が書く `.mlt` に出てくるので真似したく
なるが、これは素材を調べない指定で、`length` を併せて書かないと尺が 1 フレームに
なる。1 フレームだけの動画が静かに出てくる。

`profile` に `colorspace` を書かない。書くと素材の色域へ変換がかかる。画面素材は
full-range で録れているので、709 を宣言した時点で目に見えて暗くなる。

フェードの `<filter>` には `in` / `out` を必ず付ける。付けないと素材の全長にかかり、
2 点しかない `level` のアニメーションが折り返して、真ん中がずっと暗いまま描画される。

HTML 側にも一つ。使っていない全画面レイヤーは `visibility:hidden` で合成から外す。
`opacity:0` のままだと毎フレーム合成され、録画中にメインスレッドが詰まって映像が
スローモーションになる。`:has()` のセレクタも同じ理由で使わない。

## 環境

NixOS 向けの `flake.nix` を置いてある。`nix develop` で mlt・ffmpeg・Blender・
Kdenlive・Shotcut・FreeCAD が揃う。Python の録画と組み立ては `uv run --with …` で
都度解決するので、shell には入れていない。

このディレクトリが親リポジトリで未追跡のまま flake を評価できるよう、Makefile は
`path:` スキームで flake を指している。
