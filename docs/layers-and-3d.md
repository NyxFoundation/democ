# Bringing a screen into 3D

Capture parts of an HTML screen as transparent PNGs, then arrange them as planes in Blender. The UI stays flat; the camera moves around it.

Blender supplies depth of field, motion blur, reflections, and frame-level animation. HTML retains the text layout and editable copy. After changing the text, capture the layers again; the animation in the `.blend` file can stay in place.

```sh
make layers     # Capture to out/<demo>/build/parts/<shot>/*.png
make 3d         # Render out/<demo>/build/3d/<shot>.blend and .mp4
```

## Extract layers

Separate components can sit at different depths, move independently, and fall in or out of focus. A single flattened image limits the shot to moving the whole screen.

Define the capture in `out/<demo>/layers/<shot>.yaml`. Its location determines the output directory, `out/<demo>/build/parts/<shot>/`, so the file only needs the capture settings.

```yaml
scene: 7                      # Zero-based scene index in the script
clear: [".sc", ".stage", ".stage-wrap"]   # Remove these backgrounds for transparency
layers:
  - name: left
    select: "#sp .l"
    js: "D.cls('#sp','on'); D.html('#spL', s.left.codeHtml.join('\n'));"
```

Set each layer's state with `js` rather than seeking through playback. This keeps a change to the scene's `hold` from changing the captured image. Inside `js`, `s` is the scene specification, `DEMO.scenes[scene]`. To capture a moment during playback, set `play: true` and `at:` in seconds.

Use `scale: 2` to capture textures at twice the resolution for close camera shots. Coordinates in `layers.json` stay in CSS pixels, so the 3D placement does not change.

`element.screenshot` captures the element's rectangle, including other elements that overlap it. Clear any overlapping content before capturing a layer.

The output includes `layers.json`, which records each component's screen position. Blender uses it to place the planes.

## Set up the Blender shot

Each `out/<demo>/shots/<shot>.py` pairs with `out/<demo>/layers/<shot>.yaml`. Use `templates/shots/cards-in-3d.py` as a starting point, or see `examples/nyxis/shots/kernel.py` for a complete shot.

The screen-plane template maps a 1600×1000-pixel screen to 16×10 Blender units. Adjust scale, camera distance, focal length, and aperture together, then check focus and legibility in rendered frames. The Nyxis kernel shot instead places its graph in custom 3D coordinates and composites headings and subtitles in screen space.

A camera with a `TRACK_TO` constraint targeting an Empty can keep the subject framed during an orbit. Check representative frames when adding a dolly move or pan.

## Blender details

After rotating a plane 90° around X, its height is still local Y. Use `scale = (w, h, 1)`; `(w, 1, h)` leaves the height at 1.

In Blender 5, access action fcurves through layers, strips, and channelbags. See the keyframe code in `examples/nyxis/shots/kernel.py`.

EEVEE works with `--background`; this example was checked with Blender 5.0. Motion blur can still take several seconds per frame.

## Add the shot to the timeline

The `scene:` field in `out/<demo>/layers/<shot>.yaml` identifies both the capture source and the scene to replace. `edit/timeline.py` substitutes `out/<demo>/build/3d/<shot>.mp4` for that scene's screen recording under `build/screens/`.

If the script sets `transition.duration`, that value controls the crossfade around the shot. Otherwise, a 0.25-second fade is added before and after 3D footage.

The default `make` target does not render 3D. Run `make 3d` first, then `make` to include the exported shot.

## Hand off an editable shot

Give the next editor `out/<demo>/build/3d/<shot>.blend` as well as the preview MP4. The Blender file contains the planes, cameras, lights, and keyframes needed to continue editing.

## Keep text separate from geometry

The Nyxis kernel shot renders the graph in 3D, then composites headings and subtitles after lens effects and glow. Node contents appear only while a node is in focus, avoiding a field of small labels.

For a text-only change, recompositing a separate layer with its background can avoid rendering the entire 3D scene again. Check that the replacement region fully covers the old text, back up the original frames, and match the PNG's actual size to the CSS dimensions in `layers.json`. Rerender from source where text overlaps geometry. Keep the MP4, Blender file, and HTML copy in sync.
