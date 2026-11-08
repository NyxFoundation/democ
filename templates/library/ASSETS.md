# 素材の出典と利用範囲

ショーケースの画面外に置く制作記録。実ファイルのURL、SHA-256、取得記録は
[assets.yaml](assets.yaml) と `out/template-library/assets/*.json` に保存する。
参考動画の出典と抜粋範囲は [catalog.yaml](catalog.yaml) にある。

| 使用箇所 | 素材・作者 | 条件・記録 |
| --- | --- | --- |
| Mac mini | [Apple Mac mini AR](https://www.apple.com/mac-mini/) | Apple公開USDZ。ローカル研究用。オープンコンテンツのライセンスではない。モデル・画像はGitへ含めない。 |
| Mac Studioの差し替え素材 | [Apple Mac Studio AR](https://www.apple.com/mac-studio/) | 同上。モデルはキャッシュ済み。 |
| スタジオ照明・反射 | [Studio Small 05](https://polyhaven.com/a/studio_small_05) — Greg Zaal / Poly Haven | CC0。実写のHDRI。 |
| ドローン | [Cesium Drone](https://github.com/CesiumGS/cesium/tree/main/Apps/SampleData/models/CesiumDrone) — Ed Mackey / Analytical Graphics, Inc. | CC BY 4.0。原GLBのcopyright欄にも作者・条件がある。DJIの機体そのものではない。 |
| ヒューマノイド | [Unitree G1](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description) — Unitree Robotics | リポジトリのBSD-3-Clause。URDF・STLと共にLICENSEを取得し、著作権表示・免責を保持。 |
| 地表・雲 | [Solar System Scope textures](https://www.solarsystemscope.com/textures/) — Solar System Scope / INOVE | CC BY 4.0。NASA等の観測データを元に調整された地図。地表と雲を別レイヤーで使用。 |
| 地形 | [Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) — Mapzen / Tilezen | Terrarium z10/x906/y404、富士山周辺。元データごとの条件を引き継ぐ。標高を任意の山に置き換えた合成データではない。 |

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
