# sale_report_skills

Codex skills and standalone Python scripts for turning brand imagery into portfolio recommendations, cold email drafts, and lightweight proposal assets.

This repository contains only reusable skill instructions, workflow scripts, schemas, fixtures, and docs. It does not include portfolio images, Instagram downloads, brand run outputs, generated thumbnails, PDFs, or private application code.

## Repository Structure

```text
.
├── .codex/skills/          # Codex skill instructions
├── data/                   # Generated local outputs, ignored except .gitkeep
├── docs/                   # Current operating docs
├── fixtures/               # Small HTML fixture for local parser tests
├── portfolio/              # Put local portfolio images here; only .gitkeep is tracked
├── schemas/                # JSON schemas for records and recommendations
├── scripts/                # Python workflow scripts
│   └── instagram/          # gallery-dl helper and local download folders
└── README.md
```

## Included Skills

- `build-portfolio-metadata`: Build portfolio image metadata, thumbnails, JSON/JSONL, and a review HTML viewer.
- `brand-image-matching`: Collect brand store/Instagram imagery and recommend similar plus whitespace portfolio examples.
- `proposal-builder`: Generate cold email drafts, an internal proposal builder, SECTION-only HTML, and A4 landscape PDFs.

## New Codex User Setup

For a fresh project, a Codex user can clone this repository and run the workflow in order. The repository includes the skills, scripts, schemas, fixtures, and operating docs. It does not include the user's real portfolio images or generated brand outputs.

```bash
git clone https://github.com/iscream0328/sale_report_skills.git
cd sale_report_skills

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Then place portfolio images in the default input folder:

```text
portfolio/
```

The repository tracks the empty `portfolio/` folder with `.gitkeep`, but it does not commit real images.

After that, run the skills or scripts in this order:

1. Build the portfolio index from `portfolio/`.
2. Download Instagram images if the brand's Instagram should be included.
3. Run brand image matching with the store URL and/or Instagram folder.
4. Generate the cold email draft and internal proposal builder.
5. Export SECTION-only HTML and an A4 landscape proposal PDF.

Codex users can ask Codex to use the skills in `.codex/skills/` in the same order:

```text
Use build-portfolio-metadata for the images in portfolio/.
Use brand-image-matching with this store URL and Instagram folder.
Use proposal-builder for the generated brand run.
```

## Basic Workflow

Run commands from the repository root.

0. Install Python dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

1. Prepare portfolio images locally:

```bash
# portfolio/ already exists after clone.
# Add local .jpg, .jpeg, .png, or .webp files there.
```

2. Build portfolio metadata:

```bash
python3 scripts/build_portfolio_metadata.py
```

By default, the script reads `portfolio/`, writes `data/portfolio_index.json`, and updates the existing index incrementally. If images are added, only new or changed images are newly analyzed. If images are removed from `portfolio/`, their records are removed from the generated index. Use `--rebuild-all` only when you want to regenerate every record from scratch.

The generated HTML viewer opens with upload date newest first, then brand tag order.

3. Download Instagram images when needed:

```bash
./scripts/instagram/download_ig.command example_profile 20 chrome
```

4. Build a brand matching run:

```bash
python3 scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --instagram-folder "scripts/instagram/downloads/example_profile" \
  --brand-slug example_brand \
  --max-pages 12 \
  --max-downloads 100
```

5. Build outreach assets:

```bash
python3 scripts/build_brand_outreach_assets.py \
  --run-dir data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --contact-name "브랜드 담당자님"
```

6. Export an A4 landscape proposal PDF:

```bash
python3 scripts/export_proposal_sections_pdf.py \
  --run-dir data/brand_runs/<run>
```

## Current Docs

- [Full User Guide](docs/USERGUIDE.md)
- [Portfolio Metadata Workflow](docs/portfolio-metadata.md)
- [Brand Image Matching Workflow](docs/brand-image-matching.md)
- [Proposal Builder Workflow](docs/proposal-builder.md)
- [Instagram Download Workflow](docs/instagram-download.md)

## Generated Data Policy

The following are generated locally and intentionally ignored:

- `portfolio/*` except `portfolio/.gitkeep`
- `data/*`
- `scripts/instagram/downloads/*`
- `scripts/instagram/archive/*`
- `scripts/instagram/logs/*`
- generated HTML/PDF/image outputs

## Safety Notes

- Before external use, manually verify brand names, contact names, portfolio image rights, and client/project names.
- Customer-facing proposal outputs should not expose brand reference images, source URLs, raw analysis tags, or automation language.
- Instagram downloading uses browser cookies through `gallery-dl`; use only accounts and content you are authorized to access.
