---
name: build-portfolio-metadata
description: Build searchable portfolio metadata JSON/JSONL, thumbnails, and a visual HTML viewer from local image folders. Use when the user asks for build_portfolio_metadata, portfolio image folder meta-indexing, portfolio metadata generation, or a workflow where dropping images into a folder should produce metadata and an HTML review screen.
---

# Build Portfolio Metadata

Use this skill in the `sale_report_skills` repository when `scripts/build_portfolio_metadata.py` exists.

## Quick Start

Run from the repository root:

```bash
python3 scripts/build_portfolio_metadata.py
```

For another local image folder:

```bash
python3 scripts/build_portfolio_metadata.py \
  --source-dir path/to/folder \
  --slug folder_slug
```

## Inputs

- `--source-dir`: Local image folder. Defaults to `portfolio/`.
- `--slug`: Output prefix. Use lowercase ASCII with underscores when possible.
- `--output-dir`: Optional output directory. Defaults to `data/`.
- `--viewer-path`: Optional HTML viewer path. Defaults to `data/{slug}_metadata_viewer.html`.
- `--seed`: Optional metadata seed JSON. Defaults to `data/portfolio_seed.json` when present.
- `--rebuild-all`: Ignore the previous index and regenerate every image.

## Outputs

For `--slug portfolio`, the script writes:

- `data/portfolio_index.json`
- `data/portfolio_index.jsonl`
- `data/portfolio_summary.json`
- `data/portfolio_thumbnails/`
- `data/portfolio_metadata_viewer.html`

The JSON/JSONL files are the machine-readable portfolio index. The HTML file is the human review surface.
The viewer default sort is upload date newest first, then brand tag order. Users can still switch to brand, ID, group, upload date, or brightness sorting.

## Default And Update Behavior

If the user does not specify a folder, use `portfolio/` and run the script without `--source-dir`.

The script updates incrementally by default:

- unchanged images keep their existing metadata record;
- new images are newly analyzed and added;
- changed images are refreshed while keeping the same portfolio ID when possible;
- images deleted from `portfolio/` are removed from the generated index.

Use `--rebuild-all` only when the user explicitly wants every image reprocessed.

## Workflow

1. Confirm the current directory is the repository root.
2. If no folder is specified, run `python3 scripts/build_portfolio_metadata.py`.
3. If another folder is specified, run the metadata script with that folder and slug.
4. Validate:
   ```bash
   python3 -m py_compile scripts/build_portfolio_metadata.py
   python3 -m json.tool data/<slug>_index.json >/tmp/<slug>_index_check.json
   python3 -m json.tool data/<slug>_summary.json >/tmp/<slug>_summary_check.json
   wc -l data/<slug>_index.jsonl
   ```
5. Open or browser-test `data/<slug>_metadata_viewer.html` when UI behavior matters.
6. Report image count, skipped video count, reused/new/rebuilt/removed record counts, output paths, and any known limitations.

## Guardrails

- Do not commit generated portfolio images, thumbnails, or `data/*` outputs.
- Do not add dependencies without approval. The current script expects Pillow for image stats and thumbnails.
- Treat first-pass metadata as review aids. Before external proposals, manually verify image rights, client names, and proposal wording.
