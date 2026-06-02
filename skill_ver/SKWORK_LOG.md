# SKWORK_LOG

`skill_ver/`는 기존 `api/`, `web/` 프로그램과 분리해서 브랜드 URL 기반 포트폴리오 매칭 워크플로우를 기획하고 검증하는 작업 공간이다. 아래 기록은 2026-06-01 현재까지 이 폴더 안에서 진행한 작업 요약이다.

## 현재 산출물

- `README.md`: 별도 워크플로우의 목표, 선행 작업, 운영 원칙 정리
- `01_workflow_plan.md`: 자사몰/인스타 URL 입력부터 이미지 수집, 매칭, 사용자 선택, 영업 메일/제안서 생성까지의 전체 흐름
- `02_portfolio_metadata_plan.md`: 보유 포트폴리오를 이미지 메타 인덱스로 만드는 기준
- `03_matching_and_proposal_spec.md`: 유사 이미지 5장, 보완/반대 이미지 5장 추천과 제안서 생성 기준
- `04_brand_url_matching_workflow.md`: 브랜드 URL 이미지 수집과 포트폴리오 유사/보완 10개 추천 실행 기준
- `schemas/portfolio_image.schema.json`: 포트폴리오 이미지 메타 스키마
- `schemas/brand_source_image.schema.json`: 브랜드 URL에서 수집한 이미지 메타 스키마
- `prompts/analysis_and_proposal_prompts.md`: 이미지 분석, 매칭, 메일/제안서 생성을 위한 프롬프트 초안
- `scripts/build_portfolio_metadata.py`: 포트폴리오 이미지 폴더를 JSON/JSONL/썸네일/HTML 뷰어로 변환하는 재사용 스크립트
- `scripts/build_brand_url_matches.py`: 브랜드 URL 또는 저장 HTML을 수집해 브랜드 이미지 후보와 포트폴리오 유사/보완 추천을 생성하는 스크립트
- `scripts/build_brand_outreach_assets.py`: 브랜드 매칭 run에서 콜드메일 초안과 미니 제안서 HTML을 생성하는 스크립트
- `fixtures/brand_source_sample.html`: 네트워크 없이 수집/매칭 파이프라인을 검증하기 위한 샘플 HTML
- `portfolio_metadata_viewer.html`: `portfolio/` 샘플 12장 기준 메타데이터 검수 화면
- `portfolio_all_metadata_viewer.html`: `portfolio_all/` 전체 387장 기준 메타데이터 검수 화면
- `data/portfolio_index.json`, `data/portfolio_index.jsonl`, `data/portfolio_summary.json`: 샘플 포트폴리오 메타 산출물
- `data/portfolio_all_index.json`, `data/portfolio_all_index.jsonl`, `data/portfolio_all_summary.json`: 전체 포트폴리오 메타 산출물
- `data/*_thumbnails/`: HTML 뷰어용 썸네일 이미지
- `schemas/brand_portfolio_match_result.schema.json`: 유사/보완 포트폴리오 추천 결과 스키마
- `06_outreach_assets_workflow.md`: 매칭 결과를 콜드메일/미니 제안서로 변환하는 실행 기준

## 진행 로그

### 2026-05-31 22:10 - 별도 워크플로우 기획

- 기존 프로그램을 건드리지 않고 `skill_ver/` 안에 브랜드 URL 기반 영업 제안 워크플로우를 분리해서 설계했다.
- 핵심 흐름은 브랜드 URL 입력, 상품/기획전 이미지 후보 수집, 보유 포트폴리오 유사 5장/보완 5장 추천, 사용자 선택, 영업 메일과 이미지 포함 제안서 초안 생성으로 정리했다.
- "반대되는 이미지"는 무작위 대비가 아니라 브랜드 이미지에서 부족한 컷 유형, 톤, 커머스 역할을 보완하는 전략적 대비 이미지로 정의했다.

### 2026-05-31 22:35 - 샘플 포트폴리오 메타화

- `portfolio/` 폴더의 이미지 12장을 대상으로 1차 메타 인덱스를 생성했다.
- 이미지 크기, 비율, 방향, 대표 색상, 밝기, 대비, 그룹, 컷 유형, 시각 태그, 커머스 태그, 제안 활용 문구를 포함했다.
- 산출물:
  - `data/portfolio_index.json`
  - `data/portfolio_index.jsonl`
  - `data/portfolio_summary.json`
  - `portfolio_metadata_viewer.html`
