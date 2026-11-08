# 参考の実装を使うUI

`terminal-flow`、`code-diff`、`market-chart`、`network-globe`の実装元。
生成したHTMLへJS・CSS・フォント・端末出力を内包し、ネット接続やログインなしで再生する。
外枠と動きは`engine/scenes/source-ui.{js,css}`、組立は`tools/source_ui.py`。
依存するnpmパッケージは`package-lock.json`のバージョンとintegrityで固定する。

| 対象 | 取り込んだ実装 | 再構成した部分 |
| --- | --- | --- |
| VS Code / Copilot | [Monaco Editor](https://github.com/microsoft/monaco-editor) 0.57.0、[Codicons](https://github.com/microsoft/vscode-codicons) 0.0.46-24、[GitHub Theme](https://github.com/primer/github-vscode-theme)、[VS Codeのchat.css](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/chat/browser/widget/media/chat.css) | 参考のTrail Atlas、ファイルツリー、search.js、計画カードと入力欄のDOM。コードの色分け・行番号・差分はMonaco自身が描画。Copilot APIやテストの実行は行わない。 |
| Charm Gum | [公式demo.sh](https://github.com/charmbracelet/gum/blob/main/examples/demo.sh)、[demo.tape](https://github.com/charmbracelet/gum/blob/main/examples/demo.tape)、Gum v0.17.0、[xterm.js](https://github.com/xtermjs/xterm.js) 6.0.0 | 元が端末アプリなのでHTMLは存在しない。実際に公式シェルをPTYで実行し、ANSI出力を記録してxterm.jsで再生。余白・文字幅・パレットと入力タイミングを参考へ合わせる。 |
| TradingView | [Lightweight Charts](https://github.com/tradingview/lightweight-charts) 5.2.1 | チャート自体は公式ライブラリ。ツールバー・パネルの配置・紫の光・反射・カメラは参考に合わせたDOM / SVG / CSS。Advanced Chartsそのものの複製ではない。価格は固定seedの合成データ。 |
| XNOHub | [XNOHub.com](https://github.com/dalindev/XNOHub.com) の `three-mesh.tsx`、`network-arc.tsx`、`nano-rep-nodes.tsx`、Three.js 0.166.1 | 地球のPhong材質、23.5度の傾斜、緯度経度変換、大円の補間と浮き上がりを参照して `engine/scenes/network-globe.js`へ移植。公開ノード87地点を使い、奥側の経路を実際の深度テストで隠す。Reactとライブ取引ストリームは省き、表示金額・経路の組合せ・発光時刻を固定。画面の外枠はDOMで再構成。 |

Advanced Chartsは[ソースが公開されていない製品](https://www.tradingview.com/free-charting-libraries/)。
この実装に非公開のコードや、ログインを必要とするライブラリは含めない。
Lightweight Chartsの標準のTradingViewロゴを残し、LICENSE・NOTICEも出力HTMLへ保持する。

## 保存している原本

- `vscode/chat.css`と`vscode/LICENSE.txt`はMicrosoftのMITライセンスのソース。
- `github-theme/theme.cjs`はPrimerの`src/theme.js`のコピー。拡張子を変更し、`colors.js`とMITライセンスを同梱する。色の生成には原本と同じ`@primer/primitives` 7.10.0を使う。
- `gum/demo.sh`、`gum/demo.tape`とMITライセンスを保存。`recording.json`は実際の端末出力で、元スクリプトのSHA-256を含む。
- JetBrains Monoは`assets.yaml`の取得元とSHA-256で固定し、SIL OFLを`font-OFL.txt`に保持する。
- `xno/nodes.json`は公開の`data/defualtMergedRepsData.ts`から緯度・経度だけを抽出したもの。IPやアカウントは含めない。`xno/LICENSE.txt`は原本のMIT表記を保持する。参照コミット、原本のSHA-256、確認用コピーのSHA-256は`upstream-manifest.json`にある。
- npmのLICENSE・NOTICEと上記ライセンスは、生成HTMLのコメントにも内包する。

取り込んだテキストは行末スペースと末尾の余分な空行を正規化している。
取得したソースのハッシュは`upstream-manifest.json`。コピーに手を加えるときは更新内容をここへ記録する。
動画上に制作注釈は足さず、出典と翻案した範囲を制作記録に置く。

## 再生成

```sh
make library-render ID=terminal-flow
make library-render ID=code-diff
make library-render ID=market-chart
make library-render ID=network-globe

# 既存MP4を置き換える場合
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id terminal-flow --id code-diff --id market-chart --force

# Gumの実行出力を取り直す（GoとBashが必要）
uv run python3 tools/capture_gum.py
```

初回ビルドはNode.js / npmとネット接続が必要。`npm ci`後にesbuildでまとめ、
MonacoのWorkerもBlobへ内包する。ビルド後のHTML再生・動画生成には接続不要。
フォントが確定してから部品を作成し、端末の文字幅が最初のフレームだけ変わるのを防ぐ。
HTMLの収録はDPR 2、出力PNGは指定したCSSピクセルの寸法。接写するチャートも鮮明さを保つ。

Gum収録時の調整は、NixOS向けのshebang、ヘルプ非表示、細い入力プロンプト、緑のカーソル。
`NO_COLOR`は収録する子プロセスだけで解除する。元のデモスクリプトは上書きしない。
