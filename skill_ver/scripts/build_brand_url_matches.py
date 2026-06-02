#!/usr/bin/env python3
"""Collect brand URL imagery and match it against portfolio metadata.

This script is intentionally isolated under skill_ver. It does not touch the
existing api/ or web/ application.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import shutil
from collections import Counter, deque
from datetime import datetime
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skill_ver"
DEFAULT_PORTFOLIO_INDEX = SKILL_DIR / "data" / "portfolio_all_index.json"
DEFAULT_OUTPUT_DIR = SKILL_DIR / "data" / "brand_runs"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
SKIP_IMAGE_KEYWORDS = {
    "account",
    "basket",
    "button",
    "cart",
    "logo",
    "favicon",
    "icon",
    "mypage",
    "nav",
    "sprite",
    "placeholder",
    "blank",
    "loading",
    "payment",
    "badge",
    "pixel",
    "search",
    "tracker",
}
SKIP_IMAGE_DOMAINS = {
    "facebook.com",
    "www.facebook.com",
    "connect.facebook.net",
    "google-analytics.com",
    "www.google-analytics.com",
    "googletagmanager.com",
    "www.googletagmanager.com",
    "doubleclick.net",
}
PRODUCT_KEYWORDS = {
    "product",
    "products",
    "goods",
    "item",
    "shop",
    "detail",
    "sku",
    "pdp",
    "best",
    "new-arrivals",
    "new_arrivals",
    "ranking",
}
CAMPAIGN_KEYWORDS = {
    "campaign",
    "collection",
    "editorial",
    "lookbook",
    "collab",
    "collaboration",
    "project",
    "story",
    "stories",
    "magazine",
    "season",
    "visual",
    "event",
    "promotion",
    "holiday",
}
CUT_TYPE_ORDER = [
    "campaign_key_visual",
    "model_styling_cut",
    "product_object_cut",
    "detail_or_pattern_cut",
    "sports_active_cut",
    "seasonal_lifestyle_cut",
    "closeup_mood_cut",
]
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
CUT_TYPE_DESCRIPTIONS = {
    "campaign_key_visual": "브랜드 피드나 시즌 캠페인의 첫인상을 만드는 대표 이미지입니다.",
    "model_styling_cut": "모델 착용, 핏, 스타일링 조합을 보여주는 이미지입니다.",
    "product_object_cut": "제품 자체나 오브젝트 배치를 중심으로 상품을 전달하는 이미지입니다.",
    "detail_or_pattern_cut": "소재, 패턴, 그래픽, 디테일을 가까이 보여주는 이미지입니다.",
    "sports_active_cut": "움직임, 야외 활동, 액티브한 착용 상황이 드러나는 이미지입니다.",
    "seasonal_lifestyle_cut": "계절감, 장소, 생활 맥락을 통해 브랜드 무드를 확장하는 이미지입니다.",
    "closeup_mood_cut": "얼굴, 손, 소재, 소품 등을 가까이 잡아 감정선과 무드를 만드는 이미지입니다.",
    "unknown": "아직 명확한 컷 유형으로 분류되지 않은 이미지입니다.",
}
TAG_DEFINITIONS = {
    "active_lifestyle": "활동적인 생활 장면이나 움직임이 브랜드 무드에 포함된 컷입니다.",
    "bold_color": "강한 색감이나 그래픽 컬러가 핵심인 컷입니다. 현재는 포트폴리오 메타/휴리스틱 기준으로 판단합니다.",
    "brand_asset": "브랜드 피드, 배너, 캠페인 소재로 바로 쓰기 좋은 대표 이미지 역할입니다.",
    "brand_character": "브랜드의 성격이나 톤을 기억에 남기기 위한 캐릭터성 있는 컷입니다.",
    "bright_mood": "밝고 친근한 인상을 주는 컷입니다.",
    "bright_natural": "평균 밝기가 높거나 자연광/밝은 톤으로 보이는 컷입니다.",
    "blue_tone": "파란 계열 색감이 주요 분위기를 만드는 컷입니다.",
    "campaign_key_visual": "캠페인 첫 화면이나 대표 소재로 사용할 수 있는 컷입니다.",
    "campaign_mood": "상품 설명보다 시즌/컬렉션 분위기를 먼저 전달하는 컷입니다.",
    "campaign_support": "메인 키비주얼을 보조해 피드나 제안서 흐름을 풍성하게 만드는 컷입니다.",
    "casual": "일상적이고 부담 없는 착용/스타일링 인상을 주는 컷입니다.",
    "close_up": "피사체를 가까이 잡아 소재, 감정, 디테일을 강조한 컷입니다.",
    "dark_mood": "평균 밝기가 낮거나 어두운 톤으로 고급감/긴장감을 만드는 컷입니다.",
    "detail_or_pattern": "패턴, 로고, 소재, 봉제 등 디테일을 강조한 컷입니다.",
    "detail_focus": "전체 실루엣보다 특정 디테일을 중심으로 읽히는 컷입니다.",
    "detail_page_top": "상품 상세 상단에서 상품을 명확히 전달하기 좋은 컷입니다.",
    "dynamic_pose": "정적인 포즈보다 움직임이나 에너지가 느껴지는 컷입니다.",
    "editorial": "잡지 화보처럼 연출감과 분위기가 강한 컷입니다.",
    "fit_visible": "착용 핏, 실루엣, 기장감이 확인되는 컷입니다.",
    "friendly_expression": "표정이나 상황이 친근한 인상을 만드는 컷입니다.",
    "full_body": "전신 실루엣과 전체 스타일링을 확인할 수 있는 컷입니다.",
    "graphic_frame": "그래픽 구성, 색면, 프레임감이 강한 컷입니다.",
    "graphic_texture": "그래픽, 패턴, 질감이 이미지의 주요 정보인 컷입니다.",
    "group_model": "2명 이상 모델의 관계나 그룹 스타일링을 보여주는 컷입니다.",
    "half_body": "상반신 또는 반신 중심으로 스타일링과 표정을 함께 보여주는 컷입니다.",
    "high_contrast": "이미지 안의 밝고 어두운 영역 차이가 큰 컷입니다.",
    "lifestyle_context": "제품이 놓인 생활/장소 맥락이 함께 드러나는 컷입니다.",
    "lifestyle_top": "상세나 캠페인 상단에서 라이프스타일 분위기를 전달하기 좋은 컷입니다.",
    "lookbook": "착용 조합과 스타일링 흐름을 보여주는 룩북 성격의 컷입니다.",
    "model_styling": "모델 착용과 스타일링 조합이 주요 정보인 컷입니다.",
    "mood_cut": "상품 정보보다 감정선과 분위기를 만드는 컷입니다.",
    "neutral_background": "배경이 단순해 상품/모델에 시선이 모이는 컷입니다.",
    "object_still_life": "모델보다 제품이나 오브젝트 배치가 중심인 스틸라이프 컷입니다.",
    "outdoor_mood": "야외 장소감이나 자연광 분위기가 있는 컷입니다.",
    "portrait_frame": "세로형 프레임입니다. 모바일 피드/스토리형 소재와 잘 맞습니다.",
    "premium_mood": "고급스럽거나 에디토리얼한 인상을 강화하는 컷입니다.",
    "product_focus": "제품이 이미지의 주된 주인공으로 읽히는 컷입니다.",
    "prop_styling": "소품 연출이 브랜드 캐릭터나 색감을 보강하는 컷입니다.",
    "season_campaign": "시즌 드롭, 계절 캠페인, 컬렉션 공개에 쓰기 좋은 역할입니다.",
    "seasonal_background": "계절감 있는 배경이나 장소가 이미지 분위기를 만드는 컷입니다.",
    "seasonal_mood": "특정 계절이나 시즌 분위기가 두드러지는 컷입니다.",
    "set_design": "세트 구성이나 배경 연출이 강하게 설계된 컷입니다.",
    "shortform_ready": "짧은 피드/릴스/숏폼 썸네일로 쓰기 좋은 명확한 컷입니다.",
    "sns_detail_combo": "SNS와 상세페이지 양쪽에 활용 가능한 디테일/착용 정보가 있는 컷입니다.",
    "sns_hook": "피드에서 시선을 끌 수 있는 후킹 역할의 컷입니다.",
    "sports_active": "스포츠, 아웃도어, 액티브한 착용 상황과 연결되는 컷입니다.",
    "street_casual": "스트리트/캐주얼 스타일링으로 읽히는 컷입니다.",
    "studio_light": "스튜디오 조명이나 정돈된 촬영 환경이 느껴지는 컷입니다.",
    "summer": "여름, 리조트, 스윔 등 더운 계절의 분위기가 있는 컷입니다.",
    "target_affinity": "브랜드 타깃이 친밀하게 느낄 수 있는 표정/상황을 가진 컷입니다.",
    "wide_hero": "가로형 히어로 배너나 와이드 화면에 쓰기 좋은 컷입니다.",
    "winter": "겨울, 아우터, 차가운 계절감이 드러나는 컷입니다.",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "brand"


def as_project_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_workspace_path(path: Path) -> Path:
    expanded = path.expanduser()
    return expanded if expanded.is_absolute() else ROOT / expanded


def to_run_relative(run_dir: Path, path_value: str | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    try:
        return os.path.relpath(path, run_dir)
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_url(raw_url: str, base_url: str) -> str:
    raw_url = html.unescape(raw_url or "").strip()
    if not raw_url or raw_url.startswith(("data:", "mailto:", "tel:", "javascript:")):
        return ""
    raw_url = raw_url.split()[0]
    joined = urljoin(base_url, raw_url)
    return urldefrag(joined)[0]


def srcset_urls(value: str, base_url: str) -> list[str]:
    urls: list[str] = []
    for part in (value or "").split(","):
        candidate = normalize_url(part.strip().split(" ")[0], base_url)
        if candidate:
            urls.append(candidate)
    return urls


def looks_like_image(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc.lower() in SKIP_IMAGE_DOMAINS:
        return False
    suffix = Path(parsed.path).suffix.lower()
    if suffix in {".svg", ".gif", ".ico", ".mp4", ".mov", ".webm"}:
        return False
    if suffix and suffix not in IMAGE_EXTENSIONS:
        return False
    lowered = url.lower()
    return not any(keyword in lowered for keyword in SKIP_IMAGE_KEYWORDS)


def keyword_hits(text: str, keywords: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for keyword in keywords if keyword in lowered)


def classify_candidate(text: str) -> str:
    product_hits = keyword_hits(text, PRODUCT_KEYWORDS)
    campaign_hits = keyword_hits(text, CAMPAIGN_KEYWORDS)
    if campaign_hits > product_hits:
        return "campaign_collaboration"
    if product_hits > 0:
        return "product"
    if campaign_hits > 0:
        return "campaign_collaboration"
    return "unknown"


def candidate_score(candidate: dict[str, Any]) -> float:
    text = " ".join(
        [
            candidate.get("image_url", ""),
            candidate.get("page_url", ""),
            candidate.get("context", ""),
            candidate.get("source", ""),
        ]
    ).lower()
    score = 0.0
    if candidate.get("source") in {"og:image", "twitter:image", "json-ld"}:
        score += 14
    if candidate.get("category") == "campaign_collaboration":
        score += 24
    elif candidate.get("category") == "product":
        score += 22
    score += min(keyword_hits(text, PRODUCT_KEYWORDS) * 5, 20)
    score += min(keyword_hits(text, CAMPAIGN_KEYWORDS) * 6, 24)
    if any(word in text for word in ["thumbnail", "thumb", "small"]):
        score -= 6
    if any(word in text for word in SKIP_IMAGE_KEYWORDS):
        score -= 30
    return score


class BrandHTMLParser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.candidates: list[dict[str, Any]] = []
        self.links: list[str] = []
        self._link_stack: list[str] = []
        self._script_type = ""
        self._script_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        context = " ".join(
            attr.get(key, "")
            for key in ["alt", "title", "aria-label", "class", "id", "data-title", "data-name"]
        )
        if tag in {"img", "image"}:
            for key in ["src", "data-src", "data-original", "data-lazy-src", "data-image", "data-bg"]:
                self._add_image(attr.get(key, ""), "img", context)
            for key in ["srcset", "data-srcset"]:
                for image_url in srcset_urls(attr.get(key, ""), self.page_url):
                    self._add_image(image_url, "srcset", context)
        elif tag == "source":
            for image_url in srcset_urls(attr.get("srcset", ""), self.page_url):
                self._add_image(image_url, "srcset", context)
        elif tag == "meta":
            meta_name = (attr.get("property") or attr.get("name") or "").lower()
            if meta_name in {"og:image", "og:image:secure_url", "twitter:image"}:
                self._add_image(attr.get("content", ""), meta_name.replace(":secure_url", ""), context)
        elif tag == "link":
            rel = attr.get("rel", "").lower()
            if "image" in rel:
                self._add_image(attr.get("href", ""), "link-image", context)
            self._add_link(attr.get("href", ""))
        elif tag == "a":
            link = normalize_url(attr.get("href", ""), self.page_url)
            self._link_stack.append(link)
            self._add_link(link)
        elif tag == "script":
            self._script_type = attr.get("type", "").lower()
            self._script_chunks = []

        style = attr.get("style", "")
        for raw_url in re.findall(r"url\(['\"]?([^'\")]+)", style):
            self._add_image(raw_url, "style", context)

    def handle_data(self, data: str) -> None:
        if "ld+json" in self._script_type:
            self._script_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and "ld+json" in self._script_type:
            payload = "\n".join(self._script_chunks).strip()
            self._extract_jsonld_images(payload)
        if tag == "a" and self._link_stack:
            self._link_stack.pop()
        if tag == "script":
            self._script_type = ""
            self._script_chunks = []

    def _add_image(self, raw_url: str, source: str, context: str) -> None:
        image_url = normalize_url(raw_url, self.page_url)
        if not image_url or not looks_like_image(image_url):
            return
        linked_page_url = self._link_stack[-1] if self._link_stack else ""
        source_page_url = linked_page_url or self.page_url
        text = " ".join([image_url, source_page_url, self.page_url, context])
        self.candidates.append(
            {
                "image_url": image_url,
                "page_url": source_page_url,
                "origin_page_url": self.page_url,
                "source": source,
                "context": context.strip(),
                "category": classify_candidate(text),
            }
        )

    def _add_link(self, raw_url: str) -> None:
        link = normalize_url(raw_url, self.page_url)
        if not link:
            return
        if keyword_hits(link, PRODUCT_KEYWORDS | CAMPAIGN_KEYWORDS) > 0:
            self.links.append(link)

    def _extract_jsonld_images(self, payload: str) -> None:
        if not payload:
            return
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    if key.lower() in {"image", "thumbnail", "thumbnailurl", "contenturl"}:
                        walk_image(child)
                    else:
                        walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        def walk_image(value: Any) -> None:
            if isinstance(value, str):
                self._add_image(value, "json-ld", "")
            elif isinstance(value, list):
                for child in value:
                    walk_image(child)
            elif isinstance(value, dict):
                for key in ["url", "contentUrl", "@id"]:
                    if key in value:
                        self._add_image(str(value[key]), "json-ld", "")

        walk(data)


def read_text_source(url: str, timeout: int) -> tuple[str, dict[str, Any]]:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        path = Path(parsed.path)
        return path.read_text(encoding="utf-8", errors="ignore"), {"url": url, "status": "file"}
    if parsed.scheme in {"http", "https"}:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 Chrome/126 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="ignore"), {
                "url": response.geturl(),
                "status": response.status,
                "content_type": response.headers.get("Content-Type", ""),
            }
    path = Path(url)
    return path.read_text(encoding="utf-8", errors="ignore"), {"url": path.as_uri(), "status": "file"}


def same_site_link(base_url: str, link: str) -> bool:
    base = urlparse(base_url)
    parsed = urlparse(link)
    if base.scheme == "file":
        return parsed.scheme == "file"
    if "instagram.com" in base.netloc:
        return False
    return parsed.netloc == base.netloc


def collect_candidates(
    urls: list[str],
    source_html: Path | None,
    base_url: str | None,
    max_pages: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    pages: list[dict[str, Any]] = []
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []

    if source_html:
        resolved_base = base_url or source_html.resolve().as_uri()
        html_text = source_html.read_text(encoding="utf-8", errors="ignore")
        parser = BrandHTMLParser(resolved_base)
        parser.feed(html_text)
        candidates.extend(parser.candidates)
        pages.append({"url": resolved_base, "status": "source_html", "candidate_count": len(parser.candidates)})
        return dedupe_candidates(candidates), pages, warnings

    queue: deque[str] = deque(urls)
    visited: set[str] = set()
    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            html_text, info = read_text_source(url, timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            warnings.append(f"페이지 수집 실패: {url} ({error})")
            continue
        page_url = str(info.get("url") or url)
        parser = BrandHTMLParser(page_url)
        parser.feed(html_text)
        candidates.extend(parser.candidates)
        pages.append({**info, "candidate_count": len(parser.candidates)})
        for link in parser.links:
            if len(visited) + len(queue) >= max_pages:
                break
            if link not in visited and same_site_link(page_url, link):
                queue.append(link)

    return dedupe_candidates(candidates), pages, warnings


def load_gallery_sidecar(image_path: Path) -> tuple[dict[str, Any], Path | None]:
    sidecar_paths = [Path(f"{image_path}.json"), image_path.with_suffix(".json")]
    for sidecar_path in sidecar_paths:
        if not sidecar_path.exists():
            continue
        try:
            payload = load_json(sidecar_path)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            return payload, sidecar_path
    return {}, None


def compact_metadata_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [compact_metadata_value(item) for item in value]
        return " ".join(part for part in parts if part)
    if isinstance(value, dict):
        parts = [compact_metadata_value(value.get(key)) for key in ["username", "full_name", "name", "title"]]
        return " ".join(part for part in parts if part)
    return ""


def instagram_context(metadata: dict[str, Any], image_path: Path) -> str:
    context_keys = [
        "description",
        "caption",
        "title",
        "tags",
        "username",
        "fullname",
        "post_date",
        "date",
        "post_shortcode",
        "shortcode",
    ]
    parts = [compact_metadata_value(metadata.get(key)) for key in context_keys]
    parts.append(image_path.name)
    return " ".join(part for part in parts if part).strip()[:900]


def instagram_page_url(metadata: dict[str, Any], fallback_profile: str) -> str:
    for key in ["post_url", "webpage_url", "url"]:
        value = metadata.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    shortcode = metadata.get("post_shortcode") or metadata.get("sidecar_shortcode") or metadata.get("shortcode")
    if isinstance(shortcode, str) and shortcode:
        return f"https://www.instagram.com/p/{shortcode}/"
    username = metadata.get("username") or fallback_profile
    if isinstance(username, str) and username:
        return f"https://www.instagram.com/{username.strip('/')}/"
    return f"https://www.instagram.com/{fallback_profile}/"


def instagram_post_key(metadata: dict[str, Any], image_path: Path) -> str:
    for key in ["post_shortcode", "sidecar_shortcode", "post_id", "sidecar_media_id"]:
        value = metadata.get(key)
        if value:
            return str(value)
    return image_path.stem.split("_")[0]


def instagram_media_number(metadata: dict[str, Any], image_path: Path) -> int:
    for key in ["num", "sidecar_num", "media_number"]:
        value = metadata.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    media_id = str(metadata.get("media_id") or image_path.stem.split("_")[-1])
    return int(media_id[-6:]) if media_id[-6:].isdigit() else 999999


def parse_instagram_date(metadata: dict[str, Any]) -> float | None:
    value = metadata.get("post_date") or metadata.get("date")
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def image_creation_order(path: Path) -> float:
    stat = path.stat()
    return float(getattr(stat, "st_birthtime", stat.st_mtime))


def collect_instagram_folder_candidates(
    instagram_folders: list[Path],
    max_images_per_post: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    candidates: list[dict[str, Any]] = []
    pages: list[dict[str, Any]] = []
    warnings: list[str] = []

    for raw_folder in instagram_folders:
        folder = resolve_workspace_path(raw_folder)
        folder_label = as_project_path(folder)
        if not folder.exists():
            warnings.append(f"인스타 다운로드 폴더 없음: {folder_label}")
            continue
        if not folder.is_dir():
            warnings.append(f"인스타 다운로드 입력이 폴더가 아님: {folder_label}")
            continue

        image_entries: list[dict[str, Any]] = []
        image_paths = [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
        for image_path in image_paths:
            metadata, sidecar_path = load_gallery_sidecar(image_path)
            posted_at = parse_instagram_date(metadata)
            image_entries.append(
                {
                    "image_path": image_path,
                    "metadata": metadata,
                    "sidecar_path": sidecar_path,
                    "post_key": instagram_post_key(metadata, image_path),
                    "posted_at": posted_at,
                    "media_number": instagram_media_number(metadata, image_path),
                    "created_at": image_creation_order(image_path),
                }
            )
        image_entries.sort(
            key=lambda item: (
                0 if item["posted_at"] is not None else 1,
                -(item["posted_at"] or 0),
                item["created_at"] if item["posted_at"] is None else 0,
                item["media_number"],
                item["image_path"].name,
            )
        )
        folder_count = 0
        skipped_by_post_limit = 0
        post_counts: Counter[str] = Counter()
        source_order = len(candidates)
        for entry in image_entries:
            image_path = entry["image_path"]
            metadata = entry["metadata"]
            sidecar_path = entry["sidecar_path"]
            post_key = str(entry["post_key"])
            if max_images_per_post > 0 and post_counts[post_key] >= max_images_per_post:
                skipped_by_post_limit += 1
                continue
            post_counts[post_key] += 1
            context = instagram_context(metadata, image_path)
            page_url = instagram_page_url(metadata, folder.name)
            text = " ".join([image_path.name, context, page_url])
            category = classify_candidate(text)
            if category == "unknown":
                category = "campaign_collaboration"
            candidates.append(
                {
                    "image_url": image_path.resolve().as_uri(),
                    "page_url": page_url,
                    "source": "gallery-dl-instagram",
                    "context": context,
                    "category": category,
                    "local_source_path": as_project_path(image_path),
                    "gallery_dl_metadata_path": as_project_path(sidecar_path) if sidecar_path else "",
                    "instagram_username": metadata.get("username") or folder.name,
                    "instagram_post_shortcode": post_key,
                    "instagram_post_date": metadata.get("post_date") or metadata.get("date") or "",
                    "instagram_media_number": entry["media_number"],
                    "source_order": source_order,
                }
            )
            folder_count += 1
            source_order += 1

        pages.append(
            {
                "url": folder_label,
                "status": "gallery-dl-folder",
                "candidate_count": folder_count,
                "raw_image_count": len(image_entries),
                "skipped_by_post_limit": skipped_by_post_limit,
                "max_images_per_post": max_images_per_post,
                "source_type": "instagram_download_folder",
            }
        )

    return dedupe_candidates(candidates), pages, warnings


def dedupe_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        key = candidate["image_url"]
        candidate["candidate_score"] = round(candidate_score(candidate), 2)
        current = best.get(key)
        if current is None or candidate["candidate_score"] > current["candidate_score"]:
            best[key] = candidate
    values = list(best.values())
    if values and all(item.get("source") == "gallery-dl-instagram" for item in values):
        return sorted(values, key=lambda item: item.get("source_order", 999999))
    return sorted(
        values,
        key=lambda item: (-item["candidate_score"], item.get("source_order", 999999), item["image_url"]),
    )


def image_stats(image: Image.Image) -> dict[str, Any]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    aspect_ratio = round(width / height, 3) if height else 0
    if aspect_ratio >= 1.2:
        orientation = "landscape"
    elif aspect_ratio <= 0.82:
        orientation = "portrait"
    else:
        orientation = "square"
    sample = rgb.resize((80, 80))
    pixels = list(sample.get_flattened_data())
    luminance = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in pixels]
    avg_luminance = round(sum(luminance) / len(luminance), 2)
    contrast = round(math.sqrt(sum((value - avg_luminance) ** 2 for value in luminance) / len(luminance)), 2)
    brightness_level = "dark" if avg_luminance < 92 else "bright" if avg_luminance > 178 else "mid"
    contrast_level = "low" if contrast < 34 else "high" if contrast > 64 else "medium"
    palette = sample.quantize(colors=5).convert("RGB")
    colors = Counter(palette.get_flattened_data()).most_common(5)
    dominant_colors = ["#%02x%02x%02x" % color for color, _count in colors]
    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "orientation": orientation,
        "average_luminance": avg_luminance,
        "brightness_level": brightness_level,
        "contrast_value": contrast,
        "contrast_level": contrast_level,
        "dominant_colors": dominant_colors,
    }


def download_and_analyze(candidate: dict[str, Any], run_dir: Path, source_id: str, timeout: int) -> dict[str, Any]:
    images_dir = run_dir / "source_images"
    thumbs_dir = run_dir / "source_thumbnails"
    images_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    image_url = candidate["image_url"]
    try:
        parsed = urlparse(image_url)
        if parsed.scheme == "file":
            raw = Path(parsed.path).read_bytes()
        elif parsed.scheme in {"http", "https"}:
            request = Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
        else:
            raw = Path(image_url).read_bytes()
        with Image.open(BytesIO(raw)) as image:
            rgb = image.convert("RGBA").convert("RGB") if image.mode == "P" and "transparency" in image.info else image.convert("RGB")
            stats = image_stats(rgb)
            image_path = images_dir / f"{source_id}.jpg"
            thumb_path = thumbs_dir / f"{source_id}.jpg"
            rgb.save(image_path, "JPEG", quality=88, optimize=True)
            thumb = rgb.copy()
            thumb.thumbnail((520, 650), Image.Resampling.LANCZOS)
            thumb.save(thumb_path, "JPEG", quality=82, optimize=True)
        return {
            "download_status": "ok",
            "local_image_path": as_project_path(image_path),
            "thumbnail_path": as_project_path(thumb_path),
            "html_thumbnail_path": thumb_path.relative_to(run_dir).as_posix(),
            **stats,
        }
    except Exception as error:  # noqa: BLE001 - record per-image collection failures.
        return {"download_status": "failed", "download_error": str(error)}


def infer_source_tags(candidate: dict[str, Any], stats: dict[str, Any]) -> dict[str, Any]:
    text = " ".join([candidate.get("image_url", ""), candidate.get("page_url", ""), candidate.get("context", "")]).lower()
    category = candidate.get("category") or classify_candidate(text)
    visual_tags: list[str] = []
    commerce_tags: list[str] = []
    if stats.get("brightness_level") == "dark":
        visual_tags.append("dark_mood")
    elif stats.get("brightness_level") == "bright":
        visual_tags.append("bright_natural")
    if stats.get("contrast_level") == "high":
        visual_tags.append("high_contrast")
    if stats.get("orientation") == "portrait":
        visual_tags.append("portrait_frame")
    elif stats.get("orientation") == "landscape":
        visual_tags.append("wide_hero")

    if any(word in text for word in ["sport", "active", "swim", "outdoor", "ski", "run"]):
        cut_type = "sports_active_cut"
        visual_tags.extend(["sports_active", "dynamic_pose"])
        commerce_tags.extend(["fit_visible", "shortform_ready"])
    elif any(word in text for word in ["detail", "pattern", "fabric", "texture", "close"]):
        cut_type = "detail_or_pattern_cut"
        visual_tags.extend(["close_up", "detail_focus"])
        commerce_tags.extend(["sns_detail_combo", "product_focus"])
    elif category == "product":
        cut_type = "product_object_cut"
        visual_tags.extend(["product_focus", "object_still_life"])
        commerce_tags.extend(["detail_page_top", "product_focus"])
    elif any(word in text for word in ["season", "holiday", "summer", "winter", "resort", "lifestyle"]):
        cut_type = "seasonal_lifestyle_cut"
        visual_tags.extend(["seasonal_mood", "lifestyle_context"])
        commerce_tags.extend(["season_campaign", "sns_hook"])
    elif category == "campaign_collaboration":
        cut_type = "campaign_key_visual"
        visual_tags.extend(["campaign_mood", "brand_asset"])
        commerce_tags.extend(["sns_hook", "brand_asset"])
    else:
        cut_type = "model_styling_cut"
        visual_tags.extend(["model_styling"])
        commerce_tags.extend(["fit_visible", "lookbook"])

    return {
        "source_category": category,
        "cut_type": cut_type,
        "cut_type_label": CUT_TYPE_LABELS.get(cut_type, "미분류"),
        "visual_tags": sorted(dict.fromkeys(visual_tags)),
        "commerce_tags": sorted(dict.fromkeys(commerce_tags)),
    }


def build_source_records(candidates: list[dict[str, Any]], run_dir: Path, max_downloads: int, timeout: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates[:max_downloads], start=1):
        source_id = f"B{index:03d}"
        stats = download_and_analyze(candidate, run_dir, source_id, timeout)
        tags = infer_source_tags(candidate, stats)
        if stats.get("download_status") == "ok" and min(stats.get("width", 0), stats.get("height", 0)) < 160:
            stats["download_status"] = "skipped_small_image"
            stats["download_error"] = "이미지가 너무 작아 브랜드 무드 후보에서 제외"
        records.append(
            {
                "source_image_id": source_id,
                "image_url": candidate["image_url"],
                "page_url": candidate["page_url"],
                "origin_page_url": candidate.get("origin_page_url", ""),
                "source": candidate["source"],
                "context": candidate.get("context", ""),
                "candidate_score": candidate["candidate_score"],
                "local_source_path": candidate.get("local_source_path", ""),
                "gallery_dl_metadata_path": candidate.get("gallery_dl_metadata_path", ""),
                "instagram_username": candidate.get("instagram_username", ""),
                "instagram_post_shortcode": candidate.get("instagram_post_shortcode", ""),
                "instagram_post_date": candidate.get("instagram_post_date", ""),
                "instagram_media_number": candidate.get("instagram_media_number", ""),
                "source_order": candidate.get("source_order", 999999),
                **tags,
                **stats,
            }
        )
    return records


def is_usable_source_record(record: dict[str, Any]) -> bool:
    return (
        record.get("download_status") == "ok"
        and int(record.get("width") or 0) >= 160
        and int(record.get("height") or 0) >= 160
    )


def select_source_images(
    records: list[dict[str, Any]],
    category: str,
    count: int,
    excluded_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    exact = [record for record in records if record.get("source_category") == category]
    if category == "campaign_collaboration":
        exact.extend(record for record in records if record.get("cut_type") in {"campaign_key_visual", "seasonal_lifestyle_cut"})
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    usable_exact = [record for record in exact if is_usable_source_record(record)]

    def source_preference(record: dict[str, Any]) -> int:
        if category == "product":
            page_url = record.get("page_url", "")
            if record.get("source") == "gallery-dl-instagram":
                return 3
            if "/product/" in page_url and "/product/list" not in page_url:
                return 0
            if "/product/list" in page_url or "cate_no=" in page_url:
                return 1
            return 2
        if category == "campaign_collaboration":
            return 0 if record.get("source") == "gallery-dl-instagram" else 1
        return 0

    for record in sorted(
        usable_exact,
        key=lambda item: (
            source_preference(item),
            -item.get("candidate_score", 0),
            item.get("source_order", 999999),
            item["source_image_id"],
        ),
    ):
        if record["source_image_id"] in seen or record["source_image_id"] in excluded_ids:
            continue
        deduped.append(record)
        seen.add(record["source_image_id"])
        if len(deduped) >= count:
            return deduped[:count]
    return deduped[:count]


def summarize_brand(
    brand_slug: str,
    urls: list[str],
    pages: list[dict[str, Any]],
    warnings: list[str],
    records: list[dict[str, Any]],
    product_images: list[dict[str, Any]],
    campaign_images: list[dict[str, Any]],
    portfolio_records: list[dict[str, Any]],
) -> dict[str, Any]:
    cut_counts = Counter(record.get("cut_type", "unknown") for record in product_images + campaign_images)
    visual_counts = Counter(tag for record in product_images + campaign_images for tag in record.get("visual_tags", []))
    commerce_counts = Counter(tag for record in product_images + campaign_images for tag in record.get("commerce_tags", []))
    brightness_counts = Counter(record.get("brightness_level", "unknown") for record in product_images + campaign_images)
    portfolio_cut_types = {record.get("cut_type", "unknown") for record in portfolio_records}
    missing_cut_types = [cut_type for cut_type in CUT_TYPE_ORDER if cut_type in portfolio_cut_types and cut_type not in cut_counts]
    if not missing_cut_types:
        missing_cut_types = [cut_type for cut_type, _count in Counter(record.get("cut_type", "unknown") for record in portfolio_records).most_common(4)]
    strongest_cut = cut_counts.most_common(1)[0][0] if cut_counts else "unknown"
    strongest_brightness = brightness_counts.most_common(1)[0][0] if brightness_counts else "unknown"
    return {
        "brand_slug": brand_slug,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_urls": urls,
        "pages_scanned": pages,
        "warnings": warnings,
        "candidate_image_count": len(records),
        "selected_product_count": len(product_images),
        "selected_campaign_count": len(campaign_images),
        "selected_product_image_ids": [record["source_image_id"] for record in product_images],
        "selected_campaign_image_ids": [record["source_image_id"] for record in campaign_images],
        "observed_cut_type_counts": dict(cut_counts),
        "observed_visual_tag_counts": dict(visual_counts.most_common()),
        "observed_commerce_tag_counts": dict(commerce_counts.most_common()),
        "brightness_counts": dict(brightness_counts),
        "missing_cut_types": missing_cut_types,
        "missing_cut_type_labels": [CUT_TYPE_LABELS.get(cut_type, cut_type) for cut_type in missing_cut_types],
        "mood_summary": (
            f"수집 이미지 기준 가장 강한 컷은 {CUT_TYPE_LABELS.get(strongest_cut, strongest_cut)}이고, "
            f"전체 톤은 {strongest_brightness} 계열로 관찰됨."
        ),
    }


def overlap_score(left: list[str], right: list[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def source_portfolio_similarity(source: dict[str, Any], portfolio: dict[str, Any]) -> float:
    score = 0.0
    if source.get("cut_type") == portfolio.get("cut_type"):
        score += 0.32
    score += 0.24 * overlap_score(source.get("visual_tags", []), portfolio.get("visual_tags", []))
    score += 0.18 * overlap_score(source.get("commerce_tags", []), portfolio.get("commerce_tags", []))
    if source.get("orientation") and source.get("orientation") == portfolio.get("orientation"):
        score += 0.08
    if source.get("brightness_level") and source.get("brightness_level") == portfolio.get("brightness_level"):
        score += 0.08
    if source.get("contrast_level") and source.get("contrast_level") == portfolio.get("contrast_level"):
        score += 0.05
    return score


def best_source_reference(portfolio: dict[str, Any], sources: list[dict[str, Any]]) -> tuple[list[str], float]:
    ranked = sorted(
        ((source["source_image_id"], source_portfolio_similarity(source, portfolio)) for source in sources),
        key=lambda item: item[1],
        reverse=True,
    )
    return [source_id for source_id, score in ranked[:2] if score > 0], ranked[0][1] if ranked else 0.0


def source_reference_payload(source: dict[str, Any], portfolio: dict[str, Any]) -> dict[str, Any]:
    shared_visual = sorted(set(source.get("visual_tags", [])) & set(portfolio.get("visual_tags", [])))
    shared_commerce = sorted(set(source.get("commerce_tags", [])) & set(portfolio.get("commerce_tags", [])))
    dimensions: list[str] = []
    if source.get("cut_type") == portfolio.get("cut_type"):
        dimensions.append(f"컷 유형 일치: {source.get('cut_type_label')}")
    if shared_visual:
        dimensions.append("공통 비주얼 태그: " + ", ".join(shared_visual[:4]))
    if shared_commerce:
        dimensions.append("공통 커머스 역할: " + ", ".join(shared_commerce[:4]))
    if source.get("orientation") == portfolio.get("orientation") and source.get("orientation"):
        dimensions.append(f"프레임 방향 일치: {source.get('orientation')}")
    if source.get("brightness_level") == portfolio.get("brightness_level") and source.get("brightness_level"):
        dimensions.append(f"밝기 톤 일치: {source.get('brightness_level')}")
    if not dimensions:
        dimensions.append("컷/태그 직접 일치는 약하지만 전체 브랜드 관찰값과의 거리로 추천됨")
    return {
        "source_image_id": source.get("source_image_id"),
        "source": source.get("source"),
        "source_category": source.get("source_category"),
        "cut_type": source.get("cut_type"),
        "cut_type_label": source.get("cut_type_label"),
        "page_url": source.get("page_url"),
        "thumbnail_path": source.get("thumbnail_path"),
        "html_thumbnail_path": source.get("html_thumbnail_path"),
        "visual_tags": source.get("visual_tags", []),
        "commerce_tags": source.get("commerce_tags", []),
        "comparison_dimensions": dimensions[:5],
    }


def similar_reasons(portfolio: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    reasons = []
    cut_label = portfolio.get("cut_type_label") or CUT_TYPE_LABELS.get(portfolio.get("cut_type"), portfolio.get("cut_type"))
    if portfolio.get("cut_type") in summary.get("observed_cut_type_counts", {}):
        reasons.append(f"브랜드 수집 이미지에서도 {cut_label} 계열이 확인됨")
    shared_visual = set(portfolio.get("visual_tags", [])) & set(summary.get("observed_visual_tag_counts", {}).keys())
    if shared_visual:
        reasons.append("겹치는 비주얼 태그: " + ", ".join(sorted(shared_visual)[:3]))
    shared_commerce = set(portfolio.get("commerce_tags", [])) & set(summary.get("observed_commerce_tag_counts", {}).keys())
    if shared_commerce:
        reasons.append("겹치는 커머스 역할: " + ", ".join(sorted(shared_commerce)[:3]))
    if not reasons:
        reasons.append("브랜드의 현재 이미지 톤과 무리 없이 이어지는 포트폴리오")
    return reasons[:3]


def whitespace_reasons(portfolio: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    cut_label = portfolio.get("cut_type_label") or CUT_TYPE_LABELS.get(portfolio.get("cut_type"), portfolio.get("cut_type"))
    reasons = []
    if portfolio.get("cut_type") in summary.get("missing_cut_types", []):
        reasons.append(f"수집 이미지에서 상대적으로 비어 있는 {cut_label} 방향을 보완")
    absent_visual = set(portfolio.get("visual_tags", [])) - set(summary.get("observed_visual_tag_counts", {}).keys())
    if absent_visual:
        reasons.append("브랜드 이미지에 적게 보이는 태그: " + ", ".join(sorted(absent_visual)[:3]))
    absent_commerce = set(portfolio.get("commerce_tags", [])) - set(summary.get("observed_commerce_tag_counts", {}).keys())
    if absent_commerce:
        reasons.append("새로 제안 가능한 커머스 역할: " + ", ".join(sorted(absent_commerce)[:3]))
    if not reasons:
        reasons.append("현재 브랜드 이미지와 다른 촬영 역할을 제안할 수 있는 포트폴리오")
    return reasons[:3]


def portfolio_strength(portfolio: dict[str, Any]) -> float:
    score = 0.0
    if "source_metadata_only" not in portfolio.get("visual_tags", []):
        score += 0.08
    if portfolio.get("review_status") == "needs_review":
        score -= 0.02
    if portfolio.get("dominant_colors"):
        score += 0.04
    return score


def select_diverse(scored: list[dict[str, Any]], limit: int, excluded_ids: set[str] | None = None) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    selected: list[dict[str, Any]] = []
    project_counts: Counter[str] = Counter()
    cut_counts: Counter[str] = Counter()
    reference_counts: Counter[str] = Counter()
    deferred: list[dict[str, Any]] = []

    def can_select(item: dict[str, Any], enforce_reference_diversity: bool) -> bool:
        record = item["portfolio"]
        portfolio_id = record.get("portfolio_id", "")
        project_id = record.get("project_group_id", portfolio_id)
        cut_type = record.get("cut_type", "unknown")
        references = item.get("references", [])
        if portfolio_id in excluded_ids:
            return False
        if project_counts[project_id] >= 2:
            return False
        if cut_counts[cut_type] >= 3:
            return False
        if enforce_reference_diversity and references and any(reference_counts[reference] >= 2 for reference in references):
            return False
        return True

    def add_item(item: dict[str, Any]) -> None:
        record = item["portfolio"]
        portfolio_id = record.get("portfolio_id", "")
        project_id = record.get("project_group_id", portfolio_id)
        cut_type = record.get("cut_type", "unknown")
        selected.append(item)
        project_counts[project_id] += 1
        cut_counts[cut_type] += 1
        for reference in item.get("references", []):
            reference_counts[reference] += 1

    for item in sorted(scored, key=lambda row: row["score"], reverse=True):
        if can_select(item, enforce_reference_diversity=True):
            add_item(item)
        else:
            deferred.append(item)
        if len(selected) >= limit:
            break

    if len(selected) < limit:
        already_selected = {item["portfolio"].get("portfolio_id", "") for item in selected}
        for item in deferred:
            portfolio_id = item["portfolio"].get("portfolio_id", "")
            if portfolio_id in already_selected:
                continue
            if not can_select(item, enforce_reference_diversity=False):
                continue
            add_item(item)
            already_selected.add(portfolio_id)
            if len(selected) >= limit:
                break
    return selected


def recommendation_payload(
    item: dict[str, Any],
    rank: int,
    recommendation_type: str,
    references: list[str],
    summary: dict[str, Any],
    run_dir: Path,
    source_lookup: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    portfolio = item["portfolio"]
    reasons = similar_reasons(portfolio, summary) if recommendation_type == "similar" else whitespace_reasons(portfolio, summary)
    label = "유사" if recommendation_type == "similar" else "보완"
    reference_images = [
        source_reference_payload(source_lookup[source_id], portfolio)
        for source_id in references
        if source_lookup and source_id in source_lookup
    ]
    return {
        "rank": rank,
        "recommendation_type": recommendation_type,
        "label": label,
        "score": round(item["score"], 2),
        "portfolio_id": portfolio.get("portfolio_id"),
        "project_group_id": portfolio.get("project_group_id"),
        "file_name": portfolio.get("file_name"),
        "client_or_project": portfolio.get("client_or_project"),
        "group": portfolio.get("group"),
        "cut_type": portfolio.get("cut_type"),
        "cut_type_label": portfolio.get("cut_type_label"),
        "visual_tags": portfolio.get("visual_tags", []),
        "commerce_tags": portfolio.get("commerce_tags", []),
        "proposal_use": portfolio.get("proposal_use"),
        "image_path": portfolio.get("asset_path"),
        "thumbnail_path": portfolio.get("thumbnail_path"),
        "html_thumbnail_path": to_run_relative(run_dir, portfolio.get("thumbnail_path")),
        "brand_reference_image_ids": references,
        "brand_reference_images": reference_images,
        "reasons": reasons,
        "proposal_sentence": f"{label} 방향으로 {portfolio.get('proposal_use', '브랜드 제안에 활용')}할 수 있습니다.",
        "review_status": "recommended_needs_human_review",
    }


def match_portfolio(
    portfolio_records: list[dict[str, Any]],
    source_records: list[dict[str, Any]],
    summary: dict[str, Any],
    run_dir: Path,
    limit: int,
) -> dict[str, Any]:
    observed_cuts = set(summary.get("observed_cut_type_counts", {}).keys())
    observed_visual = set(summary.get("observed_visual_tag_counts", {}).keys())
    observed_commerce = set(summary.get("observed_commerce_tag_counts", {}).keys())
    missing_cuts = set(summary.get("missing_cut_types", []))
    similar_scored: list[dict[str, Any]] = []
    whitespace_scored: list[dict[str, Any]] = []
    selected_sources = source_records
    source_lookup = {source["source_image_id"]: source for source in source_records}
    for portfolio in portfolio_records:
        refs, best_ref_score = best_source_reference(portfolio, selected_sources)
        visual_overlap = overlap_score(portfolio.get("visual_tags", []), list(observed_visual))
        commerce_overlap = overlap_score(portfolio.get("commerce_tags", []), list(observed_commerce))
        cut_match = 1.0 if portfolio.get("cut_type") in observed_cuts else 0.0
        similar_score = 100 * (0.44 * best_ref_score + 0.22 * visual_overlap + 0.18 * commerce_overlap + 0.12 * cut_match + portfolio_strength(portfolio))
        similar_scored.append({"portfolio": portfolio, "score": similar_score, "references": refs})

        missing_fit = 1.0 if portfolio.get("cut_type") in missing_cuts else 0.0
        visual_newness = 1.0 - overlap_score(portfolio.get("visual_tags", []), list(observed_visual))
        commerce_newness = 1.0 - overlap_score(portfolio.get("commerce_tags", []), list(observed_commerce))
        guardrail = 0.55 + min(visual_overlap + commerce_overlap, 0.45)
        whitespace_score = 100 * (
            0.36 * missing_fit
            + 0.22 * visual_newness
            + 0.18 * commerce_newness
            + 0.14 * guardrail
            + portfolio_strength(portfolio)
        )
        whitespace_scored.append({"portfolio": portfolio, "score": whitespace_score, "references": refs})

    similar_selected = select_diverse(similar_scored, limit)
    excluded = {item["portfolio"].get("portfolio_id", "") for item in similar_selected}
    whitespace_selected = select_diverse(whitespace_scored, limit, excluded)
    return {
        "similar_recommendations": [
            recommendation_payload(item, rank, "similar", item.get("references", []), summary, run_dir, source_lookup)
            for rank, item in enumerate(similar_selected, start=1)
        ],
        "whitespace_recommendations": [
            recommendation_payload(item, rank, "whitespace", item.get("references", []), summary, run_dir, source_lookup)
            for rank, item in enumerate(whitespace_selected, start=1)
        ],
    }


def e(value: Any) -> str:
    return html.escape(str(value or ""))


def short_text(value: Any, limit: int = 96) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def url_label(url: str) -> str:
    if not url:
        return "출처 없음"
    parsed = urlparse(url)
    if parsed.netloc:
        path = parsed.path.rstrip("/") or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.netloc}{path}{query}"
    return url


def noisy_context(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return True
    noisy_tokens = {"thumbnail-prd", "image_big", "prdimg", "displaynone", "xans-record"}
    return all(part in noisy_tokens for part in text.split())


def product_title_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if "product" not in parts:
        return ""
    product_index = parts.index("product")
    if product_index + 1 >= len(parts):
        return ""
    slug = parts[product_index + 1]
    title = re.sub(r"[-_]+", " ", slug).strip()
    return title.title() if title else ""


def source_kind_label(record: dict[str, Any]) -> str:
    if record.get("source") == "gallery-dl-instagram":
        return "Instagram 게시글"
    page_url = record.get("page_url", "")
    if "/product/" in page_url:
        return "자사몰 상품 페이지"
    if "collection" in page_url or "campaign" in page_url or "project" in page_url:
        return "자사몰 캠페인 페이지"
    return "자사몰 수집 페이지"


def source_display_title(record: dict[str, Any]) -> str:
    if record.get("source") == "gallery-dl-instagram":
        date = str(record.get("instagram_post_date") or "").split(" ")[0]
        shortcode = record.get("instagram_post_shortcode") or record.get("source_image_id")
        return " · ".join(part for part in [date, str(shortcode)] if part)
    product_title = product_title_from_url(record.get("page_url", ""))
    if product_title:
        return product_title
    context = "" if noisy_context(record.get("context")) else short_text(record.get("context"), 54)
    if context:
        return context
    return url_label(record.get("page_url", ""))


def tag_chips(tags: list[str], limit: int = 4) -> str:
    return "".join(
        f"<span class=\"chip\" data-tooltip=\"{e(tag_explanation(tag))}\" aria-label=\"{e(tag_explanation(tag))}\">{e(tag)}</span>"
        for tag in tags[:limit]
    )


def tag_explanation(tag: str) -> str:
    if tag in CUT_TYPE_LABELS:
        return CUT_TYPE_DESCRIPTIONS.get(tag, CUT_TYPE_LABELS[tag])
    return TAG_DEFINITIONS.get(tag, f"{tag}: 내부 메타 태그입니다. 실제 검수 과정에서 의미를 더 구체화할 수 있습니다.")


def source_card(record: dict[str, Any], kind: str) -> str:
    image_path = record.get("html_thumbnail_path") or ""
    link = record.get("page_url") or record.get("image_url") or "#"
    title = record.get("source_image_id") or "source"
    is_product = kind == "product-source"
    caption = "" if is_product or noisy_context(record.get("context")) else short_text(record.get("context"), 120)
    caption_html = f"<p>{e(caption)}</p>" if caption else ""
    meta = " · ".join(
        part
        for part in [
            source_kind_label(record),
            record.get("cut_type_label"),
            record.get("source_image_id"),
        ]
        if part
    )
    return f"""
      <article class="source-card {kind}">
        <a class="image-link" href="{e(link)}" target="_blank" rel="noreferrer" title="원본 열기">
          <img src="{e(image_path)}" alt="{e(title)}">
        </a>
        <div class="source-body">
          <div class="eyebrow">{e(meta)}</div>
          <strong>{e(source_display_title(record))}</strong>
          {caption_html}
          <span class="source-hint">이미지 클릭 시 원본 열기</span>
        </div>
      </article>
    """


def html_card_grid(records: list[dict[str, Any]], kind: str, empty_message: str) -> str:
    if not records:
        return f"<p class=\"empty\">{html.escape(empty_message)}</p>"
    return "".join(source_card(record, kind) for record in records)


def source_reference_tile(source: dict[str, Any]) -> str:
    link = source.get("page_url") or "#"
    return f"""
      <a class="reference-tile" href="{e(link)}" target="_blank" rel="noreferrer">
        <img src="{e(source.get('html_thumbnail_path'))}" alt="{e(source.get('source_image_id'))}">
        <span>{e(source.get('source_image_id'))} · {e(source.get('cut_type_label'))}</span>
      </a>
    """


def comparison_notes(recommendation: dict[str, Any], references: list[dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    for source in references:
        for note in source.get("comparison_dimensions", []):
            if note not in notes:
                notes.append(note)
    for reason in recommendation.get("reasons", []):
        if reason not in notes:
            notes.append(str(reason))
    return notes[:5]


def recommendation_compare_card(
    recommendation: dict[str, Any],
    source_lookup: dict[str, dict[str, Any]],
    recommendation_type: str,
) -> str:
    references = [
        source_lookup[source_id]
        for source_id in recommendation.get("brand_reference_image_ids", [])
        if source_id in source_lookup
    ]
    ref_html = "".join(source_reference_tile(source) for source in references) or "<p class=\"empty mini\">직접 연결된 브랜드 기준 이미지가 없습니다.</p>"
    notes = comparison_notes(recommendation, recommendation.get("brand_reference_images", []))
    note_html = "".join(f"<li>{e(note)}</li>" for note in notes)
    tag_html = tag_chips(recommendation.get("visual_tags", []), 4) + tag_chips(recommendation.get("commerce_tags", []), 3)
    heading = "브랜드 이미지와 이어지는 근거" if recommendation_type == "similar" else "새롭게 제안할 수 있는 이유"
    review_hint = (
        "검수 포인트: 실제 이미지에서도 포즈, 톤, 컷 역할이 같은지 확인"
        if recommendation_type == "similar"
        else "검수 포인트: 브랜드가 아직 덜 쓰는 컷인지, 제안서에 새 방향으로 설득 가능한지 확인"
    )
    return f"""
      <article class="match-card {recommendation_type}">
        <div class="match-brand">
          <div class="eyebrow">브랜드 기준 이미지</div>
          <div class="reference-strip">{ref_html}</div>
        </div>
        <div class="match-portfolio">
          <img src="{e(recommendation.get('html_thumbnail_path'))}" alt="{e(recommendation.get('portfolio_id'))}">
          <div>
            <div class="match-title">
              <strong>{e(recommendation.get('portfolio_id'))}</strong>
              <span class="score">{e(recommendation.get('score'))}</span>
            </div>
            <p>{e(recommendation.get('cut_type_label'))} · {e(recommendation.get('proposal_use'))}</p>
            <div class="chips">{tag_html}</div>
          </div>
        </div>
        <div class="match-reason">
          <div class="eyebrow">{heading}</div>
          <ul>{note_html}</ul>
          <p class="review-hint">{e(review_hint)}</p>
        </div>
      </article>
    """


def count_chips(counts: dict[str, Any], labels: dict[str, str] | None = None, limit: int = 5) -> str:
    labels = labels or {}
    rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return "".join(
        f"<span class=\"count-chip\" data-tooltip=\"{e(tag_explanation(key))}\" aria-label=\"{e(tag_explanation(key))}\">{e(labels.get(key, key))}<strong>{e(value)}</strong></span>"
        for key, value in rows
    )


def insight_panel(summary: dict[str, Any]) -> str:
    cut_counts = summary.get("observed_cut_type_counts", {})
    visual_counts = summary.get("observed_visual_tag_counts", {})
    commerce_counts = summary.get("observed_commerce_tag_counts", {})
    missing_labels = summary.get("missing_cut_type_labels", [])
    dominant, dominant_count = sorted(cut_counts.items(), key=lambda item: item[1], reverse=True)[0] if cut_counts else ("unknown", 0)
    dominant_label = CUT_TYPE_LABELS.get(dominant, dominant)
    missing_text = ", ".join(str(label) for label in missing_labels[:4]) or "추가 검수 필요"
    total = sum(cut_counts.values()) or summary.get("selected_product_count", 0) + summary.get("selected_campaign_count", 0)
    return f"""
      <section class="insight-panel">
        <div class="insight-copy">
          <div class="eyebrow">현재 브랜드 관찰</div>
          <h2>{e(dominant_label)} {e(dominant_count)}장 중심입니다.</h2>
          <p>선택 후보 {e(total)}장 중 가장 많이 보이는 컷을 기준으로 현재 브랜드 언어를 잡았습니다. 덜 보이는 방향은 {e(missing_text)}입니다.</p>
        </div>
        <div class="insight-groups">
          <div><strong>컷 유형</strong><div>{count_chips(cut_counts, CUT_TYPE_LABELS, 3)}</div></div>
          <div><strong>비주얼 태그</strong><div>{count_chips(visual_counts, limit=4)}</div></div>
          <div><strong>커머스 역할</strong><div>{count_chips(commerce_counts, limit=4)}</div></div>
        </div>
      </section>
    """


def collect_guide_tags(summary: dict[str, Any], matches: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for key in summary.get("observed_cut_type_counts", {}).keys():
        tags.append(key)
    for key in summary.get("observed_visual_tag_counts", {}).keys():
        tags.append(key)
    for key in summary.get("observed_commerce_tag_counts", {}).keys():
        tags.append(key)
    for group in ["similar_recommendations", "whitespace_recommendations"]:
        for recommendation in matches.get(group, []):
            tags.extend(recommendation.get("visual_tags", []))
            tags.extend(recommendation.get("commerce_tags", []))
            if recommendation.get("cut_type"):
                tags.append(recommendation["cut_type"])
    return list(dict.fromkeys(tags))[:28]


def tag_guide_panel(summary: dict[str, Any], matches: dict[str, Any]) -> str:
    tags = collect_guide_tags(summary, matches)
    rows = "".join(
        f"<div><code>{e(tag)}</code><span>{e(tag_explanation(tag))}</span></div>"
        for tag in tags
    )
    return f"""
      <details class="tag-guide">
        <summary>태그 설명 보기</summary>
        <p>태그는 이미지 통계, URL/캡션 문맥, 기존 포트폴리오 메타를 조합한 1차 분류입니다. 칩에 마우스를 올리면 지연 없이 같은 설명을 볼 수 있습니다.</p>
        <div class="tag-guide-grid">{rows}</div>
      </details>
    """


def strategy_panel() -> str:
    return """
      <section class="strategy-panel">
        <div>
          <div class="eyebrow">유사 포트폴리오 추천 의도</div>
          <h2>대표무드형 매칭을 기본으로 사용합니다.</h2>
          <p>브랜드 후보 20장 각각에 1장씩 대응시키기보다, 상품/캠페인 전체에서 반복되는 컷 유형, 태그, 밝기, 프레임을 읽고 바로 이어질 수 있는 포트폴리오 10장을 고릅니다. 같은 브랜드 기준 이미지가 과도하게 반복되지 않도록 제한합니다.</p>
        </div>
        <div class="strategy-modes">
          <div class="active"><strong>현재 추천</strong><span>대표무드형: 영업 제안서에 가장 안정적인 한 세트</span></div>
          <div><strong>추가 가능</strong><span>1:1 커버리지형: 브랜드 기준 이미지마다 가장 가까운 포트폴리오 1장</span></div>
          <div><strong>추가 가능</strong><span>색감우선형: 컬러/밝기/대비 중심으로 톤을 맞추는 방식</span></div>
        </div>
      </section>
    """


def write_viewer(run_dir: Path, summary: dict[str, Any], source_records: list[dict[str, Any]], matches: dict[str, Any]) -> Path:
    product_ids = set(summary.get("selected_product_image_ids", []))
    campaign_ids = set(summary.get("selected_campaign_image_ids", []))
    product_cards = [record for record in source_records if record["source_image_id"] in product_ids]
    campaign_cards = [record for record in source_records if record["source_image_id"] in campaign_ids]
    source_lookup = {record["source_image_id"]: record for record in source_records}
    similar_cards = "".join(
        recommendation_compare_card(record, source_lookup, "similar")
        for record in matches.get("similar_recommendations", [])
    )
    whitespace_cards = "".join(
        recommendation_compare_card(record, source_lookup, "whitespace")
        for record in matches.get("whitespace_recommendations", [])
    )
    html_text = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(summary['brand_slug'])} Brand Portfolio Match</title>
  <link rel="icon" href="data:,">
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif; background: #fbfaf7; color: #16120f; line-height: 1.6; }}
    main {{ width: min(1360px, calc(100% - 40px)); margin: 0 auto; padding: 48px 0 72px; }}
    header {{ padding: 48px 0 28px; border-bottom: 1px solid rgba(29,24,20,.12); }}
    h1 {{ font-family: Georgia, "Times New Roman", serif; font-size: clamp(2.4rem, 5vw, 4.7rem); font-weight: 400; line-height: 1.05; margin: 0 0 18px; overflow-wrap: anywhere; }}
    h2 {{ font-size: 1.65rem; margin: 0; line-height: 1.25; overflow-wrap: anywhere; }}
    section {{ margin-top: 52px; }}
    .summary {{ color: #685f56; max-width: 900px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 24px; }}
    .metric, .source-card, .match-card, .insight-panel {{ background: #fff; border: 1px solid rgba(29,24,20,.1); border-radius: 12px; overflow: hidden; }}
    .metric {{ padding: 18px; }}
    .metric strong {{ display: block; font-size: 1.6rem; }}
    .section-head {{ display: flex; justify-content: space-between; align-items: end; gap: 20px; margin-bottom: 16px; }}
    .section-head p {{ margin: 0; max-width: 620px; color: #685f56; font-size: .95rem; }}
    .source-grid {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 14px; }}
    .source-card img, .match-portfolio img, .reference-tile img {{ width: 100%; object-fit: cover; background: #fff3cf; display: block; }}
    .source-card img {{ aspect-ratio: 4 / 5; }}
    .image-link {{ display: block; color: inherit; text-decoration: none; }}
    .source-body {{ display: grid; grid-template-rows: auto minmax(3.5em, auto) 1fr auto; gap: 8px; padding: 12px; min-height: 184px; }}
    .source-body strong {{ display: block; font-size: .95rem; line-height: 1.35; overflow-wrap: anywhere; }}
    .source-body p {{ margin: 0; color: #685f56; font-size: .82rem; }}
    .source-hint {{ color: #b33b16; font-size: .75rem; }}
    .eyebrow {{ color: #a6461a; font-size: .72rem; font-weight: 700; text-transform: uppercase; margin-bottom: 6px; }}
    .empty {{ margin: 0; padding: 18px; border: 1px solid rgba(29,24,20,.1); background: #fff; color: #685f56; border-radius: 8px; }}
    .empty.mini {{ font-size: .82rem; }}
    .score {{ color: #fff; background: #ff5a1f; border-radius: 6px; padding: 2px 6px; font-size: .75rem; }}
    .match-list {{ display: grid; gap: 16px; }}
    .match-card {{ display: grid; grid-template-columns: minmax(220px, .9fr) minmax(220px, .9fr) minmax(260px, 1.1fr); gap: 16px; padding: 16px; align-items: stretch; }}
    .reference-strip {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }}
    .reference-tile {{ color: inherit; text-decoration: none; border: 1px solid rgba(29,24,20,.1); border-radius: 8px; overflow: hidden; background: #fbfaf7; }}
    .reference-tile img {{ aspect-ratio: 4 / 5; }}
    .reference-tile span {{ display: block; padding: 8px; font-size: .76rem; color: #685f56; }}
    .match-portfolio {{ display: grid; grid-template-columns: 42% 1fr; gap: 12px; align-items: start; }}
    .match-portfolio img {{ aspect-ratio: 4 / 5; border-radius: 8px; border: 1px solid rgba(29,24,20,.1); }}
    .match-title {{ display: flex; justify-content: space-between; gap: 8px; align-items: start; min-width: 0; }}
    .match-portfolio p, .match-reason p {{ color: #685f56; font-size: .86rem; margin: 8px 0; }}
    .match-reason ul {{ margin: 0 0 0 18px; padding: 0; color: #332b24; font-size: .9rem; }}
    .review-hint {{ border-top: 1px solid rgba(29,24,20,.1); padding-top: 10px; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
    .chip {{ display: inline-flex; border: 1px solid rgba(29,24,20,.12); border-radius: 6px; padding: 3px 6px; color: #685f56; font-size: .72rem; background: #fff8e7; cursor: help; }}
    .insight-panel, .strategy-panel {{ display: grid; grid-template-columns: .78fr 1.22fr; gap: 20px; padding: 22px; }}
    .insight-panel p, .strategy-panel p, .tag-guide p {{ color: #685f56; margin: 10px 0 0; }}
    .insight-copy h2 {{ font-size: 1.4rem; }}
    .insight-groups {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }}
    .insight-groups > div {{ display: grid; gap: 8px; }}
    .count-chip {{ display: inline-flex; justify-content: space-between; gap: 10px; align-items: center; margin: 0 6px 6px 0; padding: 6px 8px; border-radius: 8px; background: #f4eee2; color: #332b24; font-size: .78rem; cursor: help; }}
    .count-chip strong {{ color: #b33b16; }}
    .strategy-modes {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
    .strategy-modes div {{ border: 1px solid rgba(29,24,20,.1); border-radius: 8px; padding: 12px; background: #fbfaf7; }}
    .strategy-modes .active {{ background: #fff3cf; border-color: rgba(255,90,31,.35); }}
    .strategy-modes strong {{ display: block; margin-bottom: 4px; }}
    .strategy-modes span {{ color: #685f56; font-size: .82rem; }}
    .source-card, .match-card, .insight-panel, .strategy-panel, .tag-guide, .match-portfolio, .match-brand, .match-reason {{ min-width: 0; }}
    .tag-guide {{ margin-top: 24px; background: #fff; border: 1px solid rgba(29,24,20,.1); border-radius: 12px; padding: 16px; }}
    .tag-guide summary {{ cursor: pointer; font-weight: 700; color: #a6461a; }}
    .tag-guide-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 16px; margin-top: 14px; }}
    .tag-guide-grid div {{ display: grid; grid-template-columns: 150px 1fr; gap: 10px; align-items: start; border-top: 1px solid rgba(29,24,20,.08); padding-top: 8px; }}
    .tag-guide-grid code {{ color: #b33b16; white-space: normal; overflow-wrap: anywhere; }}
    .instant-tooltip {{ position: fixed; z-index: 50; max-width: min(360px, calc(100vw - 24px)); padding: 9px 11px; border: 1px solid rgba(29,24,20,.16); border-radius: 8px; background: rgba(22,18,15,.94); color: #fffaf0; font-size: .78rem; line-height: 1.45; box-shadow: 0 12px 30px rgba(29,24,20,.18); pointer-events: none; opacity: 0; transform: translate3d(0, 4px, 0); transition: opacity 55ms ease, transform 55ms ease; }}
    .instant-tooltip.visible {{ opacity: 1; transform: translate3d(0, 0, 0); }}
    .stripe {{ height: 14px; border-radius: 8px; background: linear-gradient(90deg, #b92b1f, #f06423, #f5b335, #fff3cf); margin-top: 56px; }}
    @media (max-width: 1100px) {{ .source-grid {{ grid-template-columns: repeat(3, 1fr); }} .match-card {{ grid-template-columns: 1fr; }} .insight-panel, .strategy-panel {{ grid-template-columns: 1fr; }} .insight-groups, .strategy-modes {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 720px) {{ .metrics {{ grid-template-columns: repeat(2, 1fr); }} .section-head {{ display: block; }} .source-grid {{ grid-template-columns: repeat(2, 1fr); }} .match-portfolio {{ grid-template-columns: 1fr; }} .tag-guide-grid {{ grid-template-columns: 1fr; }} .tag-guide-grid div {{ grid-template-columns: 1fr; }} }}
    @media (max-width: 560px) {{ main {{ width: min(100% - 28px, 1360px); }} .source-grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>{html.escape(summary['brand_slug'])} URL 이미지 매칭 결과</h1>
    <p class="summary">{html.escape(summary.get('mood_summary', ''))}</p>
    <div class="metrics">
      <div class="metric"><strong>{summary.get('candidate_image_count', 0)}</strong><span>수집 후보</span></div>
      <div class="metric"><strong>{summary.get('selected_product_count', 0)}</strong><span>상품 이미지</span></div>
      <div class="metric"><strong>{summary.get('selected_campaign_count', 0)}</strong><span>기획전/캠페인</span></div>
      <div class="metric"><strong>{len(summary.get('missing_cut_types', []))}</strong><span>보완 컷 방향</span></div>
    </div>
  </header>
  {tag_guide_panel(summary, matches)}
  <section>
    <div class="section-head">
      <h2>브랜드 상품 이미지 후보</h2>
      <p>이미지를 누르면 수집 기준이 된 자사몰 상품/페이지로 이동합니다. 이 영역은 상품 상세, 상품 리스트, 베스트 상품 맥락을 우선합니다.</p>
    </div>
    <div class="source-grid">{html_card_grid(product_cards, 'product-source', '상품 후보로 분류된 이미지가 부족합니다. 자사몰 상품 URL을 함께 넣으면 이 영역이 채워집니다.')}</div>
  </section>
  <section>
    <div class="section-head">
      <h2>브랜드 기획전/콜라보/프로젝트 후보</h2>
      <p>이미지를 누르면 Instagram 게시글이나 캠페인 페이지로 이동합니다. 게시글 캡션과 컷 태그를 함께 보며 실제 무드 판단을 검수합니다.</p>
    </div>
    <div class="source-grid">{html_card_grid(campaign_cards, 'campaign-source', '기획전/콜라보/프로젝트 후보로 분류된 이미지가 부족합니다. Instagram 폴더나 캠페인 URL을 함께 넣으면 이 영역이 채워집니다.')}</div>
  </section>
  {strategy_panel()}
  <section>
    <div class="section-head">
      <h2>우리 포트폴리오와 유사한 이미지 10개</h2>
      <p>왼쪽은 시스템이 기준으로 삼은 브랜드 이미지, 가운데는 추천된 포트폴리오, 오른쪽은 실제 분류 기준입니다. 이 비교를 보며 태그가 맞는지 계속 다듬습니다.</p>
    </div>
    <div class="match-list">{similar_cards}</div>
  </section>
  {insight_panel(summary)}
  <section>
    <div class="section-head">
      <h2>브랜드에는 부족하지만 우리에게 있는 이미지 10개</h2>
      <p>현재 브랜드가 많이 쓰는 컷과 태그를 기준으로, 상대적으로 비어 있는 촬영 역할을 제안합니다. 콜드메일과 제안서의 핵심 논리로 쓰기 좋은 영역입니다.</p>
    </div>
    <div class="match-list">{whitespace_cards}</div>
  </section>
  <div class="stripe"></div>
</main>
<div class="instant-tooltip" id="instantTooltip" role="tooltip" aria-hidden="true"></div>
<script>
(() => {{
  const tooltip = document.getElementById('instantTooltip');
  const margin = 12;
  let active = null;

  const position = (event) => {{
    if (!active) return;
    const x = event.clientX ?? active.getBoundingClientRect().left;
    const y = event.clientY ?? active.getBoundingClientRect().top;
    const rect = tooltip.getBoundingClientRect();
    let left = x + margin;
    let top = y + margin;
    if (left + rect.width > window.innerWidth - margin) left = x - rect.width - margin;
    if (top + rect.height > window.innerHeight - margin) top = y - rect.height - margin;
    tooltip.style.left = `${{Math.max(margin, left)}}px`;
    tooltip.style.top = `${{Math.max(margin, top)}}px`;
  }};

  const show = (target, event) => {{
    const text = target.dataset.tooltip;
    if (!text) return;
    active = target;
    tooltip.textContent = text;
    tooltip.setAttribute('aria-hidden', 'false');
    tooltip.classList.add('visible');
    position(event);
  }};

  const hide = () => {{
    active = null;
    tooltip.classList.remove('visible');
    tooltip.setAttribute('aria-hidden', 'true');
  }};

  document.addEventListener('pointerover', (event) => {{
    const target = event.target.closest?.('[data-tooltip]');
    if (target && target !== active) show(target, event);
  }}, true);
  document.addEventListener('pointermove', (event) => {{
    if (active) position(event);
  }}, true);
  document.addEventListener('pointerout', (event) => {{
    if (!active) return;
    const next = event.relatedTarget;
    if (!next || !active.contains(next)) hide();
  }}, true);
  document.addEventListener('focusin', (event) => {{
    const target = event.target.closest?.('[data-tooltip]');
    if (target) show(target, event);
  }});
  document.addEventListener('focusout', hide);
  window.addEventListener('scroll', hide, {{ passive: true }});
}})();
</script>
</body>
</html>
"""
    viewer_path = run_dir / "index.html"
    viewer_path.write_text(html_text, encoding="utf-8")
    return viewer_path


