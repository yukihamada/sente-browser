"""Exercise IPC and the native process on the actual OS, without a browser mock."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from host import EXTENSION_ID, read_frame, write_frame
from transport import connect, stream_for

ROOT = Path(__file__).resolve().parents[1]


class TransportTests(unittest.TestCase):
    def test_process_bridge_roundtrip_lock_and_auth(self):
        with tempfile.TemporaryDirectory(prefix="sb-ipc-") as temp:
            directory = Path(temp) / "state"
            env = {**os.environ, "SENTE_BROWSER_STATE": str(directory), "PYTHONUTF8": "1"}
            command = [sys.executable, str(ROOT / "host.py"), f"chrome-extension://{EXTENSION_ID}/"]
            process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                self.assertEqual(read_frame(process.stdout), {"type": "ready"})
                second = subprocess.run(command, env=env, input=b"", capture_output=True, timeout=10)
                self.assertNotEqual(second.returncode, 0)
                self.assertIn(b"another_browser_connected", second.stderr)
                if sys.platform == "win32":
                    from multiprocessing.connection import Client
                    from multiprocessing import AuthenticationError
                    from transport import pipe_address
                    with self.assertRaises(AuthenticationError):
                        Client(pipe_address(directory), family="AF_PIPE", authkey=b"wrong")
                with connect(directory) as connection:
                    stream = stream_for(connection)
                    write_frame(stream, {"op": "arbitrary_js"})
                    self.assertEqual(read_frame(stream)["error"], "unsupported_operation")
                with connect(directory) as connection:
                    stream = stream_for(connection)
                    text = "日本語\nemoji 🪵\r\n" * 2000
                    write_frame(stream, {"op": "fill", "text": text})
                    request = read_frame(process.stdout)
                    self.assertEqual(request["request"]["text"], text)
                    value = {"id": request["id"], "ok": True, "result": {"text": text}}
                    write_frame(process.stdin, value)
                    self.assertEqual(read_frame(stream), value)
                client = subprocess.Popen([sys.executable, str(ROOT / "cli.py"), "tabs"], env=env,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                request = read_frame(process.stdout)
                write_frame(process.stdin, {"id": request["id"], "ok": True, "result": {"tabs": []}})
                stdout, stderr = client.communicate(timeout=30)
                self.assertEqual(client.returncode, 0, stderr)
                self.assertEqual(json.loads(stdout)["result"], {"tabs": []})
                process.stdin.close()
                process.wait(timeout=10)
                self.assertEqual(process.returncode, 0, process.stderr.read())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                for stream in (process.stdin, process.stdout, process.stderr):
                    stream.close()
