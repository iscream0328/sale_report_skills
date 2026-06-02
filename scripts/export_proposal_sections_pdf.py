#!/usr/bin/env python3
"""Export proposal SECTION pages as a landscape PDF without opening print UI."""

from __future__ import annotations

import argparse
import base64
import html
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import websocket


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_DIR = ROOT / "data" / "brand_runs"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def e(value: Any) -> str:
    return html.escape(str(value or ""))


def chunk(records: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [records[index : index + size] for index in range(0, len(records), size)]


def find_chrome(explicit_path: str | None = None) -> str:
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    candidates.extend(
        [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    )
    candidates.extend(
        path
        for path in [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            shutil.which("chrome"),
            shutil.which("msedge"),
        ]
        if path
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError("Chrome/Chromium executable not found. Pass --chrome-path.")


def select_records(pool: list[dict[str, Any]], selected_ids: list[str]) -> list[dict[str, Any]]:
    lookup = {record.get("portfolio_id"): record for record in pool}
    missing = [portfolio_id for portfolio_id in selected_ids if portfolio_id not in lookup]
    if missing:
        raise ValueError(f"Unknown portfolio_id: {', '.join(missing)}")
    return [lookup[portfolio_id] for portfolio_id in selected_ids]


def image_uri(output_dir: Path, src: str | None) -> str:
    if not src:
        return ""
    if src.startswith(("http://", "https://", "file://", "data:")):
        return src
    return (output_dir / src).resolve().as_uri()


def portfolio_card(record: dict[str, Any], output_dir: Path) -> str:
    image_src = image_uri(output_dir, record.get("image_src"))
    proposal_point = record.get("portfolio_scenario") or record.get("proposal_use") or ""
    return f"""
      <article class="portfolio-card">
        <img src="{e(image_src)}" alt="{e(record.get('portfolio_id'))}">
        <div class="copy">
          <div class="eyebrow">{e(record.get('portfolio_id'))} · {e(record.get('cut_type_label'))}</div>
          <h3>{e(record.get('client_or_project'))}</h3>
          <div class="field"><strong>작업 범위</strong><span>{e(record.get('work_scope_label'))}</span></div>
          <div class="field"><strong>촬영 느낌</strong><span>{e(record.get('portfolio_mood'))}</span></div>
          <div class="field"><strong>제안 포인트</strong><span>{e(proposal_point)}</span></div>
        </div>
      </article>
    """


def section_pages(section_type: str, records: list[dict[str, Any]], output_dir: Path) -> str:
    if not records:
        return ""
    label = "SECTION 1" if section_type == "similar" else "SECTION 2"
    title = "브랜드 무드와 결이 맞는 포트폴리오" if section_type == "similar" else "다른 방향으로 확장 가능한 포트폴리오"
    pages = chunk(records, 3)
    page_html = []
    for index, page in enumerate(pages, start=1):
        cards = "".join(portfolio_card(record, output_dir) for record in page)
        page_html.append(
            f"""
            <section class="page">
              <header>
                <div>
                  <div class="eyebrow">{label}</div>
                  <h2>{e(title)}</h2>
                </div>
                <div class="page-no">{index} / {len(pages)}</div>
              </header>
              <div class="cards">{cards}</div>
            </section>
            """
        )
    return "\n".join(page_html)


def build_html(asset: dict[str, Any], output_dir: Path, similar: list[dict[str, Any]], whitespace: list[dict[str, Any]]) -> str:
    body = section_pages("similar", similar, output_dir) + section_pages("whitespace", whitespace, output_dir)
    if not body:
        body = '<section class="page"><div class="empty">선택된 포트폴리오가 없습니다.</div></section>'
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(asset.get("brand_name"))} Proposal Sections Landscape</title>
  <link rel="icon" href="data:,">
  <style>
    @page {{ size: A4 landscape; margin: 10mm; }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; }}
    body {{ background: #f6f0e8; color: #17120f; font-family: Inter, -apple-system, BlinkMacSystemFont, "Noto Sans KR", sans-serif; line-height: 1.35; }}
    .page {{
      width: 277mm;
      height: 190mm;
      margin: 0 auto 12mm;
      padding: 10mm;
      background: #fff;
      border: 1px solid rgba(30,24,20,.12);
      border-radius: 5mm;
      break-after: page;
      page-break-after: always;
      overflow: hidden;
    }}
    .page:last-child {{ break-after: auto; page-break-after: auto; }}
    header {{ display: flex; justify-content: space-between; gap: 10mm; align-items: start; border-bottom: 1px solid rgba(30,24,20,.12); padding-bottom: 5mm; margin-bottom: 6mm; }}
    .eyebrow {{ color: #b23c16; font-size: 9pt; font-weight: 800; text-transform: uppercase; }}
    h2 {{ margin: 1mm 0 0; font-size: 20pt; line-height: 1.15; letter-spacing: 0; }}
    .page-no {{ color: #6f6258; font-size: 10pt; white-space: nowrap; }}
    .cards {{ display: flex; gap: 7mm; align-items: stretch; }}
    .portfolio-card {{ flex: 1 1 0; width: calc((100% - 14mm) / 3); min-width: 0; border: 1px solid rgba(30,24,20,.12); border-radius: 3mm; overflow: hidden; background: #fbfaf7; break-inside: avoid; }}
    .portfolio-card img {{ display: block; width: 100%; height: 62mm; object-fit: cover; background: #fff3cf; }}
    .copy {{ padding: 3.2mm; display: grid; gap: 1.6mm; }}
    h3 {{ margin: 0; font-size: 12.5pt; line-height: 1.18; overflow-wrap: anywhere; }}
    .field strong {{ display: block; color: #b23c16; font-size: 8pt; text-transform: uppercase; margin-bottom: 1mm; }}
    .field span {{ display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; overflow: hidden; color: #302821; font-size: 8.5pt; line-height: 1.3; }}
    .empty {{ color: #665d54; border: 1px dashed rgba(30,24,20,.2); border-radius: 3mm; padding: 8mm; }}
    @media print {{
      body {{ background: #fff; }}
      .page {{ margin: 0; border: 0; border-radius: 0; }}
    }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def read_json_url(url: str, timeout: float = 0.5) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_cdp(port: int, timeout_s: float) -> None:
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            read_json_url(f"http://127.0.0.1:{port}/json/version")
            return
        except Exception as error:  # noqa: BLE001 - keep retrying until Chrome opens CDP.
            last_error = error
            time.sleep(0.1)
    raise RuntimeError(f"Chrome DevTools did not become ready: {last_error}")


def create_cdp_target(port: int, html_uri: str) -> dict[str, Any]:
    target_url = f"http://127.0.0.1:{port}/json/new?{urllib.parse.quote(html_uri, safe=':/?&=%')}"
    for method in ("PUT", "GET"):
        request = urllib.request.Request(target_url, method=method)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if method == "GET":
                raise
    raise RuntimeError("Could not create Chrome DevTools target.")


def cdp_call(ws: websocket.WebSocket, counter: dict[str, int], method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    counter["value"] += 1
    message_id = counter["value"]
    ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == message_id:
            if "error" in message:
                raise RuntimeError(f"CDP {method} failed: {message['error']}")
            return message.get("result", {})


def wait_for_load(ws: websocket.WebSocket, timeout_s: float) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        ws.settimeout(max(0.1, min(1.0, deadline - time.time())))
        try:
            message = json.loads(ws.recv())
        except TimeoutError:
            continue
        except websocket.WebSocketTimeoutException:
            continue
        if message.get("method") == "Page.loadEventFired":
            return


def export_pdf(html_path: Path, pdf_path: Path, chrome_path: str | None = None, timeout_ms: int = 15000) -> None:
    chrome = find_chrome(chrome_path)
    port = free_port()
    with tempfile.TemporaryDirectory(prefix="proposal-pdf-chrome-") as profile_dir:
        command = [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--disable-extensions",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            "--allow-file-access-from-files",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile_dir}",
            f"--remote-debugging-port={port}",
            "about:blank",
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            wait_for_cdp(port, timeout_ms / 1000)
            target = create_cdp_target(port, html_path.resolve().as_uri())
            ws = None
            ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=timeout_ms / 1000)
            counter = {"value": 0}
            try:
                cdp_call(ws, counter, "Page.enable")
                cdp_call(ws, counter, "Page.navigate", {"url": html_path.resolve().as_uri()})
                wait_for_load(ws, timeout_ms / 1000)
                cdp_call(
                    ws,
                    counter,
                    "Runtime.evaluate",
                    {
                        "expression": "Promise.all(Array.from(document.images).map((img) => img.decode().catch(() => true))).then(() => true)",
                        "awaitPromise": True,
                        "returnByValue": True,
                    },
                )
                result = cdp_call(
                    ws,
                    counter,
                    "Page.printToPDF",
                    {
                        "landscape": True,
                        "displayHeaderFooter": False,
                        "printBackground": True,
                        "preferCSSPageSize": True,
                        "marginTop": 0,
                        "marginBottom": 0,
                        "marginLeft": 0,
                        "marginRight": 0,
                    },
                )
                pdf_path.write_bytes(base64.b64decode(result["data"]))
                try:
                    cdp_call(ws, counter, "Browser.close")
                except Exception:
                    pass
            finally:
                if ws is not None:
                    ws.close()
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export selected proposal sections as a landscape PDF.")
    parser.add_argument("--run-dir", type=Path, required=True, help="brand matching run directory")
    parser.add_argument("--output-dir", type=Path, help="defaults to <run-dir>/outreach_assets")
    parser.add_argument("--similar-ids", nargs="*", help="portfolio IDs for SECTION 1")
    parser.add_argument("--whitespace-ids", nargs="*", help="portfolio IDs for SECTION 2")
    parser.add_argument("--html-name", default="proposal_sections_landscape.html")
    parser.add_argument("--pdf-name", default="proposal_sections_landscape.pdf")
    parser.add_argument("--chrome-path", help="optional Chrome/Chromium executable path")
    parser.add_argument("--html-only", action="store_true", help="write HTML but skip PDF export")
    parser.add_argument("--timeout-ms", type=int, default=15000, help="Chrome PDF export timeout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    output_dir = (args.output_dir or (run_dir / "outreach_assets")).resolve()
    asset_path = output_dir / "outreach_assets.json"
    asset = load_json(asset_path)

    similar_ids = args.similar_ids or asset.get("selected_defaults", {}).get("similar", [])
    whitespace_ids = args.whitespace_ids or asset.get("selected_defaults", {}).get("whitespace", [])
    similar = select_records(asset.get("candidate_pools", {}).get("similar", []), similar_ids)
    whitespace = select_records(asset.get("candidate_pools", {}).get("whitespace", []), whitespace_ids)

    html_path = output_dir / args.html_name
    pdf_path = output_dir / args.pdf_name
    html_path.write_text(build_html(asset, output_dir, similar, whitespace), encoding="utf-8")
    if not args.html_only:
        export_pdf(html_path, pdf_path, args.chrome_path, args.timeout_ms)

    result = {
        "brand_name": asset.get("brand_name"),
        "html": str(html_path),
        "pdf": None if args.html_only else str(pdf_path),
        "similar_count": len(similar),
        "whitespace_count": len(whitespace),
        "page_count_expected": (len(similar) + 2) // 3 + (len(whitespace) + 2) // 3,
        "orientation": "landscape",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
