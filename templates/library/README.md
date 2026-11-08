# デモ素材ショーケース

参考クリップと、別の製品へ使える再現コードを蓄積する。
一覧には映像、製品名、ファイルとソースへのリンクだけを表示する。
出典の説明、秒数、素材の条件、再現で変えた点はこのディレクトリと取得記録へ置く。

| ID | 参考 | 残した動き | 再現 |
| --- | --- | --- | --- |
| `auto-layout` | Figma Slides | 操作から整列へ | HTML |
| `spatial-carousel` | Framer | カードが立体的に連なる | HTML |
| `cursor-zoom` | Screen Studio | 操作箇所への寄り、パン、引き | HTML |
| `port-orbit` | Mac mini | 天面から前面、背面へ | Blender / Cycles |
| `rim-reveal` | AirPods Pro | 輪郭から質感へ | Blender / Cycles |
| `macro-controls` | OP–XY | 斜光と近接ドリー | Blender / Cycles |
| `drone-orbit` | DJI Mavic 4 Pro | 機構へ寄り、機体を回り込む | Blender / EEVEE |
| `humanoid-articulation` | Unitree G1 | 接地と足の振り出し、腕振り | Blender / EEVEE |
| `orbital-earth` | NASA EPIC | 地表・雲・大気の縁と自転 | Blender / EEVEE |
| `terrain-flyover` | Mapbox GL JS | 起伏を横切るカメラ | Blender / EEVEE |
| `terminal-flow` | Charm Gum | 公式デモの入力と質問 | HTML / xterm.js / 実PTY出力 |
| `code-diff` | GitHub Copilot / VS Code | 計画からコードの変更へ | HTML / Monaco / 公式CSS・テーマ |
| `network-globe` | XNOHub | 地球上を移動する取引の光 | HTML / Three.js / WebGL |
| `market-chart` | TradingView | 重なるチャートから価格線へ寄る | HTML / Lightweight Charts / CSS 3D |

選定根拠、公式・作者の出典ページ、原素材内の開始・終了秒、動きの構成、翻案した点は
[`catalog.yaml`](catalog.yaml) に記録する。タイムコードはページ内の個別動画を起点とする。
発表イベント全編のタイムコードではない。元映像を実際に確認してから登録する。
金融・ブロックチェーン・コード・端末の再現データは、アニメーション用の合成データ。
実際の相場、取引、Copilotの実行、テスト結果を示さない。
Gumは公式のシェルを実際に実行した出力を記録して再生する。
4本のUIに取り込んだ公開ソースと再構成した範囲は[`source-ui/SOURCES.md`](source-ui/SOURCES.md)へ。

## 作る・見る

```sh
make library-list
make library                     # 参考取得 → 素材取得 → 再現MP4 → 一覧
xdg-open out/template-library/index.html

make library-collect ID=port-orbit
make library-render ID=port-orbit
make library-catalog
make library-check               # 尺・フレーム数・ハッシュ・デコードを検査
make library-materials           # CC0素材取得 → Blender試し描画 → 素材一覧
make library-materials-list
xdg-open out/template-library/materials/index.html

# コードを変えた後、対象だけ再生成する
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id port-orbit --force
```

`uv`、Chromium / Playwright、FFmpegを使う。上記4本の初回ビルドにはNode.js / npmが必要。
出力したHTMLはライブラリ・フォント・Workerを内包し、オフラインでも再生できる。
3DにはBlender 5.xが必要。
PATHにない場合は `nix develop .#full` 内で実行する。既存の動画はスキップする。
`--force` で対象を再生成する。取得失敗はエラーで止まり、収録済みとして扱わない。
比較一覧へは参考・再現の両方が揃った項目だけを載せる。
見えているカットは無音で自動再生する。行の再生ボタンで2本を最初から再生できる。
`prefers-reduced-motion` が有効な環境では手動再生にする。

初期出力は960×600・25fps・音声なし。参考映像の縦横比は維持して余白を付ける。
再現映像は16:10。透過PNGは黒背景へ合成してから動画へ変換し、輪郭の白浮きを防ぐ。
尺はフレーム単位へ丸める。参考と再現の尺が異なる項目もある。
Blenderのエンジンとサンプル数は台帳で指定する。高品質出力の例:

```sh
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id port-orbit --width 1600 --height 1000 --engine cycles --samples 96 --force
```

