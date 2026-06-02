#!/usr/bin/env python3
"""Build portfolio metadata and an offline HTML viewer."""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_DIR = ROOT / "portfolio"
SEED_PATH = ROOT / "data" / "portfolio_seed.json"
OUTPUT_DIR = ROOT / "data"
VIEWER_PATH = OUTPUT_DIR / "portfolio_metadata_viewer.html"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}


CUT_TYPE_MAP = {
    "캠페인 키비주얼": "campaign_key_visual",
    "인물 클로즈업/후킹 컷": "closeup_mood_cut",
    "스포츠 왜곡 렌즈 착용컷": "sports_active_cut",
    "액세서리 제품 오브젝트 컷": "product_object_cut",
    "블랙 제품 정물 컷": "product_object_cut",
    "스튜디오 모델 착용/스타일링 컷": "model_styling_cut",
    "패턴/얼굴 클로즈업 컷": "detail_or_pattern_cut",
    "남성 캐주얼 착용컷": "model_styling_cut",
    "겨울 아웃도어 라이프스타일 컷": "seasonal_lifestyle_cut",
    "커플/그룹 캐주얼 착용컷": "model_styling_cut",
    "다크 무드 캠페인 클로즈업": "closeup_mood_cut",
    "밝은 여름/스윔 라이프스타일 클로즈업": "seasonal_lifestyle_cut",
}


CUT_TYPE_LABELS = {
    "campaign_key_visual": "캠페인 키비주얼",
    "model_styling_cut": "모델 착용/스타일링",
    "product_object_cut": "제품 오브젝트",
    "detail_or_pattern_cut": "디테일/패턴",
    "sports_active_cut": "스포츠/액티브",
    "seasonal_lifestyle_cut": "시즌/라이프스타일",
    "closeup_mood_cut": "무드 클로즈업",
    "unknown": "미분류",
}


STRATEGY_BY_CUT_TYPE = {
    "campaign_key_visual": {
        "similar": [
            "브랜드가 이미 강한 캠페인 무드나 시즌 키비주얼을 운영하고 있을 때",
            "SNS 첫 화면에서 브랜드 캐릭터를 더 선명하게 밀고 싶을 때",
        ],
        "contrast": [
            "상품컷 중심이라 브랜드를 기억하게 만드는 대표 이미지가 부족할 때",
            "신상품 또는 시즌 메시지를 하나의 비주얼로 묶어야 할 때",
        ],
        "avoid": ["극도로 미니멀한 상품 단독컷만 필요한 제안에는 우선순위를 낮춘다."],
    },
    "model_styling_cut": {
        "similar": [
            "브랜드가 룩북/착용컷을 이미 보유하고 있고 상품 전달력을 확장하고 싶을 때",
            "상세페이지와 SNS 양쪽에 쓸 수 있는 모델 중심 컷이 필요할 때",
        ],
        "contrast": [
            "상품 단독 이미지가 많지만 실제 착용감이나 실루엣 전달이 약할 때",
            "브랜드 톤은 유지하면서 인물 스타일링으로 구매 맥락을 보강하고 싶을 때",
        ],
        "avoid": ["모델 노출 없이 제품 정물만 필요한 프로젝트에서는 단독 대표 이미지로 쓰지 않는다."],
    },
    "product_object_cut": {
        "similar": [
            "브랜드가 프리미엄 제품컷이나 오브젝트 중심 이미지를 이미 운영하고 있을 때",
            "액세서리/가방/소품류를 감도 있게 보여주는 레퍼런스가 필요할 때",
        ],
        "contrast": [
            "모델컷은 충분하지만 상품 자체의 디테일과 소유욕을 만드는 이미지가 약할 때",
            "상세페이지 상단 또는 SNS 제품 포스트를 캠페인 이미지처럼 끌어올리고 싶을 때",
        ],
        "avoid": ["착용핏 설명이 핵심인 의류 제안에서는 보조 컷으로 배치한다."],
    },
    "detail_or_pattern_cut": {
        "similar": [
            "브랜드가 소재, 패턴, 그래픽 자산을 이미 강점으로 갖고 있을 때",
            "얼굴/소품/텍스처로 썸네일 후킹을 만들고 싶을 때",
        ],
        "contrast": [
            "전신 착용컷 위주라 소재감, 표정, 패턴의 근접 설득이 부족할 때",
            "브랜드 무드를 가까운 거리의 이미지 언어로 압축해야 할 때",
        ],
        "avoid": ["상품 전체 형태와 핏이 반드시 보여야 하는 상세 컷에는 단독 사용하지 않는다."],
    },
    "sports_active_cut": {
        "similar": [
            "브랜드가 움직임, 활동성, 스포츠웨어 맥락을 이미 갖고 있을 때",
            "릴스/숏폼으로 확장 가능한 역동적 이미지를 제안할 때",
        ],
        "contrast": [
            "정적인 룩북 위주라 착용자의 움직임이나 활동성이 부족할 때",
            "운동화, 스윔, 아웃도어처럼 기능과 몸의 움직임이 구매 설득에 중요할 때",
        ],
        "avoid": ["차분한 프리미엄 정물 톤이 핵심인 제안에서는 보조 확장안으로 둔다."],
    },
    "seasonal_lifestyle_cut": {
        "similar": [
            "브랜드가 시즌 캠페인이나 라이프스타일 배경을 이미 활용하고 있을 때",
            "계절감이 있는 컬렉션을 더 생생하게 보여주고 싶을 때",
        ],
        "contrast": [
            "스튜디오 컷은 충분하지만 계절, 장소, 생활 맥락이 부족할 때",
            "브랜드를 착용 상황이나 시즌 장면과 연결해야 할 때",
        ],
        "avoid": ["시즌성이 없는 상시 제품 카탈로그에는 사용 시기를 명확히 잡는다."],
    },
    "closeup_mood_cut": {
        "similar": [
            "브랜드가 인물의 표정, 조명, 무드로 이미 첫인상을 만들고 있을 때",
            "프리미엄/에디토리얼 무드를 강화하는 키비주얼이 필요할 때",
        ],
        "contrast": [
            "상품 정보는 충분하지만 SNS에서 멈춰 보게 하는 후킹 컷이 부족할 때",
            "브랜드 감정선과 캠페인 톤을 한 장으로 압축해야 할 때",
        ],
        "avoid": ["상품 디테일 설명만 필요한 상세페이지 컷에는 보조 이미지로 배치한다."],
    },
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def extract_work_scope(description: str) -> list[str]:
    scopes: list[str] = []
    for raw_line in description.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("for @"):
            break
        if line.startswith("@"):
            continue
        scopes.append(line)
    return scopes


def extract_client_handles(description: str) -> list[str]:
    return re.findall(r"@([A-Za-z0-9_.]+)", description)


def readable_client(handles: list[str], fallback: str) -> str:
    if not handles:
        return fallback
    return " / ".join("@" + handle for handle in handles)


def normalize_brand_tags(handles: list[str], source_meta: dict[str, Any]) -> list[str]:
    tags = [handle.strip().lower() for handle in handles if handle.strip()]
    if tags:
        return sorted(dict.fromkeys(tags))
    username = str(source_meta.get("username", "")).strip().lower()
    return [username] if username else ["unknown"]


def as_project_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def relative_html_path(viewer_path: Path, asset_path: Path) -> str:
    return Path("../" + as_project_path(asset_path)).as_posix() if not asset_path.is_relative_to(viewer_path.parent) else asset_path.relative_to(viewer_path.parent).as_posix()


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "portfolio"


def collect_files(source_dir: Path) -> tuple[list[Path], list[Path], int]:
    image_paths = sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    video_paths = sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )
    json_count = len(list(source_dir.glob("*.json")))
    return image_paths, video_paths, json_count


def make_thumbnail(image_path: Path, thumbnail_dir: Path) -> Path:
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = thumbnail_dir / f"{image_path.stem}.jpg"
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        rgb.thumbnail((520, 650), Image.Resampling.LANCZOS)
        rgb.save(thumbnail_path, "JPEG", quality=82, optimize=True)
    return thumbnail_path


