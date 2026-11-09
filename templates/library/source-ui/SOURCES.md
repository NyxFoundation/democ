# UI source notes

Upstream implementations used by `terminal-flow`, `code-diff`, `market-chart`, and `network-globe`.

Generated HTML embeds JavaScript, CSS, fonts, and terminal output for playback without a network connection or login. The surrounding layout and animation live in `engine/scenes/source-ui.{js,css}`; `tools/source_ui.py` assembles the output. npm versions and integrity hashes are pinned in `package-lock.json`.

| Demo | Upstream code | Work done here |
| --- | --- | --- |
| VS Code / Copilot | [Monaco Editor](https://github.com/microsoft/monaco-editor) 0.57.0, [Codicons](https://github.com/microsoft/vscode-codicons) 0.0.46-24, [GitHub Theme](https://github.com/primer/github-vscode-theme), and [VS Code's chat.css](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/contrib/chat/browser/widget/media/chat.css) | DOM for the Trail Atlas example, file tree, search.js, plan cards, and input area. Monaco renders syntax colors, line numbers, and diffs. The demo does not call the Copilot API or run tests. |
| Charm Gum | The [official demo.sh](https://github.com/charmbracelet/gum/blob/main/examples/demo.sh), [demo.tape](https://github.com/charmbracelet/gum/blob/main/examples/demo.tape), Gum v0.17.0, and [xterm.js](https://github.com/xtermjs/xterm.js) 6.0.0 | The original is a terminal app, with no HTML interface. The official shell demo runs in a PTY; its ANSI output is recorded and replayed through xterm.js. Spacing, character width, palette, and input timing follow the reference. |
| TradingView | [Lightweight Charts](https://github.com/tradingview/lightweight-charts) 5.2.1 | Charts use the official library. DOM, SVG, CSS, and camera motion recreate the surrounding toolbars, panels, purple light, and reflections. This is not a copy of Advanced Charts. Prices use synthetic data with a fixed seed. |
| XNOHub | `three-mesh.tsx`, `network-arc.tsx`, and `nano-rep-nodes.tsx` from [XNOHub.com](https://github.com/dalindev/XNOHub.com), plus Three.js 0.166.1 | The Phong globe material, 23.5° tilt, coordinate conversion, and raised great-circle arcs were ported to `engine/scenes/network-globe.js`. The scene uses 87 public node locations and depth testing to hide paths behind the globe. React and the live transaction stream are omitted; amounts, routes, and light timings are fixed. The surrounding UI is rebuilt in the DOM. |

Advanced Charts is a [product whose source is not public](https://www.tradingview.com/free-charting-libraries/). This implementation includes no private code or libraries requiring a login. It keeps Lightweight Charts' standard TradingView logo and preserves LICENSE and NOTICE in the generated HTML.

## Files kept in the repository

- `vscode/chat.css` and `vscode/LICENSE.txt` are Microsoft's MIT-licensed source.
- `github-theme/theme.cjs` is a copy of Primer's `src/theme.js` with a different extension. It includes `colors.js` and the MIT license. Color generation uses the same `@primer/primitives` version as the original: 7.10.0.
- `gum/demo.sh`, `gum/demo.tape`, and the MIT license are included. `recording.json` contains actual terminal output and the source script's SHA-256.
- JetBrains Mono is pinned by source URL and SHA-256 in `assets.yaml`. Its SIL OFL is kept in `font-OFL.txt`.
- `xno/nodes.json` contains only latitude and longitude extracted from the public `data/defualtMergedRepsData.ts` file. It includes no IP addresses or accounts. `xno/LICENSE.txt` preserves the original MIT notice. `upstream-manifest.json` records the source commit and hashes of both the original and the verification copy.
- npm LICENSE and NOTICE files, along with the licenses above, are also embedded in generated HTML comments.

Trailing spaces and excess blank lines at the end of imported text files have been normalized. Source hashes are recorded in `upstream-manifest.json`; document changes here when editing a copy. Sources and adaptations belong in these production notes, without adding annotations to the video.

## Rebuild

```sh
make library-render ID=terminal-flow
make library-render ID=code-diff
make library-render ID=market-chart
make library-render ID=network-globe

# Replace existing MP4s
uv run --with pyyaml --with playwright python3 tools/template_library.py render \
  --id terminal-flow --id code-diff --id market-chart --force

# Record Gum output again; requires Go and Bash
uv run python3 tools/capture_gum.py
```

The first build requires Node.js, npm, and network access. After `npm ci`, esbuild bundles the code, including Monaco workers embedded as Blobs. Playback and recording then work offline.

UI components are created after fonts are ready, preventing first-frame character-width changes. Capture uses DPR 2; output PNG dimensions match the configured CSS pixel dimensions to keep chart close-ups sharp.

Gum recording adjusts the shebang for NixOS, hides help text, uses a thin prompt, and sets a green cursor. `NO_COLOR` is unset only in the recorded child process. The original demo script is left intact.
