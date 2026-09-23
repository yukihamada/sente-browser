"""Record real CLI → native bridge → extension operations on owned demo data."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from host import EXTENSION_ID

PAGE = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Sente Browser · Demo workspace</title>
<style>*{box-sizing:border-box}body{margin:0;background:#111914;color:#edf4e8;font:18px/1.6 -apple-system,sans-serif}.shell{padding:38px 65px}header{display:flex;justify-content:space-between;color:#aebdaa;font-size:14px;border-bottom:1px solid #394734;padding-bottom:23px}.brand{color:#c8f2a4;font-size:20px;font-weight:650}.stage{display:grid;grid-template-columns:1fr 360px;gap:55px;padding-top:40px}h1{font-size:42px;line-height:1.2;letter-spacing:-.045em;margin:12px 0 26px}h2{font-size:20px;margin:0 0 18px}.eyebrow{font-size:12px;letter-spacing:.15em;color:#b1c5a7}label{display:block;font-size:14px;color:#c1cebb;margin:16px 0}input,textarea{display:block;width:100%;font:18px/1.5 inherit;border:1px solid #516149;border-radius:10px;padding:14px;margin-top:7px;background:#202b21;color:#eff5e9;outline-color:#c8f2a4}textarea{height:102px;font:17px/1.6 -apple-system,sans-serif}input{font:18px -apple-system,sans-serif}button{background:#c8f2a4;color:#1b2715;border:0;border-radius:30px;padding:13px 23px;font-size:16px;font-weight:600;cursor:pointer}aside{border:1px solid #4b5f41;border-radius:18px;padding:25px;background:#1b271b;align-self:start;margin-top:25px}.dot{width:8px;height:8px;border-radius:50%;background:#c8f2a4;display:inline-block;margin-right:9px}#bridge{font-size:14px;color:#c8f2a4}.code{font:14px/2 monospace;color:#b6c7aa;border-top:1px solid #45553b;margin-top:20px;padding-top:17px}#result{margin-top:15px;color:#c8f2a4;font-size:15px}.caption{position:fixed;bottom:0;left:0;right:0;padding:18px 65px 24px;background:#0b100c;border-top:1px solid #33442c;font-size:25px;font-weight:550;letter-spacing:-.02em}.caption small{display:block;font-size:14px;font-weight:400;color:#c0cfb7;margin-top:4px}#mark{color:#c8f2a4}</style>
<div class="shell"><header><span class="brand">↗ Sente Browser</span><span>REAL BROWSER CAPTURE · LOCAL DEMO DATA</span></header><div class="stage"><section><span class="eyebrow">YOUR TAB. YOUR NEXT STEP.</span><h1>A small task.<br>A clear next step.</h1><label>Task name<input id="name" placeholder="What needs doing?"></label><label>Notes<textarea id="notes" placeholder="Add the next step"></textarea></label><button id="save">Save draft</button><div id="result" role="status"></div></section><aside><h2>↗ Work with Sente</h2><p id="bridge">Waiting for a shared tab</p><p style="font-size:14px;color:#b1c5a7">This panel explains the recording.<br>The real extension runs in Chrome.</p><div class="code">MV3 extension<br>↕ Native messaging<br>Local bridge<br>↕ Unix socket<br>CLI</div><p id="mark" style="font-size:13px">Demo data · no external submission</p></aside></div></div><div class="caption"><span id="caption-en">Your current tab. Ready for the next step.</span><small id="caption-ja">今開いているページから、一緒に。</small></div><script>document.querySelector('#save').onclick=()=>{document.querySelector('#result').textContent='✓ Draft saved locally: '+document.querySelector('#name').value;};</script></html>'''


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE.encode())

    def log_message(self, *args):
        pass


def cli(*args, text=None):
    process = subprocess.run([sys.executable, str(ROOT / "cli.py"), *map(str, args)], input=text,
                             capture_output=True, text=True, timeout=25, check=True)
    value = json.loads(process.stdout)
    assert value["ok"], value
    return value["result"]


def main():
    output = ROOT / "artifacts/demo"
    output.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    executable = os.environ.get("CHROMIUM_PATH", str(Path.home() / "Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"))
    with tempfile.TemporaryDirectory(prefix="sd-") as temp, sync_playwright() as p:
        extension = Path(temp) / "extension"
        shutil.copytree(ROOT / "extension", extension)
        manifest = json.loads((extension / "manifest.json").read_text())
        manifest["host_permissions"] = ["http://127.0.0.1/*"]
        (extension / "manifest.json").write_text(json.dumps(manifest))
        profile = Path(temp) / "profile"
        profile.mkdir()
        os.environ["SENTE_BROWSER_STATE"] = str(Path(temp) / "state")
        subprocess.run([sys.executable, str(ROOT / "install.py"), "--user-data-dir", str(profile)],
                       env={**os.environ, "HOME": temp}, capture_output=True, check=True)
        context = p.chromium.launch_persistent_context(str(profile), executable_path=executable,
            headless=True, env=dict(os.environ), viewport={"width": 1280, "height": 720},
            record_video_dir=str(output), record_video_size={"width": 1280, "height": 720},
            args=[f"--disable-extensions-except={extension}", f"--load-extension={extension}"])
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{server.server_port}/")
        worker = context.service_workers[0] if context.service_workers else context.wait_for_event("serviceworker")
        popup = context.new_page()
        popup.goto(f"chrome-extension://{EXTENSION_ID}/popup.html")
        tab_id = worker.evaluate("async()=> (await chrome.tabs.query({})).find(t=>t.url?.startsWith('http://127.0.0.1')).id")

        def caption(en, ja):
            page.evaluate("([en,ja])=>{document.querySelector('#caption-en').textContent=en;document.querySelector('#caption-ja').textContent=ja}", [en, ja])

        page.wait_for_timeout(2500)
        result = popup.evaluate("id=>chrome.runtime.sendMessage({type:'grant',tabId:id})", tab_id)
        assert result["ok"], result
        assert cli("tabs")["tabs"][0]["tabId"] == tab_id
        page.locator("#bridge").evaluate("el=>el.textContent='● Shared · connected to this Mac'")
        caption("01 / Share one tab. Keep control.", "共有したタブだけ。いつでも解除できます。")
        page.wait_for_timeout(3500)
        data = cli("read", tab_id)
        assert "Task name" in data["text"]
        caption("02 / Read the page through the local bridge.", "画面の内容を、ローカルブリッジから確認。")
        page.wait_for_timeout(3500)
        data = cli("read", tab_id)
        ref = next(e["ref"] for e in data["elements"] if e["label"] == "Task name")
        cli("fill", tab_id, data["snapshot"], ref, "--text-stdin", text="Plan the next step / 次の一手")
        caption("03 / Fill the form in your existing session.", "今のログイン状態のまま、入力を進めます。")
        page.wait_for_timeout(2200)
        data = cli("read", tab_id)
        ref = next(e["ref"] for e in data["elements"] if e["label"] == "Notes")
        cli("fill", tab_id, data["snapshot"], ref, "--text-stdin", text="Review the draft together.\n下書きを確認して、次へ。")
        assert page.locator("#notes").input_value().endswith("次へ。")
        page.wait_for_timeout(3300)
        caption("04 / Click. Then verify the actual result.", "クリックしたあと、実際の結果まで確認。")
        data = cli("read", tab_id)
        ref = next(e["ref"] for e in data["elements"] if e["label"] == "Save draft")
        cli("click", tab_id, data["snapshot"], ref)
        assert "Draft saved locally" in cli("read", tab_id)["text"]
        page.wait_for_timeout(4200)
        result = popup.evaluate("()=>chrome.runtime.sendMessage({type:'stop'})")
        assert result["ok"]
        state = popup.evaluate("()=>chrome.runtime.sendMessage({type:'status'})")
        assert not state["connected"] and state["count"] == 0
        page.locator("#bridge").evaluate("el=>el.textContent='○ Stopped · no shared tabs'")
        caption("05 / Stop sharing. You decide when it ends.", "作業が終わったら、共有を停止。")
        page.wait_for_timeout(4000)
        page.screenshot(path=str(ROOT / "site/poster.jpg"), type="jpeg", quality=88)
        video = page.video
        video_path = video.path()
        context.close()
        shutil.copy2(video_path, output / "demo.webm")
    server.shutdown()
    subprocess.run(["ffmpeg", "-y", "-i", str(output / "demo.webm"), "-an", "-c:v", "libx264",
                    "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    str(ROOT / "site/demo.mp4")], check=True, capture_output=True)
    shutil.copy2(ROOT / "extension/icons/128.png", ROOT / "site/icon.png")
    print("PASS: real share → read → bilingual fill → click → verify → stop recorded to site/demo.mp4")


if __name__ == "__main__":
    main()
