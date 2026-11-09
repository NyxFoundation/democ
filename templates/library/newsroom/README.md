# Newsroom assets

`press-cascade` sends news screenshots past the camera. `press-wall` pulls back from one screenshot to reveal a wall of screens. Both accept replacement images and a final metric through YAML.

```yaml
type: press
preset: press-cascade
images: [out/my-demo/assets/news-01.png, out/my-demo/assets/news-02.png]
metric: {value: 12800000, label: DEMO IMPRESSIONS}
copy: Word gets around.
duration: 6.8
```

Supply 1–64 PNG, JPEG, or WebP images. Crop them so headlines, logos, and photos remain readable. `metric.format: integer` shows an integer; the default uses millions, such as `12.8M`. Omit `copy` to hide the bottom line. The metric is set explicitly, rather than calculated from the image count. When replacing demo data with real results, update both the value and its label.

Without `images`, the samples use Chromium to capture six official newsroom sites listed in [sources.yaml](sources.yaml): Apple, GitHub, Mozilla, Figma, Cloudflare, and NASA. These are screenshots of the sites, with no implication of independent coverage or product endorsement. `12.8M` is a demo value, not a measurement. The samples repeat the same six images across multiple tiles.

The left side of the showcase is a reference reel that displays those images in sequence. The animation is an original composition, rather than a recreation of a brand's existing montage.

```sh
uv run --with pyyaml --with playwright python3 tools/capture_news.py
```

Captured images, URLs, page titles, timestamps, and SHA-256 hashes are saved in `out/template-library/assets/newsroom/`. Once cached, the images can be embedded in HTML and rendered again offline. Source images and HTML are excluded from Git. Each site's content belongs to its rights holder and is not offered as an open asset. For a video you plan to distribute, set `images` to your own coverage or screenshots you have permission to use.

Typography uses [Inter Variable](https://rsms.me/inter/). Its [OFL license and copyright notice](Inter-OFL.txt) are also preserved in generated HTML. The samples do not reproduce Spotify Mix or Apple's proprietary fonts.
