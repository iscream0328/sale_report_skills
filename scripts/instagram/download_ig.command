#!/bin/zsh

set -euo pipefail

cd "$(dirname "$0")"

echo "======================================"
echo " Instagram gallery-dl Downloader"
echo "======================================"
echo ""

PROFILE="${1:-}"
COUNT="${2:-}"
BROWSER="${3:-}"

if [[ -z "$PROFILE" ]]; then
  echo "다운로드할 Instagram 계정명을 입력하세요."
  echo "예: 23st5dio"
  read "PROFILE?> "
fi

if [[ -z "$COUNT" ]]; then
  echo ""
  echo "최근 몇 개 게시물을 받을까요?"
  echo "예: 5, 10, 30"
  read "COUNT?> "
fi

if [[ -z "$BROWSER" ]]; then
  echo ""
  echo "쿠키를 가져올 브라우저를 입력하세요. 기본값: chrome"
  echo "가능 예시: chrome, firefox, safari, edge, brave"
  read "BROWSER?> "
  BROWSER="${BROWSER:-chrome}"
fi

if [[ -z "$PROFILE" ]]; then
  echo "계정명이 비어 있습니다."
  exit 1
fi

if ! [[ "$COUNT" =~ '^[0-9]+$' ]]; then
  echo "게시물 개수는 숫자로 입력해야 합니다."
  exit 1
fi

if [[ "$COUNT" -lt 1 ]]; then
  echo "게시물 개수는 1 이상이어야 합니다."
  exit 1
fi

URL="https://www.instagram.com/${PROFILE}/"
POST_RANGE="1-${COUNT}"
OUTPUT_DIR="./downloads/${PROFILE}"
ARCHIVE_DIR="./archive"
LOG_DIR="./logs"
LOG_FILE="${LOG_DIR}/${PROFILE}_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$OUTPUT_DIR" "$ARCHIVE_DIR" "$LOG_DIR"

echo ""
echo "Profile      : ${PROFILE}"
echo "Recent posts : ${COUNT}"
echo "Browser      : ${BROWSER}"
echo "Output       : ${OUTPUT_DIR}"
echo "URL          : ${URL}"
echo ""

echo "gallery-dl 설치/업데이트 확인 중..."
python3 -m pip install -U gallery-dl

echo ""
echo "gallery-dl version:"
gallery-dl --version

echo ""
echo "브라우저에서 Instagram 로그인 상태를 확인합니다."
echo "프로필 페이지가 열리면 피드가 정상적으로 보이는지 확인하세요."
open "$URL" || true

echo ""
echo "확인했으면 Enter를 누르세요."
read "?계속하려면 Enter..."

echo ""
echo "다운로드 시작..."
echo "로그 파일: ${LOG_FILE}"
echo ""

gallery-dl \
  --cookies-from-browser "${BROWSER}" \
  --post-range "${POST_RANGE}" \
  --sleep 5-10 \
  --sleep-request 8-15 \
  --sleep-429 300 \
  --write-metadata \
  --write-info-json \
  --download-archive "${ARCHIVE_DIR}/${PROFILE}.txt" \
  -D "${OUTPUT_DIR}" \
  "${URL}" 2>&1 | tee "${LOG_FILE}"

echo ""
echo "======================================"
echo "완료"
echo "저장 위치: ${OUTPUT_DIR}"
echo "로그 위치: ${LOG_FILE}"
echo "======================================"

echo ""
echo "창을 닫으려면 Enter를 누르세요."
read "?Enter..."
