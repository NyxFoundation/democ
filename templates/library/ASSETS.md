# 素材の出典と利用範囲

ショーケースの画面外に置く制作記録。実ファイルのURL、SHA-256、取得記録は
[assets.yaml](assets.yaml) と `out/template-library/assets/*.json` に保存する。
参考動画の出典と抜粋範囲は [catalog.yaml](catalog.yaml) にある。

| 使用箇所 | 素材・作者 | 条件・記録 |
| --- | --- | --- |
| Mac mini | [Apple Mac mini AR](https://www.apple.com/mac-mini/) | Apple公開USDZ。ローカル研究用。オープンコンテンツのライセンスではない。モデル・画像はGitへ含めない。 |
| Mac Studioの差し替え素材 | [Apple Mac Studio AR](https://www.apple.com/mac-studio/) | 同上。モデルはキャッシュ済み。 |
| スタジオ照明・反射 | [Studio Small 05](https://polyhaven.com/a/studio_small_05) — Greg Zaal / Poly Haven | CC0。実写のHDRI。 |
| 操作部の接写 | [Boombox](https://polyhaven.com/a/boombox) — Thomas Paul Mouilleron | CC0。作者の印字・UV・PBRマップを保持し、`macro-controls`へ採用。 |
| ドローン | [Cesium Drone](https://github.com/CesiumGS/cesium/tree/main/Apps/SampleData/models/CesiumDrone) — Ed Mackey / Analytical Graphics, Inc. | CC BY 4.0。原GLBのcopyright欄にも作者・条件がある。DJIの機体そのものではない。 |
| ヒューマノイド | [Unitree G1](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description) — Unitree Robotics | リポジトリのBSD-3-Clause。URDF・STLと共にLICENSEを取得し、著作権表示・免責を保持。 |
| 地表・雲 | [Solar System Scope textures](https://www.solarsystemscope.com/textures/) — Solar System Scope / INOVE | CC BY 4.0。NASA等の観測データを元に調整された地図。地表と雲を別レイヤーで使用。 |
| 地形 | [Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) — Mapzen / Tilezen | Terrarium z10/x906/y404、富士山周辺。元データごとの条件を引き継ぐ。標高を任意の山に置き換えた合成データではない。 |

## CC0の追加素材

2026-11-08に実データを取得。モデルは全12点をBlenderで読み込み、Cyclesの確認用画像と
テクスチャをパックした`.blend`を `out/template-library/materials/<asset-id>/` に保存した。
元ファイル・作者・条件・依存テクスチャは`assets.yaml`、取得時刻とファイルごとのハッシュは
`out/template-library/assets/`内のJSONに記録する。再取得は`make library-materials`。

| 素材 | 作者 | 確認・用途 |
| --- | --- | --- |
| [Camera 01](https://polyhaven.com/a/Camera_01) | Rajil Jose Macatangay | UV・2K PBR確認。レンズ、金属、革、印字の接写候補。 |
| [Boombox](https://polyhaven.com/a/boombox) | Thomas Paul Mouilleron | 操作部の接写に採用。 |
| [Portable Cassette Player](https://polyhaven.com/a/portable_cassette_player) | Mateusz Sadek | 外装・テープ・印字の確認画像を保存。 |
| [Vintage Radio Transceiver](https://polyhaven.com/a/vintage_radio_transceiver) | Mateusz Sadek | 部品・配線・ケースを確認。全体撮影ではアンテナを含む長さに注意。 |
| [Classic Laptop](https://polyhaven.com/a/classic_laptop) | Arrangemonk | 印字・キー・外装の確認画像を保存。レトロ機器向け。 |
| [Circuit Board](https://polyhaven.com/a/circuit_board) | Benny Weimer | 基板・端子・部品の確認画像を保存。 |
| [Digital Wrist Watch](https://polyhaven.com/a/digital_wrist_watch) | Adrian C | 文字盤・金属バンドを確認。全長と文字盤の接写を分けて構図を調整する。 |
| [Vintage Spacecraft Instrument](https://polyhaven.com/a/vintage_spacecraft_instrument) | Michał Wiśniewski | パネル・ノブ・塗装の確認画像を保存。 |
| [Over-ear Headphones](https://www.innerscene.com/tools/library/3d-parts/over-ear-headphones-de211466) | Innerscene | サブカット候補。均一な表面が目立つため主役の接写には未採用。 |
| [Wireless Earbuds](https://www.innerscene.com/tools/library/3d-parts/wireless-earbuds-with-case-4599339a) | Innerscene | 同上。 |
| [Desktop Synthesizer](https://www.innerscene.com/tools/library/3d-parts/patch-voice-synthesizer-0b3e851c) | Innerscene | 同上。 |
| [FPV Racing Drone](https://www.innerscene.com/tools/library/3d-parts/fpv-racing-drone-037b67bd) | Innerscene | 同上。機体の実製品名を示すモデルではない。 |
| [Studio Small 03](https://polyhaven.com/a/studio_small_03) | Greg Zaal / Poly Haven | CC0の実写HDRI、2K。 |
| [Studio Small 09](https://polyhaven.com/a/studio_small_09) | Sergej Majboroda / Poly Haven | CC0の実写HDRI、2K。 |
| [Metal 012](https://ambientcg.com/view?id=Metal012) | ambientCG / Lennart Demes | CC0、2K PBR一式。手続き的に作られたブラッシュドスチール。Appleのアルミ外装とは別の材質。 |

配布条件の原文: [Poly Haven](https://polyhaven.com/license)、
[Innerscene Free Parts Library](https://www.innerscene.com/tools/library/terms)、
[ambientCG](https://docs.ambientcg.com/license/)。
登録前に取得に失敗した素材は、収集済みの件数へ含めない。

## 既存素材の補足

地形の出典: Terrain Tiles was accessed on 2026-11-08 from
https://registry.opendata.aws/terrain-tiles.
Global ETOPO1 terrain data: U.S. National Oceanic and Atmospheric Administration.
Global GMTED2010 and SRTM terrain data: U.S. Geological Survey.
地域別の追加条件は [Tilezenのattribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) と
[データソース一覧](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md)を参照。

参考のNASA映像: NASA / DSCOVR EPIC —
[An EPIC View of the 2017 Total Solar Eclipse](https://images.nasa.gov/details/GSFC_20170822_Total_m12690_Eclipse)。
再現は地球の見せ方を研究したもので、日食や太陽系の物理シミュレーションではない。

外部素材は利用条件ごとに扱う。ダウンロードできることを、再配布・商用利用の許可と読み替えない。
Appleの条件は [Website Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html)、
その他の条件は素材台帳の `license_url` に残す。別の製品へ転用する際は、モデルを用途に許諾された素材へ替える。
