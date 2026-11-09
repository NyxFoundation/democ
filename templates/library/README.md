# Demo library

Reference clips and reusable implementations of short motion sequences. The gallery shows each clip, its product name, and links to the files and source. This directory holds the reference notes, timing, asset terms, and implementation details.

| ID | Reference | Motion | Implementation |
| --- | --- | --- | --- |
| `auto-layout` | Figma Slides | Elements align after an interaction | HTML |
| `spatial-carousel` | Framer | Cards form a carousel in 3D space | HTML |
| `cursor-zoom` | Screen Studio | Zoom, pan, and pull back around an interaction | HTML |
| `port-orbit` | Mac mini | Camera moves from the top to the front and rear | Blender / Cycles |
| `rim-reveal` | AirPods Pro | A silhouette gives way to surface detail | Blender / Cycles |
| `macro-controls` | OP–XY | Close dolly shot with raking light | Blender / Cycles |
| `drone-orbit` | DJI Mavic 4 Pro | Camera approaches the mechanisms and orbits the drone | Blender / EEVEE |
| `humanoid-articulation` | Unitree G1 | Foot contact, leg swing, and arm swing | Blender / EEVEE |
| `orbital-earth` | NASA EPIC | Rotating Earth with surface, clouds, and an atmospheric rim | Blender / EEVEE |
| `terrain-flyover` | Mapbox GL JS | Camera crosses a terrain model | Blender / EEVEE |
| `terminal-flow` | Charm Gum | Input and prompts from the official demo | HTML / xterm.js / recorded PTY output |
| `code-diff` | GitHub Copilot / VS Code | A plan becomes a code change | HTML / Monaco / upstream CSS and theme |
| `network-globe` | XNOHub | Transaction lights travel across the globe | HTML / Three.js / WebGL |
| `market-chart` | TradingView | Camera moves from layered charts to a price line | HTML / Lightweight Charts / CSS 3D |
| `type-punch` | Apple Don’t Blink | Short words change to a rhythm | HTML / Inter Variable |
| `type-flight` | Apple Don’t Blink | Scattered letters form a phrase | HTML / CSS 3D |
| `type-morph` | Spotify Mix | Font weight moves in waves | HTML / variable font |
| `press-cascade` | Newsroom screenshot reel | Screenshots accelerate past the camera | HTML / CSS 3D |
| `press-wall` | Newsroom screenshot reel | Camera pulls back to reveal a wall of screens | HTML / CSS |

[`catalog.yaml`](catalog.yaml) records why each reference was chosen, its source page, clip boundaries, motion, and adaptations. Timecodes refer to the individual video on the page, rather than the full launch event. Watch the source before adding an entry.

Financial, blockchain, code, and terminal sequences use synthetic data for animation. They do not show live prices, transactions, Copilot runs, or test results. Gum is the exception: its sequence plays back recorded output from the official shell demo. See [`source-ui/SOURCES.md`](source-ui/SOURCES.md) for the upstream code used in the four UI demos and the parts rebuilt here.

For the press demos, the left side is a reference reel of captured screenshots. The right side is an original animation with values labeled as demo data. See [`newsroom/README.md`](newsroom/README.md) for sources and image replacement.

To preview the typography and press samples together:

```sh
uv run --with pyyaml --with playwright python3 tools/build.py \
  templates/library/editorial-demo.yaml -o out/editorial-demo.html
```

## Build and preview

```sh
make library-list
make library                     # Fetch references and assets, render, then build the gallery
xdg-open out/template-library/index.html

make library-collect ID=port-orbit
make library-render ID=port-orbit
make library-catalog
make library-check               # Check duration, frame count, hashes, and decoding
make library-materials           # Fetch CC0 assets, render previews, and build the asset gallery
make library-materials-list
xdg-open out/template-library/materials/index.html

# Render one demo again after changing its code
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id port-orbit --force
```

These commands use uv, Chromium / Playwright, and FFmpeg. The four UI demos also need Node.js and npm for their first build. Generated HTML embeds its libraries, fonts, and workers, so it can play offline. 3D demos require Blender 5.x. Run inside `nix develop .#full` if these tools are missing from your PATH.

Existing movies are skipped; use `--force` to render them again. A failed fetch stops with an error. An entry appears in the comparison gallery only when both its reference and rendered demo are available. Visible clips autoplay muted, and each row has a button to restart both clips together. With `prefers-reduced-motion` enabled, playback is manual.

The default output is 960×600 at 25 fps, without audio. Reference clips keep their aspect ratio with padding; rendered demos use 16:10. Transparent PNGs are composited over black before encoding to avoid white fringes. Durations are rounded to whole frames, and a demo may differ in length from its reference.

