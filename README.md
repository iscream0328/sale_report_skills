# sale_report_skills

Standalone Codex skills and scripts for a brand image matching and sales proposal workflow.

This repository contains only the reusable workflow code and documentation. It intentionally does not include portfolio images, Instagram downloads, brand run outputs, generated thumbnails, PDFs, or private project application code.

## What Is Included

- `.codex/skills/`
  - `build-portfolio-metadata`
  - `brand-image-matching`
  - `proposal-builder`
- `skill_ver/scripts/`
  - Portfolio metadata generation
  - Brand URL and Instagram-folder image matching
  - Cold email and proposal asset generation
  - A4 landscape PDF export through local Chrome/Chromium
- `skill_ver/schemas/`
  - JSON schemas for portfolio images, brand source images, and match results
- `skill_ver/*.md`
  - Workflow plans, operating guides, and implementation notes
- `script/ig_downloads/`
  - `gallery-dl` helper command and usage guide

## What Is Excluded

The following are generated or project-private and are ignored by git:

- `portfolio_all/`
- `portfolio/`
- `skill_ver/data/`
- `script/ig_downloads/downloads/`
- `script/ig_downloads/archive/`
- `script/ig_downloads/logs/`
- generated HTML/PDF/image outputs
- Python cache files and OS metadata

## Basic Workflow

Run commands from the repository root.

1. Prepare portfolio images locally:

```bash
mkdir -p portfolio_all
```

2. Build portfolio metadata:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py \
  --source-dir portfolio_all \
  --slug portfolio_all
```

3. Download Instagram images when needed:

```bash
./script/ig_downloads/download_ig.command example_profile 20 chrome
```

4. Build a brand matching run:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "script/ig_downloads/downloads/example_profile" \
  --brand-slug example_brand \
  --max-pages 12 \
  --max-downloads 100
```

5. Build outreach assets:

```bash
python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --contact-name "브랜드 담당자님"
```

6. Export A4 landscape proposal PDF:

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/<run>
```

## Safety Notes

- Before using externally, manually verify brand names, contact names, portfolio image rights, and client/project names.
- Customer-facing proposal outputs should not expose brand reference images, source URLs, raw analysis tags, or automation language.
- Instagram downloading uses browser cookies through `gallery-dl`; use only accounts and content you are authorized to access.