```text
templates/library/                Gitに残す選定記録とコード
  catalog.yaml                    出典・秒数・動き・翻案・初期設定
  assets.yaml                     外部モデル・画像・HDRIの取得元と条件
  ASSETS.md                       素材の出典とクレジット
  hardware.py                     モデル取込とBlenderシーンの組立
  quality_scenes.py               製品、歩行、地球、衛星地形のカット
  gallery.html                    シンプルな比較一覧の雛形
  software-demo.yaml              通常台本で使う例
engine/scenes/motion.{js,css}      整列・カルーセル・ズーム
engine/scenes/study.{js,css}       各分野の再生制御
engine/scenes/source-ui.{js,css}   端末・エディタ・金融UI
engine/scenes/network-globe.{js,css} XNOHub由来のWebGL
tools/template_library.py         一覧・取得・再現・ショーケース生成
tools/library_assets.py           外部素材の取得とハッシュ記録
out/template-library/             ローカル成果物。Git管理外
  index.html                      デモ素材ショーケース
  references/<id>.mp4, .json       参考クリップと出典・取得時刻・SHA-256
  renders/<id>.mp4, .jpg, .json    再現映像・ポスター・設定・SHA-256
  assets/                         外部素材と取得元・条件・SHA-256
  materials/index.html            CC0モデル・照明・マテリアルの一覧
  materials/<asset-id>/            確認用PNG、画像パック済み.blend、取得元と設定
  build/<id>/                     フレーム列、HTML、台本、ログ
  build/<id>/<id>.blend           編集可能な3Dプロジェクト
```

## 3Dは形と素材から始める

CC0のモデル12点、スタジオHDRI 3点、PBRマテリアル1組を取得・再利用できる。
モデル8点はPoly Havenの質感付きデータ。カメラ、ラジカセ、カセットプレーヤー、無線機、
ノートPC、基板、腕時計、宇宙機器を収集した。2KのUV・法線・粗さ・金属度マップも揃えて取得する。
Innersceneのヘッドホン、イヤホン、シンセサイザー、FPVドローン4点も保存済みだが、
形状や表面が単純なのでサブカット向けの候補として分けている。
モデル12点はCyclesの中立照明で実際に描画し、画像と編集用のパック済み`.blend`を残す。
照明・素材の単体取得とプレビュー生成は次で再実行できる。

```sh
uv run --with pyyaml python3 tools/library_materials.py fetch --id ph-camera-01
uv run --with pyyaml python3 tools/library_materials.py inspect --id ph-camera-01 --force
uv run --with pyyaml python3 tools/library_materials.py catalog
```

`all` はCC0素材だけを対象にする。AppleのARモデルはこの一括取得に含めない。
PBRのZIPは検査してから同名ディレクトリへ展開し、原本と展開後のハッシュを残す。
一覧の「元ファイル」は取得した原本、「Blender」は照明・カメラ・画像を含む編集用ファイル。
`quality_status` は素材の確認結果で、最終動画の画質保証ではない。

操作面の接写`macro-controls`は、自作のノブ列からPoly HavenのBoomboxへ差し替えた。
印字・メッシュ・表面の傷を保持し、Cyclesと移動する面光源で撮影する。
OP–XYはカメラと光の参考で、モデルの製品は異なる。

1. 公式のARモデル、作者公開のCAD / URDF / glTF、質感付きモデルを探す。
   製品の世代・比率・端子・可動部を画像と照合する。入手できる品質の高いモデルを優先する。
2. 出典、作者、使用条件、解像度、SHA-256を `assets.yaml` と取得記録へ残す。
   ファイルを入手したことと、再配布・商用利用の許諾を区別する。
3. UV、ノーマル、粗さ、材質の割当を保持して読み込む。画一的な銀色へ上書きしない。
   角の半径、段差、端子の内側、パネルの隙間が読めるかを見る。
4. 実写のスタジオHDRIを反射と環境光に使う。面光源の形・位置・大きさを調整し、
   広い反射と締まったエッジを作る。汚れや強いノイズを足して実写らしさの代用にしない。
5. マットなアルミ、光沢のあるロゴ、黒い樹脂、ゴム、端子の金属を分けて調整する。
   サンドブラストの粒は接写でわずかに読める強さに留める。
6. 少数の代表フレームで形・反射・接地影・カメラの距離を直してから動画を出す。
   素材の差し替え後はカメラを合わせ直す。天面や足元を画面外へ切らない。

Mac miniはApple公開ARモデルの形状・UV・材質を取り込み、写真ベースのHDRIとCyclesで撮影する。
Mac StudioのARモデルも素材台帳に登録済み。同じモデル取り込み口で使用できる。
これらのApple素材はローカル研究用としてキャッシュし、リポジトリへ含めない。
商用・配布向けには、その用途に許諾されたモデルへ差し替える。

