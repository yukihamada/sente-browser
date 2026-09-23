import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_runtime_survives_download_move(self):
        with tempfile.TemporaryDirectory(prefix="si-") as temp:
            home = Path(temp)
            download = home / "download with spaces"
            download.mkdir()
            for name in ("host.py", "cli.py", "install.py", "transport.py"):
                shutil.copy2(ROOT / name, download / name)
            shutil.copytree(ROOT / "extension", download / "extension")
            state = home / "state"
            env = {**os.environ, "HOME": temp, "USERPROFILE": temp,
                   "XDG_CONFIG_HOME": str(home / ".config"), "SENTE_BROWSER_STATE": str(state)}
            subprocess.run([sys.executable, str(download / "install.py")], env=env, check=True, capture_output=True)
            download.rename(home / "moved")
            extension = home / "Library/Application Support/Sente Browser/extension" if sys.platform == "darwin" else state / "extension"
            self.assertTrue((extension / "manifest.json").exists())
            from host import EXTENSION_ID, read_frame
            import io
            launcher = str(state / ("native-host.cmd" if sys.platform == "win32" else "native-host"))
            process = subprocess.run([launcher, f"chrome-extension://{EXTENSION_ID}/"],
                                     env=env, input=b"", capture_output=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(read_frame(io.BytesIO(process.stdout)), {"type": "ready"})
            if sys.platform != "win32":
                self.assertEqual(state.stat().st_mode & 0o777, 0o700)
            denied = subprocess.run([launcher, "chrome-extension://wrong/"],
                                    env=env, input=b"", capture_output=True)
            self.assertNotEqual(denied.returncode, 0)
