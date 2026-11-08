# シーンの引数

デモ 1 本の台本は `out/<名前>/<名前>.yaml` 1 ファイル。`scenes` に場面を並べる。
動きは型が持っていて、YAML が決めるのは中身だけ。文言を変えれば画面に出る時間も
付いてくるので、まず文言を書いてから秒を疑う。

## 全体

| 鍵 | 既定 | 何を決めるか |
|---|---|---|
| `title` | ファイル名 | タブとコントロールに出る名前 |
| `accent` | `#5fd7d7` | 強調の 1 色。`<em>` と `<b>` がこの色になる |
| `reading.cps` | 5.5 | 1 秒あたりに読める文字数 |
| `reading.lead` | 0.9 | 目が文字に追いつくまでの頭（秒） |
| `reading.min` / `.max` | 2.4 / 5.2 | 1 枚の下限と上限（秒） |

保持時間は `lead + 文字数 / cps` を `min`〜`max` で挟んで決まる。日本語字幕の実務値
（4 CPS 基準・最大 7・1 枚 6 秒まで）の内側に取ってある。どの場面も `hold:` を書けば
秒で固定でき、`gap:` で前の場面との間（既定 0.42 秒）を変えられる。

## 共通の書き方

文章（`text` `band` `note` `labels.*`）には HTML をそのまま書ける。`<em>` と `<b>` が
accent 色、`<s>` が灰色、`<br>` が改行。

コード（`code` `lines` `need` `has` `error` `done`）は素のまま書く。色は `lang` から
付く。印は 2 つだけで、`{{ここ}}` が赤い差し、`<<ここ>>` が黄色い注記。

`icon` はファイルタブの色で、`cedar` `lean` `js` `ts` `sh` `json` が用意してある。

## card — 文字ドン・数字ドン

| 鍵 | 何を出すか |
|---|---|
| `text` | 真ん中の一行。長くすると自動で小さくなる |
| `number` | 0 から動いて着地する数字。`format: plain` で桁区切りを外す |
| `code` + `lang` | 文の下に置くコード |
| `tab` + `icon` | コードの上のファイル名 |
| `sub` | 小さい補足。使わないほうがよい |

連続する card は暗転を挟まずに入れ替わる。

## browser — 事故を起こしているウェブアプリ

`brand` `nav` `user{email,initial}` が枠、`url` `crumb` `files` が最初の画面。
`change` に二枚目を書くと、まず `url` の `{{ }}` だけが変わり、少し置いて `crumb` と
`files` が入れ替わって赤くなる。`change.stamp` が最後に出る一行。

`settle` は何事もない画面を見せておく秒数（既定 1.2）。ここが短いと事故が事故に
見えないので、1.8 前後を取るとよい。

## code — レビューが見ている画面

`lines` は `行番号 スペース コード` のブロック。空行は間隔になる。

`good` と `bad` は行番号の配列で、読ませたあとに色が付く。`badges` は行番号から
吹き出しの文言への対応。`missing: {after, text}` は「書かれなかった行」を
その行の後ろに開く。`note` は下に出る一文で、出た瞬間にコードが沈む。

`read` は色が付く前に読ませる秒数。

## split — 書いたものが右の一部になる

`left` と `right` にそれぞれ `tab` `icon` `lang` `code`。`left.fly` と `right.land` は
`"1-3"` のような行範囲で、左のその範囲が箱になって飛び、空中で右の表記に変わって
着地する。着地先は飛ぶまで見えない。

`band` は着地後に出る一文。`flight` は飛んでいる秒数（既定 1.25）。

## tree — 依存の木と型の照合

`root` が頂点、`levels.l1` `levels.l2` が名前付きの層、`levels.dots` が無名の点の数、
`axioms` が葉。幅は件数から割り付けるので、増やしても端は切れない。

`error` は木が伸びる前に一度出す失敗の形。`total` と `unit` が右下で数えあがる。
`labels` は 4 つの帯で、順に `built`（木ができた）`compare`（節を開いた）`ok`（全部
一致した）`fail`（一致しなかった）。

`inspect` は開く節の配列で、1 つめが一致する例、2 つめが一致しない例。各要素は
`node` `ok` `need` `has`、それに `read`（開いている秒数、既定 2.1）。見出しの文言は
`inspect_labels` の `need` `has` `ok` `ng`。

`done` は最後に出る一行。

## terminal — 出てくる成果物

`title` が窓の名前、`lines` が出力のブロック。1 行ずつ出る間隔は `gap_ms`（既定 390）。
`side` に `tab` `icon` `lang` `code` `after` を書くと、`after` 行目を出したところで
右の小窓が開く。

## 型を増やす

`engine/scenes/<名前>.css` と `<名前>.js` を足して、`D.register('<名前>', {mount, reset, play})`
を書く。`mount()` は一度だけ呼ばれて markup を返し、`play(s)` が YAML の 1 要素を受け取る。
`tools/build.py` の `BUILDERS` に変換関数を足せば、YAML 側で素のコードを書けるようになる。