- HTML 뷰어에서 이미지, 차트, 검색, 필터, 상세 drawer를 확인했다.

### 2026-05-31 22:52 - 전체 포트폴리오 메타화와 워크스페이스 스킬 생성

- `scripts/build_portfolio_metadata.py`를 폴더 인자 기반 CLI로 확장했다.
- `portfolio_all/` 전체 이미지 387장을 메타화했다.
- MP4 39개는 현재 이미지 분석 대상이 아니므로 `skipped_video_files`에 기록했다.
- 전체 산출물:
  - `data/portfolio_all_index.json`
  - `data/portfolio_all_index.jsonl`
  - `data/portfolio_all_summary.json`
  - `data/portfolio_all_thumbnails/`
  - `portfolio_all_metadata_viewer.html`
- 워크스페이스 전용 스킬 `.codex/skills/build-portfolio-metadata`를 만들었다. 이 스킬은 현재 프로젝트에서만 `build_portfolio_metadata` 워크플로우를 재사용하기 위한 것이다.

### 2026-05-31 23:09 - 카드 표시 안정화와 브랜드 태그 필터

- `portfolio_all_metadata_viewer.html`에서 387개 이미지를 한 번에 렌더링하지 않고 초기 60개 카드만 보여주고 `더 보기`로 추가 렌더링하게 변경했다.
- 인스타 핸들 기반 `brand_tags`와 `brand_counts`를 생성하고, 브랜드 select/칩 필터를 추가했다.
- 현재 전체 데이터 기준 브랜드 태그는 49개다.
- 예시로 `musinsa.official` 필터는 89장을 반환한다.

### 2026-05-31 23:19 - 새로고침 후 페이드아웃 문제 수정

- 새로고침하면 화면이 보였다가 사라지는 문제가 있었다.
- 원인은 `data-reveal` 섹션에 `.reveal` 클래스가 붙으며 `opacity: 0`이 된 뒤, 브라우저 새로고침/스크롤 복원 타이밍에 `visible` 상태로 돌아오지 못하는 구조였다.
- 해결:
  - `.reveal` 기본 상태를 항상 보이게 변경
  - IntersectionObserver 의존 제거
  - 초기화 시 `reveal visible`을 즉시 부여
  - select 필터가 브라우저별 이벤트 차이에 영향을 받지 않도록 `input`과 `change` 이벤트를 모두 처리

### 2026-05-31 23:37 - 탭, 테이블, 상세 JSON 개선

- 메인 화면은 `포트폴리오 카드` 중심으로 정리했다.
- `분포 분석`과 `데이터 테이블`은 상단 탭으로 분리했다.
- 데이터 테이블은 `colgroup` 기반 고정 컬럼 폭을 적용해 프로젝트, 브랜드 태그, 그룹, 컷 유형, 태그, 제안 활용 문구가 읽히도록 개선했다.
- 상세 drawer의 `전체 JSON`은 기본 접힘 상태로 만들고, 클릭해서 열고 닫을 수 있게 변경했다.
- 숨겨진 탭에서 Chart.js가 잘못 그려지는 일을 피하기 위해 `분포 분석` 탭을 열 때 차트를 생성하도록 처리했다.

### 2026-06-01 10:02 - 브랜드 URL 수집 및 포트폴리오 10+10 매칭 워크플로우 추가

- `scripts/build_brand_url_matches.py`를 추가했다.
- 입력 방식:
  - `--url`: 자사몰 또는 인스타 URL을 직접 읽어 이미지 후보 수집
  - `--source-html`: 인스타그램/동적몰처럼 직접 수집이 막히는 경우 저장 HTML을 입력
- 수집 대상:
  - `img src`
  - `srcset`
  - lazy-load 계열 속성
  - `og:image`, `twitter:image`
  - JSON-LD image
  - inline `background-image`
