# 브랜드 URL 수집 및 포트폴리오 매칭 워크플로우

이 문서는 자사몰 URL 또는 인스타 URL을 입력받아 브랜드 이미지 무드를 수집하고, `portfolio_all` 메타데이터와 비교해 유사 이미지 10개와 보완 이미지 10개를 만드는 실행 워크플로우를 정의한다.

## 목표

입력 URL 하나 또는 여러 개를 기준으로 아래 산출물을 만든다.

1. 브랜드 페이지에서 상품 이미지 후보 최대 10장 선정
2. 기획전, 캠페인, 콜라보레이션, 프로젝트 이미지 후보 최대 10장 선정
3. 우리 보유 포트폴리오 중 브랜드와 유사한 이미지 10장 추천
4. 현재 브랜드 이미지에서는 부족하지만 우리 포트폴리오에는 있는 보완 이미지 10장 추천
5. 결과를 JSON/JSONL/HTML 리뷰 화면으로 저장

## 실행 명령

자사몰 URL을 직접 수집할 때:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://example-brand.com" \
  --brand-slug example_brand
```

여러 URL을 함께 넣을 때:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://example-brand.com" \
  --url "https://example-brand.com/collections/new" \
  --url "https://example-brand.com/pages/campaign" \
  --brand-slug example_brand
```

인스타그램 또는 동적 페이지가 직접 수집을 막을 때는 브라우저에서 저장한 HTML을 입력한다.

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --source-html /path/to/saved-instagram-or-brand-page.html \
  --base-url "https://www.instagram.com/brand/" \
  --brand-slug example_brand_instagram
```

인스타그램은 로그인 쿠키가 필요한 경우가 많으므로, `script/ig_downloads/IGDOWNGUIDE.md`의 `download_ig.command`로 먼저 이미지를 받은 뒤 그 폴더를 입력할 수 있다.

```bash
./script/ig_downloads/download_ig.command adsb_anderssonbell 20 chrome

python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://anderssonbell.com/" \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --brand-slug anderssonbell
```

인스타그램 폴더만으로도 실행할 수 있다.

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --brand-slug anderssonbell_instagram
```

## 출력 위치

기본 출력은 아래 폴더에 생성된다.

```text
skill_ver/data/brand_runs/{brand_slug}_{YYYYMMDD_HHMMSS}/
```

각 run 폴더에는 다음 파일이 들어간다.

- `brand_source_images.json`: 수집된 브랜드 이미지 후보 전체
- `brand_source_images.jsonl`: 브랜드 이미지 후보 JSONL
- `brand_source_summary.json`: 브랜드 이미지 무드 요약
- `portfolio_recommendations.json`: 유사 10개와 보완 10개 추천 결과
- `run_manifest.json`: 주요 산출물 경로
- `index.html`: 담당자 검수용 결과 화면
- `source_images/`: 수집 성공한 브랜드 이미지
- `source_thumbnails/`: 브랜드 이미지 썸네일

## HTML 리뷰 화면

`index.html`은 단순 이미지 나열이 아니라 아래 흐름으로 검수한다.

- `브랜드 상품 이미지 후보`: 상품명과 수집 메타만 보여주고 긴 URL은 화면에 노출하지 않는다. 원본 이동은 이미지 클릭으로 처리하며, 수집 기준이 된 자사몰 상품 상세/상품 페이지로 이동한다.
- `브랜드 기획전/콜라보/프로젝트 후보`: 이미지를 클릭하면 Instagram 게시글 또는 캠페인 페이지로 이동한다.
- `태그 설명 보기`: 컷 유형, 비주얼 태그, 커머스 역할 태그의 의미를 접힘 패널로 확인한다. 각 태그 칩에도 즉시 반응하는 hover 설명을 넣어 어떤 분석 근거가 일치했는지 검수한다.
- `우리 포트폴리오와 유사한 이미지`: 기본값은 `대표무드형 매칭`이다. 브랜드 후보 20장 각각을 1:1로 강제 대응하지 않고, 반복되는 컷 유형, 시각 태그, 커머스 역할, 밝기, 프레임을 기준으로 영업 제안서에 바로 묶기 좋은 10장 세트를 고른다.
- `현재 브랜드 관찰`: 선택된 브랜드 상품/캠페인 후보 20장의 컷 유형, 비주얼 태그, 커머스 역할 분포를 compact 패널로 요약하고, 덜 보이는 제안 방향을 함께 표시한다.
- `브랜드에는 부족하지만 우리에게 있는 이미지`: 현재 브랜드에서 덜 보이는 컷/태그를 근거로 새롭게 제안할 수 있는 포트폴리오를 보여준다.

자사몰 이미지가 상품 리스트 안의 `<a href>`에 감싸져 있으면 해당 상품 상세 URL을 원본 링크로 저장한다. 상품명이 별도로 없으면 URL slug를 사람이 읽을 수 있는 제목으로 변환해 표시한다.

## 수집 방식

