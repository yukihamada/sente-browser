"""Extended real-MV3 regression matrix; localhost fixtures, isolated host/profile."""
import concurrent.futures
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
sys.path.insert(0, str(ROOT))
from host import EXTENSION_ID

HTML = '''<!doctype html><meta charset="utf-8"><title>Matrix fixture</title>
<style>body{min-height:3000px}.hidden{display:none}</style><h1>Local test</h1>
<label>Name<input id="name"></label><label>Notes<textarea id="notes"></textarea></label>
<label>Email<input id="email" type="email"></label><label>Secret<input type="password" value="PASSWORD_SENTINEL"></label>
<label>Read only<input id="ro" readonly></label><label>File<input id="file" type="file"></label>
<fieldset disabled><label>Disabled group<input id="group"></label><button id="groupbtn">Disabled group button</button></fieldset>
<button id="disabled" disabled>Disabled button</button><button aria-disabled="true">ARIA disabled</button>
<button id="save">Save</button><a id="link" href="/next">Next</a>
<button class="hidden">Hidden button</button><button aria-hidden="true">ARIA hidden</button>
<div inert><button>Inert button</button></div><label>Tick<input type="checkbox" id="tick"></label>
<div id="result"></div><iframe src="/frame"></iframe><div id="shadow"></div>
<script>window.saved=0;window.events=[];document.querySelector('#name').oninput=()=>events.push('input');
document.querySelector('#name').onchange=()=>events.push('change');
document.querySelector('#save').onclick=()=>{saved++;document.querySelector('#result').textContent=document.querySelector('#name').value};
document.querySelector('#shadow').attachShadow({mode:'open'}).innerHTML='<button>Shadow button</button>';</script>'''