- 수집한 이미지는 상품 후보와 기획전/캠페인/콜라보/프로젝트 후보로 나눈다.
- 수집 성공 이미지는 `source_images/`, `source_thumbnails/`에 저장하고, Pillow로 크기, 비율, 방향, 대표 색상, 밝기, 대비를 분석한다.
- `portfolio_all_index.json`과 비교해 다음 결과를 만든다.
  - 브랜드와 유사한 포트폴리오 10개
  - 브랜드에는 부족하지만 우리에게 있는 보완 포트폴리오 10개
- 출력은 `skill_ver/data/brand_runs/{brand_slug}_{timestamp}/` 아래에 생성된다.
  - `brand_source_images.json`
  - `brand_source_images.jsonl`
  - `brand_source_summary.json`
  - `portfolio_recommendations.json`
  - `run_manifest.json`
  - `index.html`
- 로컬 fixture 실행으로 후보 4개 수집, 유사 10개, 보완 10개 추천 생성까지 검증했다.

### 2026-06-01 11:13 - 앤더슨벨 자사몰/인스타 URL 매칭 run

- 입력 URL:
  - `https://anderssonbell.com/`
  - `https://www.instagram.com/anderssonbell/`
- 출력 폴더: `data/brand_runs/anderssonbell_20260601_110801/`
- 생성 파일:
  - `brand_source_images.json`
  - `brand_source_images.jsonl`
  - `brand_source_summary.json`
  - `portfolio_recommendations.json`
  - `run_manifest.json`
  - `index.html`
- 수집 결과:
  - 페이지 12개 스캔
  - 이미지 후보 506개 발견
  - 상위 60개 이미지 다운로드/분석
  - 상품 이미지 10개 선정
  - 기획전/캠페인/콜라보 후보 10개 선정
  - 유사 포트폴리오 10개 생성
  - 브랜드에 부족한 보완 포트폴리오 10개 생성
- 관찰된 앤더슨벨 이미지 무드:
  - 현재 정적 수집 기준으로는 `제품 오브젝트` 컷이 강하게 잡힘
  - 주요 태그는 `object_still_life`, `product_focus`, `dark_mood`, `portrait_frame`, `high_contrast`
  - 보완 방향은 `캠페인 키비주얼`, `모델 착용/스타일링`, `디테일/패턴`, `스포츠/액티브`, `시즌/라이프스타일`, `무드 클로즈업`
- 상위 추천:
  - 유사: `P049`, `P052`, `P055` 등 제품 오브젝트 중심
  - 보완: `P026`, `P030`, `P035`, `P056`, `P058` 등 캠페인/무드/스타일링/디테일 방향
- 한계:
  - 인스타그램 URL은 200 응답이지만 정적 HTML에서 이미지 후보가 0개였다.
  - 이번 run은 자사몰 정적 HTML 수집 중심 결과다.
  - 인스타 피드 이미지까지 반영하려면 저장 HTML 입력 또는 Playwright 렌더링 DOM 수집 확장이 필요하다.
- 검증:
  - JSON 산출물 로드 검증 통과
  - `index.html` 브라우저 확인에서 카드 40개와 이미지 40개가 모두 로드됨
  - 콘솔에는 `favicon.ico` 404만 발생

### 2026-06-01 11:16 - 앤더슨벨 정정 인스타 URL 재실행

- 정정 인스타 URL: `https://www.instagram.com/adsb_anderssonbell/`
- 출력 폴더: `data/brand_runs/anderssonbell_20260601_1114_adsb/`
- 결과:
  - 페이지 12개 스캔
  - 이미지 후보 506개 발견
  - 상위 60개 이미지 다운로드/분석
  - 상품 이미지 10개 선정
  - 기획전/캠페인/콜라보 후보 10개 선정
  - 유사 포트폴리오 10개 생성
  - 보완 포트폴리오 10개 생성
- 정정된 인스타 URL도 200 응답은 받았지만 정적 HTML에서 이미지 후보는 0개였다.
- 이번 결과 역시 자사몰 정적 HTML 중심이다.
- 브라우저 검증에서 카드 40개와 이미지 40개가 모두 로드됐다.

## 메타화 스크립트 사용법

기본 샘플 포트폴리오:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py
```

전체 포트폴리오:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py --source-dir portfolio_all --slug portfolio_all
```

