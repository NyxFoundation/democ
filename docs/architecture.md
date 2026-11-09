# Pipeline and implementation notes

## Demo layout

```text
out/my-demo/
  my-demo.yaml          Source script: scenes, text, and timing
  notes.md              Sources and production notes
  layers/*.yaml         Scene replacements and layer selection for 3D
  shots/*.py            Blender geometry, lighting, and cameras
  build/
    page.html           Generated browser preview
    screens/            Per-scene MP4s and hashes
    parts/              Transparent PNGs for individual layers
    3d/                 Blender renders and editable .blend files
    edit.mlt            MLT timeline
    edit.kdenlive       Kdenlive timeline
    demo.mp4            Final movie
```

`tools/build.py` turns YAML into a single HTML page. `tools/record.py` records each scene, `edit/timeline.py` assembles an MLT timeline, and `melt` exports the final MP4. Scenes configured for 3D use clips rendered in Blender.

## Source files

| Path | Purpose |
| --- | --- |
| `templates/starter.yaml` | Starter script for a new demo |
| `examples/` | Scripts available through `make new FROM=` |
| `engine/engine.{css,js}` | Stage, playback, and transitions |
| `engine/scenes/` | Scene layouts and animation |
| `templates/library/catalog.yaml` | Reference clips, durations, and demo settings |
| `templates/library/hardware.py` | 3D templates that import external models |
| `templates/library/source-ui/` | Upstream UI code, pinned dependencies, and licenses |
| `tools/record.py` / `tools/snap.py` | Video recording and still-frame capture |
| `tools/readme_demos.py` | README previews and MP4 updates |

## Rebuilding and recording

YAML, JS, and CSS are the source for the screen content. Text is baked into the MP4s used in Kdenlive, so text edits require updating the YAML and exporting again. GUI timeline changes are not written back to the Python source.

Recording is split by scene. Only scenes whose content hashes have changed are recorded again. Changes to shared engine code also trigger recording for affected scenes. Recording ends when the engine sets `body[data-done]`, rather than after an estimated duration.

`make 3d` is separate from the default build because rendering is expensive. After editing 3D source, run `make 3d`, then export the final MP4. `make clean` removes `out/*/build` and preserves YAML scripts and shot source files.

## MLT and HTML details

- Avoid `avformat-novalidate`. A source without an explicit `length` can be treated as a single frame.
- Add `colorspace` to the profile only when needed. It can change the appearance of screen recordings through color conversion.
- Set `in` and `out` on fade filters; otherwise the effect applies across the full source.
- Use `visibility:hidden` to remove unused full-screen layers from compositing.
- Composite transparent PNGs over black before encoding to MP4. Dropping alpha alone can leave white fringes.
- Reset the frame range after importing an external model. A USD source timeline can change the shot length.

See [layers and Blender](layers-and-3d.md) for 3D layer extraction, the [scene reference](scenes.md) for options, and the [asset inventory](../templates/library/ASSETS.md) for external assets.