def infer_seed_from_source(source_meta: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    description = source_meta.get("description", "")
    text = " ".join(
        [
            description,
            source_meta.get("filename", ""),
            source_meta.get("post_shortcode", ""),
            source_meta.get("shortcode", ""),
        ]
    ).lower()
    visual_tags: list[str] = []
    commerce_tags: list[str] = []

    if stats["brightness_level"] == "dark":
        visual_tags.append("dark_mood")
    elif stats["brightness_level"] == "bright":
        visual_tags.append("bright_natural")
    if stats["contrast_level"] == "high":
        visual_tags.append("high_contrast")
    if stats["orientation"] == "portrait":
        visual_tags.append("portrait_frame")
    elif stats["orientation"] == "landscape":
        visual_tags.append("wide_hero")

    if any(keyword in text for keyword in ["reebok", "critic", "barrel", "swim", "ski", "sport", "oamaru"]):
        group = "스포츠/액티브 스타일링"
        cut_type = "스포츠 왜곡 렌즈 착용컷"
        visual_tags.extend(["sports_active", "dynamic_pose"])
        commerce_tags.extend(["fit_visible", "shortform_ready"])
        proposal_use = "움직임, 계절감, 착용 상황을 보여주는 액티브 캠페인 레퍼런스로 제안"
    elif any(keyword in text for keyword in ["bag", "chloe", "margiela", "alexander", "very", "accessory", "object"]):
        group = "프리미엄 제품 오브젝트"
        cut_type = "액세서리 제품 오브젝트 컷"
        visual_tags.extend(["object_still_life", "product_focus", "prop_styling"])
        commerce_tags.extend(["premium_product", "detail_page_top"])
        proposal_use = "상품 단독컷을 감도 있는 오브젝트 이미지로 끌어올리는 제안"
    elif any(keyword in text for keyword in ["benetton", "color", "graphic"]):
        group = "팝 컬러 캠페인/인물"
        cut_type = "캠페인 키비주얼"
        visual_tags.extend(["bold_color", "campaign_mood"])
        commerce_tags.extend(["sns_hook", "season_campaign"])
        proposal_use = "브랜드 첫인상을 선명하게 만드는 컬러 캠페인 키비주얼로 제안"
    elif any(keyword in text for keyword in ["editorial", "beauty", "close", "mminm", "face"]):
        group = "무드/뷰티 클로즈업"
        cut_type = "다크 무드 캠페인 클로즈업" if stats["brightness_level"] == "dark" else "인물 클로즈업/후킹 컷"
        visual_tags.extend(["close_up", "mood_cut"])
        commerce_tags.extend(["sns_hook", "brand_asset"])
        proposal_use = "브랜드 무드와 감정선을 압축하는 SNS 후킹 컷으로 제안"
    else:
        group = "스튜디오 룩북/상품 전달"
        cut_type = "스튜디오 모델 착용/스타일링 컷"
        visual_tags.extend(["model_styling", "source_metadata_only"])
        commerce_tags.extend(["lookbook", "fit_visible"])
        proposal_use = "룩북과 상세페이지 양쪽에 활용 가능한 착용/스타일링 컷으로 제안"

    return {
        "group": group,
        "cut_type": cut_type,
        "visual_tags": sorted(dict.fromkeys(visual_tags)),
        "commerce_tags": sorted(dict.fromkeys(commerce_tags)),
        "proposal_use": proposal_use,
    }


def get_image_stats(image_path: Path) -> dict[str, Any]:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        small = rgb.resize((80, 80))
        if hasattr(small, "get_flattened_data"):
            pixels = list(small.get_flattened_data())
        else:
            pixels = list(small.getdata())
        luminance = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels]
        avg_luma = sum(luminance) / len(luminance)
        contrast = statistics.pstdev(luminance)
        quantized = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette() or []
        color_counts = sorted(quantized.getcolors() or [], reverse=True)
        dominant_colors: list[str] = []
        for _, palette_index in color_counts:
            offset = palette_index * 3
            if offset + 2 >= len(palette):
                continue
            r, g, b = palette[offset], palette[offset + 1], palette[offset + 2]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            if hex_color not in dominant_colors:
                dominant_colors.append(hex_color)
            if len(dominant_colors) == 5:
                break

    if avg_luma < 85:
        brightness_level = "dark"
    elif avg_luma > 175:
        brightness_level = "bright"
    else:
        brightness_level = "mid"

    if contrast < 38:
        contrast_level = "low"
    elif contrast > 72:
        contrast_level = "high"
    else:
        contrast_level = "medium"

    if width == height:
        orientation = "square"
    elif width > height:
        orientation = "landscape"
    else:
        orientation = "portrait"

    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(width / height, 4),
        "orientation": orientation,
        "dominant_colors": dominant_colors,
        "average_luminance": round(avg_luma, 2),
        "brightness_level": brightness_level,
        "contrast_value": round(contrast, 2),
        "contrast_level": contrast_level,
    }


def infer_presence(normalized_cut_type: str, visual_tags: list[str], commerce_tags: list[str]) -> tuple[str, str]:
    tags = set(visual_tags + commerce_tags)
    if "group_model" in tags:
        model_presence = "multiple"
    elif normalized_cut_type in {"model_styling_cut", "sports_active_cut", "seasonal_lifestyle_cut", "closeup_mood_cut"}:
        model_presence = "single"
    elif normalized_cut_type == "product_object_cut":
        model_presence = "none"
    else:
        model_presence = "unknown"

    if normalized_cut_type == "product_object_cut" or "product_focus" in tags:
        product_presence = "single"
    elif "fit_visible" in tags or normalized_cut_type in {"model_styling_cut", "sports_active_cut", "seasonal_lifestyle_cut"}:
        product_presence = "multiple"
    elif normalized_cut_type == "closeup_mood_cut":
        product_presence = "unclear"
    else:
        product_presence = "unknown"

    return model_presence, product_presence


def build_record(
    index: int,
    image_count: int,
    image_path: Path,
    source_meta: dict[str, Any],
    seed_meta: dict[str, Any],
    seed_matched: bool,
    source_dir: Path,
    viewer_path: Path,
    thumbnail_dir: Path | None,
) -> dict[str, Any]:
    image_name = image_path.name
    description = source_meta.get("description", "")
    handles = extract_client_handles(description)
    brand_tags = normalize_brand_tags(handles, source_meta)
    stats = get_image_stats(image_path)
    if not seed_meta:
        seed_meta = infer_seed_from_source(source_meta, stats)
    raw_cut_type = seed_meta.get("cut_type", "미분류")
    normalized_cut_type = CUT_TYPE_MAP.get(raw_cut_type, "unknown")
    visual_tags = seed_meta.get("visual_tags", [])
    commerce_tags = seed_meta.get("commerce_tags", [])
    work_scope = extract_work_scope(description)
    model_presence, product_presence = infer_presence(normalized_cut_type, visual_tags, commerce_tags)
    strategy = STRATEGY_BY_CUT_TYPE.get(normalized_cut_type, STRATEGY_BY_CUT_TYPE["campaign_key_visual"])
    post_id = str(source_meta.get("post_id", "unknown"))
    project_group_id = f"ig_{post_id}"
    portfolio_id = f"P{index:0{max(2, len(str(image_count)))}d}"
    source_url = source_meta.get("post_url", "")
    proposal_use = seed_meta.get("proposal_use", "")
    group = seed_meta.get("group", "미분류")
    client_or_project = readable_client(handles, source_meta.get("fullname") or source_meta.get("username", "Unknown"))
    display_asset_path = make_thumbnail(image_path, thumbnail_dir) if thumbnail_dir else image_path
    metadata_sources = [
        f"{as_project_path(source_dir)}/*",
        f"{as_project_path(source_dir)}/*.json",
        "data/portfolio_seed.json",
        "Pillow image statistics",
    ]
    if not seed_matched:
        metadata_sources.append("metadata heuristic fallback")

    return {
        "portfolio_id": portfolio_id,
        "project_group_id": project_group_id,
        "file_name": image_name,
        "asset_path": as_project_path(image_path),
        "thumbnail_path": as_project_path(display_asset_path),
        "html_image_path": relative_html_path(viewer_path, display_asset_path),
        "source_type": "instagram",
        "source_url": source_url,
        "post_shortcode": source_meta.get("post_shortcode", ""),
        "image_shortcode": source_meta.get("shortcode", ""),
        "media_id": str(source_meta.get("media_id", "")),
        "post_date": source_meta.get("post_date", source_meta.get("date", "")),
        "instagram_carousel_index": source_meta.get("num"),
        "instagram_carousel_count": source_meta.get("count"),
        "client_or_project": client_or_project,
        "client_handles": handles,
        "brand_tags": brand_tags,
        "description": description,
        "rights_note": "제안서 사용 전 원 포트폴리오 이미지 사용 권한과 클라이언트 표기 검수 필요",
        "group": group,
        "cut_type": normalized_cut_type,
        "cut_type_label": CUT_TYPE_LABELS.get(normalized_cut_type, raw_cut_type),
        "raw_cut_type_label": raw_cut_type,
        "visual_tags": visual_tags,
        "commerce_tags": commerce_tags,
        "work_scope": work_scope,
        "model_presence": model_presence,
        "product_presence": product_presence,
        "proposal_use": proposal_use,
        "similar_when": strategy["similar"],
        "contrast_when": strategy["contrast"],
        "do_not_use_when": strategy["avoid"],
        "analysis_summary": f"{group} / {raw_cut_type}. {proposal_use}",
        "metadata_sources": metadata_sources,
        "review_status": "needs_review",
        "review_notes": "AI/휴리스틱 1차 메타. 영업 제안서 반영 전 권리, 브랜드명, 제안 문구 검수 필요.",
        "file_size_bytes": image_path.stat().st_size,
        **stats,
    }