새 폴더를 메타화할 때:

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py --source-dir path/to/image_folder --slug image_folder_slug
```

출력 규칙:

- `skill_ver/data/<slug>_index.json`
- `skill_ver/data/<slug>_index.jsonl`
- `skill_ver/data/<slug>_summary.json`
- `skill_ver/data/<slug>_thumbnails/`
- `skill_ver/<slug>_metadata_viewer.html`

## 브랜드 URL 매칭 스크립트 사용법

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

인스타그램 또는 동적 페이지가 직접 수집을 막을 때:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --source-html /path/to/saved-page.html \
  --base-url "https://www.instagram.com/brand/" \
  --brand-slug example_brand_instagram
```

## 현재 데이터 상태

- `portfolio/`: 이미지 12장, 프로젝트 그룹 8개
- `portfolio_all/`: 이미지 387장, 프로젝트 그룹 56개, 브랜드 태그 49개
- `portfolio_all/`의 영상 파일 39개는 아직 분석하지 않고 summary에 스킵 목록으로 남긴다.
- 다수 레코드는 `review_status: needs_review` 상태다. 외부 제안서에 쓰기 전 권리, 클라이언트명, 문구 검수가 필요하다.

## 검증 기록

- `python3 -m py_compile skill_ver/scripts/build_portfolio_metadata.py`: 통과
- JSON 로드 검증: `portfolio_all` 387장, summary count 387장 확인
- 앤더슨벨 run JSON 로드 검증: 후보 60개, 상품 10개, 캠페인 10개, 유사 10개, 보완 10개 확인
- 앤더슨벨 정정 인스타 URL run JSON/HTML 검증: 카드 40개, 이미지 40개 로드 확인
- `.codex/skills/build-portfolio-metadata` quick validate: 통과
- 브라우저 검증:
  - 카드 탭 초기 60장 표시
  - 브랜드 필터 동작
  - `분포 분석` 탭 차트 렌더링
  - `데이터 테이블` 387행/8컬럼 표시
  - 상세 drawer JSON 접기/펼치기
  - 375px 모바일 폭에서 문서 전체 가로 overflow 없음

## 알려진 한계

- 현재 메타는 Pillow 이미지 통계, 인스타 sidecar JSON, 기존 seed, 휴리스틱을 조합한 1차 메타다.
- 영상 파일은 아직 이미지처럼 분석하지 않는다.
- 브랜드 태그는 인스타 핸들 기반이라 `benetton`/`benetton_korea`처럼 같은 브랜드의 복수 핸들이 분리될 수 있다.
- 브랜드 URL 수집은 정적 HTML 기반 1차 수집이다. JS 렌더링 이후에만 나타나는 이미지는 `--source-html` 또는 이후 Playwright 렌더링 수집 확장이 필요하다.
- 실제 영업 제안서에 반영하기 전에는 권리, 브랜드명 표기, 제안 문구를 사람이 검수해야 한다.

## [2026-06-01 11:23] Instagram 로그인 다운로드 폴더 연동
- 수행: `skill_ver/scripts/build_brand_url_matches.py`에 `--instagram-folder` 입력을 추가해 `script/ig_downloads/downloads/{profile}` 같은 gallery-dl 다운로드 폴더의 이미지와 `.jpg.json` sidecar 메타데이터를 브랜드 소스 이미지로 읽도록 구현함. `04_brand_url_matching_workflow.md`에 사용 예시를 추가하고 `05_instagram_logged_in_download_workflow.md`를 새로 작성함
- 이유: Instagram 정적 HTML에서 이미지 후보가 잡히지 않는 경우가 있어, 사용자가 로그인한 브라우저 쿠키로 먼저 이미지를 받은 뒤 그 결과를 기존 포트폴리오 매칭에 넣을 수 있어야 했기 때문
- 결과: `py_compile` 통과. 기존 샘플 `script/ig_downloads/downloads/23st5dio`로 실행해 후보 20개, 분석 20개, 유사 10개, 보완 10개 생성 확인. HTML viewer 이미지 40개 경로 누락 0건 확인. fixture HTML + Instagram 폴더 병합 실행도 후보 24개, 추천 10+10 생성 확인
- 다음: 앤더슨벨 실제 인스타그램은 `./script/ig_downloads/download_ig.command adsb_anderssonbell 20 chrome` 실행 후 `--instagram-folder script/ig_downloads/downloads/adsb_anderssonbell`로 재분석

