# skill_ver 사용자 가이드

이 문서는 `skill_ver/` 기반 독립 워크플로우를 처음부터 끝까지 실행하는 방법을 정리한다.

목표는 브랜드 자사몰 URL 또는 Instagram 이미지를 수집해, 보유 포트폴리오와 비교하고, 담당자가 선택한 이미지로 콜드메일과 미니 제안서, 가로형 PDF를 만드는 것이다.

기존 `api/`, `web` 프로그램은 건드리지 않는다. 이 워크플로우는 `skill_ver/`, `portfolio_all/`, `script/ig_downloads/`, `.codex/skills/`를 중심으로 동작한다.

## 전체 흐름

```text
1. 포트폴리오 이미지 폴더 준비
   portfolio_all/

2. 포트폴리오 메타화
   build-portfolio-metadata
   -> skill_ver/data/portfolio_all_index.json
   -> skill_ver/portfolio_all_metadata_viewer.html

3. 브랜드 이미지 수집/매칭
   brand-image-matching
   -> 자사몰 상품 후보 10장
   -> 기획전/콜라보/프로젝트 후보 10장
   -> 유사 포트폴리오 10장
   -> 보완 제안 포트폴리오 10장

4. 콜드메일/제안서 제작
   proposal-builder
   -> cold_email_draft.md
   -> mini_proposal.html
   -> proposal_sections_landscape.pdf

5. 사람이 최종 검수
   브랜드명, 담당자명, 이미지 권리, 문구, 제안 범위 확인
```

## 사용하는 스킬

이 워크스페이스에는 아래 세 가지 스킬이 있다.

| 스킬명 | 호출 alias | 역할 |
| --- | --- | --- |
| `build-portfolio-metadata` | `build_portfolio_metadata` | 포트폴리오 이미지 폴더를 JSON/JSONL/HTML 뷰어로 메타화 |
| `brand-image-matching` | `brand_image_matching` | 브랜드 자사몰/Instagram 이미지 수집, 유사/보완 포트폴리오 추천 |
| `proposal-builder` | `Proposal_builder`, `proposal_builder` | 콜드메일, 선택형 미니 제안서, SECTION HTML, 가로형 PDF 생성 |

Codex에게 작업을 맡길 때는 예를 들어 이렇게 말하면 된다.

```text
build_portfolio_metadata 스킬로 portfolio_all 다시 메타화해줘
```

```text
brand_image_matching 스킬로 이 브랜드 URL과 인스타 폴더를 매칭해줘
```

```text
Proposal_builder 스킬로 이 run에서 콜드메일과 가로형 PDF 만들어줘
```

## 사전 준비

프로젝트 루트에서 실행한다.

```bash
cd <project-root>
```

필요한 폴더/파일:

```text
portfolio_all/                         # 포트폴리오 원본 이미지 폴더
skill_ver/scripts/build_portfolio_metadata.py
skill_ver/scripts/build_brand_url_matches.py
skill_ver/scripts/build_brand_outreach_assets.py
skill_ver/scripts/export_proposal_sections_pdf.py
script/ig_downloads/download_ig.command
```

권장 확인:

```bash
python3 -m py_compile \
  skill_ver/scripts/build_portfolio_metadata.py \
  skill_ver/scripts/build_brand_url_matches.py \
  skill_ver/scripts/build_brand_outreach_assets.py \
  skill_ver/scripts/export_proposal_sections_pdf.py
```

가로형 PDF를 만들려면 로컬에 Chrome 또는 Chromium이 필요하다. 기본 위치의 Google Chrome은 자동 탐색한다. 별도 위치라면 `--chrome-path`를 사용한다.

## 1. 포트폴리오 메타화

새 포트폴리오 이미지를 `portfolio_all/`에 넣은 뒤 실행한다.

```bash
python3 skill_ver/scripts/build_portfolio_metadata.py \
  --source-dir portfolio_all \
  --slug portfolio_all
```

생성 산출물:

```text
skill_ver/data/portfolio_all_index.json
skill_ver/data/portfolio_all_index.jsonl
skill_ver/data/portfolio_all_summary.json
skill_ver/data/portfolio_all_thumbnails/
skill_ver/portfolio_all_metadata_viewer.html
```

검증:

```bash
python3 -m json.tool skill_ver/data/portfolio_all_index.json >/tmp/portfolio_all_index_check.json
python3 -m json.tool skill_ver/data/portfolio_all_summary.json >/tmp/portfolio_all_summary_check.json
wc -l skill_ver/data/portfolio_all_index.jsonl
```

HTML 뷰어에서 확인할 것:

- 카드가 보이는가
- 브랜드 태그 필터가 동작하는가
- 검색/그룹/컷 유형 필터가 동작하는가
- 상세 JSON을 열고 닫을 수 있는가
- `review_status: needs_review` 항목은 외부 제안 전 사람이 검수했는가

## 2. Instagram 이미지 다운로드

Instagram은 로그인 쿠키가 필요한 경우가 많다. 먼저 브라우저에서 Instagram에 로그인한 뒤 다운로드한다.