현재 1차 수집기는 새 외부 의존성 없이 정적 HTML에서 이미지를 찾는다.

- `img src`
- `img srcset`
- `source srcset`
- `data-src`, `data-original`, `data-lazy-src`
- `og:image`, `twitter:image`
- JSON-LD의 `image`, `thumbnailUrl`, `contentUrl`
- inline style의 `background-image: url(...)`

자사몰은 같은 도메인의 상품, 컬렉션, 캠페인, 에디토리얼, 프로젝트 성격 링크를 최대 `--max-pages`개까지 추가로 탐색한다.

추가로 `--instagram-folder`를 전달하면 gallery-dl이 내려받은 이미지 파일과 `.jpg.json` sidecar 메타데이터를 읽는다.

- 이미지 파일: `.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`
- 메타데이터: `description`, `tags`, `username`, `post_url`, `post_date`, `shortcode`
- 소스 표기: `gallery-dl-instagram`
- 정적 HTML 수집 이미지와 합쳐서 중복 제거 후 분석한다.
- Instagram 폴더는 `post_date` 최신순, 캐러셀 내부 순번순으로 읽는다.
- 기본값은 게시물 1개당 최대 2장만 사용한다. 필요하면 `--instagram-max-images-per-post 0`으로 제한을 끌 수 있다.

## 분류 기준

브랜드 수집 이미지는 아래 두 그룹으로 우선 나눈다.

- `product`: 상품, 상품 상세, 베스트 상품, 신상품, 쇼핑 맥락
- `campaign_collaboration`: 기획전, 컬렉션, 캠페인, 룩북, 콜라보, 프로젝트, 매거진, 시즌 스토리 맥락

결과 화면의 `브랜드 상품 이미지 후보`는 자사몰 상품 이미지가 있으면 자사몰을 우선하고, `브랜드 기획전/콜라보/프로젝트 후보`는 Instagram/캠페인 성격 이미지를 우선한다. 한쪽 후보가 부족해도 다른 그룹 이미지를 그대로 복사해 채우지 않는다.

이미지를 내려받을 수 있으면 Pillow로 크기, 비율, 방향, 대표 색상, 밝기, 대비를 분석한다. 이후 URL, alt/title/context, 이미지 통계를 조합해 컷 유형과 태그를 붙인다.

## 매칭 기준

기본 포트폴리오 데이터는 `skill_ver/data/portfolio_all_index.json`을 사용한다.

### 유사 이미지 10개

브랜드가 이미 보여주고 있는 방향과 자연스럽게 이어지는 포트폴리오다.

현재 추천 의도는 `대표무드형 매칭`으로 둔다. 이 방식은 한 브랜드 기준 이미지당 포트폴리오 1장을 강제로 고르는 방식보다, 담당자에게 "이 브랜드의 현재 무드와 이어지는 우리 포트폴리오 세트"를 먼저 보여주기 좋다. 필요하면 이후에 `1:1 커버리지형`이나 `색감우선형` 모드를 별도 옵션으로 추가한다.

주요 점수 요소:

- 브랜드 수집 이미지와 컷 유형이 겹치는지
- 비주얼 태그가 겹치는지
- 커머스 역할 태그가 겹치는지
- 방향, 밝기, 대비가 유사한지
- 같은 프로젝트, 컷 유형, 브랜드 기준 이미지가 과도하게 반복되지 않는지

### 보완 이미지 10개

브랜드 이미지에는 부족하지만 우리 포트폴리오에는 있는 촬영 방향이다.

주요 점수 요소:

- 브랜드 수집 이미지에서 비어 있는 컷 유형인지
- 브랜드에 적게 보이는 비주얼 태그를 제안할 수 있는지
- 새롭게 보강할 커머스 역할이 있는지
- 브랜드와 너무 멀어지지 않는 최소 유사성이 있는지
- 유사 추천과 같은 이미지를 중복 사용하지 않는지

## 검수 포인트

- 자사몰/인스타 페이지의 이미지 사용 권한은 별도 확인해야 한다.
- 인스타그램은 로그인, 지역, 차단, 렌더링 상태에 따라 정적 HTML 수집량이 적을 수 있다.
- 동적 렌더링 이미지가 부족하면 `download_ig.command`로 로그인 브라우저 쿠키 기반 이미지를 내려받아 `--instagram-folder`로 넣거나, `--source-html`에 브라우저에서 저장한 페이지 HTML을 넣는다.
- 인스타그램 다운로드는 계정 로그인 상태와 플랫폼 정책의 영향을 받으므로 최근 게시물 수를 과하게 크게 잡지 않는다.
- 추천 결과는 영업 담당자의 선택을 돕는 1차 큐레이션이며, 발송 전 권리/브랜드명/문구 검수가 필요하다.

## 다음 확장

- Playwright 렌더링 DOM 수집 모드
- 이미지 임베딩 기반 유사도 추가
- 사용자가 선택한 추천 이미지로 영업 메일과 제안서 자동 생성
- 브랜드별 run을 비교하는 히스토리 뷰어
