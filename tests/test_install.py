import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "darwin", "macOS installer")
class InstallerTests(unittest.TestCase):
    def test_runtime_survives_download_move(self):
        with tempfile.TemporaryDirectory(prefix="si-") as temp:
            home = Path(temp)
            download = home / "download with spaces"
            download.mkdir()
            for name in ("host.py", "cli.py", "install.py"):
                shutil.copy2(ROOT / name, download / name)
            shutil.copytree(ROOT / "extension", download / "extension")
            state = home / "state"
            env = {**os.environ, "HOME": temp, "SENTE_BROWSER_STATE": str(state)}
            subprocess.run([sys.executable, str(download / "install.py")], env=env, check=True, capture_output=True)
            download.rename(home / "moved")
            extension = home / "Library/Application Support/Sente Browser/extension"
            self.assertTrue((extension / "manifest.json").exists())
            from host import EXTENSION_ID, read_frame
            import io
            process = subprocess.run([str(state / "native-host"), f"chrome-extension://{EXTENSION_ID}/"],
                                     env=env, input=b"", capture_output=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(read_frame(io.BytesIO(process.stdout)), {"type": "ready"})
            self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            denied = subprocess.run([str(state / "native-host"), "chrome-extension://wrong/"],
                                    env=env, input=b"", capture_output=True)
            self.assertNotEqual(denied.returncode, 0)