class Fixture(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(("<button>Frame only</button>" if self.path == "/frame" else HTML).encode())

    def log_message(self, *args):
        pass


def cli(*args, text=None, ok=True):
    result = subprocess.run([sys.executable, str(ROOT / "cli.py"), *map(str, args)], input=text,
                            text=True, capture_output=True, timeout=30)
    value = json.loads(result.stdout or result.stderr)
    assert value.get("ok") is ok, value
    return value["result"] if ok else value


def main():
    reports = []
    def test(name, fn):
        try:
            fn()
            reports.append({"name": name, "passed": True})
            print("PASS", name)
        except Exception as error:
            reports.append({"name": name, "passed": False, "error": str(error)})
            print("FAIL", name, str(error))

    def expect(condition, message="unexpected result"):
        assert condition, message

    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    executable = os.environ.get("CHROMIUM_PATH", str(Path.home() / "Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"))
    with tempfile.TemporaryDirectory(prefix="bm-") as temp, sync_playwright() as p:
        ext = Path(temp) / "extension"
        shutil.copytree(ROOT / "extension", ext)
        manifest = json.loads((ext / "manifest.json").read_text())
        manifest["host_permissions"] = ["http://127.0.0.1/*"]
        (ext / "manifest.json").write_text(json.dumps(manifest))
        profile = Path(temp) / "profile"
        profile.mkdir()
        os.environ["SENTE_BROWSER_STATE"] = str(Path(temp) / "state")
        subprocess.run([sys.executable, str(ROOT / "install.py"), "--user-data-dir", str(profile)],
                       env={**os.environ, "HOME": temp}, check=True, capture_output=True)
        context = p.chromium.launch_persistent_context(str(profile), executable_path=executable,
            env=dict(os.environ), headless=True, args=[f"--disable-extensions-except={ext}", f"--load-extension={ext}"])
        try:
            worker = context.service_workers[0] if context.service_workers else context.wait_for_event("serviceworker")
            page = context.new_page()
            base = f"http://127.0.0.1:{server.server_port}"
            page.goto(base + "/")
            popup = context.new_page()
            popup.goto(f"chrome-extension://{EXTENSION_ID}/popup.html")
            def tab_id(url):
                return worker.evaluate("async url=>(await chrome.tabs.query({})).find(t=>t.url===url).id", url)
            ident = tab_id(page.url)
            def message(kind, target=ident):
                return popup.evaluate("([type,tabId])=>chrome.runtime.sendMessage({type,tabId})", [kind, target])
            def share():
                expect(message("grant")["ok"])
            def read():
                return cli("read", ident)
            def action(op, label, text=None):
                data = read()
                ref = next(x["ref"] for x in data["elements"] if x["label"] == label)
                args = [op, ident, data["snapshot"], ref]
                if op == "fill": args.append("--text-stdin")
                return args
            share()
            test("password value excluded", lambda: expect("PASSWORD_SENTINEL" not in json.dumps(read())))
            test("hidden/inert/frame/shadow controls excluded", lambda: expect(not {"Hidden button", "ARIA hidden", "Inert button", "Frame only", "Shadow button"}.intersection(e["label"] for e in read()["elements"])))
            def fill_unicode():
                cli(*action("fill", "Name"), text="日本語 👨‍👩‍👧‍👦 café <script>x</script>")
                expect(page.locator("#name").input_value().startswith("日本語"))
                expect(page.evaluate("events") == ["input", "change"])
            test("Japanese/emoji/HTML literal input and DOM events", fill_unicode)
            test("multiline textarea", lambda: (cli(*action("fill", "Notes"), text="一行目\nsecond line"), expect(page.locator("#notes").input_value() == "一行目\nsecond line")))
            test("email input", lambda: (cli(*action("fill", "Email"), text="test@example.com"), expect(page.locator("#email").input_value() == "test@example.com")))
            for label, error in [("Read only", "not_text_input"), ("File", "unsupported_input_type"), ("Secret", "unsupported_input_type"), ("Disabled group", "element_unavailable")]:
                test("reject fill: " + label, lambda label=label, error=error: expect(cli(*action("fill", label), text="x", ok=False)["error"] == error))
            for label in ("Disabled button", "ARIA disabled", "Disabled group button"):
                test("reject click: " + label, lambda label=label: expect(cli(*action("click", label), ok=False)["error"] == "element_unavailable"))
            def click_once():
                args = action("click", "Save")
                cli(*args)
                expect(page.evaluate("saved") == 1)
                expect(cli(*args, ok=False)["error"] == "stale_snapshot_read_again")
                expect(page.evaluate("saved") == 1)
            test("click once; reject replay", click_once)
            test("checkbox click", lambda: (cli(*action("click", "Tick")), expect(page.locator("#tick").is_checked())))
            def changed():
                args = action("click", "Save")
                page.locator("#save").evaluate("e=>e.textContent='Changed'")
                expect(cli(*args, ok=False)["error"] == "element_changed_read_again")
                page.locator("#save").evaluate("e=>e.textContent='Save'")
            test("changed label rejects old reference", changed)
            def changed_link():
                args = action("click", "Next")
                page.locator("#link").evaluate("e=>e.href='/different'")
                expect(cli(*args, ok=False)["error"] == "element_changed_read_again")
            test("changed link destination rejects old reference", changed_link)
            def detached():
                args = action("click", "Save")
                page.locator("#save").evaluate("e=>e.replaceWith(e.cloneNode(true))")
                expect(cli(*args, ok=False)["error"] == "element_unavailable")
            test("replaced DOM node rejects old reference", detached)
            def hidden_after_read():
                args = action("click", "Save")
                page.locator("#save").evaluate("e=>e.style.display='none'")
                expect(cli(*args, ok=False)["error"] == "element_unavailable")
                page.locator("#save").evaluate("e=>e.style.display=''")
            test("newly hidden target rejected", hidden_after_read)
            test("disabled fields accurately reported", lambda: expect(all(e["disabled"] for e in read()["elements"] if e["label"] in {"Disabled group", "Disabled group button", "ARIA disabled"})))
            def long_input():
                value = "日" * 10000
                cli(*action("fill", "Notes"), text=value)
                expect(page.locator("#notes").input_value() == value)
                result = subprocess.run([sys.executable, str(ROOT / "cli.py"), *map(str, action("fill", "Notes"))],
                                        input=value + "x", text=True, capture_output=True)
                expect(result.returncode != 0 and "input_too_long" in result.stderr)
                expect(page.locator("#notes").input_value() == value)
            test("10000 characters accepted; 10001 rejected unchanged", long_input)
            def emoji_boundary():
                value = "😀" * 10000
                cli(*action("fill", "Notes"), text=value)
                expect(page.locator("#notes").input_value() == value)
            test("Unicode codepoint limit matches CLI", emoji_boundary)
            def maxlength():
                page.locator("#name").evaluate("e=>e.maxLength=3")
                expect(cli(*action("fill", "Name"), text="long input", ok=False)["error"] == "input_exceeds_maxlength")
                page.locator("#name").evaluate("e=>e.removeAttribute('maxlength')")
            test("maxlength respected before input", maxlength)
            def focus_change():
                page.locator("#name").evaluate("e=>{e.blur();e.onfocus=()=>e.type='password'}")
                args = action("fill", "Name")
                expect(cli(*args, text="must-not-enter", ok=False)["error"] == "element_changed_read_again")
                expect(page.locator("#name").input_value() != "must-not-enter")
            test("focus handler changing field type blocks input", focus_change)
            page.locator("#name").evaluate("e=>{e.onfocus=null;e.type='text';e.removeAttribute('maxlength')}")
            def scroll():
                d = read()
                cli("scroll", ident, d["snapshot"], "down")
                expect(page.evaluate("scrollY") > 0)
                expect(cli("scroll", ident, d["snapshot"], "down", ok=False)["error"] == "stale_snapshot_read_again")
            test("scroll and snapshot invalidation", scroll)
            def regrant():
                args = action("click", "Save")
                message("revoke")
                expect(cli("read", ident, ok=False)["error"] == "tab_not_shared")
                share()
                expect(cli(*args, ok=False)["error"] == "stale_snapshot_read_again")
            test("revoke/regrant invalidates previous snapshot", regrant)
            def second_tab():
                other = context.new_page()
                other.goto(base + "/two")
                oid = tab_id(other.url)
                expect(message("grant", oid)["ok"])
                expect(len(cli("tabs")["tabs"]) == 2)
                message("revoke", oid)
                expect(len(cli("tabs")["tabs"]) == 1)
                expect(cli("read", oid, ok=False)["error"] == "tab_not_shared")
                expect(read()["title"] == "Matrix fixture")
                expect(message("grant", oid)["ok"])
                other.close()
                expect(len(cli("tabs")["tabs"]) == 1)
            test("two tabs; individual revoke; tab close", second_tab)
            test("parallel reads complete", lambda: expect(all(v["title"] == "Matrix fixture" for v in concurrent.futures.ThreadPoolExecutor(4).map(lambda _: cli("read", ident), range(4)))))
            def bounded_read():
                page.evaluate("()=>{let d=document.createElement('div');d.id='many';d.textContent='x'.repeat(40000);for(let i=0;i<350;i++){let b=document.createElement('button');b.textContent='Extra '+i;d.append(b)}document.body.append(d)}")
                data = read()
                expect(len(data["text"].encode("utf-16-le")) // 2 == 30000 and len(data["elements"]) == 300,
                       {"characters": len(data["text"]), "elements": len(data["elements"])})
                page.locator("#many").evaluate("e=>e.remove()")
            test("large page text and controls bounded", bounded_read)
            def reload():
                page.reload()
                expect(cli("read", ident, ok=False)["error"] == "tab_not_shared")
                share()
                page.evaluate("history.pushState({},'', '/spa')")
                expect(cli("read", ident, ok=False)["error"] == "tab_not_shared")
                share()
            test("reload and SPA navigation revoke", reload)
            def unsupported():
                tid = worker.evaluate("async()=>(await chrome.tabs.create({url:'chrome://version'})).id")
                expect(message("grant", tid)["error"] == "unsupported")
                worker.evaluate("id=>chrome.tabs.remove(id)", tid)
            test("Chrome internal page sharing refused", unsupported)
            # Simulate actual native-host process exit, not grant state mutation.
            def host_exit():
                pid = subprocess.check_output(["pgrep", "-f", str(Path(temp) / "state/host.py")], text=True).splitlines()
                expect(len(pid) == 1, pid)
                os.kill(int(pid[0]), 15)
                popup.wait_for_function("async()=>(await chrome.runtime.sendMessage({type:'status'})).connected===false")
                expect(message("status")["count"] == 0)
                share()
                expect(read()["title"] == "Matrix fixture")
            test("native host exit revokes and reconnects", host_exit)
            test("stop all", lambda: (message("stop"), expect(message("status") == {"connected": False, "count": 0, "tabs": []})))
            def simultaneous_grants():
                results = popup.evaluate("id=>Promise.all([chrome.runtime.sendMessage({type:'grant',tabId:id}),chrome.runtime.sendMessage({type:'grant',tabId:id})])", ident)
                expect(all(r["ok"] for r in results), results)
                expect(len(cli("tabs")["tabs"]) == 1)
            test("simultaneous grants use single connection", simultaneous_grants)
            def revoke_during_grant():
                worker.evaluate("""()=>{globalThis.originalGet=chrome.tabs.get;globalThis.getBlocked=false;
                  chrome.tabs.get=async(...args)=>{globalThis.getBlocked=true;await new Promise(r=>globalThis.releaseGet=r);return originalGet(...args)}}""")
                popup.evaluate("id=>{globalThis.pendingGrant=chrome.runtime.sendMessage({type:'grant',tabId:id})}", ident)
                popup.wait_for_function("()=>true")
                expect(worker.evaluate("()=>getBlocked"))
                message("revoke")
                worker.evaluate("()=>{chrome.tabs.get=originalGet;releaseGet()}")
                result = popup.evaluate("()=>pendingGrant")
                expect(not result.get("ok"), result)
                expect(message("status")["count"] == 0)
            test("revoke cancels in-flight grant", revoke_during_grant)
            share()
            def revoke_during_read():
                worker.evaluate("""()=>{globalThis.originalGet=chrome.tabs.get;globalThis.getBlocked=false;
                  chrome.tabs.get=async(...args)=>{globalThis.getBlocked=true;await new Promise(r=>globalThis.releaseGet=r);return originalGet(...args)}}""")
                with concurrent.futures.ThreadPoolExecutor(1) as pool:
                    future = pool.submit(cli, "read", ident, ok=False)
                    # Poll browser state without blocking its event loop.
                    import time
                    for _ in range(100):
                        if worker.evaluate("()=>getBlocked"): break
                        time.sleep(.02)
                    expect(worker.evaluate("()=>getBlocked"))
                    message("revoke")
                    worker.evaluate("()=>{chrome.tabs.get=originalGet;releaseGet()}")
                    expect(future.result()["error"] == "tab_not_shared")
            test("revoke cancels request awaiting tab lookup", revoke_during_read)
            message("stop")
        finally:
            context.close()
            server.shutdown()
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    (output / "browser-matrix.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2))
    print(f"RESULT {sum(r['passed'] for r in reports)}/{len(reports)} passed")
    return int(any(not r["passed"] for r in reports))


if __name__ == "__main__":
    sys.exit(main())