```bash
./script/ig_downloads/download_ig.command adsb_anderssonbell 20 chrome
```

명령 형식:

```bash
./script/ig_downloads/download_ig.command 계정명 최근게시물개수 브라우저
```

예시:

```bash
./script/ig_downloads/download_ig.command profile_name 20 chrome
```

생성 위치:

```text
script/ig_downloads/downloads/profile_name/
```

주의:

- Instagram 폴더는 `gallery-dl` sidecar JSON의 `post_date` 기준으로 최신순 처리된다.
- 기본적으로 게시물 1개당 최대 2장만 후보로 사용한다. 한 캐러셀 이미지가 결과를 독점하지 않게 하기 위함이다.
- 자세한 내용은 `script/ig_downloads/IGDOWNGUIDE.md`를 참고한다.

## 3. 브랜드 이미지 수집/매칭

자사몰 URL과 Instagram 다운로드 폴더를 함께 넣는 기본 명령:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://anderssonbell.com/" \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --brand-slug anderssonbell_combined \
  --max-pages 12 \
  --max-downloads 100
```

특정 run 이름으로 재생성하고 싶을 때:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://anderssonbell.com/" \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --brand-slug anderssonbell_combined \
  --run-id 20260601_evidence_view \
  --max-pages 12 \
  --max-downloads 100 \
  --overwrite
```

Instagram만 넣는 경우:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --instagram-folder "script/ig_downloads/downloads/profile_name" \
  --brand-slug example_instagram
```

자사몰만 넣는 경우:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://example-brand.com/" \
  --brand-slug example_brand
```

생성 위치:

```text
skill_ver/data/brand_runs/{brand_slug}_{run_id}/
```

주요 산출물:

```text
brand_source_images.json
brand_source_summary.json
portfolio_recommendations.json
index.html
source_images/
source_thumbnails/
```

`index.html`에서 확인할 것:

- 브랜드 상품 이미지 후보 10장이 자사몰 상품 상세로 연결되는가
- 브랜드 기획전/콜라보/프로젝트 후보 10장이 Instagram 게시글 또는 캠페인 출처로 연결되는가
- 유사 포트폴리오 10장이 어떤 브랜드 기준 이미지와 왜 연결됐는지 이해 가능한가
- 보완 제안 포트폴리오 10장이 브랜드에 새롭게 제안할 만한 방향을 주는가
- 태그 hover 설명이 즉시 보이는가
- 모바일/데스크톱에서 카드 정렬과 텍스트가 깨지지 않는가

검증:

```bash
python3 -m json.tool skill_ver/data/brand_runs/<run>/brand_source_images.json >/tmp/brand_source_images_check.json
python3 -m json.tool skill_ver/data/brand_runs/<run>/portfolio_recommendations.json >/tmp/portfolio_recommendations_check.json
```

## 4. 콜드메일/미니 제안서 생성

브랜드 매칭 run이 만들어진 뒤 `proposal-builder` 단계로 넘어간다.

기본 생성:

```bash
python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --brand-name "앤더슨벨" \
  --contact-name "브랜드 담당자님"
```

생성 위치:

```text
skill_ver/data/brand_runs/<run>/outreach_assets/
```

주요 산출물:

```text
outreach_assets.json
cold_email_draft.md
mini_proposal.html
```

`mini_proposal.html` 화면 구성:

- 콜드메일 초안
- 우리 포트폴리오와 유사한 이미지 10개
- 브랜드에는 부족하지만 우리에게 있는 이미지 10개
- `제안서 생성`
- `SECTION HTML 다운로드`
- `가로형 PDF 다운로드`

중요:

- `mini_proposal.html`은 내부 담당자용 선택 화면이다.
- 고객에게 보낼 SECTION에는 브랜드 레퍼런스 이미지, 자사몰/인스타 출처, 분석 태그를 노출하지 않는다.
- 콜드메일도 “자사몰과 Instagram을 분석했다”는 뉘앙스가 아니라, 브랜드를 관심 있게 보고 포트폴리오를 공유하는 톤을 유지한다.

## 5. 보낼 이미지 선택

기본값은 유사 3장, 보완 3장이다.

HTML에서 담당자가 직접 선택할 수 있다.

1. `mini_proposal.html`을 연다.
2. 유사/보완 후보 중 사용할 포트폴리오를 체크한다.
3. `제안서 생성`을 눌러 SECTION 미리보기를 확인한다.
4. 화면에서 선택한 portfolio ID를 기록한다.
5. 최종 PDF에는 그 ID를 CLI로 넘겨 다시 생성한다.

예시:

```bash
python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --brand-name "앤더슨벨" \
  --similar-ids P081 P082 P048 \
  --whitespace-ids P030 P083 P084
```

이 명령은 `mini_proposal.html`의 기본 체크 상태도 선택 ID 기준으로 다시 만든다.

## 6. 가로형 PDF 생성

기본 선택값으로 A4 landscape PDF를 만든다.

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view
```

명시한 portfolio ID로 PDF를 만들 때:

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --similar-ids P081 P082 P048 \
  --whitespace-ids P030 P083 P084
```

