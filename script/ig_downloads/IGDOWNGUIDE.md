# IGDOWNGUIDE.md

## Instagram 이미지 다운로드 도구 사용 가이드

이 문서는 `gallery-dl`을 이용해 Instagram 프로필의 최근 게시물 이미지를 다운로드하는 `download_ig.command` 사용법을 정리한 가이드입니다.

기준 환경은 macOS입니다.

---

## 1. 전체 구조

사용할 폴더 구조는 아래와 같습니다.

```text
ig-gallery-downloader/
├── download_ig.command
├── downloads/
│   └── 23st5dio/
│       ├── 이미지/영상 파일
│       ├── metadata 파일
│       └── info.json
├── archive/
│   └── 23st5dio.txt
└── logs/
    └── 23st5dio_YYYYMMDD_HHMMSS.log
```

각 폴더의 역할은 다음과 같습니다.

| 경로 | 설명 |
|---|---|
| `download_ig.command` | Instagram 다운로드 실행 파일 |
| `downloads/` | 다운로드된 이미지, 영상, 메타데이터 저장 위치 |
| `archive/` | 이미 다운로드한 게시물을 중복 다운로드하지 않기 위한 기록 파일 |
| `logs/` | 실행 로그 저장 위치 |

---

## 2. 작업 폴더 생성

원하는 위치에 다운로드 도구용 폴더를 만듭니다.

예시는 사용자 홈 폴더 기준입니다.

```bash
mkdir -p ~/ig-gallery-downloader
cd ~/ig-gallery-downloader
```

---

## 3. `download_ig.command` 파일 생성

아래 명령어로 실행 파일을 생성합니다.

```bash
nano download_ig.command
```

아래 내용을 그대로 붙여넣습니다.

```zsh
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
```

저장 방법은 다음과 같습니다.

```text
Ctrl + O → Enter → Ctrl + X
```

---

## 4. 실행 권한 부여

`download_ig.command` 파일을 실행할 수 있도록 권한을 부여합니다.

```bash
chmod +x download_ig.command
```

권한이 제대로 들어갔는지 확인하려면 아래 명령어를 실행합니다.

```bash
ls -al download_ig.command
```

아래처럼 `x`가 포함되어 있으면 실행 권한이 부여된 상태입니다.

```text
-rwxr-xr-x  1 user  staff  ... download_ig.command
```

---

## 5. 실행 전 준비사항

Chrome에서 Instagram에 로그인되어 있어야 합니다.

먼저 브라우저에서 대상 프로필을 열어 피드가 정상적으로 보이는지 확인합니다.

```bash
open "https://www.instagram.com/23st5dio/"
```

정상적으로 보이면 다운로드를 실행합니다.

---

## 6. 실행 방법 1: 더블클릭 실행

Finder에서 아래 폴더를 엽니다.

```text
~/ig-gallery-downloader
```

`download_ig.command` 파일을 더블클릭합니다.

실행하면 아래 정보를 순서대로 입력합니다.

```text
다운로드할 Instagram 계정명: 23st5dio
최근 몇 개 게시물: 10
브라우저: chrome
```

브라우저 입력값은 비워두면 기본값으로 `chrome`이 사용됩니다.

---

## 7. 실행 방법 2: 명령어로 실행

폴더 안에서 아래 형식으로 실행할 수 있습니다.

```bash
./download_ig.command 계정명 최근게시물개수 브라우저
```

예시입니다.

```bash
./download_ig.command 23st5dio 10 chrome
```

위 명령어는 `23st5dio` 계정의 최근 10개 게시물을 Chrome 로그인 쿠키를 이용해 다운로드합니다.

최근 5개만 받으려면 다음과 같이 실행합니다.

```bash
./download_ig.command 23st5dio 5 chrome
```

Firefox 쿠키를 사용하려면 다음과 같이 실행합니다.

```bash
./download_ig.command 23st5dio 10 firefox
```

---

## 8. 최근 n개 게시물 다운로드 기준

스크립트는 `gallery-dl`의 `--post-range` 옵션을 사용합니다.

예를 들어 아래 명령어는 최근 10개 게시물을 대상으로 합니다.

```bash
./download_ig.command 23st5dio 10 chrome
```

내부적으로는 다음 범위가 적용됩니다.

```text
--post-range 1-10
```

주의할 점은 **게시물 기준**이라는 것입니다.

