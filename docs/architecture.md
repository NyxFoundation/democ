# パイプラインと実装ノート

## デモ1本の構成

```text
out/my-demo/
  my-demo.yaml          場面・文言・表示時間の正本
  notes.md              出典と制作メモ
  layers/*.yaml         3Dへ置き換える場面と部品の指定
  shots/*.py            Blenderの形状・照明・カメラ
  build/
    page.html           生成したプレビュー
    screens/            場面ごとのMP4とハッシュ
    parts/              部品ごとの透過PNG
    3d/                 Blender出力と編集可能な.blend
    edit.mlt            MLTのタイムライン
    edit.kdenlive       Kdenlive向けタイムライン
    demo.mp4            完成動画
```

`tools/build.py`がYAMLを1枚のHTMLへ組み立てる。`tools/record.py`で場面ごとに収録し、
`edit/timeline.py`でMLTへ並べて、`melt`で最終MP4を書き出す。
3Dの指定がある場面には、Blenderで描画したクリップを使う。

## ソースの場所

| 場所 | 役割 |
| --- | --- |
| `templates/starter.yaml` | 新規デモの雛形 |
| `examples/` | `make new FROM=`で複製できる台本 |
| `engine/engine.{css,js}` | ステージ・再生・場面転換 |
| `engine/scenes/` | 場面ごとのレイアウトと動き |
| `templates/library/catalog.yaml` | 参考映像・尺・再現の設定 |
| `templates/library/hardware.py` | 素材を取り込む3Dテンプレート |
| `templates/library/source-ui/` | 取り込んだUI実装・固定した依存関係・ライセンス |
| `tools/record.py` `tools/snap.py` | 動画収録・静止画確認 |
| `tools/readme_demos.py` | READMEのプレビューとMP4の更新 |

## 更新と収録

画面の正本はYAMLとJS / CSS。Kdenliveに入るMP4には文字が焼き込まれているので、
文字を直すときはYAMLを更新して再出力する。
GUIで変更したタイムラインをPythonへ自動的に書き戻す処理はない。

収録は場面ごとに分け、内容のハッシュが変わった場面だけを撮り直す。
コードを共通エンジンで変更した場合は、影響を受ける場面を再収録する。
録画の終端は秒数の見積もりではなく、エンジンの`body[data-done]`を使う。

`make 3d`は重い処理のため、通常の`make`では再実行しない。
3Dのソースを直したら`make 3d`を実行し、その後に最終MP4を出力する。
`make clean`が消すのは`out/*/build`。YAMLやショットのソースは保持する。

## MLTとHTMLの注意点

- `avformat-novalidate`は使わない。`length`なしで素材を指定すると1フレームとして扱われる場合がある。
- プロファイルへ不用意に`colorspace`を足さない。画面収録の色域変換で見た目が変わる。
- フェードの`filter`には`in` / `out`を指定する。指定なしでは素材全長に効果がかかる。
- 使わない全画面レイヤーは`visibility:hidden`で合成から外す。
- 透過PNGからMP4へ変換するときは黒背景へ合成する。アルファを落とすだけでは輪郭が白くなる。
- 外部モデルの取り込み後にフレーム範囲を設定し直す。USDの元タイムラインで尺が変わることがある。

3Dの部品分けは[レイヤーとBlender](layers-and-3d.md)、
引数は[シーン一覧](scenes.md)、外部素材は[素材台帳](../templates/library/ASSETS.md)へ。