def build_run(args: argparse.Namespace) -> dict[str, Any]:
    portfolio_records = load_json(args.portfolio_index)
    if not isinstance(portfolio_records, list):
        raise ValueError("portfolio index must be a JSON list")
    urls = args.url or []
    if args.source_html and not urls:
        urls = [args.base_url or args.source_html.resolve().as_uri()]
    instagram_folders = args.instagram_folder or []
    if args.brand_slug:
        brand_slug = args.brand_slug
    elif urls:
        brand_slug = slugify(urlparse(urls[0]).netloc)
    elif args.source_html:
        brand_slug = slugify(args.source_html.stem)
    else:
        brand_slug = slugify(instagram_folders[0].name)
    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.output_dir / f"{brand_slug}_{run_id}"
    if run_dir.exists() and args.overwrite:
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    candidates, pages, warnings = collect_candidates(
        urls=urls,
        source_html=args.source_html,
        base_url=args.base_url,
        max_pages=args.max_pages,
        timeout=args.timeout,
    )
    instagram_candidates, instagram_pages, instagram_warnings = collect_instagram_folder_candidates(
        instagram_folders,
        args.instagram_max_images_per_post,
    )
    candidates = dedupe_candidates(candidates + instagram_candidates)
    pages.extend(instagram_pages)
    warnings.extend(instagram_warnings)
    source_records = build_source_records(candidates, run_dir, args.max_downloads, args.timeout)
    product_images = select_source_images(source_records, "product", args.product_count)
    campaign_images = select_source_images(
        source_records,
        "campaign_collaboration",
        args.campaign_count,
        excluded_ids={record["source_image_id"] for record in product_images},
    )
    source_refs = list(urls)
    if args.source_html:
        source_refs.append(as_project_path(resolve_workspace_path(args.source_html)))
    source_refs.extend(as_project_path(resolve_workspace_path(folder)) for folder in instagram_folders)
    summary = summarize_brand(
        brand_slug=brand_slug,
        urls=source_refs,
        pages=pages,
        warnings=warnings,
        records=source_records,
        product_images=product_images,
        campaign_images=campaign_images,
        portfolio_records=portfolio_records,
    )
    selected_sources = product_images + [record for record in campaign_images if record not in product_images]
    matches = match_portfolio(portfolio_records, selected_sources, summary, run_dir, args.recommend_count)
    viewer_path = write_viewer(run_dir, summary, source_records, matches)

    write_json(run_dir / "brand_source_images.json", source_records)
    write_jsonl(run_dir / "brand_source_images.jsonl", source_records)
    write_json(run_dir / "brand_source_summary.json", summary)
    write_json(run_dir / "portfolio_recommendations.json", matches)
    write_json(
        run_dir / "run_manifest.json",
        {
            "brand_slug": brand_slug,
            "run_id": run_id,
            "run_dir": as_project_path(run_dir),
            "viewer_path": as_project_path(viewer_path),
            "source_images_path": as_project_path(run_dir / "brand_source_images.json"),
            "summary_path": as_project_path(run_dir / "brand_source_summary.json"),
            "recommendations_path": as_project_path(run_dir / "portfolio_recommendations.json"),
        },
    )
    return {
        "brand_slug": brand_slug,
        "run_id": run_id,
        "run_dir": as_project_path(run_dir),
        "viewer_path": as_project_path(viewer_path),
        "candidate_count": len(candidates),
        "source_record_count": len(source_records),
        "similar_count": len(matches["similar_recommendations"]),
        "whitespace_count": len(matches["whitespace_recommendations"]),
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect brand URL images and match portfolio recommendations.")
    parser.add_argument("--url", action="append", help="Brand storefront or Instagram URL. Can be passed multiple times.")
    parser.add_argument("--source-html", type=Path, help="Saved HTML file to parse instead of fetching a live URL.")
    parser.add_argument(
        "--instagram-folder",
        action="append",
        type=Path,
        help="gallery-dl Instagram download folder, for example script/ig_downloads/downloads/brand.",
    )
    parser.add_argument(
        "--instagram-max-images-per-post",
        type=int,
        default=2,
        help="Maximum image files to use per Instagram post from --instagram-folder. Use 0 for no limit.",
    )
    parser.add_argument("--base-url", help="Base URL for resolving relative paths in --source-html.")
    parser.add_argument("--brand-slug", help="Output slug. Defaults to URL host or source HTML filename.")
    parser.add_argument("--portfolio-index", type=Path, default=DEFAULT_PORTFOLIO_INDEX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--run-id", help="Deterministic run id for tests or reruns.")
    parser.add_argument("--max-pages", type=int, default=8)
    parser.add_argument("--max-downloads", type=int, default=42)
    parser.add_argument("--product-count", type=int, default=10)
    parser.add_argument("--campaign-count", type=int, default=10)
    parser.add_argument("--recommend-count", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if not args.url and not args.source_html and not args.instagram_folder:
        parser.error("one of --url, --source-html, or --instagram-folder is required")
    return args


def main() -> None:
    result = build_run(parse_args())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
