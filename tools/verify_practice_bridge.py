"""Exercise the actual landing-page practice form through MV3 and native messaging."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from browser import cli, EXTENSION_ID


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(SimpleHTTPRequestHandler, directory=str(ROOT / "site")))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    executable = str(Path.home() / "Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")
    with tempfile.TemporaryDirectory(prefix="bp-") as temp, sync_playwright() as p:
        ext = Path(temp) / "extension"
        shutil.copytree(ROOT / "extension", ext)
        manifest = json.loads((ext / "manifest.json").read_text())
        manifest["host_permissions"] = ["http://127.0.0.1/*"]
        (ext / "manifest.json").write_text(json.dumps(manifest))
        profile = Path(temp) / "profile"
        profile.mkdir()
        os.environ["SENTE_BROWSER_STATE"] = str(Path(temp) / "state")
        subprocess.run([sys.executable, str(ROOT / "install.py"), "--user-data-dir", str(profile)], env={**os.environ, "HOME": temp}, check=True, capture_output=True)
        context = p.chromium.launch_persistent_context(str(profile), executable_path=executable, headless=True, env=dict(os.environ), args=[f"--disable-extensions-except={ext}", f"--load-extension={ext}"])
        try:
            worker = context.service_workers[0] if context.service_workers else context.wait_for_event("serviceworker")
            page = context.new_page()
            popup = context.new_page()
            popup.goto(f"chrome-extension://{EXTENSION_ID}/popup.html")
            for lang, label, button in (("ja", "練習メモ", "練習を完了"), ("en", "Practice note", "Complete practice")):
                page.goto(f"http://127.0.0.1:{server.server_port}/?lang={lang}")
                ident = worker.evaluate("async url=>(await chrome.tabs.query({})).find(t=>t.url===url).id", page.url)
                assert popup.evaluate("id=>chrome.runtime.sendMessage({type:'grant',tabId:id})", ident)["ok"]
                data = cli("read", ident)
                ref = next(e["ref"] for e in data["elements"] if e["label"] == label)
                cli("fill", ident, data["snapshot"], ref, "--text-stdin", text="はじめての先手 / First step")
                data = cli("read", ident)
                ref = next(e["ref"] for e in data["elements"] if e["label"] == button)
                cli("click", ident, data["snapshot"], ref)
                assert page.locator("#practice-note").get_attribute("aria-invalid") == "false"
                assert page.locator("#practice-result").inner_text()
                print("PASS actual bridge practice journey", lang)
            popup.evaluate("()=>chrome.runtime.sendMessage({type:'stop'})")
        finally:
            context.close()
            server.shutdown()


if __name__ == "__main__":
    main()
