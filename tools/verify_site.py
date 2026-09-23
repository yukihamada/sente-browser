"""Check ja/en mobile/desktop layout, links, images, and actual video playback."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    remote = os.environ.get("SITE_URL")
    server = None
    if not remote:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT / "site"))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        remote = f"http://127.0.0.1:{server.server_port}/"
    output = ROOT / "artifacts/site"
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in ("ja", "en"):
            for width in (390, 1440):
                page = browser.new_page(viewport={"width": width, "height": 1000})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                response = page.goto(remote + "?lang=" + lang)
                assert response.status == 200
                assert page.locator("html").get_attribute("lang") == lang
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (lang, width)
                assert page.locator("h1").inner_text().startswith("今" if lang == "ja" else "Work")
                for platform, command, path_part in (("windows", "py -3 install.py", "%LOCALAPPDATA%"),
                                                       ("linux", "python3 install.py", ".local/share"),
                                                       ("macos", "python3 install.py", "Library")):
                    page.locator("#platform").select_option(platform)
                    assert page.locator("#install-command").inner_text() == command
                    assert path_part in page.locator("#extension-path").inner_text()
                    assert ("%LOCALAPPDATA%" in page.locator("#ai-request").inner_text()) == (platform == "windows")
                    page.locator("#language").click()
                    assert page.locator("#platform").input_value() == platform
                    assert page.locator("#install-command").inner_text() == command
                    page.locator("#language").click()
                assert page.evaluate("[...document.images].every(i=>i.complete&&i.naturalWidth>0)")
                for link in page.locator('a[href^="#"]').all():
                    assert page.locator(link.get_attribute("href")).count() == 1
                page.locator("video").evaluate("v=>v.play()")
                page.wait_for_function("document.querySelector('video').currentTime > .5")
                video = page.locator("video").evaluate("v=>({width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error})")
                assert video["width"] == 1280 and video["height"] == 720 and video["duration"] > 20 and not video["error"], video
                page.locator("video").evaluate("v=>v.pause()")
                page.screenshot(path=str(output / f"{lang}-{width}.png"), full_page=True)
                page.locator("#language").click()
                assert page.locator("html").get_attribute("lang") != lang
                assert not errors, errors
                page.close()
        page = browser.new_page()
        assert page.goto(remote + "privacy.html").status == 200
        assert "Your AI client may" in page.locator("body").inner_text()
        browser.close()
    if server:
        server.shutdown()
    print("PASS: ja/en × mobile/desktop, language switch, images, anchors, privacy, MP4 playback; no JS errors")


if __name__ == "__main__":
    main()
