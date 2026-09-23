#!/usr/bin/env python3
"""Install a user-local native host; no browser restart or profile modification."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
from host import EXTENSION_ID, ALLOWED_EXTENSION_IDS, state_dir
from transport import prepare_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-data-dir", type=Path, action="append", default=[],
                        help="Also register for Chrome started with this --user-data-dir (repeatable)")
    args = parser.parse_args()
    if sys.platform not in {"darwin", "linux", "win32"}:
        parser.error("Supported systems: macOS, Windows and Linux. Python 3.9+ and Chrome 120+ required.")
    for profile in args.user_data_dir:
        if not profile.expanduser().is_dir():
            parser.error("Chrome user-data directory must already exist: " + str(profile))
    root = Path(__file__).resolve().parent
    directory = state_dir()
    prepare_directory(directory)
    extension = (Path.home() / "Library/Application Support/Sente Browser/extension"
                 if sys.platform == "darwin" else directory / "extension")
    if (root / "extension").resolve() != extension.resolve():
        shutil.copytree(root / "extension", extension, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    launcher = directory / ("native-host.cmd" if sys.platform == "win32" else "native-host")
    # Keep the runtime independent of Downloads or the extracted release folder.
    for name in ("host.py", "cli.py", "transport.py"):
        destination = directory / name
        if (root / name).resolve() != destination.resolve():
            shutil.copy2(root / name, destination)
        if sys.platform != "win32":
            destination.chmod(0o600)
    if sys.platform == "win32":
        # cmd expands percent even inside quotes; escape literal path characters.
        python = sys.executable.replace("%", "%%")
        script = str(directory / "host.py").replace("%", "%%")
        launcher.write_text(f'@echo off\nchcp 65001 >nul\nsetlocal DisableDelayedExpansion\n"{python}" "{script}" %*\n', encoding="utf-8")
    else:
        launcher.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " " + shlex.quote(str(directory / "host.py")) + ' "$@"\n')
    launcher.chmod(0o700)
    manifest = {"name": "io.teai.sente_browser", "description": "Sente local browser bridge",
                "path": str(launcher), "type": "stdio",
                "allowed_origins": ["chrome-extension://" + ident + "/" for ident in ALLOWED_EXTENSION_IDS]}
    if sys.platform == "win32":
        import winreg
        path = directory / "io.teai.sente_browser.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\NativeMessagingHosts\io.teai.sente_browser") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, str(path))
        print("Registered:", path, "(HKCU / Google Chrome)")
        profiles = []
    elif sys.platform == "linux":
        config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
        profiles = [config / "google-chrome", config / "chromium"]
    else:
        profiles = [Path.home() / "Library/Application Support/Google/Chrome"]
    profiles.extend(profile.expanduser().resolve() for profile in args.user_data_dir)
    for profile in dict.fromkeys(profiles):
        target = profile / "NativeMessagingHosts"
        target.mkdir(parents=True, exist_ok=True)
        path = target / "io.teai.sente_browser.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        path.chmod(0o600)
        print("Registered:", path)
    print("Load unpacked:", extension)
    print("Extension ID:", EXTENSION_ID)
    print("CLI:", sys.executable, directory / "cli.py", "tabs")
    print("Runtime and extension installed. The original download can now be moved.")


if __name__ == "__main__":
    main()
