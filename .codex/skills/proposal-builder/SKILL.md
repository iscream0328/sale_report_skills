---
name: proposal-builder
description: Build cold email drafts, internal proposal builder HTML, SECTION-only HTML exports, and A4 landscape PDF proposal files from brand-image-matching outputs in this sale_report_skills repository. Use when the user asks for Proposal_builder, proposal_builder, proposal builder, 미니 제안서, 콜드메일, 제안서 생성, SECTION PDF, 가로형 PDF 다운로드, or turning brand_image_matching results into sales proposal assets.
---

# Proposal Builder

This is a workspace-only skill for `<project-root>`. Use it after a `brand-image-matching` run exists under `skill_ver/data/brand_runs/<run>/`.

## Quick Start

Create the cold email, selection UI, and default proposal data:

```bash
python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/<run> \
  --brand-name "브랜드명" \
  --contact-name "브랜드 담당자님"
```

Create the direct-download A4 landscape PDF:

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/<run>
```

## Inputs

- `--run-dir`: Required. A brand matching run directory containing `brand_source_summary.json` and `portfolio_recommendations.json`.
- `--brand-name`: Display name for the email/proposal.
- `--contact-name`: Email greeting target. Defaults to `브랜드 담당자님`.
- `--similar-ids`: Optional portfolio IDs for SECTION 1.
- `--whitespace-ids`: Optional portfolio IDs for SECTION 2.

If the user picked images in the HTML UI and wants the PDF to match that selection, ask for or read the selected portfolio IDs, then pass them to `export_proposal_sections_pdf.py`.

## Outputs

The scripts write into `<run>/outreach_assets/`:

- `outreach_assets.json`: Structured email/proposal data and candidate pools.
- `cold_email_draft.md`: Editable Korean cold email draft.
- `mini_proposal.html`: Internal 담당자 screen for selecting portfolio images and previewing proposal SECTIONs.
- `proposal_sections_landscape.html`: SECTION-only customer-facing HTML.
- `proposal_sections_landscape.pdf`: A4 landscape PDF generated without opening print UI.

## Workflow

1. Confirm the current directory is `<project-root>`.
2. Generate or refresh outreach assets with `build_brand_outreach_assets.py`.
3. Generate the landscape PDF with `export_proposal_sections_pdf.py`.
4. Validate:
   ```bash
   python3 -m py_compile skill_ver/scripts/build_brand_outreach_assets.py skill_ver/scripts/export_proposal_sections_pdf.py
   python3 -m json.tool skill_ver/data/brand_runs/<run>/outreach_assets/outreach_assets.json >/dev/null
   pdfinfo skill_ver/data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.pdf
   ```
5. If layout changed, render at least the first PDF page to PNG with `pdftoppm` and inspect it.
6. Report the output paths, selected counts, PDF page count, and any known limitations.

## Selection Examples

Use defaults from `outreach_assets.json`:

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/<run>
```

Use explicit selected portfolio IDs:

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/<run> \
  --similar-ids P081 P082 P048 \
  --whitespace-ids P030 P083 P084
```

## Content Rules

- Customer-facing SECTION outputs should show only the studio portfolio: image, portfolio ID/cut, client/project, work scope, shooting mood, and proposal point.
- Do not expose brand reference images, source URLs, raw analysis tags, or “we analyzed your site/Instagram” language in customer-facing outputs.
- Cold email tone should feel like a human observed the brand and is sharing relevant work, not like an automated analysis report.
- Before external use, manually verify image rights, brand/client names, and proposal wording.

## Guardrails

- Keep edits inside `skill_ver/` and `.codex/skills/`; do not touch existing `api/` or `web/` unless explicitly requested.
- Do not add dependencies without approval. The PDF exporter uses local Chrome/Chromium via DevTools and existing Python packages.
- If Chrome is not found, pass `--chrome-path` to `export_proposal_sections_pdf.py`.
