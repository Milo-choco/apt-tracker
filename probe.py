"""네이버부동산 알바트로스 매매 목록 화면을 열어서, 오가는 데이터(JSON)를 그대로 저장한다.
첫 실행은 '어떤 데이터가 오는지' 확인하는 용도다. 결과는 probe_output/ 폴더에 저장된다."""
import json
import os
from playwright.sync_api import sync_playwright

# 사용자가 준 주소 (단지번호 106550, 매매 탭)
URL = (
    "https://fin.land.naver.com/map?layer="
    "NobwRAlgJmBcYGMD2BbADgGwKYA8D6UWALgIYQZgA0YaJATiSgM5zjLrY4CSMsAjAAYAbAFYRAgL7UmWeggAWABXqMWs"
    "cKQBGcMPSIQE2Krrr7DWACoNCFgJ5osasAEE%2BYCRIC6QA"
)
OUT = "probe_output"
os.makedirs(OUT, exist_ok=True)

captured = []


def on_response(resp):
    try:
        ctype = resp.headers.get("content-type", "")
        if "json" not in ctype:
            return
        item = {
            "url": resp.url,
            "status": resp.status,
            "method": resp.request.method,
            "post_data": resp.request.post_data,
        }
        try:
            item["body"] = resp.text()[:300000]
        except Exception as e:  # 본문을 못 읽는 응답
            item["body_error"] = str(e)
        captured.append(item)
    except Exception as e:
        captured.append({"url": getattr(resp, "url", "?"), "error": str(e)})


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        locale="ko-KR",
        timezone_id="Asia/Seoul",
        viewport={"width": 1400, "height": 1000},
    )
    page = ctx.new_page()
    page.on("response", on_response)

    info = {"requested_url": URL}
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(15000)  # 데이터가 다 올 때까지 대기
        info["final_url"] = page.url
        info["title"] = page.title()
        try:
            info["body_text_head"] = page.inner_text("body")[:3000]
        except Exception as e:
            info["body_text_error"] = str(e)
        page.screenshot(path=os.path.join(OUT, "page.png"))
    except Exception as e:
        info["error"] = str(e)
        try:
            page.screenshot(path=os.path.join(OUT, "page.png"))
        except Exception:
            pass
    browser.close()

info["captured_count"] = len(captured)
with open(os.path.join(OUT, "info.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=2)
with open(os.path.join(OUT, "captured.json"), "w", encoding="utf-8") as f:
    json.dump(captured, f, ensure_ascii=False, indent=2)

print("captured:", len(captured))
print(json.dumps({k: info.get(k) for k in ("final_url", "title", "error")}, ensure_ascii=False))
