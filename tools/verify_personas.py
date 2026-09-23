"""Exercise first-time, developer and mobile journeys; no AI or paid services."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    server = None
    base = os.environ.get("SITE_URL")
    if not base:
        server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT / "site")))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}/"
    output = ROOT / "artifacts/personas"
    output.mkdir(parents=True, exist_ok=True)
    results = []
    axe = os.environ.get("AXE_PATH")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in ("ja", "en"):
            for width in (320, 390, 768, 1440):
                context = browser.new_context(viewport={"width": width, "height": 900}, permissions=["clipboard-read", "clipboard-write"])
                page = context.new_page()
                page.add_init_script("window.layoutShifts=0;new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(!e.hadRecentInput)window.layoutShifts+=e.value})).observe({type:'layout-shift',buffered:true})")
                requests, errors = [], []
                page.on("request", lambda r: requests.append(r))
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(base + "?lang=" + lang, wait_until="networkidle")
                assert page.locator("h1").count() == 1
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (lang, width)
                assert page.locator(".hero .primary").bounding_box()["y"] < 700
                assert not any("demo.mp4" in r.url for r in requests), "video loaded before play"
                assert all(r.url.startswith(base) for r in requests), "unexpected third-party runtime"
                assert page.evaluate("layoutShifts") <= .1
                for key in ("install-command", "extension-path", "ai-request"):
                    page.locator(f'[data-copy="{key}"]').click()
                    actual = page.evaluate("navigator.clipboard.readText()")
                    assert actual == page.locator("#" + key).text_content().strip(), key
                # A local success, with no form request or secret persistence.
                page.locator('#practice-form button[type="submit"]').click()
                assert page.locator("#practice-note").get_attribute("aria-invalid") == "true"
                count = len(requests)
                page.locator("#practice-note").fill("日本語 <script>alert(1)</script>")
                page.locator('#practice-form button[type="submit"]').click()
                assert page.locator("#practice-note").get_attribute("aria-invalid") == "false"
                assert "外部送信" in page.locator("#practice-result").inner_text() if lang == "ja" else "Nothing was sent" in page.locator("#practice-result").inner_text()
                page.locator('#practice-form button[type="reset"]').click()
                assert page.locator("#practice-note").input_value() == ""
                assert len(requests) == count
                # Clipboard denial must have a usable manual path and restore focus.
                page.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true})")
                control = page.locator('[data-copy="install-command"]')
                control.click()
                assert page.locator("#copy-fallback").is_visible()
                assert page.locator("#fallback-text").input_value() == "python3 install.py"
                page.keyboard.press("Escape")
                assert page.locator("#copy-fallback").is_hidden()
                assert control.evaluate("e=>document.activeElement===e")
                page.locator("#language").click()
                assert page.locator("html").get_attribute("lang") != lang
                page.locator("#language").click()
                page.keyboard.press("Control+Home")
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(output / f"{lang}-{width}.png"), full_page=True)
                violations = []
                if axe:
                    page.add_script_tag(path=axe)
                    report = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa']}})")
                    violations = [{"id": v["id"], "impact": v["impact"], "targets": [n["target"] for n in v["nodes"]]} for v in report["violations"]]
                results.append({"lang": lang, "width": width, "axe": violations, "cls": page.evaluate("layoutShifts"), "errors": errors})
                context.close()
        mobile = browser.new_context(**p.devices["iPhone 13"])
        page = mobile.new_page()
        page.goto(base + "?lang=en")
        assert page.locator("#device-note").is_visible()
        assert "Mac" in page.locator("#device-note").inner_text()
        assert page.locator(".hero .primary").get_attribute("href") == "#install"
        mobile.close()
        context = browser.new_context()
        page = context.new_page()
        page.goto(base + "?lang=en")
        page.keyboard.press("Tab")
        assert page.locator(".skip").evaluate("e=>document.activeElement===e")
        page.keyboard.press("Enter")
        assert page.locator("#main").evaluate("e=>document.activeElement===e")
        browser.close()
    (output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
    if server:
        server.shutdown()
    assert not any(r["errors"] or r["axe"] for r in results), results
    print("PASS: 8 ja/en viewport journeys, clipboard/fallback, local practice/reset, mobile path, keyboard skip; axe:", bool(axe))


if __name__ == "__main__":
    main()