def build_records(
    source_dir: Path,
    seed_path: Path,
    viewer_path: Path,
    thumbnail_dir: Path | None,
) -> tuple[list[dict[str, Any]], list[Path], int]:
    seed = load_json(seed_path)
    records: list[dict[str, Any]] = []
    image_paths, video_paths, json_count = collect_files(source_dir)
    image_count = len(image_paths)
    for index, image_path in enumerate(image_paths, start=1):
        source_meta = load_json(image_path.with_suffix(image_path.suffix + ".json"))
        seed_meta = seed.get(image_path.name, {})
        seed_matched = bool(seed_meta)
        records.append(
            build_record(
                index,
                image_count,
                image_path,
                source_meta,
                seed_meta,
                seed_matched,
                source_dir,
                viewer_path,
                thumbnail_dir,
            )
        )
    return records, video_paths, json_count


def summarize(
    records: list[dict[str, Any]],
    source_dir: Path,
    viewer_path: Path,
    video_paths: list[Path],
    json_count: int,
) -> dict[str, Any]:
    group_counts = Counter(record["group"] for record in records)
    cut_counts = Counter(record["cut_type_label"] for record in records)
    visual_tag_counts = Counter(tag for record in records for tag in record["visual_tags"])
    commerce_tag_counts = Counter(tag for record in records for tag in record["commerce_tags"])
    brand_counts = Counter(tag for record in records for tag in record.get("brand_tags", ["unknown"]))
    project_counts = Counter(record["project_group_id"] for record in records)
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "portfolio_count": len(records),
        "project_group_count": len(project_counts),
        "group_counts": dict(group_counts),
        "cut_type_counts": dict(cut_counts),
        "top_visual_tags": dict(visual_tag_counts.most_common(12)),
        "top_commerce_tags": dict(commerce_tag_counts.most_common(12)),
        "brand_counts": dict(brand_counts.most_common()),
        "source_directory": as_project_path(source_dir),
        "viewer_path": as_project_path(viewer_path),
        "image_count": len(records),
        "video_count": len(video_paths),
        "json_count": json_count,
        "skipped_video_files": [path.name for path in video_paths],
    }