## [2026-06-01 11:48] 앤더슨벨 Instagram 이미지 다운로드 및 매칭
- 수행: 로그인된 Chrome 쿠키를 사용하는 `gallery-dl`로 `https://www.instagram.com/adsb_anderssonbell/` 최근 20개 게시물을 `script/ig_downloads/downloads/adsb_anderssonbell`에 다운로드함. 해당 폴더를 `--instagram-folder`로 넣어 `anderssonbell_instagram_20260601_ig_downloaded` 매칭 run을 생성함
- 이유: 정적 Instagram HTML 수집에서 이미지 후보가 0개였기 때문에 실제 인스타그램 게시물 이미지를 로컬 소스로 확보해 브랜드 무드 분석과 포트폴리오 추천에 반영하기 위함
- 결과: 이미지 122장, JSON 메타 125개, 영상 2개 다운로드. 메타 기준 고유 게시물 20개, 날짜 범위 2026-04-06 06:45:49 - 2026-05-27 05:25:43. 매칭 run은 후보 122개 중 80개 분석, 유사 10개, 보완 10개 생성. JSON 로드 검증과 HTML 이미지 40개 경로 누락 0건 확인
- 다음: 필요 시 `--max-downloads`를 122로 올려 전체 이미지 분석 run을 별도로 생성하거나, 자사몰 URL과 Instagram 폴더를 합친 통합 run을 생성

## [2026-06-01 13:46] Instagram 최신순/게시물 다양성 보정과 통합 run 검증
- 수행: `build_brand_url_matches.py`에서 Instagram 폴더를 `post_date` 최신순 및 캐러셀 순번순으로 읽도록 바꾸고, 기본 `--instagram-max-images-per-post 2` 제한을 추가함. 상품 후보는 자사몰 우선, 캠페인 후보는 Instagram/캠페인 우선으로 정렬하고 부족분 fallback으로 두 섹션이 같은 이미지가 되는 흐름을 제거함
- 이유: 기존 결과가 파일명 정렬과 게시물당 무제한 수집 때문에 오래된 게시물이나 대형 캐러셀에 치우쳤고, 상품/캠페인 후보가 같은 이미지처럼 보였기 때문
- 결과: 앤더슨벨 Instagram diverse run은 원본 122장 중 후보 36장으로 축소, 게시물당 최대 2장 적용, 첫 후보가 2026-05-27 최신 게시물 이미지 1/2번으로 확인됨. 통합 run `anderssonbell_combined_20260601_web_ig_diverse`는 후보 576개 중 100개 분석, 자사몰 68장/Instagram 32장 소스 구성, 상품 후보 10장은 자사몰 상품 리스트 중심, 캠페인 후보 10장은 Instagram 게시물 중심으로 분리됨. HTML 이미지 40개 경로 누락 0건, favicon 404 외 브라우저 오류 없음
- 다음: 자사몰의 기획전/룩북 전용 URL이 확인되면 `--url`로 추가해 캠페인 후보를 Instagram뿐 아니라 자사몰 캠페인 페이지에서도 보강

## [2026-06-01 14:04] 브랜드 매칭 뷰어 출처/비교/인사이트 개선
- 수행: `build_brand_url_matches.py` HTML 파서가 이미지 주변 `<a href>`를 원본 `page_url`로 저장하도록 보강하고, 상품 후보는 상품 상세 URL을 우선 선택하도록 변경함. HTML viewer를 브랜드 소스 증거, 유사 포트폴리오 비교 맵, 현재 브랜드 관찰 패널, 보완 제안 맵 구조로 재구성함. 추천 JSON에 `brand_reference_images`와 `comparison_dimensions`를 추가함
- 이유: 브랜드 후보 이미지가 어느 상품/게시글에서 왔는지 확인해야 하고, 유사/보완 추천이 어떤 브랜드 이미지와 어떤 기준으로 연결되는지 검수 가능해야 했기 때문
- 결과: `anderssonbell_combined_20260601_evidence_view` run 생성. 상품 후보 10개 모두 `anderssonbell.com/product/...` 상세 URL로 연결, 캠페인 후보는 Instagram 게시글 URL로 연결. HTML 이미지 80개 경로 누락 0건, 외부 원본 링크 80개 확인. 추천 JSON 비교 근거 로드 검증 통과. Playwright 브라우저 검증에서 새 레이아웃 렌더링 확인, favicon 404 외 오류 없음
- 다음: 상품명은 URL slug 기반 변환이므로, 더 정확한 한글/영문 상품명을 원하면 상품 상세 페이지의 title/JSON-LD를 추가 수집하는 단계로 확장

