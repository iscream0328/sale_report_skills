# 인스타그램 로그인 기반 이미지 수집 워크플로우

이 문서는 `script/ig_downloads/IGDOWNGUIDE.md`의 gallery-dl 방식을 브랜드 포트폴리오 매칭 워크플로우에 연결하는 절차를 정리한다.

## 목표

Instagram 정적 HTML에서 이미지가 잡히지 않을 때, 사용자가 로그인한 브라우저 쿠키를 이용해 최근 게시물 이미지를 내려받고, 그 폴더를 `skill_ver/scripts/build_brand_url_matches.py`가 바로 분석하게 한다.

## 사전 조건

- Chrome 또는 사용할 브라우저에서 Instagram에 로그인되어 있어야 한다.
- 대상 프로필 피드가 브라우저에서 정상적으로 보여야 한다.
- `script/ig_downloads/download_ig.command`를 사용할 수 있어야 한다.

## 1. Instagram 이미지 다운로드

예시: 앤더슨벨 공식 인스타그램 `adsb_anderssonbell` 최근 20개 게시물 다운로드.

```bash
./script/ig_downloads/download_ig.command adsb_anderssonbell 20 chrome
```

실행 중 브라우저 프로필 페이지가 열리면 로그인 상태와 피드 노출을 확인한 뒤 Enter를 누른다.

다운로드 결과는 아래 폴더에 쌓인다.

```text
script/ig_downloads/downloads/adsb_anderssonbell/
```

이 폴더에는 이미지 파일, 영상 파일, 이미지별 `.jpg.json` 메타데이터, `info.json`이 들어간다. 현재 매칭 스크립트는 이미지 파일과 이미지별 JSON sidecar를 사용하고, 영상 파일은 건너뛴다.

매칭 스크립트는 Instagram 폴더를 읽을 때 `post_date` 최신순과 캐러셀 내부 순번순을 기준으로 정렬한다. 기본적으로 게시물 1개당 최대 2장만 사용하므로, 이미지가 많은 캐러셀 하나가 결과를 독점하지 않는다.

## 2. 자사몰과 Instagram을 함께 분석

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --url "https://anderssonbell.com/" \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --instagram-max-images-per-post 2 \
  --brand-slug anderssonbell
```

## 3. Instagram 폴더만 분석

자사몰 없이 Instagram 무드만 먼저 보고 싶을 때:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --instagram-max-images-per-post 2 \
  --brand-slug anderssonbell_instagram
```

게시물별 제한 없이 전체 이미지를 분석하고 싶을 때:

```bash
python3 skill_ver/scripts/build_brand_url_matches.py \
  --instagram-folder "script/ig_downloads/downloads/adsb_anderssonbell" \
  --instagram-max-images-per-post 0 \
  --brand-slug anderssonbell_instagram_full
```

## 4. 산출물 확인

기본 출력 위치:

```text
skill_ver/data/brand_runs/{brand_slug}_{YYYYMMDD_HHMMSS}/
```

주요 파일:

- `index.html`: 브랜드 수집 이미지, 유사 포트폴리오 10개, 보완 포트폴리오 10개 리뷰 화면
- `brand_source_images.json`: 자사몰/인스타에서 읽은 소스 이미지 분석 결과
- `brand_source_summary.json`: 수집 이미지 무드 요약
- `portfolio_recommendations.json`: 포트폴리오 추천 결과

## 5. 운영 메모

- `download_ig.command`는 `--cookies-from-browser`로 로그인 쿠키를 읽는다.
- 다운로드 수는 처음에는 10-30개 정도로 작게 시작한다.
- 이미지가 많은 캐러셀 계정은 게시물 수보다 실제 이미지 수가 훨씬 많아질 수 있으므로 `--instagram-max-images-per-post` 제한을 유지하는 편이 검수에 유리하다.
- Instagram 쪽 네트워크 제한이나 로그인 상태 문제는 `script/ig_downloads/logs/` 로그를 먼저 확인한다.
- 실제 제안서에 쓰기 전에는 브랜드 이미지 사용권과 포트폴리오 권리 검수를 별도로 진행한다.