즉, 최근 10개 게시물을 받더라도 캐러셀 게시물이 포함되어 있으면 실제 저장되는 이미지 파일 수는 10개보다 많을 수 있습니다.

---

## 9. 저장 위치

다운로드 결과는 아래 위치에 저장됩니다.

```text
./downloads/계정명/
```

예시입니다.

```text
./downloads/23st5dio/
```

실행 로그는 아래 위치에 저장됩니다.

```text
./logs/
```

중복 다운로드 방지 기록은 아래 위치에 저장됩니다.

```text
./archive/계정명.txt
```

---

## 10. 중복 다운로드 초기화

이미 받은 게시물을 다시 받고 싶으면 해당 계정의 archive 파일을 삭제합니다.

예시입니다.

```bash
rm ./archive/23st5dio.txt
```

그다음 다시 실행합니다.

```bash
./download_ig.command 23st5dio 10 chrome
```

---

## 11. 자주 발생하는 문제

### 11.1 `Permission denied`가 나올 때

실행 권한이 없는 상태입니다.

```bash
chmod +x download_ig.command
```

다시 실행합니다.

```bash
./download_ig.command 23st5dio 10 chrome
```

---

### 11.2 `command not found: gallery-dl`이 나올 때

스크립트가 실행 중 `gallery-dl`을 설치하지만, PATH 문제로 바로 인식되지 않을 수 있습니다.

아래 명령어로 직접 설치합니다.

```bash
python3 -m pip install -U gallery-dl
```

설치 확인:

```bash
gallery-dl --version
```

그래도 안 되면 아래처럼 Python 모듈 방식으로 실행하도록 스크립트를 바꿀 수 있습니다.

기존:

```bash
gallery-dl \
```

변경:

```bash
python3 -m gallery_dl \
```

---

### 11.3 Chrome 쿠키를 못 읽을 때

Chrome이 실행 중이거나 macOS 권한 문제로 쿠키를 읽지 못할 수 있습니다.

대안은 Firefox를 사용하는 것입니다.

1. Firefox 설치
2. Firefox에서 Instagram 로그인
3. 아래 명령어 실행

```bash
./download_ig.command 23st5dio 10 firefox
```

---

### 11.4 429 또는 Too Many Requests가 나올 때

Instagram에서 요청이 많다고 판단한 상태입니다.

이 경우 반복 실행하지 말고 잠시 중단하는 것이 좋습니다.

스크립트에는 아래 옵션이 포함되어 있습니다.

```bash
--sleep 5-10
--sleep-request 8-15
--sleep-429 300
```

그래도 429가 계속 나오면 다음을 시도합니다.

```bash
./download_ig.command 23st5dio 3 chrome
```

적은 개수로 테스트한 뒤, 시간이 지난 후 다시 실행합니다.

---

### 11.5 브라우저에서는 보이는데 다운로드가 안 될 때

아래 순서로 확인합니다.

1. Chrome에서 Instagram 로그인이 되어 있는지 확인
2. 대상 프로필 페이지가 정상적으로 열리는지 확인
3. Chrome 대신 Firefox로 로그인 후 실행
4. 최근 게시물 개수를 3개 이하로 줄여 테스트

예시:

```bash
./download_ig.command 23st5dio 3 firefox
```

---

## 12. 권장 사용 순서

처음에는 적은 개수로 테스트합니다.

```bash
./download_ig.command 23st5dio 3 chrome
```

정상 동작하면 개수를 늘립니다.

```bash
./download_ig.command 23st5dio 10 chrome
```

더 많이 받을 때는 너무 자주 반복 실행하지 않는 것이 좋습니다.

```bash
./download_ig.command 23st5dio 30 chrome
```

---

## 13. Instaloader 정리 명령어

기존 Instaloader를 더 이상 사용하지 않을 경우 아래 명령어로 삭제할 수 있습니다.

```bash
python3 -m pip uninstall -y instaloader browser-cookie3
rm -f ~/.config/instaloader/session-smoh89
```

이전에 만들었던 fallback 스크립트가 있다면 삭제합니다.

```bash
rm -f ig_fallback_download.py
```

---

## 14. 최종 요약

가장 기본적인 사용 흐름은 아래와 같습니다.

```bash
mkdir -p ~/ig-gallery-downloader
cd ~/ig-gallery-downloader
nano download_ig.command
chmod +x download_ig.command
./download_ig.command 23st5dio 10 chrome
```

더블클릭으로 실행하고 싶다면 Finder에서 `download_ig.command` 파일을 실행하면 됩니다.