## [2026-06-01 14:25] 브랜드 매칭 뷰어 추천 의도/태그 설명 개선
- 수행: `build_brand_url_matches.py`에 `대표무드형 매칭` 전략 설명, 태그 설명 패널, 태그 hover tooltip, compact 브랜드 관찰 패널을 추가함. 상품 후보 카드는 화면에서 긴 URL 설명을 숨기고 상품명/메타/클릭 안내만 보이게 정리함. 긴 브랜드 slug와 카드 텍스트가 모바일에서 가로 overflow를 만들지 않도록 CSS 줄바꿈과 `min-width`를 보강함
- 이유: 담당자가 유사 포트폴리오 10장이 어떤 의도로 뽑혔는지 이해하고, 태그가 왜 일치했다고 판단됐는지 검수할 수 있어야 했기 때문
- 결과: `anderssonbell_combined_20260601_evidence_view`를 자사몰+Instagram 통합 기준으로 재생성함. 후보 576개, 분석 소스 100개, 상품 후보 10개, 캠페인 후보 10개, 유사 10개, 보완 10개 생성. `py_compile`, JSON 로드, HTML 텍스트/링크 assertion 통과. Playwright에서 데스크톱 1280px와 모바일 390px 모두 가로 overflow 0, 상품 URL 화면 노출 없음, 카드 20개/소스 후보 20개 표시, 콘솔 오류 0건 확인
- 다음: 필요하면 추천 모드를 `대표무드형`, `1:1 커버리지형`, `색감우선형` 중 선택하는 CLI/HTML 옵션으로 확장

## [2026-06-01 14:54] 즉시 hover tooltip과 `brand-image-matching` 스킬 생성
- 수행: 태그 칩과 카운트 칩의 설명을 `title` 속성에서 `data-tooltip` 기반 fixed layer로 바꿔 hover 즉시 표시되게 개선함. HTML에 data favicon을 추가해 로컬 검증 시 favicon 404 콘솔 오류가 나지 않게 함. `.codex/skills/brand-image-matching/SKILL.md`를 추가해 `brand_image_matching` alias, 입력, 산출물, 검증 절차, guardrail을 정리함
- 이유: 태그 의미를 확인하는 hover 반응이 느리면 이미지와 메타 태그 일치 여부를 빠르게 검수하기 어렵고, 브랜드 URL/Instagram 폴더 기반 매칭 workflow는 반복 실행될 가능성이 높기 때문
- 결과: fixture run으로 템플릿 생성 확인 후 앤더슨벨 통합 run `anderssonbell_combined_20260601_evidence_view`를 재생성함. 후보 576개, 분석 소스 100개, 상품/캠페인 후보 각 10개, 유사/보완 추천 각 10개. `py_compile`, JSON 로드, HTML tooltip assertion, 스킬 파일 assertion 통과. Playwright에서 데스크톱/모바일 tooltip 즉시 표시, 모바일 viewport 내 위치, overflow 0, 콘솔 오류 0건 확인
- 다음: 새 브랜드 요청 시 이 스킬을 기준으로 `download_ig.command`와 `build_brand_url_matches.py`를 순서대로 사용

## [2026-06-01 15:11] 콜드메일/미니 제안서 생성 workflow 추가
- 수행: `scripts/build_brand_outreach_assets.py`를 추가해 브랜드 매칭 run의 summary/source/recommendation JSON을 읽고 `outreach_assets/outreach_assets.json`, `outreach_assets/cold_email_draft.md`, `outreach_assets/mini_proposal.html`을 생성하도록 구현함. `06_outreach_assets_workflow.md`를 추가하고 `brand-image-matching` 스킬에 outreach 생성 절차를 연결함
- 이유: 브랜드 이미지 매칭 결과를 내부 검수 화면에서 끝내지 않고, 실제 영업 담당자가 수정 가능한 콜드메일과 이미지 중심 미니 제안서로 바로 이어야 하기 때문
- 결과: 앤더슨벨 통합 run에서 기본 유사 3장/보완 3장 기준 산출물 생성 완료. 선택 ID 기반 재생성도 검증함. `py_compile`, JSON 로드, HTML assertion 통과. Playwright에서 미니 제안서 이미지 26개 로드, broken 0, 데스크톱/모바일 overflow 0, 콘솔 오류 0건 확인
- 다음: 실제 발송 전에는 담당자가 `--similar-ids`, `--whitespace-ids`로 사용할 이미지를 확정하고 브랜드명/권리/제안 범위를 검수