## motion — 製品動画から抽出した動き

`preset` は `auto-layout`（要素の整列）、`spatial-carousel`（立体的なカード列）、
`cursor-zoom`（表の操作へズーム）のいずれか。`duration` は秒（既定6秒）。
文字による見出しを足さず、UIや図形の動きで伝える。

| 鍵 | 内容 |
|---|---|
| `brand` | UIのアプリ名。既定Orbit |
| `labels` | 整列するカード3枚、またはカルーセル7枚の名前 |
| `turns` | カルーセルの回転数。既定0.36 |
| `colors` | カルーセル用の7個の `#RRGGBB` |
| `rows` | 表の見出しを含む6行5列。データ行の最終列は数値 |

`labels` / `brand` / `rows` はプレーンテキストとして描く。HTML装飾は使わない。
出典、参考クリップ、Blender用テンプレート、差し替え方法は
[Motion library](../templates/library/README.md)を参照。

## incident — コードレビューとブログを並べる

左のendpointと、右のブログ下書きUIを同時に見せる。URLの投稿IDが3から7に変わる。

| 鍵 | 内容 |
|---|---|
| text / caption | 場面上部の見出し / 下部の字幕 |
| code / lang | 左のコードと構文色 |
| missing | 欠落している2行。codeの最初の空行に赤い挿入欄を開く |
| safe | trueならポリシー実行後の403を表示。省略時は他人の下書きを200で表示 |
| hold | URLを変えて結果を出した後の保持秒数 |
| timing | `settle`（最初の画面）、`request`（URL変更後）、`reveal`（結果表示後）の待ち秒数 |

## policy — ポリシー入力とビルド判定

codeにCedarの短いポリシー、schemaに正しい効果宣言、invalidに不整合がある宣言を書く。
行単位でポリシーを入力し、ビルド成功→不整合で失敗の2状態を見せる。
textは見出し。出典や保証の範囲は制作ノートに記録する。
映像中の結果は挙動を説明するアニメーションで、実際のビルド処理を起動しない。
timingで各待ち秒数を上書きできる。lineは入力1行、prepareは入力後、buildは検査中、
pass / failは成功・失敗の表示時間。

## kernel — Leanの証明依存ツリー

rootに定理名、propositionに短い命題、captionsに説明文の配列、durationに秒数。
textは左上の見出し。#kernelHeaderを文字と背景の合成用レイヤーとして切り出す。
3d/kernel.mp4がHTMLから見える相対位置にあれば、そのBlender映像を再生する。
未生成ならHTMLの概形を再生する。タイムラインへの差し替えはlayers/kernel.yamlで指定。
speedは再生倍率（既定1）。durationは元動画の秒数で、実際の尺はduration / speed。
HTMLとMP4の両方に反映し、元のBlender動画は保持する。編集用の加速素材はbuild/retimed/にキャッシュする。
inspectionsにノードの一時表示を記述する。titleは宣言名、descriptionは短い説明、codeは定義や型の抜粋。
`D.Scenes.kernel.inspect(s, i)`でHTMLの内容を設定し、layers/kernel.yamlから透過画像として切り出す。
球体・輪・接続線と表示のタイミングはshots/kernel.pyで構成する。常駐する小さな補題ラベルは使わない。

## cardの追加フィールド

unitは数字の単位。補足説明やリンクはsubに記述する。番号付きの小見出しや細かい脚注は表示しない。
styleはhero（青緑の明るい背景）、danger（赤い数字）、brand（大きい製品名）。
count_msで数字が最終値に到達する時間をミリ秒で指定できる。holdはカウント後の保持秒数。

## 場面転換

全体の設定に transition: {duration: 0.4} を指定すると、場面間の空白をなくし、
前の画面を残したまま次へ溶かす。durationは秒数。指定がなければ従来の再生方法を使う。
HTMLでは動画の最終フレームも保持し、次の画面が準備できてから切り替える。
録画素材も最終状態を保持し、MP4では同じ長さで末尾と先頭を重ねる。
MLT / Kdenliveでは、その境目が短い独立したクリップとして並ぶ。

## study — 分野別の短いモーション

`preset` は `terminal-flow`（端末の入力・選択・処理）、`code-diff`（コード差分）、
`network-globe`（地球上の取引の流れ）、`market-chart`（金融チャート）。
`duration` は秒（既定4.8秒）。表示内容はアニメーション用の合成データ。

`network-globe` の `texture_path` には地表画像のローカルパスを渡す。
ビルド時にHTMLへ埋め込む。画像準備の `ready` Promiseを公開し、ライブラリの録画は準備完了を待つ。
通常の台本では `type: study` と `preset`、`duration` で呼び出せる。
出典・使用条件は [素材台帳](../templates/library/ASSETS.md)、一覧生成は
[ショーケースの手順](../templates/library/README.md)を参照。