The catalog sets the Blender engine and sample count. For a larger render:

```sh
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id port-orbit --width 1600 --height 1000 --engine cycles --samples 96 --force
```

```text
templates/library/                 Tracked reference notes and code
  catalog.yaml                     Sources, timing, motion, adaptations, and defaults
  assets.yaml                      Sources and terms for models, images, and HDRIs
  ASSETS.md                        Asset credits and usage notes
  hardware.py                      Model import and Blender scene setup
  quality_scenes.py                Product, walking, Earth, and terrain shots
  gallery.html                     Comparison gallery template
  software-demo.yaml               Example for a regular demo script
engine/scenes/motion.{js,css}       Alignment, carousel, and zoom
engine/scenes/study.{js,css}        Playback control for the study presets
engine/scenes/source-ui.{js,css}    Terminal, editor, and chart UIs
engine/scenes/network-globe.{js,css} WebGL implementation based on XNOHub
tools/template_library.py          Listing, collection, rendering, and gallery generation
tools/library_assets.py            Asset downloads and hash records
out/template-library/              Local output; ignored by Git
  index.html                       Demo comparison gallery
  references/<id>.mp4, .json        Reference clips, sources, timestamps, and SHA-256
  renders/<id>.mp4, .jpg, .json      Rendered clips, posters, settings, and SHA-256
  assets/                          Downloaded assets, sources, terms, and SHA-256
  materials/index.html             CC0 model, lighting, and material gallery
  materials/<asset-id>/            Preview PNG, packed .blend, source, and settings
  build/<id>/                      Frames, HTML, scripts, and logs
  build/<id>/<id>.blend             Editable 3D project
```

## 3D models and materials

The asset tools can fetch 12 CC0 models, three studio HDRIs, and one PBR material set. Eight textured models come from Poly Haven: a camera, boombox, cassette player, radio, laptop, circuit board, watch, and spacecraft instrument. Downloads include their 2K UV textures, normal maps, roughness maps, and metallic maps.

Four Innerscene models—headphones, earbuds, a synthesizer, and an FPV drone—are also available. Their simpler geometry and surfaces make them candidates for secondary shots. All 12 models have been rendered under neutral lighting in Cycles, with preview images and editable `.blend` files containing packed textures.

To fetch and inspect an individual asset:

```sh
uv run --with pyyaml python3 tools/library_materials.py fetch --id ph-camera-01
uv run --with pyyaml python3 tools/library_materials.py inspect --id ph-camera-01 --force
uv run --with pyyaml python3 tools/library_materials.py catalog
```

`all` selects CC0 assets only; it excludes Apple's AR models. PBR ZIP files are checked before extraction into a directory of the same name. Both the archive and extracted files have recorded hashes. In the gallery, the source-file link opens the downloaded original; the Blender link opens the editable file with lighting, cameras, and textures. `quality_status` records the asset inspection result, rather than a quality rating for the final movie.

`macro-controls` uses Poly Haven's Boombox, replacing an earlier row of procedural knobs. It preserves the lettering, mesh, and surface wear, with Cycles and a moving area light. OP–XY supplies the camera and lighting reference; the rendered model is a different product.

When preparing a shot:

1. Look for official AR models, published CAD / URDF / glTF files, or textured models. Compare the product generation, proportions, ports, and moving parts against photos.
2. Record the source, author, terms, resolution, and SHA-256 in `assets.yaml` and the download records. Access to a file does not establish permission to redistribute it or use it commercially.
3. Preserve UVs, normals, roughness, and material assignments on import. Check that corner radii, steps, port interiors, and panel gaps remain visible.
4. Use a photographic studio HDRI for reflections and ambient light. Adjust area-light shape, position, and size to control broad reflections and edge definition.
5. Tune matte aluminum, glossy logos, black plastic, rubber, and port metal separately. Keep sandblasted grain subtle, even in close shots.
6. Review a few representative frames before rendering the full movie. Check geometry, reflections, contact shadows, and camera distance. Reframe after replacing a model so the top or feet stay in view.

The Mac mini shot imports geometry, UVs, and materials from Apple's AR model and uses a photographic HDRI with Cycles. The Mac Studio AR model is also registered in the asset catalog and uses the same importer. These Apple assets are cached for local research and excluded from the repository. For commercial work or distribution, replace them with models licensed for that use.

The AirPods shot separates the left and right earbuds from Apple's official AR model while keeping their meshes, markings, and materials. The drone is aurumjuda747's Mavic 3 Cine, licensed under CC BY 4.0; the reference shows a Mavic 4 Pro.

