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
| `macro-controls` | OP–XY | 斜光と近接ドリー | Blender / EEVEE |
| `drone-orbit` | DJI Mavic 4 Pro | 機構へ寄り、機体を回り込む | Blender / EEVEE |
| `humanoid-articulation` | Unitree G1 | 肩と肘の協調動作 | Blender / EEVEE |
| `orbital-earth` | NASA EPIC | 地表・雲・大気の縁と自転 | Blender / EEVEE |
| `terrain-flyover` | Mapbox GL JS | 起伏を横切るカメラ | Blender / EEVEE |
| `terminal-flow` | Charm Gum | 入力、選択、処理、完了 | HTML / Canvas |
| `code-diff` | GitHub Copilot / VS Code | 同じ場所で変更と結果を見せる | HTML / Canvas |
| `network-globe` | XNOHub | 地球上を移動する取引の光 | HTML / Canvas |
| `market-chart` | TradingView | 金融チャートを描き進める | HTML / Canvas |

選定根拠、公式・作者の出典ページ、原素材内の開始・終了秒、動きの構成、翻案した点は
[`catalog.yaml`](catalog.yaml) に記録する。タイムコードはページ内の個別動画を起点とする。
発表イベント全編のタイムコードではない。元映像を実際に確認してから登録する。
金融・ブロックチェーン・コード・端末の再現データは、アニメーション用の合成データ。
実際の相場、取引、コマンド実行、テスト結果を示さない。

## 作る・見る

```sh
make library-list
make library                     # 参考取得 → 素材取得 → 再現MP4 → 一覧
xdg-open out/template-library/index.html

make library-collect ID=port-orbit
make library-render ID=port-orbit
make library-catalog
make library-check               # 尺・フレーム数・ハッシュ・デコードを検査

# コードを変えた後、対象だけ再生成する
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id port-orbit --force
```

`uv`、Chromium / Playwright、FFmpegを使う。3DにはBlender 5.xが必要。
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
  hardware.py                     モデル取込、地形、照明、カメラ、関節のテンプレート
  gallery.html                    シンプルな比較一覧の雛形
  software-demo.yaml              通常台本で使う例
engine/scenes/motion.{js,css}      整列・カルーセル・ズーム
engine/scenes/study.{js,css}       TUI・コード・ネットワーク・金融
tools/template_library.py         一覧・取得・再現・ショーケース生成
tools/library_assets.py           外部素材の取得とハッシュ記録
out/template-library/             ローカル成果物。Git管理外
  index.html                      デモ素材ショーケース
  references/<id>.mp4, .json       参考クリップと出典・取得時刻・SHA-256
  renders/<id>.mp4, .jpg, .json    再現映像・ポスター・設定・SHA-256
  assets/                         外部素材と取得元・条件・SHA-256
  build/<id>/                     フレーム列、HTML、台本、ログ
  build/<id>/<id>.blend           編集可能な3Dプロジェクト
```

## 3Dは形と素材から始める

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

ドローンは質感付きのCesium Droneモデル、G1はUnitree公開のURDFとSTLを利用する。
G1の再現は関節を見せるキーフレームアニメーションで、歩行制御や動力学の検証ではない。
地形はMapzen / TilezenのTerrarium標高画像を復号し、富士山周辺の地形メッシュへ変換する。
地球は公開の地表と雲のテクスチャを別レイヤーにする。日食の物理計算は含めない。

`hardware.py` は `--config` のJSONから `model_path`、`hdri_path`、`texture_path`、
`clouds_path`、`terrain_path` を受け取る。モデルはUSDZ / USD / glTF / GLB / blendに対応。
`model_rotation` は度単位のXYZ、`body_width` はモデルの正規化後の幅。
光源やカメラ位置は同じ正規化座標に置く。`.blend` には画像をパックする。
`motion_duration` は動き全体の秒数。`duration` を短くすると、その動きの前半だけを出力できる。
マクロカットは6秒の動きのうち前半3.2秒を使う。

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
地球上のネットワークには `texture_path` へ地表画像のローカルパスを指定する。
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
