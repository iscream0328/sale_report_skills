# 포트폴리오 사전 메타화 계획

## 1. 목적

`portfolio/` 폴더의 이미지를 검색 가능한 영업 자산으로 바꾼다. 단순 파일 목록이 아니라, 브랜드 이미지와 비교할 수 있는 시각 언어, 커머스 역할, 제안 활용도를 구조화한다.

## 2. 입력 데이터

현재 구조:

- `portfolio/*.jpg`: 포트폴리오 이미지
- `portfolio/*.jpg.json`: 인스타 게시물/이미지 메타데이터

기존 JSON에서 우선 활용할 필드:

- `post_id`
- `post_shortcode`
- `description`
- `post_url`
- `username`
- `post_date`
- `media_id`
- `display_url`
- `width`, `height`
- `filename`, `extension`

## 3. 포트폴리오 메타 필드

### 파일/출처 메타

- `portfolio_id`: 내부 고유 ID
- `asset_path`: 로컬 이미지 경로
- `source_type`: instagram, upload, archive 등
- `source_url`: 원 게시물 또는 프로젝트 링크
- `client_or_project`: 브랜드/프로젝트명
- `created_at`: 촬영 또는 게시 날짜
- `rights_note`: 영업 제안서에 사용할 수 있는지에 대한 메모

### 이미지 구조 메타

- `width`, `height`, `aspect_ratio`
- `dominant_colors`
- `brightness_level`
- `contrast_level`
- `composition_tags`
- `subject_tags`
- `background_tags`
- `model_presence`
- `product_presence`

### 전략 메타

- `cut_type`: 캠페인 키비주얼, 제품 오브젝트, 착용컷, 클로즈업 등
- `visual_tags`: 색감, 조명, 구도, 연출 태그
- `commerce_tags`: SNS 후킹, 상세 상단, 룩북, 시즌 캠페인 등
- `work_scope`: Visual Directing, Styling, Set Design 등
- `proposal_use`: 브랜드에게 어떤 상황에서 제안할지
- `similar_when`: 어떤 브랜드 이미지와 유사 매칭할지
- `contrast_when`: 어떤 부족 지점에 보완 매칭할지
- `do_not_use_when`: 잘못 추천되기 쉬운 상황

## 4. 태그 체계 초안

### 컷 유형

- `campaign_key_visual`
- `model_styling_cut`
- `product_object_cut`
- `detail_or_pattern_cut`
- `sports_active_cut`
- `seasonal_lifestyle_cut`
- `closeup_mood_cut`

### 시각 태그

- 색/톤: `bold_color`, `neutral_background`, `blue_tone`, `dark_mood`, `bright_natural`, `high_contrast`, `pastel_tone`
- 구도: `close_up`, `full_body`, `half_body`, `group_model`, `object_still_life`, `fisheye`, `wide_hero`
- 연출: `set_design`, `graphic_frame`, `prop_styling`, `studio_light`, `natural_light`, `seasonal_background`, `editorial`
- 피사체: `single_product`, `multi_product`, `model_focus`, `face_focus`, `texture_focus`, `accessory_focus`

### 커머스 태그

- `sns_hook`
- `detail_page_top`
- `lookbook`
- `fit_visible`
- `product_focus`
- `season_campaign`
- `brand_character`
- `premium_product`
- `shortform_ready`

## 5. 사람이 검수해야 하는 필드

AI가 1차 생성하되, 최종 인덱스 반영 전 사람이 확인해야 할 필드:

- `client_or_project`
- `rights_note`
- `cut_type`
- `proposal_use`
- `similar_when`
- `contrast_when`
- `do_not_use_when`

특히 영업 제안에 바로 들어가는 문장은 브랜드/프로젝트명 오표기 위험이 있으므로 검수 필수다.

## 6. 추천 인덱스 형태

초기 구현은 DB보다 JSONL이 빠르다.

```text
skill_ver/data/portfolio_index.jsonl
skill_ver/data/portfolio_embeddings.jsonl
skill_ver/data/portfolio_review_notes.jsonl
```

한 줄에 이미지 하나를 저장하면 새 이미지 추가와 재분석이 쉽다. 추후 UI 연동이 필요해지면 SQLite 또는 기존 앱 DB로 옮긴다.

## 7. 포트폴리오 메타화 작업 순서

1. 파일 스캔: `portfolio/`에서 이미지와 동명 JSON을 페어링한다.
2. 기본 메타 추출: 크기, 비율, 파일명, 게시물 설명, 출처 URL.
3. 이미지 분석: 컷 유형, 색감, 구도, 피사체, 상품/모델 여부.
4. 태그 정규화: 자유 문장을 고정 태그로 매핑한다.
5. 제안 문구 생성: 어떤 브랜드 상황에 유효한지 한 문장으로 정리한다.
6. 사람 검수: 오표기, 과장, 사용권 메모를 확인한다.
7. 인덱스 저장: 검색/매칭 가능한 JSONL로 저장한다.

## 8. 샘플 기준으로 필요한 보강

현재 샘플 12장은 인스타 메타가 풍부하지만, 작업 범위와 제안 활용도는 자유 문장에 가깝다. 매칭 품질을 높이려면 아래를 보강해야 한다.

- 프로젝트/브랜드명 정규화
- 이미지마다 1개 대표 컷 유형 지정
- 유사 매칭용 태그와 보완 매칭용 태그 분리
- 제안서 노출 가능 여부 기록
- 같은 포스트의 여러 이미지를 하나의 프로젝트 그룹으로 묶기
