# Brand Image Matching Workflow

Use this workflow after `data/portfolio_all_index.json` exists.

## Command

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand \
  --max-pages 12 \
  --max-downloads 100
```

## Inputs

- `--url`: Brand store, product detail, collection, lookbook, campaign, editorial, or project URL. Repeat for multiple URLs.
- `--instagram-folder`: Local gallery-dl folder from `scripts/instagram/download_ig.command`.
- `--source-html`: Saved HTML fixture or static page.
- `--portfolio-index`: Defaults to `data/portfolio_all_index.json`.
- `--output-dir`: Defaults to `data/brand_runs/`.

## Outputs

```text
data/brand_runs/<run>/
├── brand_source_images.json
├── brand_source_images.jsonl
├── brand_source_summary.json
├── portfolio_recommendations.json
├── index.html
├── source_images/
└── source_thumbnails/
```

## Recommendation Semantics

- Similar recommendations follow a representative-mood strategy. They are selected as a coherent set, not as strict one-to-one matches for every brand source image.
- Whitespace recommendations focus on cut types, commerce roles, or visual directions that are underrepresented in the current brand source set.
- Tags and labels are first-pass classifications for review, not final truth.

## Validation

```bash
python3 -m py_compile scripts/build_brand_url_matches.py
python3 -m json.tool data/brand_runs/<run>/brand_source_images.json >/tmp/brand_source_images_check.json
python3 -m json.tool data/brand_runs/<run>/portfolio_recommendations.json >/tmp/portfolio_recommendations_check.json
```

When layout or interactions changed, open `index.html` in a browser and check image loading, source links, no horizontal overflow, and tooltip behavior.