## [2026-06-01 17:00] 선택형 제안서 생성 UI와 콜드메일 톤 개선
- 수행: `build_brand_outreach_assets.py`의 콜드메일 문구에서 분석/태그 노출을 제거하고, 브랜드를 관심 있게 보고 포트폴리오를 공유하는 톤으로 조정함. `mini_proposal.html`은 10개 유사 후보와 10개 보완 후보를 담당자가 선택한 뒤 `제안서 생성` 버튼으로 우리 포트폴리오 설명만 담은 제안서를 만드는 화면으로 개편함. 제안서 페이지는 선택 이미지를 3장씩 나눠 렌더링함
- 이유: 브랜드 레퍼런스나 분석 흔적을 고객용 제안서에 노출하기보다, 내부 담당자가 우리 포트폴리오를 고르고 설명 중심 제안서를 만드는 구조가 필요했기 때문
- 결과: 앤더슨벨 산출물 재생성 완료. `outreach_assets.json`에 유사/보완 후보 각 10개와 포트폴리오 메타 설명 포함. Playwright에서 후보 카드 20개, 기본 선택 6개, 버튼 생성 후 페이지 2개/카드 6개 확인. 임의 선택 9개로 페이지 4개 및 페이지별 3/1/3/2장 분할 확인. 모바일 overflow 0, 이미지 broken 0, 콘솔 오류 0건
- 다음: 실제 담당자 선택값을 기준으로 최종 PDF/프린트 레이아웃을 더 다듬을 수 있음

## [2026-06-01 17:31] SECTION 전용 HTML/PDF 출력 개선
- 수행: `mini_proposal.html`의 출력 버튼을 `SECTION HTML 다운로드`와 `SECTION PDF 만들기`로 분리하고, 두 기능이 같은 SECTION 전용 HTML을 사용하도록 `build_brand_outreach_assets.py`를 수정함. SECTION 전용 HTML에는 내부 편집 UI, 콜드메일, 후보 선택 영역 없이 선택된 우리 포트폴리오 SECTION 페이지만 포함되게 함. PDF 출력용 CSS는 A4 기준 flex 3열로 고정해 CSS grid 인쇄 분절 문제를 피함
- 이유: 브라우저 인쇄/PDF에서 3장씩 묶인 SECTION이 아니라 개별 카드처럼 페이지가 쪼개져 보였기 때문. 담당자 화면과 고객용 출력물을 명확히 분리해야 했음
- 결과: 앤더슨벨 산출물 재생성 완료. Playwright에서 기본 선택 6개는 SECTION HTML/PDF 2페이지, 임의 선택 9개는 페이지별 3/1/3/2장 분할 및 PDF 4페이지 확인. 다운로드 HTML은 절대 이미지 URL을 사용하고, SECTION 문서에는 builder UI가 없으며 이미지 broken 0, 모바일 overflow 0, 콘솔 오류 0건 확인
- 다음: 완전한 원클릭 PDF 파일 저장은 브라우저 보안상 프린트/PDF 창을 거치므로, 서버형/CLI형 자동 PDF 저장이 필요하면 별도 export 명령으로 확장