AirPodsはApple公式ARモデルの左右の本体を分離し、メッシュ・印字・元の材質を保持する。
ドローンはaurumjuda747のMavic 3 Cine（CC BY 4.0）。参考のMavic 4 Proとは機種が異なる。
G1はUnitree公開のURDF・STLの材質指定と関節位置を読み、脚の逆運動学で歩行を付ける。
実機の歩行制御や動力学の検証ではない。屋外照明はSergej MajborodaのUrban Courtyard 02（CC0）。
地形は参考と同じアゾレス諸島サンミゲル島。Terrarium標高16枚とEOXの2016年衛星画像64枚を
Mercator座標で結合して湖・カルデラ・海岸を再構成する。標高は1.65倍。
地球はNASA由来の8K地表とSolar System Scopeの8K雲を別レイヤーにする。日食の物理計算は含めない。

`hardware.py` は `--config` のJSONから `model_path`、`hdri_path`、`texture_path`、
`clouds_path`、`terrain_path` を受け取る。モデルはUSDZ / USD / glTF / GLB / blendに対応。
`model_rotation` は度単位のXYZ、`body_width` はモデルの正規化後の幅。
光源やカメラ位置は同じ正規化座標に置く。`.blend` には画像をパックする。
`motion_duration` は動き全体の秒数。`duration` を短くすると、その動きの前半だけを出力できる。
操作面の接写は3.2秒の一続きのドリー移動。

```sh
blender -b -t 8 -P templates/library/hardware.py -- \
  --preset port-orbit --out out/my-shot/frames --duration 3.5 \
  --engine cycles --samples 64 --config out/my-shot/materials.json
ffmpeg -framerate 25 -i out/my-shot/frames/f%04d.png \
  -filter_complex "color=black:s=960x600:r=25[bg];[bg][0:v]overlay=shortest=1:format=auto:alpha=straight[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p out/my-shot/shot.mp4

# 最初・中間・最後だけ確認する
blender -b -P templates/library/hardware.py -- \
  --preset port-orbit --out out/review/frames --duration 3.5 \
  --config out/my-shot/materials.json --frames 1,44,88
```

## 通常の台本へ使う

`motion` の `preset` は `auto-layout`、`spatial-carousel`、`cursor-zoom`。
`duration` は秒。`brand` はアプリ名、`labels` は整列なら3個・カルーセルなら7個。
`turns` はカルーセルの回転数、`colors` は7個の `#RRGGBB`。
`rows` は表の見出しを含む6行5列で、データ行の最終列を数値にする。

```yaml
transition: {duration: 0.2}
scenes:
  - type: motion
    name: 整列
    preset: auto-layout
    duration: 4.7
    brand: Your product
    labels: [Discover, Build, Ship]
  - type: study
    name: リリース
    preset: terminal-flow
    duration: 4.8
```

`study` の `preset` は `terminal-flow`、`code-diff`、`network-globe`、`market-chart`。
XNOHubのネットワークは元のThree.js実装を参照したWebGL。
`network-globe`は地表・雲・夜景・水域を初回に取得する。画像の差し替えは
`texture_path`・`clouds_path`・`night_path`・`water_path`で指定できる。
ビルド時に画像を埋め込むため、生成HTMLを単独で持ち運べる。
通常の `make edit` / 録画 / 編集パイプラインで利用できる。

BlenderのMP4を既存シーンへ差し替える場合は、`out/<demo>/layers/<shot>.yaml` の
`scene` にシーン番号（0起点）を指定し、MP4を `out/<demo>/build/3d/<shot>.mp4` に置く。
MLT / Kdenliveへ直接動画素材として追加することもできる。

## 次の一本を加える

1. 公式・作者の製品動画から、2〜8秒で一つの変化を見せる箇所を選ぶ。
   コンタクトシートと個別フレームで確認し、動きが曖昧なら連続再生も確認する。
2. `catalog.yaml` に出典ページ、安定した動画URL、素材内の秒数、動きの構成、翻案を書く。
   期限付きの署名URLを正本にしない。取得できない候補を採用済みと扱わない。
3. `collect --id <id>` で参考部分だけ取得する。取得済みの原素材なら
   `collect --id <id> --source /path/to/original.mp4` を使う。入力元は取得記録へ残る。
4. 素材を使う場合は `assets.yaml` へ登録し、項目の `assets` と `parameters` から参照する。
   `model_asset` / `hdri_asset` / `texture_asset` / `clouds_asset` / `terrain_asset` がローカルパスへ解決される。
5. HTMLは時間だけで絵が決まる `drawAt(scene, seconds)` を用意する。
   画像の準備が必要なら `ready` Promiseを公開する。ライブラリ録画は準備完了を待つ。
   BlenderはCLIのプリセット選択肢と分岐に追加する。
6. 代表フレームを見て、はみ出し、反射、関節、カメラの衝突、文字量、止まりすぎを直す。
   全区間を再生し、`render --id <id>`、`catalog` で一覧へ加える。

参考クリップと外部素材は `out/` に保存する。第三者素材の条件とクレジットは
[ASSETS.md](ASSETS.md) と素材台帳に残し、ショーケースの映像へ注釈として焼き込まない。
