---
name: build-portfolio-metadata
description: Build searchable portfolio metadata JSON/JSONL and a visual HTML viewer from image folders in this sale_report_skills repository. Use when the user asks for build_portfolio_metadata, portfolio image folder meta-indexing, portfolio_all/portfolio folder metadata generation, or a reusable workflow where dropping images into a folder should produce metadata and an HTML review screen.
---

# Build Portfolio Metadata

This is a workspace-only skill for `<project-root>`. Do not use it outside this workspace unless the same `skill_ver/scripts/build_portfolio_metadata.py` script exists.

## Quick Start

Run the workspace script from the project root:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py --source-dir portfolio_all --slug portfolio_all
```

For another image folder:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py --source-dir path/to/folder --slug folder_slug
```

Default run, for the small curated sample:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py
```

## What It Produces

For `--slug portfolio_all`, the script writes:

- `skill_ver/data/portfolio_all_index.json`
- `skill_ver/data/portfolio_all_index.jsonl`
- `skill_ver/data/portfolio_all_summary.json`
- `skill_ver/data/portfolio_all_thumbnails/`
- `skill_ver/portfolio_all_metadata_viewer.html`

The JSONL file is the main machine-readable index. The HTML file is the human review surface.
The HTML viewer includes brand-tag filtering from `brand_tags`/`client_handles`, group/cut filters, search, paged card rendering, and a detail drawer.

## Workflow

1. Confirm the current directory is `<project-root>`.
2. Count source files if useful:
   ```bash
   find portfolio_all -maxdepth 1 -type f | awk 'BEGIN{IGNORECASE=1} {n=$0; sub(/^.*\\./,"",n); ext[tolower(n)]++} END{for (e in ext) print e, ext[e]}' | sort
   ```
3. Run the metadata script with the requested folder and slug.
4. Validate outputs:
   ```bash
   python3 -m py_compile skill_ver/scripts/build_portfolio_metadata.py
   python3 -m json.tool skill_ver/data/<slug>_index.json >/tmp/<slug>_index_check.json
   python3 -m json.tool skill_ver/data/<slug>_summary.json >/tmp/<slug>_summary_check.json
   wc -l skill_ver/data/<slug>_index.jsonl
   ```
5. Open or browser-test the HTML viewer. If using a local server, start it only temporarily and stop it after verification.
6. Report image count, skipped video count, output paths, and any known limitations.

## Input Rules

- Supported image files: `.jpg`, `.jpeg`, `.png`, `.webp`.
- Supported sidecar metadata: a same-name JSON file such as `image.jpg.json`.
- Video files are not analyzed yet; they are counted and listed under `skipped_video_files` in the summary.
- If `api/app/data/portfolio_seed.json` contains a filename key, curated tags and proposal text override heuristics.
- If no seed entry exists, the script uses sidecar metadata, filename text, image brightness/contrast, and simple keyword rules. Mark these records as first-pass metadata requiring human review.
- Brand tags come from Instagram handles in the sidecar description first, then source username fallback.

## Output Semantics

Each image record includes:

- source paths and thumbnail paths
- Instagram/source metadata when available
- dimensions, aspect ratio, orientation, dominant colors, brightness, contrast
- group, cut type, visual tags, commerce tags
- brand tags for filtering and brand-level browsing
- proposal use text
- similar/contrast recommendation conditions
- review status and rights note

Treat `review_status: needs_review` as intentional. Before using records in external proposals, manually verify rights, client names, and proposal wording.

## Implementation Notes

- Keep this workflow inside `skill_ver/`; do not modify the existing `api/` or `web/` app unless the user explicitly asks for integration.
- Do not install new dependencies without approval. The current workspace already has Pillow available for image stats and thumbnails.
- Use `--no-thumbnails` only when the user specifically wants the HTML to reference original images. For large folders, keep thumbnails enabled.
