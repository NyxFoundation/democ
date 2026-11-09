# Scene reference

Each demo uses one script at `out/<name>/<name>.yaml`, with scenes listed under `scenes`. Scene types define the animation; YAML supplies the content. Text length affects automatic timing, so write the copy before adjusting durations.

## Global settings

| Key | Default | Purpose |
| --- | --- | --- |
| `title` | Filename | Name shown in the browser tab and controls |
| `accent` | `#5fd7d7` | Accent color, also used by `<em>` and `<b>` |
| `reading.cps` | 5.5 | Characters per second |
| `reading.lead` | 0.9 | Initial reading delay in seconds |
| `reading.min` / `.max` | 2.4 / 5.2 | Minimum and maximum scene duration in seconds |

Automatic hold time is `lead + character count / cps`, clamped to `min` and `max`. These defaults were chosen for Japanese subtitles, using a 4 CPS baseline, a 7 CPS upper reference, and a six-second ceiling per card. Set `hold:` on any scene to fix its duration in seconds. `gap:` changes the pause before it; the default is 0.42 seconds.

## Text, code, and icons

Text fields (`text`, `band`, `note`, and `labels.*`) accept HTML. `<em>` and `<b>` use the accent color, `<s>` is gray, and `<br>` inserts a line break.

Code fields (`code`, `lines`, `need`, `has`, `error`, and `done`) take plain code. `lang` selects syntax highlighting. Use `{{this}}` for a red highlight and `<<this>>` for a yellow annotation.

`icon` selects a file-tab color: `cedar`, `lean`, `js`, `ts`, `sh`, or `json`.

## card — text and numbers

| Key | Content |
| --- | --- |
| `text` | Centered text; shrinks automatically when long |
| `number` | Counter starting at zero; `format: plain` removes digit grouping |
| `code` + `lang` | Code beneath the text |
| `tab` + `icon` | Filename above the code |
| `sub` | Optional small supporting text; use sparingly |

Consecutive cards replace one another without a blackout.

Additional fields:

- `unit` sets the number's unit. Use `sub` for supporting text or a link, rather than numbered subheadings or small footnotes.
- `style` accepts `hero` (bright teal background), `danger` (red number), or `brand` (large product name).
- `count_ms` sets how long the counter takes to reach its value, in milliseconds. `hold` sets the pause after counting ends.

## browser — a web application incident

`brand`, `nav`, and `user{email,initial}` define the frame. `url`, `crumb`, and `files` define the opening view.

Set `change` for a second state. First, the `{{ }}` portion of `url` changes. After a short delay, `crumb` and `files` change and turn red. `change.stamp` is the final line.

`settle` sets how long the normal view remains visible, with a default of 1.2 seconds. Around 1.8 seconds gives viewers more time to recognize the change.

## code — a code review

`lines` is a block with one line number, a space, and code on each line. Blank lines add spacing.

`good` and `bad` are arrays of line numbers highlighted after a reading pause. `badges` maps line numbers to callout text. `missing: {after, text}` opens a space for a missing line after the given line. `note` appears at the bottom and shifts the code down as it enters.

`read` sets the reading pause before highlighting, in seconds.

## split — code moves between panes

Both `left` and `right` accept `tab`, `icon`, `lang`, and `code`. Set `left.fly` and `right.land` to line ranges such as `"1-3"`. The selected lines leave the left pane as a block, change to the right pane's text in flight, and land in a position hidden until the move begins.

`band` is a line shown after landing. `flight` sets the travel time in seconds, with a default of 1.25.

## tree — dependencies and type checks

`root` names the root. `levels.l1` and `levels.l2` define named levels, `levels.dots` sets the number of unnamed nodes, and `axioms` defines the leaves. Layout width adjusts to the number of entries.

`error` shows an initial failure before the tree grows. `total` and `unit` define the counter at the bottom right. `labels` supplies four banners: `built` when the tree is complete, `compare` during inspection, `ok` for a match, and `fail` for a mismatch.

`inspect` is an array of nodes to open. The first illustrates a match; the second illustrates a mismatch. Each entry accepts `node`, `ok`, `need`, `has`, and `read` (inspection time in seconds, default 2.1). `inspect_labels` supplies the `need`, `has`, `ok`, and `ng` headings.

`done` is the final line.

## terminal — command output

`title` names the window. `lines` is the output block, revealed line by line at `gap_ms` intervals (default 390 milliseconds).

Set `side` with `tab`, `icon`, `lang`, `code`, and `after` to open a small pane on the right once line `after` has appeared.

## Adding a scene type

Add `engine/scenes/<name>.css` and `<name>.js`, then register the type with `D.register('<name>', {mount, reset, play})`. `mount()` is called once and returns markup; `play(s)` receives one YAML scene.

Add a conversion function to `BUILDERS` in `tools/build.py` to support plain code in YAML.

## motion — product motion presets

`preset` accepts `auto-layout` (element alignment), `spatial-carousel` (cards in 3D space), or `cursor-zoom` (zoom into a table interaction). `duration` is in seconds, with a default of 6. The presets communicate through UI and shape movement, without added headings.