def write_data(records: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path, slug: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{slug}_index.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with (output_dir / f"{slug}_index.jsonl").open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    (output_dir / f"{slug}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def html_template() -> str:
    return """<!DOCTYPE html>
<html lang="ko" class="theme-light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Portfolio Metadata Atlas</title>
  <link rel="icon" href="data:,">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Noto+Sans+KR:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <script>if (typeof Chart !== 'undefined') { Chart.defaults.animation = false; }</script>
  <script src="https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root { interpolate-size: allow-keywords; }
    html.theme-light {
      --bg: #fafaf9; --surface: #ffffff; --surface-hover: #f7f3ea;
      --border: rgba(29, 24, 20, 0.1); --text: #16120f; --text-secondary: #685f56;
      --accent: #ff5a1f; --accent-secondary: #245c73; --positive: #13795b;
      --negative: #b42318; --warning: #d38a00;
      --cream: #fff3cf; --cream-soft: #fffaf0; --ink: #16120f; --stripe-a: #b92b1f;
      --stripe-b: #f06423; --stripe-c: #f5b335; --stripe-d: #fff3cf;
    }
    html.theme-dark {
      --bg: #0a0a0a; --surface: #17130f; --surface-hover: #221b15;
      --border: rgba(255, 245, 226, 0.11); --text: #f4efe7; --text-secondary: #b9aa99;
      --accent: #ff7a32; --accent-secondary: #6db0c8; --positive: #39b98d;
      --negative: #ff6b5f; --warning: #f5b335;
      --cream: #352719; --cream-soft: #1f1a15; --ink: #f4efe7; --stripe-a: #7f1d1d;
      --stripe-b: #c2410c; --stripe-c: #d97706; --stripe-d: #6f4e1f;
    }
    body {
      min-height: 100vh; background: var(--bg); color: var(--text);
      font-family: "Inter", "Noto Sans KR", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 1rem; line-height: 1.6; letter-spacing: 0;
      -webkit-font-smoothing: antialiased; scrollbar-gutter: stable;
      transition: background 0.25s ease, color 0.25s ease;
    }
    h1, h2, h3, h4 { color: var(--text); letter-spacing: 0; text-wrap: balance; }
    h1 { font-family: Georgia, "Times New Roman", serif; font-size: clamp(2.5rem, 6vw, 5.25rem); font-weight: 400; line-height: 1.05; }
    h2 { font-size: clamp(2rem, 4vw, 3rem); font-weight: 600; line-height: 1.16; }
    h3 { font-size: 1.5rem; font-weight: 600; line-height: 1.25; }
    h4 { font-size: 1.05rem; font-weight: 600; }
    p, li, td, th, span, label, button, input, select { color: inherit; font-weight: 400; }
    a { color: var(--accent); }
    button, input, select { font: inherit; }
    button { cursor: pointer; }
    img { max-width: 100%; display: block; }
    .skip-to-content {
      position: fixed; left: 16px; top: -80px; z-index: 10000;
      background: var(--accent); color: #fff; padding: 10px 14px;
      border-radius: 8px; text-decoration: none; transition: top 0.2s ease;
    }
    .skip-to-content:focus { top: 16px; }
    .viz-menu { position: fixed; top: 16px; right: 16px; z-index: 9999; }
    .viz-menu-toggle {
      width: 44px; height: 44px; border-radius: 8px; background: color-mix(in srgb, var(--surface), transparent 10%);
      border: 1px solid var(--border); color: var(--text); display: flex; align-items: center; justify-content: center;
      backdrop-filter: blur(12px); transition: background 0.2s ease, box-shadow 0.2s ease;
    }
    .viz-menu-toggle:hover { background: var(--surface-hover); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    .viz-menu-dropdown {
      position: absolute; top: 52px; right: 0; min-width: 210px; background: var(--surface);
      border: 1px solid var(--border); border-radius: 12px; padding: 8px; opacity: 0; visibility: hidden;
      transform: translateY(-8px); transition: all 0.2s ease; box-shadow: 0 16px 48px rgba(0,0,0,0.12);
    }
    .viz-menu-dropdown.open { opacity: 1; visibility: visible; transform: translateY(0); }
    .viz-menu-dropdown button {
      width: 100%; padding: 10px 12px; border: none; background: transparent; border-radius: 8px;
      display: flex; gap: 10px; align-items: center; text-align: left; color: var(--text);
    }
    .viz-menu-dropdown button:hover { background: var(--surface-hover); }
    .page-shell { width: min(1280px, calc(100% - 48px)); margin: 0 auto; }
    section { margin-top: 64px; }
    .hero {
      position: relative; min-height: 520px; display: grid; grid-template-columns: minmax(0, 1.02fr) minmax(320px, 0.98fr);
      gap: 40px; align-items: stretch; padding: 96px 0 72px;
    }
    .hero::after, .sunset-stripe {
      content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 12px;
      background: linear-gradient(90deg, var(--stripe-a), var(--stripe-b), var(--stripe-c), var(--stripe-d));
      border-radius: 8px;
    }
    .eyebrow {
      color: var(--accent); text-transform: uppercase; letter-spacing: 1px; font-size: 0.74rem; font-weight: 700;
      margin-bottom: 18px;
    }
    .hero-copy { align-self: center; }
    .hero-copy p { color: var(--text-secondary); font-size: 1.08rem; max-width: 650px; margin-top: 22px; line-height: 1.75; }
    .hero-panel {
      background: var(--cream); border: 1px solid var(--border); border-radius: 12px; padding: 24px;
      display: flex; flex-direction: column; justify-content: space-between; min-height: 430px;
    }
    .hero-mosaic { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    .hero-mosaic img { width: 100%; aspect-ratio: 4 / 5; object-fit: cover; border-radius: 8px; border: 1px solid rgba(0,0,0,0.08); }
    .hero-meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 24px; }
    .metric, .control-panel, .data-table-wrap, .chart-panel, .detail-drawer {
      background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    }
    .metric { padding: 22px; }
    .metric strong { display: block; font-family: Georgia, "Times New Roman", serif; font-size: 2.3rem; font-weight: 400; line-height: 1; }
    .metric span { display: block; margin-top: 8px; color: var(--text-secondary); font-size: 0.92rem; }
    .section-head { display: flex; justify-content: space-between; gap: 24px; align-items: end; margin-bottom: 24px; }
    .section-head p { color: var(--text-secondary); max-width: 720px; margin-top: 10px; }
    .controls { display: grid; grid-template-columns: 1.7fr 1.1fr 1fr 1fr 0.9fr; gap: 12px; }
    .control-panel { padding: 18px; position: sticky; top: 12px; z-index: 8; }
    .field label { display: block; font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 6px; font-weight: 600; }
    input, select {
      width: 100%; height: 44px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg);
      color: var(--text); padding: 0 12px; outline: none;
    }
    input:focus, select:focus { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent), transparent 82%); }
    .status-line { margin-top: 14px; color: var(--text-secondary); font-size: 0.92rem; }
    .brand-panel { margin-top: 16px; border-top: 1px solid var(--border); padding-top: 16px; }
    .brand-panel-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; margin-bottom: 10px; }
    .brand-panel-head h3 { font-size: 1rem; }
    .brand-panel-head span { color: var(--text-secondary); font-size: 0.86rem; }
    .brand-chips { display: flex; flex-wrap: wrap; gap: 8px; max-height: 132px; overflow: auto; padding-right: 4px; }
    .brand-chip {
      min-height: 32px; border-radius: 999px; border: 1px solid var(--border); background: var(--bg);
      color: var(--text); padding: 5px 10px; display: inline-flex; align-items: center; gap: 8px; font-size: 0.84rem;
    }
    .brand-chip strong { font-weight: 700; color: var(--accent); font-size: 0.78rem; }
    .brand-chip.active { background: var(--ink); color: var(--bg); border-color: var(--ink); }
    .brand-chip.active strong { color: currentColor; }
    .view-tabs {
      display: flex; gap: 8px; align-items: center; margin-top: 28px; padding: 8px;
      border: 1px solid var(--border); border-radius: 12px; background: var(--surface);
      overflow-x: auto;
    }
    .view-tab {
      min-height: 40px; border: 1px solid transparent; border-radius: 8px; background: transparent;
      color: var(--text-secondary); padding: 8px 14px; font-size: 0.92rem; font-weight: 600; white-space: nowrap;
    }
    .view-tab.active {
      background: var(--ink); color: var(--bg); border-color: var(--ink);
    }
    .view-panel[hidden] { display: none; }
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
    .charts { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px; }
    .chart-panel { padding: 24px; min-height: 390px; }
    .chart-box { height: 320px; position: relative; margin-top: 20px; }
    .chart-box canvas { width: 100% !important; height: 100% !important; max-width: 100%; }
    .gallery { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
    .portfolio-card {
      background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
      transition: box-shadow 0.2s ease; display: flex; flex-direction: column; min-width: 0;
    }
    .portfolio-card:hover { box-shadow: 0 12px 28px rgba(0,0,0,0.08); }
    .portfolio-card button.image-button { border: none; background: transparent; padding: 0; text-align: left; width: 100%; }
    .image-frame { background: var(--cream-soft); aspect-ratio: 4 / 5; overflow: hidden; }
    .image-frame img { width: 100%; height: 100%; object-fit: cover; }
    .card-body { padding: 18px; display: flex; flex-direction: column; gap: 12px; flex: 1; }
    .card-top { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
    .card-title { min-width: 0; }
    .card-title h3 { font-size: 1.08rem; line-height: 1.35; }
    .card-title p { color: var(--text-secondary); font-size: 0.86rem; margin-top: 4px; overflow-wrap: anywhere; }
    .badge {
      display: inline-flex; align-items: center; min-height: 26px; border-radius: 999px; padding: 4px 10px;
      background: var(--cream); color: var(--text); border: 1px solid var(--border); font-size: 0.76rem; font-weight: 700; white-space: nowrap;
    }
    .tags { display: flex; flex-wrap: wrap; gap: 6px; }
    .tag { border: 1px solid var(--border); border-radius: 6px; padding: 3px 7px; font-size: 0.75rem; color: var(--text-secondary); background: var(--bg); }
    .proposal { color: var(--text-secondary); font-size: 0.91rem; line-height: 1.62; }
    .swatches { display: flex; gap: 6px; }
    .swatch { width: 22px; height: 22px; border-radius: 50%; border: 1px solid rgba(0,0,0,0.16); }
    .card-actions { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-top: auto; }
    .text-button {
      border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text);
      min-height: 36px; padding: 7px 10px; display: inline-flex; align-items: center; gap: 8px; font-size: 0.88rem;
    }
    .text-button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
    .table-scroll { overflow-x: auto; border-radius: 12px; }
    .metadata-table { width: 100%; border-collapse: collapse; table-layout: fixed; min-width: 1680px; }
    .col-id { width: 92px; }
    .col-project { width: 260px; }
    .col-brand { width: 230px; }
    .col-group { width: 190px; }
    .col-cut { width: 180px; }
    .col-visual { width: 270px; }
    .col-commerce { width: 240px; }
    .col-proposal { width: 360px; }
    th, td { padding: 14px 16px; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
    th { color: var(--text-secondary); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; background: var(--cream-soft); }
    td { font-size: 0.9rem; overflow-wrap: anywhere; }
    .table-project { font-weight: 600; line-height: 1.45; }
    .table-file { display: block; margin-top: 6px; color: var(--text-secondary); font-size: 0.78rem; line-height: 1.45; }
    .table-proposal { line-height: 1.65; color: var(--text-secondary); }
    .data-table-wrap { overflow: hidden; }
    .drawer-backdrop {
      position: fixed; inset: 0; background: rgba(0,0,0,0.38); z-index: 9990; opacity: 0; visibility: hidden; transition: all 0.2s ease;
    }
    .drawer-backdrop.open { opacity: 1; visibility: visible; }
    .detail-drawer {
      position: fixed; top: 0; right: 0; bottom: 0; width: min(560px, 100%); z-index: 9991; border-radius: 0;
      transform: translateX(104%); transition: transform 0.25s ease; overflow-y: auto; padding: 28px;
    }
    .detail-drawer.open { transform: translateX(0); }
    .drawer-head { display: flex; justify-content: space-between; gap: 16px; align-items: start; margin-bottom: 22px; }
    .icon-button {
      width: 38px; height: 38px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface);
      color: var(--text); display: inline-flex; align-items: center; justify-content: center; flex: 0 0 auto;
    }
    .drawer-image { border-radius: 12px; overflow: hidden; border: 1px solid var(--border); margin-bottom: 22px; }
    .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 18px 0; }
    .detail-box { padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); }
    .detail-box span { display: block; color: var(--text-secondary); font-size: 0.78rem; margin-bottom: 4px; }
    .json-block {
      white-space: pre-wrap; overflow-wrap: anywhere; background: #101010; color: #f4efe7; border-radius: 8px;
      padding: 16px; font: 0.8rem/1.55 "SF Mono", Menlo, Consolas, monospace; margin-top: 12px;
    }
    .json-details {
      margin-top: 22px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); overflow: hidden;
    }
    .json-details summary {
      min-height: 44px; display: flex; align-items: center; justify-content: space-between; gap: 12px;
      padding: 10px 14px; cursor: pointer; color: var(--text); font-weight: 700; list-style: none;
    }
    .json-details summary::-webkit-details-marker { display: none; }
    .json-details summary::after {
      content: "열기"; color: var(--text-secondary); font-size: 0.78rem; font-weight: 700;
    }
    .json-details[open] summary::after { content: "닫기"; }
    .json-details .json-block { border-radius: 0; margin-top: 0; max-height: 520px; overflow: auto; }
    .empty { border: 1px dashed var(--border); border-radius: 12px; padding: 42px; text-align: center; color: var(--text-secondary); }
    .load-more-wrap { display: flex; justify-content: center; margin-top: 22px; }
    .load-more-wrap[hidden] { display: none; }
    .sunset-stripe { position: relative; height: 18px; margin: 72px auto 36px; width: min(1280px, calc(100% - 48px)); }
    .footer-note { width: min(1280px, calc(100% - 48px)); margin: 0 auto 56px; color: var(--text-secondary); font-size: 0.9rem; }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .animate { animation: fadeInUp 0.6s ease-out both; }
    .animate.delay-1 { animation-delay: 0.1s; }
    .animate.delay-2 { animation-delay: 0.2s; }
    .animate.delay-3 { animation-delay: 0.3s; }
    .reveal { opacity: 1; transform: none; }
    .reveal.visible { opacity: 1; transform: none; }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation: none !important; transition: none !important; }
      .reveal { opacity: 1; transform: none; }
    }
    @media print {
      body { background: white !important; color: black !important; }
      .viz-menu, .control-panel, .drawer-backdrop, .detail-drawer { display: none !important; }
      .portfolio-card, .metric, .chart-panel, .data-table-wrap { break-inside: avoid; box-shadow: none; }
      * { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
    }
    @page { margin: 0.75in; }
    @media (max-width: 920px) {
      .hero, .charts { grid-template-columns: 1fr; }
      .controls, .stats-grid { grid-template-columns: 1fr 1fr; }
      .gallery { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .hero { padding-top: 72px; }
    }
    @media (max-width: 640px) {
      .page-shell, .sunset-stripe, .footer-note { width: min(100% - 28px, 1280px); }
      section { margin-top: 52px; }
      .controls, .stats-grid, .gallery, .hero-meta, .detail-grid { grid-template-columns: 1fr; }
      .section-head { display: block; }
      .hero-panel { min-height: auto; }
      .hero-mosaic { grid-template-columns: repeat(3, 1fr); }
      .chart-panel { padding: 18px; }
      .detail-drawer { padding: 20px; }
    }
    @media (max-width: 375px) {
      body { overflow-x: hidden; }
      .hero-mosaic { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <a href="#main-content" class="skip-to-content">본문으로 이동</a>
  <div class="viz-menu">
    <button class="viz-menu-toggle" onclick="toggleMenu()" aria-label="메뉴 열기">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
        <line x1="3" y1="5" x2="17" y2="5"></line><line x1="3" y1="10" x2="17" y2="10"></line><line x1="3" y1="15" x2="17" y2="15"></line>
      </svg>
    </button>
    <div class="viz-menu-dropdown" id="vizMenuDropdown">
      <button onclick="cycleTheme()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 3v2M12 19v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M3 12h2M19 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path><circle cx="12" cy="12" r="4"></circle></svg>
        <span id="themeLabel">Light</span>
      </button>
      <button onclick="downloadImage()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><path d="M7 10l5 5 5-5"></path><path d="M12 15V3"></path></svg>
        <span>Download PNG</span>
      </button>
      <button onclick="window.print()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 9V2h12v7"></path><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path><path d="M6 14h12v8H6z"></path></svg>
        <span>Print / PDF</span>
      </button>
    </div>
  </div>
  <main id="main-content" role="main">
    <header class="page-shell hero">
      <div class="hero-copy animate">
        <div class="eyebrow">Portfolio Metadata Atlas</div>
        <h1>보유 이미지가 영업 제안 자산으로 읽히는 방식.</h1>
        <p>__SOURCE_LABEL__ 폴더의 이미지와 인스타 메타, 기존 큐레이션 seed를 합쳐 검색 가능한 포트폴리오 메타 인덱스로 정리했습니다. 이 화면은 이후 브랜드 URL 분석과 유사/보완 추천의 기준점으로 쓰입니다.</p>
      </div>
      <aside class="hero-panel animate delay-1" aria-label="포트폴리오 이미지 미리보기">
        <div class="hero-mosaic" id="heroMosaic"></div>
        <div class="hero-meta">
          <div class="metric"><strong data-count="__COUNT__">0</strong><span>메타화 이미지</span></div>
          <div class="metric"><strong data-count="__GROUP_COUNT__">0</strong><span>분류 그룹</span></div>
          <div class="metric"><strong data-count="__PROJECT_COUNT__">0</strong><span>프로젝트 그룹</span></div>
        </div>
      </aside>
    </header>

    <section class="page-shell animate delay-2" aria-labelledby="controls-title">
      <div class="section-head">
        <div>
          <div class="eyebrow">Browse</div>
          <h2 id="controls-title">전체 메타데이터 탐색</h2>
          <p>검색어와 필터를 조합해 컷 유형, 프로젝트, 태그, 제안 활용 문구까지 한 번에 확인할 수 있습니다.</p>
        </div>
      </div>
      <div class="control-panel">
        <div class="controls">
          <div class="field">
            <label for="searchInput">검색</label>
            <input id="searchInput" type="search" placeholder="브랜드, 태그, 제안 문구, 파일명 검색">
          </div>
          <div class="field">
            <label for="brandFilter">브랜드 태그</label>
            <select id="brandFilter"></select>
          </div>
          <div class="field">
            <label for="groupFilter">그룹</label>
            <select id="groupFilter"></select>
          </div>
          <div class="field">
            <label for="cutFilter">컷 유형</label>
            <select id="cutFilter"></select>
          </div>
          <div class="field">
            <label for="sortSelect">정렬</label>
            <select id="sortSelect">
              <option value="id">ID 순</option>
              <option value="group">그룹 순</option>
              <option value="date">게시일 최신순</option>
              <option value="brightness">밝기 순</option>
            </select>
          </div>
        </div>
        <p class="status-line" id="resultStatus"></p>
        <div class="brand-panel" aria-label="브랜드 태그 빠른 선택">
          <div class="brand-panel-head">
            <h3>브랜드 태그별 빠른 보기</h3>
            <span id="brandSummary"></span>
          </div>
          <div class="brand-chips" id="brandChips"></div>
        </div>
      </div>
    </section>

    <nav class="page-shell view-tabs animate delay-3" id="viewTabs" role="tablist" aria-label="포트폴리오 메타데이터 보기">
      <button class="view-tab active" id="tab-gallery" type="button" role="tab" aria-selected="true" aria-controls="panel-gallery" data-view="gallery">포트폴리오 카드</button>
      <button class="view-tab" id="tab-insights" type="button" role="tab" aria-selected="false" aria-controls="panel-insights" data-view="insights">분포 분석</button>
      <button class="view-tab" id="tab-table" type="button" role="tab" aria-selected="false" aria-controls="panel-table" data-view="table">데이터 테이블</button>
    </nav>

    <section class="page-shell view-panel" id="panel-gallery" data-view-panel="gallery" role="tabpanel" aria-labelledby="tab-gallery">
      <div class="section-head">
        <div>
          <div class="eyebrow">Cards</div>
          <h2 id="gallery-title">포트폴리오 카드</h2>
          <p>이미지별 큐레이션 태그, 색상, 제안 활용 문구를 카드 형태로 확인합니다.</p>
        </div>
      </div>
      <div class="gallery" id="gallery"></div>
      <div class="load-more-wrap" id="loadMoreWrap" hidden>
        <button class="text-button primary" id="loadMoreButton" type="button">더 보기</button>
      </div>
      <div class="empty" id="emptyState" hidden>조건에 맞는 포트폴리오가 없습니다.</div>
    </section>

    <section class="page-shell view-panel" id="panel-insights" data-view-panel="insights" role="tabpanel" aria-labelledby="tab-insights" hidden>
      <div class="section-head">
        <div>
          <div class="eyebrow">Shape of Library</div>
          <h2 id="stats-title">분류와 태그 분포</h2>
          <p>현재 포트폴리오가 어떤 컷 유형과 제안 역할에 강한지 빠르게 볼 수 있습니다.</p>
        </div>
      </div>
      <div class="stats-grid" id="statsGrid"></div>
      <div class="charts" style="margin-top: 16px;">
        <div class="chart-panel">
          <h3>그룹별 이미지 수</h3>
          <div class="chart-box"><canvas id="groupChart" role="img" aria-label="포트폴리오 그룹별 이미지 수 막대 차트"></canvas></div>
        </div>
        <div class="chart-panel">
          <h3>컷 유형 분포</h3>
          <div class="chart-box"><canvas id="cutChart" role="img" aria-label="컷 유형 분포 도넛 차트"></canvas></div>
        </div>
      </div>
    </section>

    <section class="page-shell view-panel" id="panel-table" data-view-panel="table" role="tabpanel" aria-labelledby="tab-table" hidden>
      <div class="section-head">
        <div>
          <div class="eyebrow">Data Table</div>
          <h2 id="table-title">전체 데이터 테이블</h2>
          <p>브랜드 제안 자동화에서 사용할 핵심 필드를 표로 검수합니다.</p>
        </div>
      </div>
      <div class="data-table-wrap">
        <div class="table-scroll">
          <table class="metadata-table">
            <colgroup>
              <col class="col-id">
              <col class="col-project">
              <col class="col-brand">
              <col class="col-group">
              <col class="col-cut">
              <col class="col-visual">
              <col class="col-commerce">
              <col class="col-proposal">
            </colgroup>
            <thead>
              <tr>
                <th>ID</th>
                <th>프로젝트</th>
                <th>브랜드 태그</th>
                <th>그룹</th>
                <th>컷 유형</th>
                <th>Visual Tags</th>
                <th>Commerce Tags</th>
                <th>제안 활용</th>
              </tr>
            </thead>
            <tbody id="dataTable"></tbody>
          </table>
        </div>
      </div>
    </section>
  </main>

  <div class="drawer-backdrop" id="drawerBackdrop" onclick="closeDetail()"></div>
  <aside class="detail-drawer" id="detailDrawer" aria-label="상세 메타데이터" aria-hidden="true"></aside>
  <div class="sunset-stripe"></div>
  <p class="footer-note">Generated from __SOURCE_LABEL__ images, Instagram JSON metadata, curated seed tags, and local image statistics. Review rights and client names before sending proposals.</p>

  <script>
    var PORTFOLIO_DATA = __DATA__;
    var PORTFOLIO_SUMMARY = __SUMMARY__;
    var filteredData = PORTFOLIO_DATA.slice();
    var visibleLimit = 60;
    var chartsBuilt = false;
    var activeView = 'gallery';
    var ChartManager = {
      charts: new Map(),
      safeInit: function(canvasId, config) {
        if (typeof Chart === 'undefined') {
          console.error('Chart.js library not loaded - check CDN inclusion');
          return null;
        }
        try {
          if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
            this.charts.delete(canvasId);
          }
          var ctx = document.getElementById(canvasId);
          if (!ctx) {
            console.error('Canvas element not found: ' + canvasId);
            return null;
          }
          if (ctx.chart) {
            ctx.chart.destroy();
            delete ctx.chart;
          }
          ctx.setAttribute('role', 'img');
          if (!ctx.getAttribute('aria-label')) ctx.setAttribute('aria-label', 'Chart visualization');
          var chart = new Chart(ctx, config);
          this.charts.set(canvasId, chart);
          return chart;
        } catch (error) {
          console.error('Chart initialization failed for ' + canvasId + ':', error);
          return null;
        }
      },
      updateTheme: function() {
        if (typeof Chart === 'undefined') return;
        this.charts.forEach(function(chart) {
          try { chart.update(); } catch (error) { console.error('Chart theme update failed:', error); }
        });
      },
      destroyAll: function() {
        this.charts.forEach(function(chart) {
          try { chart.destroy(); } catch (error) { console.error('Chart destruction failed:', error); }
        });
        this.charts.clear();
      }
    };

    function toggleMenu() {
      var dropdown = document.getElementById('vizMenuDropdown');
      if (dropdown) dropdown.classList.toggle('open');
    }
    document.addEventListener('click', function(event) {
      if (!event.target.closest('.viz-menu')) {
        var dropdown = document.getElementById('vizMenuDropdown');
        if (dropdown) dropdown.classList.remove('open');
      }
    });
    document.addEventListener('keydown', function(event) {
      if (event.key === 'Escape') {
        closeDetail();
        var dropdown = document.getElementById('vizMenuDropdown');
        if (dropdown) dropdown.classList.remove('open');
      }
    });
    var savedTheme = localStorage.getItem('portfolio-viz-theme');
    var currentTheme = savedTheme || 'light';
    function applyTheme(theme) {
      document.documentElement.className = 'theme-' + theme;
      var label = document.getElementById('themeLabel');
      if (label) label.textContent = theme === 'dark' ? 'Dark' : 'Light';
      localStorage.setItem('portfolio-viz-theme', theme);
      currentTheme = theme;
      if (typeof onThemeChange === 'function') onThemeChange();
    }
    function cycleTheme() { applyTheme(currentTheme === 'dark' ? 'light' : 'dark'); }
    applyTheme(currentTheme);
    async function downloadImage() {
      var menu = document.querySelector('.viz-menu');
      if (menu) menu.style.display = 'none';
      try {
        var url = await htmlToImage.toPng(document.body, { quality: 1, pixelRatio: 2, filter: function(node) { return !node.classList || !node.classList.contains('viz-menu'); } });
        var link = document.createElement('a');
        link.href = url;
        link.download = 'portfolio-metadata-atlas.png';
        link.click();
      } catch(error) {
        console.error('Download failed:', error);
      }
      if (menu) menu.style.display = '';
    }

    function uniqueSorted(field) {
      var values = {};
      PORTFOLIO_DATA.forEach(function(item) { values[item[field]] = true; });
      return Object.keys(values).sort();
    }
    function uniqueBrandTags() {
      var values = {};
      PORTFOLIO_DATA.forEach(function(item) {
        getBrandTags(item).forEach(function(tag) { values[tag] = true; });
      });
      return Object.keys(values).sort();
    }
    function getBrandTags(item) {
      if (Array.isArray(item.brand_tags) && item.brand_tags.length) return item.brand_tags;
      if (Array.isArray(item.client_handles) && item.client_handles.length) return item.client_handles;
      return ['unknown'];
    }
    function fillSelect(id, values, allLabel) {
      var select = document.getElementById(id);
      select.innerHTML = '<option value="all">' + allLabel + '</option>' + values.map(function(value) {
        return '<option value="' + escapeHtml(value) + '">' + escapeHtml(value) + '</option>';
      }).join('');
    }
    function escapeHtml(value) {
      return String(value || '').replace(/[&<>"']/g, function(char) {
        return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[char];
      });
    }
    function matchesSearch(item, query) {
      if (!query) return true;
      var haystack = [
        item.portfolio_id, item.file_name, item.client_or_project, item.group, item.cut_type_label,
        item.proposal_use, item.description, item.analysis_summary,
        getBrandTags(item).join(' '), item.visual_tags.join(' '), item.commerce_tags.join(' '), item.work_scope.join(' ')
      ].join(' ').toLowerCase();
      return haystack.indexOf(query.toLowerCase()) !== -1;
    }
    function getFilteredData() {
      var query = document.getElementById('searchInput').value.trim();
      var brand = document.getElementById('brandFilter').value;
      var group = document.getElementById('groupFilter').value;
      var cut = document.getElementById('cutFilter').value;
      var sort = document.getElementById('sortSelect').value;
      var result = PORTFOLIO_DATA.filter(function(item) {
        return matchesSearch(item, query) &&
          (brand === 'all' || getBrandTags(item).indexOf(brand) !== -1) &&
          (group === 'all' || item.group === group) &&
          (cut === 'all' || item.cut_type_label === cut);
      });
      result.sort(function(a, b) {
        if (sort === 'group') return (a.group + a.portfolio_id).localeCompare(b.group + b.portfolio_id);
        if (sort === 'date') return String(b.post_date).localeCompare(String(a.post_date));
        if (sort === 'brightness') return b.average_luminance - a.average_luminance;
        return a.portfolio_id.localeCompare(b.portfolio_id);
      });
      return result;
    }
    function renderHero() {
      var mosaic = document.getElementById('heroMosaic');
      mosaic.innerHTML = PORTFOLIO_DATA.slice(0, 8).map(function(item) {
        return '<img src="' + item.html_image_path + '" alt="' + escapeHtml(item.portfolio_id + ' ' + item.cut_type_label) + '">';
      }).join('');
    }
    function renderStats() {
      var statsGrid = document.getElementById('statsGrid');
      var visualTags = {};
      var commerceTags = {};
      PORTFOLIO_DATA.forEach(function(item) {
        item.visual_tags.forEach(function(tag) { visualTags[tag] = true; });
        item.commerce_tags.forEach(function(tag) { commerceTags[tag] = true; });
      });
      var stats = [
        ['이미지', PORTFOLIO_DATA.length, '전체 포트폴리오 컷'],
        ['프로젝트', PORTFOLIO_SUMMARY.project_group_count, '인스타 포스트 기준 묶음'],
        ['비주얼 태그', Object.keys(visualTags).length, '색감, 구도, 연출'],
        ['커머스 태그', Object.keys(commerceTags).length, 'SNS, 상세, 캠페인 역할']
      ];
      statsGrid.innerHTML = stats.map(function(stat) {
        return '<article class="metric"><strong data-count="' + stat[1] + '">0</strong><span>' + stat[0] + ' · ' + stat[2] + '</span></article>';
      }).join('');
      animateCounters();
    }
    function tagList(tags) {
      return tags.map(function(tag) { return '<span class="tag">' + escapeHtml(tag) + '</span>'; }).join('');
    }
    function swatches(colors) {
      return colors.map(function(color) { return '<span class="swatch" style="background:' + escapeHtml(color) + '" title="' + escapeHtml(color) + '"></span>'; }).join('');
    }
    function renderBrandPanel() {
      var counts = PORTFOLIO_SUMMARY.brand_counts || {};
      var entries = Object.keys(counts).map(function(tag) { return { tag: tag, count: counts[tag] }; });
      entries.sort(function(a, b) { return b.count - a.count || a.tag.localeCompare(b.tag); });
      var selected = document.getElementById('brandFilter').value || 'all';
      var chips = [
        '<button class="brand-chip' + (selected === 'all' ? ' active' : '') + '" type="button" data-brand="all">전체 <strong>' + PORTFOLIO_DATA.length + '</strong></button>'
      ].concat(entries.map(function(entry) {
        return '<button class="brand-chip' + (selected === entry.tag ? ' active' : '') + '" type="button" data-brand="' + escapeHtml(entry.tag) + '">@' + escapeHtml(entry.tag) + ' <strong>' + entry.count + '</strong></button>';
      }));
      document.getElementById('brandChips').innerHTML = chips.join('');
      document.getElementById('brandSummary').textContent = entries.length + '개 브랜드 태그';
      document.querySelectorAll('.brand-chip').forEach(function(button) {
        button.addEventListener('click', function() {
          document.getElementById('brandFilter').value = button.dataset.brand;
          visibleLimit = 60;
          applyFilters();
        });
      });
    }
    function renderGallery() {
      var gallery = document.getElementById('gallery');
      var emptyState = document.getElementById('emptyState');
      var loadMoreWrap = document.getElementById('loadMoreWrap');
      var visibleItems = filteredData.slice(0, visibleLimit);
      emptyState.hidden = filteredData.length !== 0;
      if (loadMoreWrap) loadMoreWrap.hidden = filteredData.length <= visibleLimit;
      gallery.innerHTML = visibleItems.map(function(item) {
        return '<article class="portfolio-card">' +
          '<button class="image-button" onclick="openDetail(\\'' + item.portfolio_id + '\\')" aria-label="' + escapeHtml(item.portfolio_id + ' 상세 보기') + '">' +
          '<div class="image-frame"><img src="' + item.html_image_path + '" alt="' + escapeHtml(item.cut_type_label + ' 이미지') + '"></div></button>' +
          '<div class="card-body">' +
          '<div class="card-top"><div class="card-title"><h3>' + escapeHtml(item.portfolio_id + ' · ' + item.cut_type_label) + '</h3><p>' + escapeHtml(item.client_or_project) + '</p></div><span class="badge">' + escapeHtml(item.group) + '</span></div>' +
          '<div class="tags">' + tagList(getBrandTags(item).map(function(tag) { return '@' + tag; })) + '</div>' +
          '<div class="swatches">' + swatches(item.dominant_colors) + '</div>' +
          '<div class="tags">' + tagList(item.visual_tags.slice(0, 5)) + '</div>' +
          '<p class="proposal">' + escapeHtml(item.proposal_use) + '</p>' +
          '<div class="card-actions"><span class="text-secondary">' + escapeHtml(item.orientation) + ' · ' + item.width + 'x' + item.height + '</span><button class="text-button primary" onclick="openDetail(\\'' + item.portfolio_id + '\\')">상세 보기</button></div>' +
          '</div></article>';
      }).join('');
    }
    function renderTable() {
      var table = document.getElementById('dataTable');
      table.innerHTML = filteredData.map(function(item) {
        return '<tr>' +
          '<td><button class="text-button" onclick="openDetail(\\'' + item.portfolio_id + '\\')">' + escapeHtml(item.portfolio_id) + '</button></td>' +
          '<td><div class="table-project">' + escapeHtml(item.client_or_project) + '</div><span class="table-file">' + escapeHtml(item.file_name) + '</span></td>' +
          '<td>' + tagList(getBrandTags(item).map(function(tag) { return '@' + tag; })) + '</td>' +
          '<td>' + escapeHtml(item.group) + '</td>' +
          '<td>' + escapeHtml(item.cut_type_label) + '</td>' +
          '<td>' + tagList(item.visual_tags) + '</td>' +
          '<td>' + tagList(item.commerce_tags) + '</td>' +
          '<td><p class="table-proposal">' + escapeHtml(item.proposal_use) + '</p></td>' +
          '</tr>';
      }).join('');
    }
    function updateStatus() {
      var visible = Math.min(filteredData.length, visibleLimit);
      document.getElementById('resultStatus').textContent = '총 ' + PORTFOLIO_DATA.length + '장 중 ' + filteredData.length + '장 필터됨 · 현재 카드 ' + visible + '장 표시';
    }
    function applyFilters() {
      filteredData = getFilteredData();
      renderBrandPanel();
      renderGallery();
      renderTable();
      updateStatus();
    }
    function openDetail(id) {
      var item = PORTFOLIO_DATA.find(function(record) { return record.portfolio_id === id; });
      if (!item) return;
      var drawer = document.getElementById('detailDrawer');
      drawer.innerHTML = '<div class="drawer-head"><div><div class="eyebrow">' + escapeHtml(item.portfolio_id) + '</div><h2>' + escapeHtml(item.cut_type_label) + '</h2><p class="text-secondary">' + escapeHtml(item.client_or_project) + '</p></div><button class="icon-button" onclick="closeDetail()" aria-label="닫기"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"></path></svg></button></div>' +
        '<div class="drawer-image"><img src="' + item.html_image_path + '" alt="' + escapeHtml(item.cut_type_label) + '"></div>' +
        '<p class="proposal">' + escapeHtml(item.analysis_summary) + '</p>' +
        '<div class="detail-grid">' +
        '<div class="detail-box"><span>브랜드 태그</span>' + escapeHtml(getBrandTags(item).map(function(tag) { return '@' + tag; }).join(' / ')) + '</div>' +
        '<div class="detail-box"><span>그룹</span>' + escapeHtml(item.group) + '</div>' +
        '<div class="detail-box"><span>크기</span>' + item.width + 'x' + item.height + '</div>' +
        '<div class="detail-box"><span>밝기/대비</span>' + escapeHtml(item.brightness_level + ' / ' + item.contrast_level) + '</div>' +
        '<div class="detail-box"><span>모델/상품</span>' + escapeHtml(item.model_presence + ' / ' + item.product_presence) + '</div>' +
        '</div>' +
        '<h3>Visual Tags</h3><div class="tags" style="margin: 10px 0 18px;">' + tagList(item.visual_tags) + '</div>' +
        '<h3>Commerce Tags</h3><div class="tags" style="margin: 10px 0 18px;">' + tagList(item.commerce_tags) + '</div>' +
        '<h3>유사 추천 조건</h3><ul style="margin: 10px 0 18px 20px;">' + item.similar_when.map(function(text) { return '<li>' + escapeHtml(text) + '</li>'; }).join('') + '</ul>' +
        '<h3>보완 추천 조건</h3><ul style="margin: 10px 0 18px 20px;">' + item.contrast_when.map(function(text) { return '<li>' + escapeHtml(text) + '</li>'; }).join('') + '</ul>' +
        '<details class="json-details"><summary>전체 JSON 보기</summary><pre class="json-block">' + escapeHtml(JSON.stringify(item, null, 2)) + '</pre></details>';
      drawer.classList.add('open');
      drawer.setAttribute('aria-hidden', 'false');
      document.getElementById('drawerBackdrop').classList.add('open');
    }
    function closeDetail() {
      var drawer = document.getElementById('detailDrawer');
      var backdrop = document.getElementById('drawerBackdrop');
      if (drawer) {
        drawer.classList.remove('open');
        drawer.setAttribute('aria-hidden', 'true');
      }
      if (backdrop) backdrop.classList.remove('open');
    }
    function chartColors() {
      var isDark = document.documentElement.classList.contains('theme-dark');
      return {
        text: isDark ? '#f4efe7' : '#16120f',
        grid: isDark ? 'rgba(255,245,226,0.14)' : 'rgba(29,24,20,0.1)',
        palette: ['#ff5a1f', '#245c73', '#f5b335', '#13795b', '#7b3f98', '#b42318', '#6b7280']
      };
    }
    function buildCharts() {
      if (typeof Chart === 'undefined') { console.error('Chart.js not loaded'); return; }
      var colors = chartColors();
      var groupLabels = Object.keys(PORTFOLIO_SUMMARY.group_counts);
      var groupValues = groupLabels.map(function(label) { return PORTFOLIO_SUMMARY.group_counts[label]; });
      var cutLabels = Object.keys(PORTFOLIO_SUMMARY.cut_type_counts);
      var cutValues = cutLabels.map(function(label) { return PORTFOLIO_SUMMARY.cut_type_counts[label]; });
      ChartManager.destroyAll();
      ChartManager.safeInit('groupChart', {
        type: 'bar',
        data: { labels: groupLabels, datasets: [{ label: '이미지 수', data: groupValues, backgroundColor: colors.palette[0], borderRadius: 8 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { tooltip: { enabled: true }, legend: { display: false } },
          scales: {
            x: { ticks: { color: colors.text }, grid: { color: colors.grid } },
            y: { beginAtZero: true, ticks: { color: colors.text, precision: 0 }, grid: { color: colors.grid } }
          }
        }
      });
      ChartManager.safeInit('cutChart', {
        type: 'doughnut',
        data: { labels: cutLabels, datasets: [{ label: '컷 유형', data: cutValues, backgroundColor: colors.palette, borderColor: colors.grid, borderWidth: 1 }] },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { tooltip: { enabled: true }, legend: { position: 'bottom', labels: { color: colors.text, boxWidth: 12 } } }
        }
      });
      chartsBuilt = true;
    }
    function onThemeChange() {
      if (chartsBuilt && activeView === 'insights') buildCharts();
    }
    function animateCounters() {
      document.querySelectorAll('[data-count]').forEach(function(element) {
        if (element.dataset.counted === '1') return;
        element.dataset.counted = '1';
        var target = parseFloat(element.dataset.count || element.textContent || '0');
        var start = performance.now();
        var duration = 900;
        function tick(now) {
          var progress = Math.min((now - start) / duration, 1);
          var eased = 1 - Math.pow(1 - progress, 3);
          element.textContent = Math.round(target * eased).toLocaleString();
          if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
      });
    }
    function initReveal() {
      document.querySelectorAll('[data-reveal]').forEach(function(element) {
        element.classList.add('reveal', 'visible');
      });
    }
    function setActiveView(view) {
      activeView = view;
      document.querySelectorAll('.view-tab').forEach(function(button) {
        var isActive = button.dataset.view === view;
        button.classList.toggle('active', isActive);
        button.setAttribute('aria-selected', isActive ? 'true' : 'false');
        button.tabIndex = isActive ? 0 : -1;
      });
      document.querySelectorAll('[data-view-panel]').forEach(function(panel) {
        panel.hidden = panel.dataset.viewPanel !== view;
      });
      if (view === 'insights') {
        window.setTimeout(buildCharts, 30);
      }
    }
    function initTabs() {
      document.querySelectorAll('.view-tab').forEach(function(button) {
        button.addEventListener('click', function() {
          setActiveView(button.dataset.view);
        });
      });
      setActiveView(activeView);
    }
    function init() {
      fillSelect('brandFilter', uniqueBrandTags(), '전체 브랜드');
      fillSelect('groupFilter', uniqueSorted('group'), '전체 그룹');
      fillSelect('cutFilter', uniqueSorted('cut_type_label'), '전체 컷 유형');
      renderHero();
      renderStats();
      applyFilters();
      initTabs();
      initReveal();
      ['searchInput', 'brandFilter', 'groupFilter', 'cutFilter', 'sortSelect'].forEach(function(id) {
        var control = document.getElementById(id);
        function onFilterChange() {
          visibleLimit = 60;
          applyFilters();
        }
        control.addEventListener('input', onFilterChange);
        control.addEventListener('change', onFilterChange);
      });
      document.getElementById('loadMoreButton').addEventListener('click', function() {
        visibleLimit += 60;
        renderGallery();
        updateStatus();
      });
      var resizeTimer = null;
      window.addEventListener('resize', function() {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(function() {
          if (chartsBuilt && activeView === 'insights') buildCharts();
        }, 160);
      });
    }
    window.addEventListener('load', init);
  </script>
</body>
</html>
"""


def write_html(records: list[dict[str, Any]], summary: dict[str, Any], viewer_path: Path) -> None:
    html = html_template()
    html = html.replace("__DATA__", json.dumps(records, ensure_ascii=False))
    html = html.replace("__SUMMARY__", json.dumps(summary, ensure_ascii=False))
    html = html.replace("__COUNT__", str(summary["portfolio_count"]))
    html = html.replace("__GROUP_COUNT__", str(len(summary["group_counts"])))
    html = html.replace("__PROJECT_COUNT__", str(summary["project_group_count"]))
    html = html.replace("__SOURCE_LABEL__", summary["source_directory"])
    viewer_path.parent.mkdir(parents=True, exist_ok=True)
    viewer_path.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build portfolio metadata JSON/JSONL and a standalone HTML viewer."
    )
    parser.add_argument(
        "--source-dir",
        default=str(PORTFOLIO_DIR),
        help="Image folder to scan. Defaults to ./portfolio.",
    )
    parser.add_argument(
        "--seed",
        default=str(SEED_PATH),
        help="Optional curated seed JSON keyed by image filename.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory for generated JSON, JSONL, summary, and thumbnails.",
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="Output filename prefix. Defaults to the source folder name.",
    )
    parser.add_argument(
        "--viewer-path",
        default=None,
        help="HTML viewer path. Defaults to data/{slug}_metadata_viewer.html.",
    )
    parser.add_argument(
        "--no-thumbnails",
        action="store_true",
        help="Use original images in the HTML viewer instead of generated thumbnails.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir).expanduser()
    if not source_dir.is_absolute():
        source_dir = ROOT / source_dir
    seed_path = Path(args.seed).expanduser()
    if not seed_path.is_absolute():
        seed_path = ROOT / seed_path
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    slug = slugify(args.slug or source_dir.name)
    viewer_path = Path(args.viewer_path).expanduser() if args.viewer_path else output_dir / f"{slug}_metadata_viewer.html"
    if not viewer_path.is_absolute():
        viewer_path = ROOT / viewer_path
    thumbnail_dir = None if args.no_thumbnails else output_dir / f"{slug}_thumbnails"

    records, video_paths, json_count = build_records(source_dir, seed_path, viewer_path, thumbnail_dir)
    summary = summarize(records, source_dir, viewer_path, video_paths, json_count)
    write_data(records, summary, output_dir, slug)
    write_html(records, summary, viewer_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
