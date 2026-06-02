# Portfolio Metadata Workflow

Use this workflow to turn local portfolio image folders into a searchable metadata index and review HTML.

## Command

```bash
python3 scripts/build_portfolio_metadata.py
```

## Inputs

- Local source folder. Defaults to `portfolio/` when no folder is specified.
- Optional sidecar metadata such as `image.jpg.json`
- Optional seed metadata at `data/portfolio_seed.json`

Supported image extensions:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

Video files are not analyzed. They are counted and listed in the summary as skipped.

## Outputs

```text
data/<slug>_index.json
data/<slug>_index.jsonl
data/<slug>_summary.json
data/<slug>_thumbnails/
data/<slug>_metadata_viewer.html
```

With the default folder, `<slug>` is `portfolio`.

The HTML viewer opens with upload date newest first, then brand tag order. Use the sort menu to switch to brand, ID, group, upload date, or brightness sorting.

## Incremental Updates

The script reads the existing `data/<slug>_index.json` before writing a new one.

- Unchanged images keep their existing metadata record.
- New images are analyzed and appended with new portfolio IDs.
- Changed images are refreshed while keeping the same portfolio ID when possible.
- Deleted images are removed from the generated index.
- Use `--rebuild-all` to ignore the previous index and regenerate every record.

## Review Notes

The metadata uses local heuristics for cut type, color, brightness, contrast, visual tags, commerce tags, brand tags, and proposal-use text. Treat `review_status: needs_review` as intentional. Human review is required before external proposals.