| Key | Content |
| --- | --- |
| `brand` | App name in the UI; default `Orbit` |
| `labels` | Three alignment-card names or seven carousel-card names |
| `turns` | Carousel rotation count; default 0.36 |
| `colors` | Seven `#RRGGBB` values for the carousel |
| `rows` | Six rows of five columns, including the header; each data row ends with a number |

`labels`, `brand`, and `rows` are rendered as plain text without HTML formatting. See the [demo library](../templates/library/README.md) for sources, reference clips, Blender templates, and replacement instructions.

## incident — code review and a blog

Shows an endpoint on the left and a blog-draft UI on the right. The post ID in the URL changes from 3 to 7.

| Key | Content |
| --- | --- |
| `text` / `caption` | Top heading / bottom caption |
| `code` / `lang` | Left-pane code and syntax language |
| `missing` | Two missing lines; opens a red insertion area at the first blank line in `code` |
| `safe` | If true, shows a 403 after policy enforcement; otherwise shows another user's draft with a 200 |
| `hold` | Hold time after the URL change and result |
| `timing` | Delays in seconds: `settle` for the opening view, `request` after the URL change, `reveal` after the result |

## policy — policy input and build results

Set `code` to a short Cedar policy, `schema` to a valid effect declaration, and `invalid` to an inconsistent declaration. The scene types the policy line by line, shows a successful build, then shows failure after introducing the inconsistency.

`text` is the heading. Record sources and the scope of any correctness claims in production notes. The displayed results are animated illustrations; the scene does not run a build.

Override pauses with `timing`: `line` for each typed line, `prepare` after typing, `build` during checking, and `pass` / `fail` for result display times. Values are in seconds.

## kernel — Lean proof dependencies

`root` is the theorem name, `proposition` is a short statement, `captions` is an array of captions, and `duration` is in seconds. `text` sets the top-left heading. Capture `#kernelHeader` as a separate layer for compositing its text and background.

If `3d/kernel.mp4` exists relative to the HTML, the scene plays that Blender clip. Otherwise, it uses an HTML animation to preview the sequence. `layers/kernel.yaml` controls replacement in the final timeline.

`speed` sets playback speed (default 1). `duration` is the source clip's length; playback lasts `duration / speed`. This applies to both HTML and MP4 output while preserving the original Blender clip. Retimed editing clips are cached in `build/retimed/`.

`inspections` defines temporary node details: `title` is the declaration name, `description` is a short explanation, and `code` is an excerpt of its definition or type. `D.Scenes.kernel.inspect(s, i)` sets the HTML content, which `layers/kernel.yaml` captures as a transparent image.

`shots/kernel.py` defines the spheres, rings, connecting lines, and display timing. Node details appear briefly, rather than as persistent small lemma labels.

## Transitions

Set `transition: {duration: 0.4}` at the top level to remove gaps and crossfade between scenes. `duration` is in seconds. Without this setting, the engine uses its default playback behavior.

In HTML, the previous view—including a video's final frame—stays visible until the next scene is ready. Recordings also hold their final state. MP4 output overlaps clip ends and starts by the same duration. In MLT and Kdenlive, each transition appears as a separate short clip.

## study — terminal, code, globe, and chart presets

`preset` accepts `terminal-flow` (terminal input, choices, and processing), `code-diff` (a code diff), `network-globe` (transactions on a globe), or `market-chart` (financial charts). `duration` is in seconds, with a default of 4.8. Displayed data is prepared for the animation.

`network-globe` uses Three.js / WebGL based on XNOHub's public source. Surface, cloud, night, and water textures are downloaded on the first build. Supply local paths through `texture_path`, `clouds_path`, `night_path`, and `water_path` to replace them. Textures are resized to 4K and embedded in the HTML. The scene requires a browser with WebGL 2.

The scene exposes a `ready` Promise for image loading; recording waits for it. Use `type: study`, `preset`, and `duration` in a regular script. See the [asset inventory](../templates/library/ASSETS.md) for sources and terms, and the [demo library](../templates/library/README.md) for gallery generation.

## typography — animated text

| Preset | Motion | Editable content |
| --- | --- | --- |
| `type-punch` | Short words change with black-and-white inversions | `words`: 1–12 words |
| `type-flight` | Letters gather from 3D space into a phrase | `lines`: 1–3 lines |
| `type-morph` | Variable font weight moves in waves | `lines`: 1–3 lines |

`duration` is in seconds, with a default of 5.6. `font_size` optionally sets the maximum text size. Inter Variable is fetched on the first build and embedded in the HTML. Japanese text falls back to a CJK font. See [editorial-demo.yaml](../templates/library/editorial-demo.yaml) for examples.

## press — newsroom screenshots

`preset` accepts `press-cascade` (screens accelerate past the camera) or `press-wall` (the camera pulls back from one screen to reveal many). `duration` defaults to 6.8 seconds. The screens settle at the end and reveal a metric, such as `metric: {value: 12800000, label: DEMO IMPRESSIONS}`.

`metric.format: integer` shows an integer; the default formats the value in millions. `copy` is an optional line of text.

`images` takes 1–64 local PNG, JPEG, or WebP paths. Images are embedded in the HTML. If omitted, the scene captures six official newsroom sites on its first build. Sample metrics are demo values; impressions are not estimated from the number of images. See [newsroom assets](../templates/library/newsroom/README.md) for replacement instructions and sources.
