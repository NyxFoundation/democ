# demo-creator

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Blender](https://img.shields.io/badge/Blender-5.x-E87D0D?logo=blender&logoColor=white)](https://www.blender.org/) [![FFmpeg](https://img.shields.io/badge/FFmpeg-MP4-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/) [![Demos](https://img.shields.io/badge/Demos-19-8957e5)](#デモ)

**プロダクトのデモを、コードでつくる。**

YAMLで場面を組み、HTMLとBlenderからMP4を出力します。
文言や動きを直して、同じ動画を何度でも書き出せます。

[デモ](#デモ) · [はじめる](#はじめる) · [編集する](#編集する) · [テンプレート](templates/library/README.md)

## デモ

UI・3D・タイポグラフィ・ニュース演出の19本。プレビューは自動再生し、クリックするとMP4を開きます。

<!-- demos:start -->

|  |  |  |  |
| :--- | :--- | :--- | :--- |
| **Figma Slides**<br>[<img src="docs/demos/auto-layout.gif" width="180" alt="要素が一つの秩序に揃う">](docs/demos/auto-layout.mp4)<br>[MP4](docs/demos/auto-layout.mp4) · [実装](engine/scenes/motion.js) | **Framer**<br>[<img src="docs/demos/spatial-carousel.gif" width="180" alt="平面が奥行きのある帯になる">](docs/demos/spatial-carousel.mp4)<br>[MP4](docs/demos/spatial-carousel.mp4) · [実装](engine/scenes/motion.js) | **Screen Studio**<br>[<img src="docs/demos/cursor-zoom.gif" width="180" alt="操作する場所へ視線が届く">](docs/demos/cursor-zoom.mp4)<br>[MP4](docs/demos/cursor-zoom.mp4) · [実装](engine/scenes/motion.js) | **Apple Mac mini**<br>[<img src="docs/demos/port-orbit.gif" width="180" alt="天面から機能面へ回り込む">](docs/demos/port-orbit.mp4)<br>[MP4](docs/demos/port-orbit.mp4) · [実装](templates/library/hardware.py) |
| **Apple AirPods Pro**<br>[<img src="docs/demos/rim-reveal.gif" width="180" alt="輪郭が質感へ変わる">](docs/demos/rim-reveal.mp4)<br>[MP4](docs/demos/rim-reveal.mp4) · [実装](templates/library/quality_scenes.py) | **teenage engineering OP–XY**<br>[<img src="docs/demos/macro-controls.gif" width="180" alt="斜光が操作面をなぞる">](docs/demos/macro-controls.mp4)<br>[MP4](docs/demos/macro-controls.mp4) · [実装](templates/library/hardware.py) | **DJI Mavic 4 Pro**<br>[<img src="docs/demos/drone-orbit.gif" width="180" alt="機体の輪郭と機構を追う">](docs/demos/drone-orbit.mp4)<br>[MP4](docs/demos/drone-orbit.mp4) · [実装](templates/library/quality_scenes.py) | **Unitree G1**<br>[<img src="docs/demos/humanoid-articulation.gif" width="180" alt="接地する足から動きが伝わる">](docs/demos/humanoid-articulation.mp4)<br>[MP4](docs/demos/humanoid-articulation.mp4) · [実装](templates/library/quality_scenes.py) |
| **NASA · EPIC**<br>[<img src="docs/demos/orbital-earth.gif" width="180" alt="地球の輪郭から広がるスケール">](docs/demos/orbital-earth.mp4)<br>[MP4](docs/demos/orbital-earth.mp4) · [実装](templates/library/quality_scenes.py) | **Mapbox GL JS**<br>[<img src="docs/demos/terrain-flyover.gif" width="180" alt="地形の起伏へ降りていく">](docs/demos/terrain-flyover.mp4)<br>[MP4](docs/demos/terrain-flyover.mp4) · [実装](templates/library/quality_scenes.py) | **Charm Gum**<br>[<img src="docs/demos/terminal-flow.gif" width="180" alt="入力が次の対話につながる">](docs/demos/terminal-flow.mp4)<br>[MP4](docs/demos/terminal-flow.mp4) · [実装](engine/scenes/source-ui.js) | **GitHub Copilot · VS Code**<br>[<img src="docs/demos/code-diff.gif" width="180" alt="計画からコードの変更へ">](docs/demos/code-diff.mp4)<br>[MP4](docs/demos/code-diff.mp4) · [実装](engine/scenes/source-ui.js) |
| **XNOHub**<br>[<img src="docs/demos/network-globe.gif" width="180" alt="取引の流れが世界をつなぐ">](docs/demos/network-globe.mp4)<br>[MP4](docs/demos/network-globe.mp4) · [実装](engine/scenes/network-globe.js) | **TradingView Advanced Charts**<br>[<img src="docs/demos/market-chart.gif" width="180" alt="重なるチャートから価格線へ">](docs/demos/market-chart.mp4)<br>[MP4](docs/demos/market-chart.mp4) · [実装](engine/scenes/source-ui.js) | **Apple · Type punch**<br>[<img src="docs/demos/type-punch.gif" width="180" alt="短い言葉がリズムをつくる">](docs/demos/type-punch.mp4)<br>[MP4](docs/demos/type-punch.mp4) · [実装](engine/scenes/typography.js) | **Apple · Letter flight**<br>[<img src="docs/demos/type-flight.gif" width="180" alt="散らばった文字が一つの言葉になる">](docs/demos/type-flight.mp4)<br>[MP4](docs/demos/type-flight.mp4) · [実装](engine/scenes/typography.js) |
| **Spotify Mix · Variable type**<br>[<img src="docs/demos/type-morph.gif" width="180" alt="文字の太さが波になって伝わる">](docs/demos/type-morph.mp4)<br>[MP4](docs/demos/type-morph.mp4) · [実装](engine/scenes/typography.js) | **Newsroom · Cascade**<br>[<img src="docs/demos/press-cascade.gif" width="180" alt="ニュースが加速して視界を埋める">](docs/demos/press-cascade.mp4)<br>[MP4](docs/demos/press-cascade.mp4) · [実装](engine/scenes/press.js) | **Newsroom · Wall**<br>[<img src="docs/demos/press-wall.gif" width="180" alt="一つの記事から広がりを見渡す">](docs/demos/press-wall.mp4)<br>[MP4](docs/demos/press-wall.mp4) · [実装](engine/scenes/press.js) |  |

<!-- demos:end -->

参考との比較、素材の取得元、再現コードは[デモ素材ショーケース](templates/library/README.md)へ。

## はじめる

```sh
git clone https://github.com/NyxFoundation/demo-creator.git
cd demo-creator
nix develop .#full
make new N=my-demo
make edit N=my-demo
```

ブラウザで確認しながら `out/my-demo/my-demo.yaml` を編集し、MP4を書き出します。

```sh
make out/my-demo/build/demo.mp4
```

完成ファイルは `out/my-demo/build/demo.mp4`。HTML・素材・編集用タイムラインも同じフォルダに残ります。

Nixを使わない場合は、Python 3.12・uv・Chromium・FFmpeg・MLT（`melt`）を用意してください。
3DにはBlender 5.x、UIテンプレートの初回ビルドにはNode.js / npmを使います。

## 編集する

### タイトル・文言・尺

編集するファイルは `out/my-demo/my-demo.yaml` です。
映像内の見出しは `text`、ブラウザのプレビュー名は先頭の `title` で変えます。

```yaml
title: My Product
accent: "#5fd7d7"
transition: {duration: 0.3}
scenes:
  - type: card
    text: "アイデアから、<br><em>公開まで。</em>"
    hold: 2.4
  - type: card
    text: "github.com/your/project"
    hold: 2.0
```

`scenes`の順番を変えると場面が入れ替わります。`hold`は表示秒数、`transition.duration`は場面転換の秒数です。
型ごとの設定は[シーン一覧](docs/scenes.md)を参照してください。

```sh
make watch N=my-demo                     # 保存するとHTMLを更新
make edit N=my-demo                      # ブラウザで確認。更新はF5
make out/my-demo/build/demo.mp4          # 変更した場面を再収録して書き出し
```

### 動画の見た目・3D・カット割り

| 変えたいもの | 編集する場所 |
| --- | --- |
| UIの配置・配色・アニメーション | `engine/scenes/` のJS / CSS |
| Blenderの形・質感・カメラ | `out/my-demo/shots/` のPythonと`.blend` |
| 3Dに置き換える場面 | `out/my-demo/layers/` のYAML |
| 最終的なカットの並び・長さ | `make open N=my-demo` でKdenliveを開く |

3Dを直したら `make 3d`、その後にMP4を書き出します。
GUIでの編集は最終調整に使い、文字は元のYAMLで直してください。
[3Dの作成手順](docs/layers-and-3d.md) · [パイプラインと実装ノート](docs/architecture.md)

### ショーケースのサンプルを編集する

[台帳](templates/library/catalog.yaml)の`title`・`duration`・`parameters`と、各サンプルの実装を編集して対象だけ再出力できます。

```sh
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id terminal-flow --force
make library-catalog                   # 比較サイトを更新
make readme-demos ID=terminal-flow      # READMEのプレビューとMP4を更新
```

## テンプレートと素材

```sh
make new N=my-demo FROM=nyxis           # 既存のデモから作る
make library                           # 参考・再現・比較サイトを生成
make library-materials                 # フリー素材を取得してBlenderで確認
make example N=my-demo                 # 台本とソースをexamples/へ保存
```

通常の作業と生成物は `out/`、共有する台本は `examples/` に置きます。
README用の短いプレビューとMP4は `docs/demos/` に保存します。
素材の出典と利用条件は[素材台帳](templates/library/ASSETS.md)、公開ソースの使用範囲は[UIの実装元](templates/library/source-ui/SOURCES.md)へ。

## コントリビュート

シーンやテンプレートの追加・改善はIssue / Pull Requestからどうぞ。
新しい場面の引数と実行例を[シーン一覧](docs/scenes.md)に追加し、生成したHTMLとMP4で動きを確認してください。
