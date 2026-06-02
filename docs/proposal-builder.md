# Proposal Builder Workflow

Use this workflow after a brand matching run exists under `data/brand_runs/<run>/`.

## Build Outreach Assets

```bash
python3 scripts/build_brand_outreach_assets.py \
  --run-dir data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --contact-name "브랜드 담당자님"
```

## Use Explicit Portfolio IDs

```bash
python3 scripts/build_brand_outreach_assets.py \
  --run-dir data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --similar-ids P081 P048 P055 \
  --whitespace-ids P030 P083 P117
```

## Outputs

```text
data/brand_runs/<run>/outreach_assets/
├── outreach_assets.json
├── cold_email_draft.md
├── mini_proposal.html
├── proposal_sections_landscape.html
└── proposal_sections_landscape.pdf
```

## Export PDF

```bash
python3 scripts/export_proposal_sections_pdf.py \
  --run-dir data/brand_runs/<run>
```

For explicit selection:

```bash
python3 scripts/export_proposal_sections_pdf.py \
  --run-dir data/brand_runs/<run> \
  --similar-ids P081 P082 P048 \
  --whitespace-ids P030 P083 P084
```

## Customer-Facing Rules

Customer-facing SECTION HTML/PDF should show only the studio portfolio:

- Image
- Portfolio ID and cut type
- Client/project
- Work scope
- Shooting mood
- Proposal point

Do not expose brand reference images, source URLs, raw analysis tags, or automation language.

## Validation

```bash
python3 -m py_compile scripts/build_brand_outreach_assets.py scripts/export_proposal_sections_pdf.py
python3 -m json.tool data/brand_runs/<run>/outreach_assets/outreach_assets.json >/tmp/outreach_assets_check.json
pdfinfo data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.pdf
```

Render PDF pages to PNG when layout changes and verify that each page keeps at most three portfolio cards.
