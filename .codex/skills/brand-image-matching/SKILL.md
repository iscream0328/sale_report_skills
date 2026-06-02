---
name: brand-image-matching
description: Build a brand image matching run from a brand store URL and/or Instagram download folder, producing source image candidates, similar portfolio recommendations, whitespace recommendations, and a visual HTML review page. Use when the user asks for brand_image_matching, brand URL matching, 자사몰/인스타 이미지 수집, or similar/whitespace portfolio recommendations from brand imagery.
---

# Brand Image Matching

Use this skill in the `sale_report_skills` repository after a portfolio index exists at `data/portfolio_all_index.json`.

## Quick Start

Run from the repository root:

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand \
  --max-pages 12 \
  --max-downloads 100
```

If Instagram images are needed, download them first:

```bash
./scripts/instagram/download_ig.command example_profile 20 chrome
```

Then pass the resulting folder:

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand
```

## Inputs

- `--url`: Brand store, product list, collection, campaign, lookbook, editorial, or project URL. Repeat for multiple URLs.
- `--instagram-folder`: A gallery-dl download folder created by `scripts/instagram/download_ig.command`.
- `--source-html`: Saved HTML for pages that cannot be fetched directly.
- `--brand-slug`: Stable output slug. Use lowercase ASCII with underscores when possible.
- `--run-id`: Optional stable run id when regenerating a known viewer.
- `--portfolio-index`: Optional portfolio index. Defaults to `data/portfolio_all_index.json`.
- `--instagram-max-images-per-post`: Defaults to 2 so one carousel does not dominate the brand mood.

## Outputs

The script writes to:

```text
data/brand_runs/{brand_slug}_{run_id}/
```

Core files:

- `brand_source_images.json`: All analyzed brand source image records.
- `brand_source_summary.json`: Product/campaign selections and observed mood distribution.
- `portfolio_recommendations.json`: Similar 10 and whitespace 10 recommendations with evidence.
- `index.html`: Human review surface with source links, recommendation strategy, tag guide, and comparison cards.
- `source_images/`, `source_thumbnails/`: Local image assets for the review page.

## Recommended Workflow

1. Confirm you are in the repository root.
2. If Instagram should be included, follow `docs/instagram-download.md`.
3. Run `scripts/build_brand_url_matches.py` with the store URL and/or Instagram folder.
4. Validate:
   ```bash
   python3 -m py_compile scripts/build_brand_url_matches.py
   python3 -m json.tool data/brand_runs/<run>/brand_source_images.json >/dev/null
   python3 -m json.tool data/brand_runs/<run>/portfolio_recommendations.json >/dev/null
   ```
5. Browser-test `index.html` when layout or interactions changed. Check desktop and mobile widths for image loading, no horizontal overflow, clickable source images, and tooltip behavior.
6. Report the viewer path, candidate count, selected product/campaign counts, similar/whitespace counts, and any warnings.

## Matching Semantics

- Product candidates should prefer store/product-detail sources.
- Campaign/collaboration/project candidates should prefer Instagram or campaign-like sources.
- Similar recommendations use `대표무드형 매칭` by default: select a coherent set of 10 portfolio images that follows the brand's repeated cut types, tags, brightness, frame, and commerce roles.
- Whitespace recommendations focus on what the brand shows less often but the portfolio can offer as a new proposal direction.
- Tag chips in the HTML viewer are first-pass classifications. Treat them as review aids, not final truth.

## Guardrails

- Do not commit generated brand run outputs under `data/brand_runs/`.
- Do not add dependencies without approval.
- If network fetch fails in the sandbox, rerun the same command with the required network approval instead of accepting a partial store-less run.
- Before external sales use, manually verify image rights, brand names, product names, and proposal wording.