The G1 shot reads material assignments and joint positions from Unitree's URDF and STL files, then adds walking motion with leg inverse kinematics. It illustrates motion rather than validating a physical controller or robot dynamics. Outdoor lighting uses Sergej Majboroda's Urban Courtyard 02, licensed under CC0.

The terrain covers São Miguel in the Azores, matching the reference. It combines 16 Terrarium elevation tiles and 64 EOX satellite-image tiles from 2016 in Mercator coordinates, with elevation exaggerated by 1.65×. Earth uses separate layers for NASA-derived 8K surface textures and Solar System Scope's 8K clouds. The scene does not calculate eclipse physics.

`hardware.py` reads `model_path`, `hdri_path`, `texture_path`, `clouds_path`, and `terrain_path` from the JSON passed to `--config`. It accepts USDZ, USD, glTF, GLB, and blend models. `model_rotation` is XYZ rotation in degrees; `body_width` sets the model's normalized width. Lights and cameras use the same normalized coordinates. Images are packed into the `.blend` file.

`motion_duration` sets the length of the full motion. A shorter `duration` renders only its opening portion. The control-panel close-up uses a continuous 3.2-second dolly move.

```sh
blender -b -t 8 -P templates/library/hardware.py -- \
  --preset port-orbit --out out/my-shot/frames --duration 3.5 \
  --engine cycles --samples 64 --config out/my-shot/materials.json
ffmpeg -framerate 25 -i out/my-shot/frames/f%04d.png \
  -filter_complex "color=black:s=960x600:r=25[bg];[bg][0:v]overlay=shortest=1:format=auto:alpha=straight[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p out/my-shot/shot.mp4

# Review the first, middle, and last frames
blender -b -P templates/library/hardware.py -- \
  --preset port-orbit --out out/review/frames --duration 3.5 \
  --config out/my-shot/materials.json --frames 1,44,88
```

## Use a preset in a demo

The `motion` presets are `auto-layout`, `spatial-carousel`, and `cursor-zoom`. `duration` is in seconds. `brand` sets the app name. `labels` takes three names for alignment or seven for the carousel. `turns` sets the carousel's rotation count, and `colors` takes seven `#RRGGBB` values. `rows` takes six rows of five columns, including the header; the last column of each data row must be numeric.

```yaml
transition: {duration: 0.2}
scenes:
  - type: motion
    name: Alignment
    preset: auto-layout
    duration: 4.7
    brand: Your product
    labels: [Discover, Build, Ship]
  - type: study
    name: Release
    preset: terminal-flow
    duration: 4.8
```

The `study` presets are `terminal-flow`, `code-diff`, `network-globe`, and `market-chart`. The XNOHub globe uses WebGL based on its upstream Three.js implementation. On the first build, `network-globe` fetches surface, cloud, night, and water textures. Set `texture_path`, `clouds_path`, `night_path`, and `water_path` to replace them. Images are embedded at build time, so the HTML is self-contained. These presets work with the usual `make edit`, recording, and editing commands.

To replace a scene with a Blender MP4, set `scene` to its zero-based index in `out/<demo>/layers/<shot>.yaml`, then place the clip at `out/<demo>/build/3d/<shot>.mp4`. You can also add it directly to an MLT or Kdenlive timeline.

## Add a demo

1. Choose a 2–8 second segment from an official product video or the creator's video, with one clear change. Inspect contact sheets and individual frames; watch it continuously when the motion is hard to judge.
2. Add the source page, a stable video URL, clip boundaries, motion breakdown, and adaptations to `catalog.yaml`. Avoid expiring signed URLs as the canonical source. Leave unavailable candidates out of the completed entries.
3. Run `collect --id <id>` to fetch the segment. For a local original, use `collect --id <id> --source /path/to/original.mp4`. The input source is recorded with the download metadata.
4. Register any assets in `assets.yaml` and reference them from the entry's `assets` and `parameters`. `model_asset`, `hdri_asset`, `texture_asset`, `clouds_asset`, and `terrain_asset` resolve to local paths.
5. For HTML, implement `drawAt(scene, seconds)` so time alone determines the frame. If images need to load first, expose a `ready` Promise; recording waits for it. For Blender, add the preset to the CLI choices and scene dispatch.
6. Inspect representative frames for clipping, reflections, joints, camera collisions, dense text, and long pauses. Watch the full sequence, then run `render --id <id>` and `catalog` to add it to the gallery.

Reference clips and external assets stay in `out/`. Keep their terms and credits in [ASSETS.md](ASSETS.md) and the asset records, rather than burning production notes into the showcase video.
