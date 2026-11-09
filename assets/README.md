# Shared assets

Store assets here when they are reused across demos. Scripts, text, and code for a single demo belong in `out/<name>/<name>.yaml`.

| Path | Contents |
| --- | --- |
| `snippets/` | Reusable code snippets to include in YAML scripts |

Scripts, editing decisions, and 3D setup for an individual demo stay in `out/<name>/`, which is ignored by Git.

Images and videos can live here too. Prefer keeping the source or generator when an asset can be regenerated, and avoid duplicating files from `out/`.
