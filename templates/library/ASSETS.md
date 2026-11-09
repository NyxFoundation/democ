# Asset sources and usage

These production notes sit outside the showcase video. File URLs, SHA-256 hashes, and download records are kept in [assets.yaml](assets.yaml) and `out/template-library/assets/*.json`. Reference video sources and excerpt boundaries are recorded in [catalog.yaml](catalog.yaml).

The typography presets were selected after reviewing the [published Apple Don’t Blink excerpt](https://motionographer.com/2016/09/14/4-ways-dont-blink-is-a-masterclass-of-type-and-rhythm/) and [Spotify Mix's official GIF](https://newsroom.spotify.com/2024-05-22/introducing-spotify-mix-our-new-and-exclusive-font/). The implementations use original copy and [Inter Variable](https://rsms.me/inter/), licensed under the SIL OFL. They do not redistribute the original ad copy or proprietary fonts. Reference footage is kept for local research, like the other reference clips.

News images are screenshots of official newsroom sites. They remain copyrighted works of their respective owners and are not treated as open assets. Sources, rights, and use in the demos are recorded in the [newsroom notes](newsroom/README.md).

| Use | Asset and author | Terms and notes |
| --- | --- | --- |
| Mac mini | [Apple Mac mini AR](https://www.apple.com/mac-mini/) | Apple's published USDZ, cached for local research. It has no open-content license. Models and source images are excluded from Git. |
| Mac Studio alternative | [Apple Mac Studio AR](https://www.apple.com/mac-studio/) | Same terms as above. The model has been cached. |
| AirPods Pro | [Apple AirPods Pro AR](https://www.apple.com/airpods-pro/) — Apple | Uses the left and right earbuds from the official USDZ, preserving materials, UVs, meshes, and markings. The charging case is excluded. Like Mac mini, this is cached for local research, without an open redistribution license. |
| Studio lighting and reflections | [Studio Small 05](https://polyhaven.com/a/studio_small_05) — Greg Zaal / Poly Haven | CC0. Photographic HDRI. |
| Control-panel close-up | [Boombox](https://polyhaven.com/a/boombox) — Thomas Paul Mouilleron | CC0. Preserves the author's lettering, UVs, and PBR maps; used in `macro-controls`. |
| Drone | [Mavic 3 Cine](https://sketchfab.com/3d-models/mavic-3-cine-60d4a042a6eb4a1e944b1af2d4e9368b) — aurumjuda747 | CC BY 4.0. Uses [OpenAirTwin's normalized GLB](https://github.com/HKUOpenSource/OpenAirTwin/tree/master/backend/static/assets/radar/drones/dji-mavic-3-cine), preserving author and model credits. This differs from the reference's Mavic 4 Pro. The earlier Cesium model remains in the catalog. |
| Humanoid | [Unitree G1](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description) — Unitree Robotics | The repository's BSD-3-Clause license. LICENSE is fetched with the URDF and STL files; copyright and disclaimer are preserved. |
| Outdoor lighting | [Urban Courtyard 02](https://polyhaven.com/a/urban_courtyard_02) — Sergej Majboroda / Poly Haven | CC0. 2K HDRI used for the G1's reflections and background. |
| Earth surface, night, and water | [NASA textures / daily-cloud-maps](https://github.com/matteason/daily-cloud-maps) — NASA / Matt Eason | 8K surface, night, and water textures. CC0; NASA's original data is public domain. Credits NASA GIBS/EOSDIS and Matt Eason, without implying NASA endorsement. |
| Clouds | [Solar System Scope textures](https://www.solarsystemscope.com/textures/) — Solar System Scope / INOVE | CC BY 4.0. An 8K static composite, animated independently of the surface. It does not show live weather. |
| Terrain elevation | [Terrain Tiles](https://registry.opendata.aws/terrain-tiles/) — Mapzen / Tilezen | Terrarium z12/x1752–1755/y1580–1583, covering São Miguel in the Azores. Terms follow each underlying dataset. Elevation is exaggerated by 1.65×. |
| Terrain satellite imagery | [Sentinel-2 cloudless 2016](https://cloudless.eox.at/documentation/faq) — EOX IT Services GmbH / Copernicus | The **2016 edition, licensed under CC BY 4.0**. A 2K mosaic made from 64 z13 tiles. Sentinel-2 cloudless 2016 by EOX IT Services GmbH. Contains modified Copernicus Sentinel data 2016. Used for terrain footage; later editions with noncommercial terms are separate. Raw GIS datasets are not redistributed. |

## Additional CC0 assets

Assets were downloaded on 2026-11-08. All 12 models were opened in Blender and rendered in Cycles. Preview images and `.blend` files with packed textures are saved in `out/template-library/materials/<asset-id>/`.

Original files, authors, terms, and texture dependencies are listed in `assets.yaml`. Download timestamps and per-file hashes are recorded in JSON under `out/template-library/assets/`. Run `make library-materials` to fetch and inspect them again.

| Asset | Author | Inspection and use |
| --- | --- | --- |
| [Camera 01](https://polyhaven.com/a/Camera_01) | Rajil Jose Macatangay | UVs and 2K PBR checked. Candidate for lens, metal, leather, and lettering close-ups. |
| [Boombox](https://polyhaven.com/a/boombox) | Thomas Paul Mouilleron | Used in `macro-controls`. |
| [Portable Cassette Player](https://polyhaven.com/a/portable_cassette_player) | Mateusz Sadek | Preview images saved for the housing, tape, and lettering. |
| [Vintage Radio Transceiver](https://polyhaven.com/a/vintage_radio_transceiver) | Mateusz Sadek | Parts, wiring, and housing inspected. Include the antenna when framing the full model. |
| [Classic Laptop](https://polyhaven.com/a/classic_laptop) | Arrangemonk | Lettering, keys, and housing inspected. Suitable for retro hardware shots. |
| [Circuit Board](https://polyhaven.com/a/circuit_board) | Benny Weimer | Board, ports, and components inspected. |
| [Digital Wrist Watch](https://polyhaven.com/a/digital_wrist_watch) | Adrian C | Face, metal, and band inspected. Frame the face close-up separately from the full watch. |
| [Vintage Spacecraft Instrument](https://polyhaven.com/a/vintage_spacecraft_instrument) | Michał Wiśniewski | Panels, knobs, and paint inspected. |
| [Over-ear Headphones](https://www.innerscene.com/tools/library/3d-parts/over-ear-headphones-de211466) | Innerscene | Candidate for secondary shots. The uniform surface is less suitable for a hero close-up. |
| [Wireless Earbuds](https://www.innerscene.com/tools/library/3d-parts/wireless-earbuds-with-case-4599339a) | Innerscene | Same as above. |
| [Desktop Synthesizer](https://www.innerscene.com/tools/library/3d-parts/patch-voice-synthesizer-0b3e851c) | Innerscene | Same as above. |
| [FPV Racing Drone](https://www.innerscene.com/tools/library/3d-parts/fpv-racing-drone-037b67bd) | Innerscene | Same as above. The model does not represent a specific commercial product. |
| [Studio Small 03](https://polyhaven.com/a/studio_small_03) | Greg Zaal / Poly Haven | CC0. Photographic HDRI, 2K. |
| [Studio Small 09](https://polyhaven.com/a/studio_small_09) | Sergej Majboroda / Poly Haven | CC0. Photographic HDRI, 2K. |
| [Metal 012](https://ambientcg.com/view?id=Metal012) | ambientCG / Lennart Demes | CC0. 2K PBR set for procedural brushed steel, distinct from Apple's aluminum housing. |

Original terms: [Poly Haven](https://polyhaven.com/license), [Innerscene Free Parts Library](https://www.innerscene.com/tools/library/terms), and [ambientCG](https://docs.ambientcg.com/license/).

Assets whose download failed before registration are excluded from the collected count.

## Additional credits

Terrain Tiles was accessed on 2026-11-08 from https://registry.opendata.aws/terrain-tiles.

Global ETOPO1 terrain data: U.S. National Oceanic and Atmospheric Administration.
Global GMTED2010 and SRTM terrain data: U.S. Geological Survey.

See [Tilezen's attribution](https://github.com/tilezen/joerd/blob/master/docs/attribution.md) and [data sources](https://github.com/tilezen/joerd/blob/master/docs/data-sources.md) for regional terms.

NASA reference footage: NASA / DSCOVR EPIC — [An EPIC View of the 2017 Total Solar Eclipse](https://images.nasa.gov/details/GSFC_20170822_Total_m12690_Eclipse). The demo studies the presentation of Earth; it is not an eclipse or solar-system physics simulation.

External assets keep their individual terms. Being able to download a file does not establish permission to redistribute it or use it commercially. Apple's terms are in its [Website Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html); other terms are recorded under `license_url` in the asset catalog. When adapting a shot for another product, use a model licensed for the intended use.
