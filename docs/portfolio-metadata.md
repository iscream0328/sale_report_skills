# Portfolio Metadata Workflow

Use this workflow to turn local portfolio image folders into a searchable metadata index and review HTML.

## Command

```bash
python3 scripts/build_portfolio_metadata.py \
  --source-dir portfolio \
  --slug portfolio
```

## Inputs

- Local source folder such as `portfolio/`
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

## Review Notes

The metadata uses local heuristics for cut type, color, brightness, contrast, visual tags, commerce tags, brand tags, and proposal-use text. Treat `review_status: needs_review` as intentional. Human review is required before external proposals.
