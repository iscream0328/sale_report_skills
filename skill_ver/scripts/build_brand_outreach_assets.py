#!/usr/bin/env python3
"""Create cold email and mini proposal drafts from a brand image matching run."""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import build_brand_url_matches as matching


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUN_DIR = ROOT / "skill_ver" / "data" / "brand_runs"
DEFAULT_PORTFOLIO_INDEX = ROOT / "skill_ver" / "data" / "portfolio_all_index.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def e(value: Any) -> str:
    return html.escape(str(value or ""))


def clean_brand_name(slug: str) -> str:
    text = re.sub(r"_(combined|instagram|web|ig|diverse|evidence_view)$", "", slug)
    text = text.replace("_", " ").strip()
    return " ".join(word.capitalize() for word in text.split()) or slug


def clean_client_name(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "포트폴리오 프로젝트"
    parts = re.split(r"\s*/\s*|\s+", text)
    clean_parts = []
    for part in parts:
        part = part.strip().strip(",")
        if not part:
            continue
        clean_parts.append(part[1:] if part.startswith("@") else part)
    return ", ".join(dict.fromkeys(clean_parts)) or text


def normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def portfolio_lookup(index_path: Path) -> dict[str, dict[str, Any]]:
    records = load_json(index_path)
    if not isinstance(records, list):
        raise ValueError(f"portfolio index must be a list: {index_path}")
    return {record.get("portfolio_id"): record for record in records if record.get("portfolio_id")}


def first_sentence(value: Any, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return fallback
    parts = re.split(r"(?<=[.!?。])\s+", text)
    return parts[0].strip() if parts and parts[0].strip() else text


def portfolio_mood(meta: dict[str, Any], recommendation: dict[str, Any]) -> str:
    summary = meta.get("analysis_summary") or recommendation.get("proposal_use")
    if summary:
        return first_sentence(summary)
    cut_label = meta.get("cut_type_label") or recommendation.get("cut_type_label") or "포트폴리오"
    group = meta.get("group") or recommendation.get("group") or "촬영 작업"
    return f"{group}에서 {cut_label} 성격을 보여주는 작업입니다."


def portfolio_scenario(meta: dict[str, Any], recommendation_type: str) -> str:
    key = "similar_when" if recommendation_type == "similar" else "contrast_when"
    values = normalize_list(meta.get(key))
    if values:
        return values[0]
    return meta.get("proposal_use") or "브랜드 제안에 맞춰 활용 가능한 포트폴리오입니다."


def natural_cut_phrase(label: str | None) -> str:
    mapping = {
        "제품 오브젝트": "제품의 형태와 소재가 또렷하게 보이는 오브젝트 컷",
        "스포츠/액티브": "움직임이 살아있는 착용 컷",
        "무드 클로즈업": "브랜드의 감정선을 압축하는 클로즈업 컷",
        "시즌/라이프스타일": "계절감과 착용 상황이 느껴지는 라이프스타일 컷",
        "모델 착용/스타일링": "스타일링과 실루엣이 자연스럽게 보이는 모델 컷",
        "캠페인 키비주얼": "시즌 메시지를 한 장으로 보여주는 캠페인 컷",
        "디테일/패턴": "소재와 디테일을 설득력 있게 보여주는 컷",
    }
    return mapping.get(str(label or ""), str(label or "촬영"))


def natural_angles(labels: list[str]) -> str:
    phrases = [natural_cut_phrase(label) for label in labels[:2]]
    return ", ".join(dict.fromkeys(phrases)) or "제품과 브랜드 무드가 자연스럽게 이어지는 촬영"


def top_items(counts: dict[str, Any], limit: int = 3, labels: dict[str, str] | None = None) -> list[dict[str, Any]]:
    labels = labels or {}
    return [
        {
            "key": key,
            "label": labels.get(key, key),
            "count": value,
            "explanation": matching.tag_explanation(key),
        }
        for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]


def select_recommendations(
    recommendations: list[dict[str, Any]],
    selected_ids: list[str] | None,
    count: int,
    label: str,
) -> list[dict[str, Any]]:
    if selected_ids:
        lookup = {record["portfolio_id"]: record for record in recommendations}
        missing = [portfolio_id for portfolio_id in selected_ids if portfolio_id not in lookup]
        if missing:
            raise ValueError(f"{label} 추천에서 찾을 수 없는 portfolio_id: {', '.join(missing)}")
        return [lookup[portfolio_id] for portfolio_id in selected_ids]
    return recommendations[:count]


def selected_source_records(summary: dict[str, Any], source_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    source_ids = []
    source_ids.extend(summary.get("selected_product_image_ids", [])[:4])
    source_ids.extend(summary.get("selected_campaign_image_ids", [])[:4])
    return [source_lookup[source_id] for source_id in source_ids if source_id in source_lookup]


def src_for_outreach(path: str | None) -> str:
    if not path:
        return ""
    return posixpath.normpath("../" + path)


def recommendation_image_src(record: dict[str, Any]) -> str:
    return src_for_outreach(record.get("html_thumbnail_path") or record.get("thumbnail_path") or record.get("image_path"))


def source_image_src(record: dict[str, Any]) -> str:
    return src_for_outreach(record.get("html_thumbnail_path") or record.get("thumbnail_path") or record.get("local_image_path"))


def reference_tiles(record: dict[str, Any], source_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    tiles = []
    for source_id in record.get("brand_reference_image_ids", [])[:2]:
        source = source_lookup.get(source_id)
        if not source:
            continue
        tiles.append(
            {
                "source_image_id": source_id,
                "cut_type_label": source.get("cut_type_label"),
                "page_url": source.get("page_url"),
                "image_src": source_image_src(source),
            }
        )
    return tiles


def summarize_strategy(
    summary: dict[str, Any],
    similar: list[dict[str, Any]],
    whitespace: list[dict[str, Any]],
) -> dict[str, Any]:
    dominant_cut = top_items(summary.get("observed_cut_type_counts", {}), 1, matching.CUT_TYPE_LABELS)
    top_visual = top_items(summary.get("observed_visual_tag_counts", {}), 4)
    top_commerce = top_items(summary.get("observed_commerce_tag_counts", {}), 4)
    missing_labels = summary.get("missing_cut_type_labels", [])[:4]
    similar_cuts = list(dict.fromkeys(record.get("cut_type_label") for record in similar if record.get("cut_type_label")))
    whitespace_cuts = list(dict.fromkeys(record.get("cut_type_label") for record in whitespace if record.get("cut_type_label")))
    return {
        "dominant_cut": dominant_cut[0] if dominant_cut else None,
        "top_visual_tags": top_visual,
        "top_commerce_tags": top_commerce,
        "missing_cut_type_labels": missing_labels,
        "similar_cut_labels": similar_cuts,
        "whitespace_cut_labels": whitespace_cuts,
    }


def make_subjects(brand_name: str, strategy: dict[str, Any]) -> list[str]:
    return [
        f"{brand_name}에 어울릴 촬영 포트폴리오를 공유드립니다",
        f"{brand_name} 제품/캠페인 무드와 맞닿는 작업 사례",
        f"{brand_name}에 제안드리고 싶은 촬영 방향입니다",
    ]


def make_email_body(
    brand_name: str,
    contact_name: str,
    studio_name: str,
    strategy: dict[str, Any],
    similar: list[dict[str, Any]],
    whitespace: list[dict[str, Any]],
) -> str:
    similar_angles = natural_angles(strategy.get("similar_cut_labels", []))
    whitespace_angles = natural_angles(strategy.get("whitespace_cut_labels", []))

    return "\n\n".join(
        [
            f"안녕하세요, {contact_name}. {studio_name}입니다.",
            f"{brand_name}이 보여주는 제품의 실루엣과 시즌 무드가 인상 깊어, 저희가 진행했던 작업 중 함께 참고하실 만한 포트폴리오를 정리해 연락드립니다.",
            f"저희는 여러 패션/라이프스타일 브랜드와 {similar_angles} 같은 촬영을 진행해왔고, 필요할 때는 {whitespace_angles}처럼 조금 다른 결의 이미지도 함께 제안해왔습니다.",
            "제품이 먼저 또렷하게 보이면서도 브랜드의 분위기가 남는 컷, 착용 장면과 디테일을 자연스럽게 연결하는 촬영을 특히 중요하게 보고 있습니다.",
            "간단한 포트폴리오 형태로 몇 가지 작업을 추려두었습니다. 가볍게 확인해보시고 향후 시즌 촬영이나 협업 콘텐츠에 맞는 레퍼런스가 필요하실 때 편하게 말씀 주세요.",
            "감사합니다.",
        ]
    )


def make_concepts(strategy: dict[str, Any], similar: list[dict[str, Any]], whitespace: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dominant = (strategy.get("dominant_cut") or {}).get("label") or "현재 이미지 무드"
    missing = ", ".join(strategy.get("missing_cut_type_labels", [])[:2]) or "보완 컷"
    similar_ids = ", ".join(record["portfolio_id"] for record in similar[:2])
    whitespace_ids = ", ".join(record["portfolio_id"] for record in whitespace[:2])
    return [
        {
            "title": "현재 무드 확장",
            "body": f"{dominant} 흐름을 유지하면서 {similar_ids}처럼 상품/캠페인 사이의 연결감을 강화합니다.",
        },
        {
            "title": "보완 컷 제안",
            "body": f"현재 후보에서 덜 보이는 {missing} 방향을 {whitespace_ids} 같은 포트폴리오로 보강합니다.",
        },
        {
            "title": "상세페이지와 SNS 동시 활용",
            "body": "상세 상단, SNS 후킹 컷, 릴스 커버로 나눠 같은 촬영에서 여러 커머스 역할을 만들 수 있게 설계합니다.",
        },
    ]


def recommendation_payload(
    records: list[dict[str, Any]],
    portfolio_records: dict[str, dict[str, Any]],
    recommendation_type: str,
) -> list[dict[str, Any]]:
    payload = []
    for record in records:
        portfolio_id = record.get("portfolio_id")
        meta = portfolio_records.get(portfolio_id, {})
        work_scope = normalize_list(meta.get("work_scope"))
        client_label = clean_client_name(meta.get("client_or_project") or record.get("client_or_project"))
        payload.append(
            {
            "portfolio_id": record.get("portfolio_id"),
            "rank": record.get("rank"),
            "score": record.get("score"),
            "recommendation_type": recommendation_type,
            "section_label": "SECTION 1" if recommendation_type == "similar" else "SECTION 2",
            "section_title": "브랜드 무드와 결이 맞는 포트폴리오" if recommendation_type == "similar" else "다른 방향으로 확장 가능한 포트폴리오",
            "client_or_project": client_label,
            "project_group_id": meta.get("project_group_id") or record.get("project_group_id"),
            "group": meta.get("group") or record.get("group"),
            "cut_type_label": record.get("cut_type_label"),
            "work_scope": work_scope,
            "work_scope_label": ", ".join(work_scope) if work_scope else "Visual Direction / Styling",
            "portfolio_mood": portfolio_mood(meta, record),
            "portfolio_scenario": portfolio_scenario(meta, recommendation_type),
            "proposal_use": record.get("proposal_use"),
            "proposal_sentence": record.get("proposal_sentence"),
            "reasons": record.get("reasons", [])[:4],
            "visual_tags": (meta.get("visual_tags") or record.get("visual_tags") or [])[:6],
            "commerce_tags": (meta.get("commerce_tags") or record.get("commerce_tags") or [])[:5],
            "rights_note": meta.get("rights_note"),
            "review_status": meta.get("review_status") or record.get("review_status"),
            "image_src": recommendation_image_src(record),
        }
        )
    return payload


def source_payload(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_image_id": record.get("source_image_id"),
            "cut_type_label": record.get("cut_type_label"),
            "source": record.get("source"),
            "page_url": record.get("page_url"),
            "image_src": source_image_src(record),
        }
        for record in records
    ]


def markdown_email(subjects: list[str], body: str, selected: dict[str, Any]) -> str:
    similar_ids = ", ".join(record["portfolio_id"] for record in selected["similar_recommendations"])
    whitespace_ids = ", ".join(record["portfolio_id"] for record in selected["whitespace_recommendations"])
    subject_lines = "\n".join(f"- {subject}" for subject in subjects)
    return f"""# 콜드메일 초안

## 제목 후보

{subject_lines}

## 본문

{body}

## 사용 이미지

- 유사 포트폴리오: {similar_ids}
- 보완 포트폴리오: {whitespace_ids}

## 발송 전 검수

- 브랜드명, 담당자명, 권리/사용 가능 이미지, 실제 제안 범위를 사람이 최종 확인해야 합니다.
"""


def chip_html(items: list[str]) -> str:
    return "".join(f"<span>{e(item)}</span>" for item in items)


def source_grid_html(records: list[dict[str, Any]]) -> str:
    return "".join(
        f"""
        <a class="source-thumb" href="{e(record.get('page_url'))}" target="_blank" rel="noreferrer">
          <img src="{e(record.get('image_src'))}" alt="{e(record.get('source_image_id'))}">
          <span>{e(record.get('source_image_id'))} · {e(record.get('cut_type_label'))}</span>
        </a>
        """
        for record in records
    )


def recommendation_card_html(record: dict[str, Any], label: str) -> str:
    reasons = "".join(f"<li>{e(reason)}</li>" for reason in record.get("reasons", [])[:3])
    refs = "".join(
        f"""
        <a href="{e(ref.get('page_url'))}" target="_blank" rel="noreferrer">
          <img src="{e(ref.get('image_src'))}" alt="{e(ref.get('source_image_id'))}">
          <span>{e(ref.get('source_image_id'))}</span>
        </a>
        """
        for ref in record.get("brand_references", [])
    )
    return f"""
      <article class="proposal-card">
        <div class="card-media">
          <img src="{e(record.get('image_src'))}" alt="{e(record.get('portfolio_id'))}">
          <div class="ref-strip">{refs}</div>
        </div>
        <div class="card-copy">
          <div class="eyebrow">{e(label)} · {e(record.get('cut_type_label'))}</div>
          <h3>{e(record.get('portfolio_id'))}</h3>
          <p>{e(record.get('proposal_use'))}</p>
          <ul>{reasons}</ul>
          <div class="chips">{chip_html(record.get('visual_tags', [])[:4] + record.get('commerce_tags', [])[:3])}</div>
        </div>
      </article>
    """


def proposal_html(asset: dict[str, Any]) -> str:
    brand = asset["brand_name"]
    strategy = asset["strategy"]
    dominant = (strategy.get("dominant_cut") or {}).get("label") or "현재 이미지 무드"
    top_tags = ", ".join(item["key"] for item in strategy.get("top_visual_tags", [])[:4])
    missing = ", ".join(strategy.get("missing_cut_type_labels", [])[:4]) or "추가 검수 필요"
    concept_html = "".join(
        f"<li><strong>{e(item['title'])}</strong><span>{e(item['body'])}</span></li>"
        for item in asset["concept_options"]
    )
    similar_cards = "".join(recommendation_card_html(record, "유사 레퍼런스") for record in asset["selected"]["similar_recommendations"])
    whitespace_cards = "".join(recommendation_card_html(record, "보완 제안") for record in asset["selected"]["whitespace_recommendations"])
    source_html = source_grid_html(asset["brand_source_images"])
    subjects = "".join(f"<li>{e(subject)}</li>" for subject in asset["cold_email"]["subject_candidates"])
    email_body = "<br><br>".join(e(paragraph) for paragraph in asset["cold_email"]["body"].split("\n\n"))
    generated_at = asset["generated_at"]
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(brand)} Mini Proposal</title>
  <link rel="icon" href="data:,">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif; background: #fbfaf7; color: #17120f; line-height: 1.55; }}
    main {{ width: min(1180px, calc(100% - 40px)); margin: 0 auto; padding: 44px 0 72px; }}
    section {{ margin-top: 34px; background: #fff; border: 1px solid rgba(30,24,20,.12); border-radius: 12px; padding: 26px; }}
    header {{ padding: 34px 0 18px; border-bottom: 1px solid rgba(30,24,20,.12); }}
    h1 {{ margin: 0; font-family: Georgia, "Times New Roman", serif; font-weight: 400; font-size: clamp(2.4rem, 6vw, 5rem); line-height: 1.03; overflow-wrap: anywhere; }}
    h2 {{ margin: 0 0 14px; font-size: 1.45rem; }}
    h3 {{ margin: 0 0 8px; font-size: 1.25rem; }}
    p {{ color: #665d54; margin: 0; }}
    .eyebrow {{ color: #b23c16; font-size: .74rem; font-weight: 800; text-transform: uppercase; letter-spacing: .02em; }}
    .summary-grid {{ display: grid; grid-template-columns: .9fr 1.1fr; gap: 22px; align-items: start; }}
    .metric-list {{ display: grid; gap: 10px; margin-top: 16px; }}
    .metric-list div {{ display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border-radius: 8px; background: #f6f0e6; }}
    .source-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
    .source-thumb {{ color: inherit; text-decoration: none; border: 1px solid rgba(30,24,20,.1); border-radius: 8px; overflow: hidden; background: #fbfaf7; }}
    .source-thumb img, .proposal-card img {{ width: 100%; aspect-ratio: 4 / 5; object-fit: cover; display: block; background: #fff3cf; }}
    .source-thumb span {{ display: block; padding: 8px; color: #665d54; font-size: .75rem; }}
    .proposal-list {{ display: grid; gap: 14px; }}
    .proposal-card {{ display: grid; grid-template-columns: 260px 1fr; gap: 18px; border: 1px solid rgba(30,24,20,.1); border-radius: 10px; padding: 14px; background: #fbfaf7; }}
    .card-media {{ display: grid; grid-template-columns: 1fr 74px; gap: 8px; align-items: start; }}
    .card-media > img {{ border-radius: 8px; }}
    .ref-strip {{ display: grid; gap: 8px; }}
    .ref-strip a {{ color: inherit; text-decoration: none; }}
    .ref-strip img {{ border-radius: 6px; }}
    .ref-strip span {{ display: block; color: #665d54; font-size: .68rem; }}
    ul {{ margin: 10px 0 0 18px; padding: 0; color: #312923; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }}
    .chips span {{ border: 1px solid rgba(30,24,20,.12); border-radius: 6px; padding: 3px 6px; color: #665d54; background: #fff8e7; font-size: .72rem; }}
    .concepts {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 0; padding: 0; list-style: none; }}
    .concepts li {{ border-radius: 10px; background: #fff3cf; padding: 14px; }}
    .concepts strong, .concepts span {{ display: block; }}
    .email-box {{ background: #17120f; color: #fffaf0; border-radius: 10px; padding: 18px; }}
    .email-box p, .email-box li {{ color: #fffaf0; }}
    .email-box ol {{ margin: 10px 0 18px 20px; padding: 0; }}
    .scope {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .scope span {{ background: #f4eee2; border-radius: 999px; padding: 7px 10px; color: #312923; font-size: .86rem; }}
    footer {{ color: #85786c; font-size: .82rem; margin-top: 22px; }}
    @media (max-width: 860px) {{
      .summary-grid, .proposal-card {{ grid-template-columns: 1fr; }}
      .source-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .concepts {{ grid-template-columns: 1fr; }}
      .card-media {{ grid-template-columns: 1fr; }}
      .ref-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
<main>
  <header>
    <div class="eyebrow">Mini Proposal Draft · {e(generated_at)}</div>
    <h1>{e(brand)} 이미지 기반 촬영 제안</h1>
  </header>

  <section class="summary-grid">
    <div>
      <div class="eyebrow">현재 이미지 관찰</div>
      <h2>{e(dominant)} 중심의 이미지 언어가 보입니다.</h2>
      <p>자사몰/Instagram 후보에서 반복되는 태그는 {e(top_tags)}입니다. 보완 여지는 {e(missing)} 방향으로 정리했습니다.</p>
      <div class="metric-list">
        <div><span>상품 후보</span><strong>{e(asset['source_counts']['product'])}</strong></div>
        <div><span>캠페인 후보</span><strong>{e(asset['source_counts']['campaign'])}</strong></div>
        <div><span>사용 포트폴리오</span><strong>{e(asset['source_counts']['selected_portfolio'])}</strong></div>
      </div>
    </div>
    <div class="source-grid">{source_html}</div>
  </section>

  <section>
    <div class="eyebrow">Section 1</div>
    <h2>현재 브랜드 무드와 이어지는 포트폴리오</h2>
    <div class="proposal-list">{similar_cards}</div>
  </section>

  <section>
    <div class="eyebrow">Section 2</div>
    <h2>브랜드에 새롭게 제안할 수 있는 촬영 방향</h2>
    <div class="proposal-list">{whitespace_cards}</div>
  </section>

  <section>
    <div class="eyebrow">Section 3</div>
    <h2>제안 컨셉</h2>
    <ul class="concepts">{concept_html}</ul>
  </section>

  <section>
    <div class="eyebrow">Section 4</div>
    <h2>작업 범위와 메일 초안</h2>
    <div class="scope">
      <span>Visual Direction</span><span>Styling Guide</span><span>Key Visual</span><span>Detail Page Top</span><span>SNS Hook</span><span>Short-form Cover</span>
    </div>
    <div class="email-box" style="margin-top: 18px;">
      <strong>제목 후보</strong>
      <ol>{subjects}</ol>
      <p>{email_body}</p>
    </div>
  </section>
  <footer>발송 전 브랜드명, 담당자명, 이미지 권리, 실제 제안 범위를 사람이 최종 검수해야 합니다.</footer>
</main>
</body>
</html>
"""


def json_for_script(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def proposal_html(asset: dict[str, Any]) -> str:
    brand = e(asset["brand_name"])
    generated_at = e(asset["generated_at"])
    data_json = json_for_script(asset)
    template = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__BRAND__ Proposal Builder</title>
  <link rel="icon" href="data:,">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif; background: #fbfaf7; color: #17120f; line-height: 1.55; }
    main { width: min(1240px, calc(100% - 40px)); margin: 0 auto; padding: 42px 0 72px; }
    header { display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: end; padding: 34px 0 20px; border-bottom: 1px solid rgba(30,24,20,.12); }
    h1 { margin: 0; font-family: Georgia, "Times New Roman", serif; font-weight: 400; font-size: clamp(2.35rem, 5vw, 4.6rem); line-height: 1.04; overflow-wrap: anywhere; }
    h2 { margin: 0; font-size: 1.45rem; line-height: 1.25; }
    h3 { margin: 0 0 8px; font-size: 1rem; line-height: 1.3; }
    p { margin: 0; color: #665d54; }
    button, .download-link { border: 0; border-radius: 8px; padding: 11px 14px; background: #17120f; color: #fffaf0; font-weight: 800; cursor: pointer; font: inherit; text-decoration: none; display: inline-flex; align-items: center; }
    button.secondary, .download-link.secondary { background: #f0e8da; color: #302821; }
    section { margin-top: 30px; }
    .eyebrow { color: #b23c16; font-size: .74rem; font-weight: 800; text-transform: uppercase; letter-spacing: .02em; }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .panel { background: #fff; border: 1px solid rgba(30,24,20,.12); border-radius: 12px; padding: 22px; }
    .email-grid { display: grid; grid-template-columns: .72fr 1.28fr; gap: 18px; }
    .subject-list { margin: 12px 0 0 18px; padding: 0; color: #302821; }
    .email-body { white-space: pre-line; color: #302821; background: #fbfaf7; border-radius: 10px; padding: 16px; }
    .section-head { display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 12px; }
    .counter { color: #b23c16; font-weight: 800; }
    .candidate-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
    .candidate-card { display: grid; grid-template-rows: auto 1fr; border: 1px solid rgba(30,24,20,.12); border-radius: 10px; overflow: hidden; background: #fff; cursor: pointer; min-width: 0; }
    .candidate-card input { position: absolute; opacity: 0; pointer-events: none; }
    .candidate-card img { width: 100%; aspect-ratio: 4 / 5; object-fit: cover; background: #fff3cf; display: block; }
    .candidate-card .copy { padding: 12px; display: grid; gap: 8px; }
    .candidate-card p { font-size: .83rem; }
    .candidate-card.selected { border-color: rgba(255,90,31,.85); box-shadow: 0 0 0 2px rgba(255,90,31,.18); }
    .meta-line { color: #8a7d70; font-size: .76rem; overflow-wrap: anywhere; }
    .chips { display: flex; flex-wrap: wrap; gap: 5px; }
    .chips span { border-radius: 999px; background: #f4eee2; color: #5d5249; padding: 3px 7px; font-size: .7rem; }
    .proposal-output { display: none; }
    .proposal-output.visible { display: block; }
    .proposal-page { margin-top: 24px; background: #fff; border: 1px solid rgba(30,24,20,.14); border-radius: 12px; padding: 26px; break-after: page; }
    .proposal-head { display: grid; grid-template-columns: 1fr auto; gap: 16px; border-bottom: 1px solid rgba(30,24,20,.1); padding-bottom: 14px; margin-bottom: 18px; }
    .proposal-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
    .portfolio-sheet { border: 1px solid rgba(30,24,20,.1); border-radius: 10px; overflow: hidden; background: #fbfaf7; min-width: 0; }
    .portfolio-sheet img { width: 100%; aspect-ratio: 4 / 5; object-fit: cover; display: block; background: #fff3cf; }
    .portfolio-sheet .copy { padding: 14px; display: grid; gap: 10px; }
    .field strong { display: block; font-size: .72rem; color: #b23c16; text-transform: uppercase; margin-bottom: 2px; }
    .field span { display: block; color: #302821; font-size: .88rem; }
    .empty { border: 1px dashed rgba(30,24,20,.2); border-radius: 10px; padding: 18px; color: #665d54; background: #fff; }
    footer { color: #85786c; font-size: .82rem; margin-top: 22px; }
    @media print {
      @page { size: A4; margin: 12mm; }
      body { background: #fff; }
      header, .editor, .email-panel, footer { display: none !important; }
      main { width: 100%; padding: 0; }
      .proposal-output { display: block !important; }
      .proposal-page { border: 0; border-radius: 0; margin: 0; min-height: auto; break-after: page; page-break-after: always; }
      .proposal-grid { display: flex !important; flex-wrap: nowrap; gap: 8mm; align-items: flex-start; }
      .portfolio-sheet { flex: 1 1 0; width: calc((100% - 16mm) / 3); break-inside: avoid; page-break-inside: avoid; }
      .portfolio-sheet img { height: 82mm; aspect-ratio: auto; }
      .portfolio-sheet .copy { padding: 4mm; gap: 2mm; }
      .field span { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; font-size: 9.5pt; line-height: 1.35; }
    }
    @media screen and (max-width: 980px) {
      header, .email-grid { grid-template-columns: 1fr; }
      .toolbar { justify-content: flex-start; }
      .candidate-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .proposal-grid { grid-template-columns: 1fr; }
    }
    @media screen and (max-width: 620px) {
      main { width: min(100% - 28px, 1240px); }
      .candidate-grid { grid-template-columns: 1fr; }
      .proposal-head { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
<main>
  <header>
    <div>
      <div class="eyebrow">Proposal Builder · __GENERATED_AT__</div>
      <h1>__BRAND__ 포트폴리오 제안서</h1>
    </div>
    <div class="toolbar">
      <button id="generateProposal">제안서 생성</button>
      <button class="secondary" id="downloadSections">SECTION HTML 다운로드</button>
      <a class="download-link secondary" href="proposal_sections_landscape.pdf" download>가로형 PDF 다운로드</a>
    </div>
  </header>

  <section class="panel email-panel">
    <div class="email-grid">
      <div>
        <div class="eyebrow">Cold Email</div>
        <h2>콜드메일 초안</h2>
        <ol class="subject-list" id="subjectList"></ol>
      </div>
      <div class="email-body" id="emailBody"></div>
    </div>
  </section>

  <div class="editor">
    <section>
      <div class="section-head">
        <div>
          <div class="eyebrow">Section 1</div>
          <h2>우리 포트폴리오와 유사한 이미지 10개</h2>
        </div>
        <div class="counter"><span id="similarCount">0</span> 선택</div>
      </div>
      <div class="candidate-grid" id="similarCandidates"></div>
    </section>

    <section>
      <div class="section-head">
        <div>
          <div class="eyebrow">Section 2</div>
          <h2>브랜드에는 부족하지만 우리에게 있는 이미지 10개</h2>
        </div>
        <div class="counter"><span id="whitespaceCount">0</span> 선택</div>
      </div>
      <div class="candidate-grid" id="whitespaceCandidates"></div>
    </section>
  </div>

  <section class="proposal-output" id="proposalOutput"></section>
  <footer>최종 발송 전 포트폴리오 이미지 사용 권리, 브랜드명 표기, 제안 문구를 사람이 검수해야 합니다.</footer>
</main>
<script id="outreachData" type="application/json">__ASSET_JSON__</script>
<script>
const data = JSON.parse(document.getElementById('outreachData').textContent);
const state = {
  similar: new Set(data.selected_defaults.similar),
  whitespace: new Set(data.selected_defaults.whitespace)
};

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[char]));
}

function byType(type) {
  return type === 'similar' ? data.candidate_pools.similar : data.candidate_pools.whitespace;
}

function chips(items) {
  return (items || []).slice(0, 4).map((item) => `<span>${escapeHtml(item)}</span>`).join('');
}

function candidateCard(item, type) {
  const checked = state[type].has(item.portfolio_id);
  return `
    <label class="candidate-card ${checked ? 'selected' : ''}">
      <input type="checkbox" data-type="${type}" data-id="${escapeHtml(item.portfolio_id)}" ${checked ? 'checked' : ''}>
      <img src="${escapeHtml(item.image_src)}" alt="${escapeHtml(item.portfolio_id)}">
      <div class="copy">
        <div class="eyebrow">${escapeHtml(item.portfolio_id)} · ${escapeHtml(item.cut_type_label)}</div>
        <h3>${escapeHtml(item.client_or_project)}</h3>
        <p>${escapeHtml(item.portfolio_mood)}</p>
        <div class="meta-line">${escapeHtml(item.work_scope_label)}</div>
        <div class="chips">${chips(item.work_scope)}</div>
      </div>
    </label>
  `;
}

function renderCandidates(type) {
  const target = document.getElementById(type === 'similar' ? 'similarCandidates' : 'whitespaceCandidates');
  target.innerHTML = byType(type).map((item) => candidateCard(item, type)).join('');
  updateCounts();
}

function selectedRecords(type) {
  return byType(type).filter((item) => state[type].has(item.portfolio_id));
}

function updateCounts() {
  document.getElementById('similarCount').textContent = state.similar.size;
  document.getElementById('whitespaceCount').textContent = state.whitespace.size;
}

function chunk(records, size) {
  const pages = [];
  for (let index = 0; index < records.length; index += size) pages.push(records.slice(index, index + size));
  return pages;
}

function absoluteUrl(src) {
  try {
    return new URL(src || '', document.baseURI).href;
  } catch (error) {
    return src || '';
  }
}

function portfolioSheet(item, absoluteImages = false) {
  const imageSrc = absoluteImages ? absoluteUrl(item.image_src) : item.image_src;
  return `
    <article class="portfolio-sheet">
      <img src="${escapeHtml(imageSrc)}" alt="${escapeHtml(item.portfolio_id)}">
      <div class="copy">
        <div class="eyebrow">${escapeHtml(item.portfolio_id)} · ${escapeHtml(item.cut_type_label)}</div>
        <h3>${escapeHtml(item.client_or_project)}</h3>
        <div class="field"><strong>작업 범위</strong><span>${escapeHtml(item.work_scope_label)}</span></div>
        <div class="field"><strong>촬영 느낌</strong><span>${escapeHtml(item.portfolio_mood)}</span></div>
        <div class="field"><strong>제안 포인트</strong><span>${escapeHtml(item.portfolio_scenario || item.proposal_use)}</span></div>
      </div>
    </article>
  `;
}

function proposalPages(type, records, options = {}) {
  if (!records.length) return '';
  const absoluteImages = options.absoluteImages === true;
  const title = type === 'similar' ? '브랜드 무드와 결이 맞는 포트폴리오' : '다른 방향으로 확장 가능한 포트폴리오';
  const label = type === 'similar' ? 'SECTION 1' : 'SECTION 2';
  return chunk(records, 3).map((page, index, pages) => `
    <section class="proposal-page">
      <div class="proposal-head">
        <div>
          <div class="eyebrow">${label}</div>
          <h2>${escapeHtml(title)}</h2>
        </div>
        <div class="meta-line">${index + 1} / ${pages.length}</div>
      </div>
      <div class="proposal-grid">${page.map((item) => portfolioSheet(item, absoluteImages)).join('')}</div>
    </section>
  `).join('');
}

function selectedProposalPages(options = {}) {
  const similar = selectedRecords('similar');
  const whitespace = selectedRecords('whitespace');
  return {
    similar,
    whitespace,
    html: proposalPages('similar', similar, options) + proposalPages('whitespace', whitespace, options)
  };
}

function generateProposal(scrollToOutput = true) {
  const pages = selectedProposalPages();
  const output = document.getElementById('proposalOutput');
  if (!pages.similar.length && !pages.whitespace.length) {
    output.classList.add('visible');
    output.innerHTML = '<div class="empty">선택된 포트폴리오가 없습니다.</div>';
    return;
  }
  output.classList.add('visible');
  output.innerHTML = pages.html;
  if (scrollToOutput) output.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function sectionFilename(extension) {
  const slug = String(data.brand_slug || data.brand_name || 'proposal')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9가-힣_-]+/g, '_')
    .replace(/^_+|_+$/g, '') || 'proposal';
  return `${slug}_proposal_sections.${extension}`;
}

function sectionDocumentHtml() {
  const pages = selectedProposalPages({ absoluteImages: true });
  const bodyHtml = pages.html || '<div class="empty">선택된 포트폴리오가 없습니다.</div>';
  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(data.brand_name)} Proposal Sections</title>
  <link rel="icon" href="data:,">
  <style>
    @page { size: A4; margin: 12mm; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif; background: #f7f3ec; color: #17120f; line-height: 1.45; }
    main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0; }
    .proposal-page { background: #fff; border: 1px solid rgba(30,24,20,.14); border-radius: 10px; padding: 22px; margin: 0 0 24px; break-after: page; page-break-after: always; }
    .proposal-page:last-child { break-after: auto; page-break-after: auto; }
    .proposal-head { display: grid; grid-template-columns: 1fr auto; gap: 16px; border-bottom: 1px solid rgba(30,24,20,.1); padding-bottom: 12px; margin-bottom: 16px; }
    .eyebrow { color: #b23c16; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .02em; }
    h2 { margin: 0; font-size: 23px; line-height: 1.25; }
    h3 { margin: 0; font-size: 15px; line-height: 1.25; }
    .meta-line { color: #8a7d70; font-size: 11px; }
    .proposal-grid { display: flex; flex-wrap: nowrap; gap: 12px; align-items: flex-start; }
    .portfolio-sheet { flex: 1 1 0; width: calc((100% - 24px) / 3); border: 1px solid rgba(30,24,20,.1); border-radius: 8px; overflow: hidden; background: #fbfaf7; min-width: 0; break-inside: avoid; page-break-inside: avoid; }
    .portfolio-sheet img { width: 100%; aspect-ratio: 4 / 5; object-fit: cover; display: block; background: #fff3cf; }
    .portfolio-sheet .copy { padding: 11px; display: grid; gap: 7px; }
    .field strong { display: block; font-size: 10px; color: #b23c16; text-transform: uppercase; margin-bottom: 2px; }
    .field span { display: block; color: #302821; font-size: 12px; }
    .empty { border: 1px dashed rgba(30,24,20,.22); border-radius: 10px; padding: 18px; color: #665d54; background: #fff; }
    @media print {
      body { background: #fff; }
      main { width: 100%; padding: 0; }
      .proposal-page { border: 0; border-radius: 0; margin: 0; padding: 0; }
      .proposal-grid { display: flex; flex-wrap: nowrap; gap: 8mm; align-items: flex-start; }
      .portfolio-sheet { flex: 1 1 0; width: calc((100% - 16mm) / 3); }
      .portfolio-sheet img { height: 82mm; aspect-ratio: auto; }
      .portfolio-sheet .copy { padding: 4mm; gap: 2mm; }
      .field span { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden; font-size: 9.5pt; line-height: 1.35; }
    }
    @media screen and (max-width: 720px) {
      .proposal-grid { display: grid; grid-template-columns: 1fr; }
      .portfolio-sheet { width: 100%; }
      .proposal-head { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>${bodyHtml}</main>
</body>
</html>`;
}

function downloadSectionsHtml() {
  generateProposal(false);
  const blob = new Blob([sectionDocumentHtml()], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = sectionFilename('html');
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

document.addEventListener('change', (event) => {
  const input = event.target.closest('input[type="checkbox"][data-type]');
  if (!input) return;
  const bucket = state[input.dataset.type];
  if (input.checked) bucket.add(input.dataset.id);
  else bucket.delete(input.dataset.id);
  input.closest('.candidate-card').classList.toggle('selected', input.checked);
  updateCounts();
});

document.getElementById('generateProposal').addEventListener('click', generateProposal);
document.getElementById('downloadSections').addEventListener('click', downloadSectionsHtml);

document.getElementById('subjectList').innerHTML = data.cold_email.subject_candidates.map((subject) => `<li>${escapeHtml(subject)}</li>`).join('');
document.getElementById('emailBody').textContent = data.cold_email.body;
renderCandidates('similar');
renderCandidates('whitespace');
generateProposal();
</script>
</body>
</html>
"""
    return (
        template.replace("__BRAND__", brand)
        .replace("__GENERATED_AT__", generated_at)
        .replace("__ASSET_JSON__", data_json)
    )


def build_assets(args: argparse.Namespace) -> dict[str, Any]:
    run_dir = args.run_dir.resolve()
    summary = load_json(run_dir / "brand_source_summary.json")
    matches = load_json(run_dir / "portfolio_recommendations.json")
    portfolio_records = portfolio_lookup(args.portfolio_index)

    all_similar = matches.get("similar_recommendations", [])
    all_whitespace = matches.get("whitespace_recommendations", [])
    similar = select_recommendations(
        all_similar,
        args.similar_ids,
        args.similar_count,
        "유사",
    )
    whitespace = select_recommendations(
        all_whitespace,
        args.whitespace_ids,
        args.whitespace_count,
        "보완",
    )
    brand_name = args.brand_name or clean_brand_name(summary.get("brand_slug", "brand"))
    strategy = summarize_strategy(summary, similar, whitespace)
    subjects = make_subjects(brand_name, strategy)
    body = make_email_body(brand_name, args.contact_name, args.studio_name, strategy, similar, whitespace)
    similar_payload = recommendation_payload(similar, portfolio_records, "similar")
    whitespace_payload = recommendation_payload(whitespace, portfolio_records, "whitespace")
    asset = {
        "brand_name": brand_name,
        "brand_slug": summary.get("brand_slug"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source_run_dir": str(run_dir),
        "strategy": strategy,
        "source_counts": {
            "candidate": summary.get("candidate_image_count", 0),
            "product": summary.get("selected_product_count", 0),
            "campaign": summary.get("selected_campaign_count", 0),
            "selected_portfolio": len(similar) + len(whitespace),
        },
        "candidate_pools": {
            "similar": recommendation_payload(all_similar, portfolio_records, "similar"),
            "whitespace": recommendation_payload(all_whitespace, portfolio_records, "whitespace"),
        },
        "selected_defaults": {
            "similar": [record.get("portfolio_id") for record in similar],
            "whitespace": [record.get("portfolio_id") for record in whitespace],
        },
        "selected": {
            "similar_recommendations": similar_payload,
            "whitespace_recommendations": whitespace_payload,
        },
        "concept_options": make_concepts(strategy, similar, whitespace),
        "cold_email": {
            "contact_name": args.contact_name,
            "studio_name": args.studio_name,
            "subject_candidates": subjects,
            "body": body,
        },
        "review_required": [
            "브랜드명과 담당자명 확인",
            "사용 이미지 권리와 외부 공개 가능 여부 확인",
            "제안 범위와 비용/일정은 별도 협의 필요",
        ],
    }

    output_dir = (args.output_dir or (run_dir / "outreach_assets")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "outreach_assets.json", asset)
    (output_dir / "cold_email_draft.md").write_text(
        markdown_email(subjects, body, asset["selected"]),
        encoding="utf-8",
    )
    (output_dir / "mini_proposal.html").write_text(proposal_html(asset), encoding="utf-8")
    return {
        "brand_name": brand_name,
        "output_dir": str(output_dir),
        "asset_json": str(output_dir / "outreach_assets.json"),
        "cold_email": str(output_dir / "cold_email_draft.md"),
        "mini_proposal": str(output_dir / "mini_proposal.html"),
        "similar_count": len(similar),
        "whitespace_count": len(whitespace),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create cold email and mini proposal drafts from brand matching outputs.")
    parser.add_argument("--run-dir", type=Path, required=True, help="brand image matching run directory")
    parser.add_argument("--brand-name", help="display brand name for the email/proposal")
    parser.add_argument("--contact-name", default="브랜드 담당자님")
    parser.add_argument("--studio-name", default="23.5스튜디오")
    parser.add_argument("--portfolio-index", type=Path, default=DEFAULT_PORTFOLIO_INDEX)
    parser.add_argument("--similar-count", type=int, default=3)
    parser.add_argument("--whitespace-count", type=int, default=3)
    parser.add_argument("--similar-ids", nargs="*", help="portfolio IDs to use for similar section")
    parser.add_argument("--whitespace-ids", nargs="*", help="portfolio IDs to use for whitespace section")
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    result = build_assets(parse_args())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
