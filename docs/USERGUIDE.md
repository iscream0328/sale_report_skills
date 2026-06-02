# User Guide

This guide explains the current end-to-end workflow for this repository.

The workflow turns local portfolio images plus a brand store URL and/or Instagram download folder into:

1. A searchable portfolio metadata index
2. A brand image matching review page
3. Similar and whitespace portfolio recommendations
4. A cold email draft
5. An internal proposal builder
6. SECTION-only HTML and A4 landscape PDF proposal outputs

Generated data is written under `data/` and is intentionally ignored by git.

## 0. Install Dependencies

Run commands from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The Python scripts require Pillow. The PDF exporter also requires `websocket-client` and a local Chrome/Chromium executable.

## 1. Build Portfolio Metadata

Put local portfolio images in `portfolio/`.

```bash
python3 scripts/build_portfolio_metadata.py
```

Expected outputs:

```text
data/portfolio_index.json
data/portfolio_index.jsonl
data/portfolio_summary.json
data/portfolio_thumbnails/
data/portfolio_metadata_viewer.html
```

The HTML viewer opens with upload date newest first, then brand tag order.

Validate:

```bash
python3 -m py_compile scripts/build_portfolio_metadata.py
python3 -m json.tool data/portfolio_index.json >/tmp/portfolio_index_check.json
python3 -m json.tool data/portfolio_summary.json >/tmp/portfolio_summary_check.json
wc -l data/portfolio_index.jsonl
```

Default behavior:

- If no folder is specified, the script scans `portfolio/`.
- Re-running the script updates `data/portfolio_index.json` incrementally.
- Images that are still present and unchanged keep their existing metadata record.
- New or changed images are analyzed and added or refreshed.
- Images removed from `portfolio/` are removed from the generated index.
- Use `--rebuild-all` only when every image should be regenerated from scratch.

## 2. Download Instagram Images

Instagram often requires logged-in browser cookies. Log in through Chrome first, then run:

```bash
./scripts/instagram/download_ig.command example_profile 20 chrome
```

Expected folder:

```text
scripts/instagram/downloads/example_profile/
```

The brand matching script reads gallery-dl sidecar JSON and limits Instagram candidates to two images per post by default so one carousel does not dominate the results.

## 3. Build Brand Image Matching Run

Use a store URL plus the Instagram folder:

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand \
  --max-pages 12 \
  --max-downloads 100
```

Store-only:

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --brand-slug example_brand
```

Instagram-only:

```bash
python3 scripts/build_brand_url_matches.py \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand_instagram
```

Expected run folder:

```text
data/brand_runs/{brand_slug}_{run_id}/
```

Core outputs:

```text
brand_source_images.json
brand_source_summary.json
portfolio_recommendations.json
index.html
source_images/
source_thumbnails/
```

Validate:

```bash
python3 -m py_compile scripts/build_brand_url_matches.py
python3 -m json.tool data/brand_runs/<run>/brand_source_images.json >/tmp/brand_source_images_check.json
python3 -m json.tool data/brand_runs/<run>/portfolio_recommendations.json >/tmp/portfolio_recommendations_check.json
```

Open `data/brand_runs/<run>/index.html` to review product candidates, campaign candidates, similar portfolio recommendations, and whitespace recommendations.

## 4. Build Cold Email And Proposal Assets

Create outreach assets:

```bash
python3 scripts/build_brand_outreach_assets.py \
  --run-dir data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --contact-name "브랜드 담당자님"
```

Expected outputs:

```text
data/brand_runs/<run>/outreach_assets/outreach_assets.json
data/brand_runs/<run>/outreach_assets/cold_email_draft.md
data/brand_runs/<run>/outreach_assets/mini_proposal.html
```

The default selection uses the top three similar recommendations and top three whitespace recommendations.

To use explicit portfolio IDs:

```bash
python3 scripts/build_brand_outreach_assets.py \
  --run-dir data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --similar-ids P081 P048 P055 \
  --whitespace-ids P030 P083 P117
```

## 5. Export A4 Landscape PDF

Use the current default selection:

```bash
python3 scripts/export_proposal_sections_pdf.py \
  --run-dir data/brand_runs/<run>
```

Use explicit selected IDs:

```bash
python3 scripts/export_proposal_sections_pdf.py \
  --run-dir data/brand_runs/<run> \
  --similar-ids P081 P082 P048 \
  --whitespace-ids P030 P083 P084
```

Expected outputs:

```text
data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.html
data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.pdf
```

Validate:

```bash
python3 -m py_compile scripts/build_brand_outreach_assets.py scripts/export_proposal_sections_pdf.py
python3 -m json.tool data/brand_runs/<run>/outreach_assets/outreach_assets.json >/tmp/outreach_assets_check.json
pdfinfo data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.pdf
```

`pdfinfo` should report A4 landscape size:

```text
Page size: 841.92 x 594.96 pts (A4)
```

## Final Human Review

Before sending anything externally, manually verify:

- Brand name and contact name
- Portfolio image rights
- External visibility of client/project names
- Cold email tone
- Customer-facing SECTION/PDF does not expose brand reference images, source URLs, or raw analysis tags
- Selected similar recommendations fit the brand mood
- Selected whitespace recommendations are plausible new directions
- PDF page count and 3-card-per-page layout
