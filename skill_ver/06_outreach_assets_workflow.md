# 콜드메일 및 미니 제안서 생성 워크플로우

이 문서는 `brand_image_matching` 결과 폴더를 입력으로 받아 브랜드에 보낼 콜드메일 초안과 이미지 중심 미니 제안서를 만드는 절차를 정의한다.

## 목표

브랜드 이미지 매칭 run에서 생성된 아래 파일을 재사용한다.

- `brand_source_summary.json`
- `brand_source_images.json`
- `portfolio_recommendations.json`
- `source_thumbnails/`
- `skill_ver/data/portfolio_all_thumbnails/`

출력은 같은 run 폴더의 `outreach_assets/` 아래에 만든다.

```text
skill_ver/data/brand_runs/{run}/outreach_assets/
├── outreach_assets.json
├── cold_email_draft.md
├── mini_proposal.html
├── proposal_sections_landscape.html
└── proposal_sections_landscape.pdf
```

## 실행 명령

기본값은 유사 추천 3개, 보완 추천 3개를 사용한다.

```bash
python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --brand-name "앤더슨벨" \
  --contact-name "브랜드 담당자님"
```

사용자가 보낼 이미지를 직접 고른 뒤 CLI로 기본 선택값을 지정해서 다시 만들 때:

```bash
python3 skill_ver/scripts/build_brand_outreach_assets.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --brand-name "앤더슨벨" \
  --similar-ids P081 P048 P055 \
  --whitespace-ids P030 P083 P117
```

## 산출물 의미

### `outreach_assets.json`

메일과 제안서에 들어가는 구조화 데이터다.

- 브랜드명
- 현재 브랜드 관찰 요약
- 사용 브랜드 소스 이미지
- 선택된 유사 포트폴리오
- 선택된 보완 포트폴리오
- 제안 컨셉 3개
- 콜드메일 제목 후보와 본문
- 발송 전 검수 체크리스트

### `cold_email_draft.md`

영업 담당자가 바로 읽고 고칠 수 있는 Markdown 메일 초안이다.

메일 구조:

1. 브랜드 이미지를 실제로 봤다는 도입
2. 현재 이미지의 강점
3. 보완 가능한 지점
4. 선택 포트폴리오와 연결되는 제안
5. 20분 미팅 또는 레퍼런스 보드 공유 제안

### `mini_proposal.html`

브라우저에서 검수하는 담당자용 제안서 제작 화면이다.

구성:

1. 콜드메일 초안
2. `우리 포트폴리오와 유사한 이미지 10개` 선택 영역
3. `브랜드에는 부족하지만 우리에게 있는 이미지 10개` 선택 영역
4. `제안서 생성` 버튼
5. 선택된 우리 포트폴리오만으로 구성된 제안서 미리보기
6. `SECTION HTML 다운로드` 버튼
7. `가로형 PDF 다운로드` 링크

제안서 미리보기에는 브랜드 레퍼런스 이미지나 분석 태그를 넣지 않는다. 우리 포트폴리오의 이미지, 촬영 브랜드/프로젝트, 작업 범위, 촬영 느낌, 제안 포인트만 보여준다.

`SECTION HTML 다운로드`는 현재 체크된 포트폴리오만 포함한 별도 HTML 파일을 만든다. 이 HTML은 내부 편집 화면, 콜드메일, 후보 선택 영역 없이 SECTION 페이지만 포함한다. 이미지 경로는 절대 URL로 변환해, 다운로드된 HTML을 따로 열어도 이미지가 끊기지 않게 한다.

`가로형 PDF 다운로드`는 별도 export 명령으로 미리 생성된 `proposal_sections_landscape.pdf`를 내려받는다. 기본값은 `outreach_assets.json`의 `selected_defaults`를 사용하고, 필요한 경우 선택한 portfolio ID를 직접 넘겨 PDF를 다시 만든다.

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view
```

선택 ID를 지정하는 예:

```bash
python3 skill_ver/scripts/export_proposal_sections_pdf.py \
  --run-dir skill_ver/data/brand_runs/anderssonbell_combined_20260601_evidence_view \
  --similar-ids P081 P082 P048 \
  --whitespace-ids P030 P083 P084
```

이 명령은 `proposal_sections_landscape.html`과 `proposal_sections_landscape.pdf`를 만든다. `mini_proposal.html`의 `가로형 PDF 다운로드` 링크는 이 PDF 파일을 직접 내려받는다.

## 선택 기준

기본 자동 선택은 `portfolio_recommendations.json` 순위를 따른다.

- 유사 포트폴리오: `similar_recommendations` 상위 3개
- 보완 포트폴리오: `whitespace_recommendations` 상위 3개

HTML 화면에서는 10+10 후보를 모두 보여주며 담당자가 체크박스로 최종 이미지를 고른다. `제안서 생성`을 누르면 선택된 이미지를 1페이지당 최대 3장씩 나눠 보여준다. HTML 다운로드는 현재 화면의 선택 상태를 사용하고, 가로형 PDF는 export 명령에 넘긴 선택 ID 또는 기본 선택값을 사용한다.

실제 발송 전에는 담당자가 HTML에서 이미지를 고르거나, 이미지 ID를 CLI에 직접 넘겨 재생성하는 것이 좋다.

## 검수 기준

- 브랜드 후보 이미지 분류가 납득 가능한가
- 유사 포트폴리오가 실제 브랜드 이미지와 시각적으로 이어지는가
- 보완 포트폴리오가 브랜드에 무리 없이 제안 가능한가
- 메일 본문이 기계적인 분석 문장처럼 보이지 않고, 브랜드에 관심을 갖고 포트폴리오를 전달하는 톤인가
- 생성된 제안서가 우리 포트폴리오 설명 중심으로 구성됐는가
- SECTION HTML/PDF에 내부 편집 UI, 콜드메일, 브랜드 레퍼런스 이미지가 섞이지 않는가
- PDF가 선택 포트폴리오를 1페이지당 3장 단위로 묶는가
- `proposal_sections_landscape.pdf`가 A4 landscape인지 확인했는가
- 상품명, 담당자명, 브랜드명, 권리 사용 가능 여부가 확인됐는가

## 한계

- 문구는 현재 메타와 휴리스틱을 기반으로 생성한 초안이다.
- 외부 발송 전 사람이 반드시 브랜드명, 권리, 제안 범위, 톤을 검수해야 한다.
- 가격, 일정, 성과, 매출 효과는 자동으로 단정하지 않는다.