## [2026-06-01 17:54] 가로형 SECTION PDF 직접 생성
- 수행: `skill_ver/scripts/export_proposal_sections_pdf.py`를 추가해 `outreach_assets.json`의 선택값 또는 CLI로 넘긴 portfolio ID를 기준으로 `proposal_sections_landscape.html`과 `proposal_sections_landscape.pdf`를 직접 생성하도록 구현함. PDF 생성은 로컬 Chrome headless의 DevTools `Page.printToPDF`를 사용해 인쇄 창을 열지 않고 파일로 저장함. `mini_proposal.html`에는 생성된 PDF를 바로 내려받는 `가로형 PDF 다운로드` 링크를 추가함
- 이유: 브라우저 인쇄/PDF 창을 거치지 않고, 브랜드 담당자에게 보낼 가로형 PDF 파일을 바로 만들고 내려받고 싶다는 요구가 있었기 때문
- 결과: 앤더슨벨 기본 선택 6개 기준 A4 landscape PDF 2페이지 생성 확인. `pdfinfo`에서 page size `841.92 x 594.96 pts`, Pages 2 확인. PDF PNG 렌더링으로 SECTION 1/2가 각각 3장씩 가로형으로 표시됨을 확인. 선택 ID 4개/5개 입력 시 예상 4페이지 생성도 확인
- 다음: HTML에서 현재 체크 상태를 즉시 서버에 넘겨 PDF까지 생성하려면 작은 로컬 서버형 export API가 필요함. 현재는 CLI로 선택 ID를 넘기는 방식이 안정적임

## [2026-06-01 18:02] Proposal Builder 스킬 분리와 출력 버튼 정리
- 수행: `mini_proposal.html`에서 `SECTION PDF 만들기` 버튼과 print iframe JS를 제거하고 `SECTION HTML 다운로드`, `가로형 PDF 다운로드`만 남김. `.codex/skills/proposal-builder/SKILL.md`를 추가해 `Proposal_builder` alias, 콜드메일/미니제안서/SECTION HTML/A4 landscape PDF 생성 절차, 검증 기준을 정리함. `brand-image-matching` 스킬은 매칭 후 제안서 작업은 `proposal-builder` 스킬을 사용하도록 안내를 보강함
- 이유: 직접 PDF 파일 다운로드 흐름이 생긴 뒤에는 브라우저 인쇄 버튼이 중복되고, 제안서 제작 workflow는 브랜드 수집/매칭 workflow와 분리해 반복 사용하는 편이 명확하기 때문
- 결과: 앤더슨벨 `mini_proposal.html` 재생성 완료. HTML에는 `SECTION HTML 다운로드`와 `가로형 PDF 다운로드`만 남고 `SECTION PDF 만들기`/`printSections`는 제거됨. `proposal_sections_landscape.pdf`는 A4 landscape 2페이지로 유지 확인
- 다음: 담당자가 HTML에서 체크한 현재 상태를 곧바로 PDF export 명령에 넘기는 로컬 서버형 API가 필요하면 후속으로 추가

## [2026-06-01 18:18] USERGUIDE 작성
- 수행: `skill_ver/USERGUIDE.md`를 추가해 포트폴리오 메타화, Instagram 로그인 다운로드, 브랜드 이미지 매칭, 콜드메일/미니 제안서, SECTION HTML, 가로형 PDF 생성까지 전체 운영 절차를 한 문서로 정리함. `build-portfolio-metadata`, `brand-image-matching`, `proposal-builder` 스킬명과 alias, 핵심 명령어, 산출물 위치, 신규 브랜드 반복 실행 순서를 포함함
- 이유: 이 세션에서 만든 여러 스크립트/스킬/HTML 산출물을 운영자가 한 번에 이해하고 재현할 수 있는 시작 문서가 필요했기 때문
- 결과: 관련 Python 스크립트 `py_compile` 통과. `USERGUIDE.md` 필수 키워드와 현재 버튼명 검증 통과. `mini_proposal.html`에 폐기된 `SECTION PDF 만들기`/`printSections`가 없고, `proposal_sections_landscape.pdf`가 A4 landscape 2페이지임을 확인함
- 다음: 신규 브랜드 run을 만들 때 `USERGUIDE.md` 순서대로 실행하고, 실제 담당자 선택 ID는 run별로 기록

## 다음 작업 후보

- 브랜드 태그 병합 매핑 추가
- Vision 분석 또는 수동 검수 UI로 `source_metadata_only` 레코드 보강
- 브랜드 URL 매칭 결과에서 사용자가 실제 발송 이미지 3~5개를 선택하는 selection UI
- 현재 체크 상태를 바로 PDF로 저장하는 로컬 서버형 export API 추가
- Playwright 렌더링 DOM 기반 수집 모드 추가
