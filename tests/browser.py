"""Real MV3 -> native host -> CLI test with isolated browser and localhost fixture."""
import functools
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
EXTENSION_ID = "jnnfblhbdlgofcadhgaicafimchnbdnl"


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        page = b'''<!doctype html><title>Browser fixture</title>
        <h1>Private fixture</h1><label>Name<input id="name"></label>
        <input type="password" value="do-not-read"><button id="save">Save</button>
        <div id="result"></div><a href="/next">Next</a>
        <script>document.querySelector('#save').onclick=()=>{
        document.querySelector('#result').textContent=document.querySelector('#name').value};</script>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page)

    def log_message(self, *args):
        pass


def cli(*args, text=None, ok=True):
    process = subprocess.run([sys.executable, str(ROOT / "cli.py"), *map(str, args)],
                             input=text, text=True, capture_output=True, timeout=30)
    value = json.loads(process.stdout or process.stderr)
    assert value.get("ok") is ok, value
    return value.get("result") if ok else value


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    executable = os.environ.get("CHROMIUM_PATH", str(Path.home() / "Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"))
    with tempfile.TemporaryDirectory(prefix="sb-") as temp, sync_playwright() as playwright:
        extension = Path(temp) / "extension"
        shutil.copytree(ROOT / "extension", extension)
        # Headless cannot click Chrome's toolbar. Only the isolated fixture receives
        # a host grant; the production manifest retains activeTab with zero host grants.
        manifest_path = extension / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["host_permissions"] = ["http://127.0.0.1/*"]
        manifest_path.write_text(json.dumps(manifest))
        # With --user-data-dir Chromium resolves the per-user native-host registry there.
        profile = Path(temp) / "profile"
        profile.mkdir()
        os.environ["SENTE_BROWSER_STATE"] = str(Path(temp) / "state")
        subprocess.run([sys.executable, str(ROOT / "install.py"), "--user-data-dir", str(profile)],
                       env={**os.environ, "HOME": temp}, check=True, capture_output=True)
        probe = subprocess.run([str(Path(temp) / "state/native-host"), f"chrome-extension://{EXTENSION_ID}/"],
                               input=b"", capture_output=True)
        assert probe.returncode == 0, probe.stderr.decode()
        context = playwright.chromium.launch_persistent_context(str(Path(temp) / "profile"),
            executable_path=executable, headless=True, env=dict(os.environ),
            args=[f"--disable-extensions-except={extension}", f"--load-extension={extension}"])
        try:
            worker = context.service_workers[0] if context.service_workers else context.wait_for_event("serviceworker")
            assert EXTENSION_ID in worker.url, worker.url
            worker.on("console", lambda message: print("worker:", message.text))
            page = context.new_page()
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            popup = context.new_page()
            popup.goto(f"chrome-extension://{EXTENSION_ID}/popup.html")
            fixture_tabs = worker.evaluate("async () => (await chrome.tabs.query({})).filter(t=>t.url?.startsWith('http://127.0.0.1'))")
            tab_id = fixture_tabs[0]["id"]
            # Grant using the exact popup -> worker -> injection -> native host path.
            result = popup.evaluate("id => chrome.runtime.sendMessage({type:'grant',tabId:id})", tab_id)
            assert result["ok"], result
            assert cli("tabs")["tabs"][0]["tabId"] == tab_id
            popup.reload()
            popup.wait_for_function("document.querySelectorAll('#tabs li').length===1")
            assert popup.locator("#tabs li").count() == 1
            if os.environ.get("CAPTURE_STORE"):
                output = ROOT / "artifacts/store"
                output.mkdir(parents=True, exist_ok=True)
                popup.set_viewport_size({"width": 400, "height": 650})
                popup.locator("body").screenshot(path=str(output / "popup.png"))
            popup.locator(".revoke").click()
            assert cli("read", tab_id, ok=False)["error"] == "tab_not_shared"
            result = popup.evaluate("id => chrome.runtime.sendMessage({type:'grant',tabId:id})", tab_id)
            assert result["ok"], result
            data = cli("read", tab_id)
            assert "Private fixture" in data["text"]
            assert "do-not-read" not in json.dumps(data)
            name = next(x["ref"] for x in data["elements"] if x["label"] == "Name")
            cli("fill", tab_id, data["snapshot"], name, "--text-stdin", text="先手 browser test")
            assert page.locator("#name").input_value() == "先手 browser test"
            assert cli("click", tab_id, data["snapshot"], name, ok=False)["error"] == "stale_snapshot_read_again"
            data = cli("read", tab_id)
            password = next(x["ref"] for x in data["elements"] if x["type"] == "password")
            assert cli("fill", tab_id, data["snapshot"], password, "--text-stdin", text="x", ok=False)["error"] == "unsupported_input_type"
            save = next(x["ref"] for x in data["elements"] if x["label"] == "Save")
            cli("click", tab_id, data["snapshot"], save)
            assert page.locator("#result").inner_text() == "先手 browser test"
            assert cli("read", tab_id + 99999, ok=False)["error"] == "tab_not_shared"
            page.goto(f"http://127.0.0.1:{server.server_port}/next")
            assert cli("read", tab_id, ok=False)["error"] == "tab_not_shared"
            assert cli("tabs")["tabs"] == []
            result = popup.evaluate("id => chrome.runtime.sendMessage({type:'grant',tabId:id})", tab_id)
            assert result["ok"], result
            popup.locator("#stop").click()
            state = popup.evaluate("() => chrome.runtime.sendMessage({type:'status'})")
            assert state == {"connected": False, "count": 0, "tabs": []}, state
            print("PASS: real MV3/native-host/CLI; read, fill, click, password exclusion, stale snapshot, unshared tab, navigation revocation, stop")
        finally:
            context.close()
            server.shutdown()


if __name__ == "__main__":
    main()
