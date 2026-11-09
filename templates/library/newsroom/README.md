# ニュース画面の素材

`press-cascade`はニュース画面がカメラを追い越す演出、`press-wall`は一画面から引いて
画面の広がりを見せる演出。どちらも画像と最後の数値をYAMLから差し替えられる。

```yaml
type: press
preset: press-cascade
images: [out/my-demo/assets/news-01.png, out/my-demo/assets/news-02.png]
metric: {value: 12800000, label: DEMO IMPRESSIONS}
copy: 話題が、広がる。
duration: 6.8
```

画像はPNG / JPEG / WebP、1〜64枚。記事の見出し・ロゴ・写真が読める縦横比で切り出す。
数値の`format: integer`で整数、既定では`12.8M`のような百万単位になる。
`copy`を省くと下のコピーを消せる。数値は記事の枚数から計算しない。
デモ値を実際の成果へ差し替えるときは、数値とラベルを一緒に編集する。

`images`を省いたサンプルは、[sources.yaml](sources.yaml)の公式ニュースルーム6サイトを
Chromiumで撮影する。Apple、GitHub、Mozilla、Figma、Cloudflare、NASAの実画面で、
独立メディアによる評価や、特定製品への推薦ではない。`12.8M`も計測結果ではなくデモ値。
サンプルは同じ6枚を複数のタイルへ繰り返して配置する。

ショーケース左側は、同じ画像を順番に並べた**素材の参照リール**。
既存のブランドが制作したモンタージュ映像を再現したと主張するものではない。

```sh
uv run --with pyyaml --with playwright python3 tools/capture_news.py
```

取得画像・URL・ページタイトル・取得時刻・SHA-256は`out/template-library/assets/newsroom/`。
キャッシュが揃えば、ネット接続なしでHTMLへ画像を内包し、再出力できる。
元の画像・HTMLはGitへ含めない。各サイトの著作物は各権利者に帰属し、オープン素材ではない。
配布する製品動画では、自分の掲載記事や使用できるスクリーンショットを`images`へ指定する。

タイポグラフィは[Inter](https://rsms.me/inter/)の可変フォントを使用。
[OFLと著作権表示](Inter-OFL.txt)は生成HTMLにも保持する。Spotify MixやAppleの専用書体を複製しない。