생성 산출물:

```text
proposal_sections_landscape.html
proposal_sections_landscape.pdf
```

PDF는 인쇄 창을 열지 않고 로컬 Chrome headless DevTools로 바로 파일 생성된다.

검증:

```bash
pdfinfo skill_ver/data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.pdf
```

확인할 값:

```text
Pages:           선택 장수 기준 예상 페이지 수
Page size:       841.92 x 594.96 pts (A4)
Encrypted:       no
```

PDF 페이지를 이미지로 확인하고 싶을 때:

```bash
mkdir -p output/playwright
pdftoppm -png -singlefile -f 1 -l 1 \
  skill_ver/data/brand_runs/<run>/outreach_assets/proposal_sections_landscape.pdf \
  output/playwright/proposal_first_page
```

## 7. 최종 검수 체크리스트

브랜드에 보내기 전 사람이 반드시 확인한다.

- 브랜드명과 담당자명이 맞는가
- 포트폴리오 이미지 외부 공유 권리가 있는가
- 클라이언트/프로젝트명이 외부 노출 가능한가
- 콜드메일이 자동 분석처럼 보이지 않는가
- 제안서 SECTION에 브랜드 레퍼런스 이미지나 분석 태그가 노출되지 않는가
- 유사 포트폴리오는 브랜드 현재 무드와 자연스럽게 이어지는가
- 보완 포트폴리오는 브랜드가 시도해볼 만한 새 방향을 주는가
- PDF가 A4 landscape이며 1페이지당 최대 3장씩 배치되는가
- 가격, 일정, 성과를 자동으로 단정하지 않았는가

## 자주 쓰는 전체 명령 예시

아래는 앤더슨벨 예시 전체 실행 순서다.

```bash
cd <project-root>

python3 skill_ver/scripts/build_portfolio_metadata.py \
  --source-dir portfolio_all \
  --slug portfolio_all

./script/ig_downloads/download_ig.command adsb_anderssonbell 20 chrome

python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://anderssonbell.com/" \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --brand-slug anderssonbell_combined \
  --run-id 20260601_evidence_view \
  --max-pages 12 \
  --max-downloads 100 \
  --overwrite

python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --brand-name "앤더슨벨" \
  --contact-name "브랜드 담당자님"

python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view
```

최종 확인 파일:

```text
skill_ver/portfolio_all_metadata_viewer.html
skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view/index.html
skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view/outreach_assets/cold_email_draft.md
skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view/outreach_assets/mini_proposal.html
skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view/outreach_assets/proposal_sections_landscape.pdf
```

## 문제 해결

### 자사몰 이미지가 너무 적게 수집될 때

- `--max-pages`를 늘린다.
- 컬렉션/룩북/캠페인 URL을 `--url`로 여러 개 넣는다.
- 정적 HTML에 이미지가 없으면 브라우저에서 저장한 HTML을 `--source-html`로 넣는 방식을 검토한다.

### Instagram 이미지가 안 받아질 때

- Chrome에서 Instagram 로그인 상태인지 확인한다.
- `script/ig_downloads/IGDOWNGUIDE.md`의 쿠키/권한 안내를 다시 확인한다.
- 계정명을 URL이 아니라 profile id로 넣는다. 예: `adsb_anderssonbell`

### 상품 후보와 캠페인 후보가 비슷해 보일 때

- 자사몰 URL과 Instagram 폴더를 함께 넣는다.
- 캠페인/룩북 URL을 추가한다.
- `index.html`에서 각 이미지의 원본 링크를 눌러 실제 출처가 상품 상세인지, Instagram 게시글인지 확인한다.

### PDF가 생성되지 않을 때

- Chrome 설치 여부를 확인한다.
- Chrome 경로가 특이하면 `--chrome-path`를 지정한다.

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/<run> \
  --chrome-path "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

### PDF 선택 이미지가 HTML 선택 상태와 다를 때

현재 `가로형 PDF 다운로드`는 이미 생성된 PDF를 내려받는다. HTML에서 체크만 바꿨다면 PDF 파일은 자동으로 바뀌지 않는다.

해결 방법:

1. HTML에서 선택한 portfolio ID를 확인한다.
2. `export_proposal_sections_pdf.py`에 `--similar-ids`, `--whitespace-ids`로 넘긴다.
3. PDF를 다시 생성한다.

## 운영 원칙

- 이 workflow는 1차 자동화다. 최종 발송 전에는 사람이 반드시 검수한다.
- 이미지 권리와 외부 공개 가능 여부를 확인하지 않은 포트폴리오는 고객용 PDF에 넣지 않는다.
- 브랜드에게 보내는 문장에는 “분석했다”, “태그가 반복됐다” 같은 표현을 피한다.
- 새 브랜드마다 결과가 완벽하다고 가정하지 말고, `index.html`에서 추천 근거를 먼저 검수한다.
- 스킬과 스크립트는 현재 워크스페이스 전용이다. 다른 프로젝트에 복사해 쓰려면 경로와 데이터 구조를 다시 확인한다.
