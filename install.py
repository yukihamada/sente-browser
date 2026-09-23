#!/usr/bin/env python3
"""Install a user-local native host; no browser restart or profile modification."""
import argparse
import json
from pathlib import Path
import shlex
import shutil
import sys
from host import EXTENSION_ID, state_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-data-dir", type=Path, action="append", default=[],
                        help="Also register for Chrome started with this --user-data-dir (repeatable)")
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("This release supports macOS. Python 3.9+ and Chrome 120+ are required.")
    for profile in args.user_data_dir:
        if not profile.expanduser().is_dir():
            parser.error("Chrome user-data directory must already exist: " + str(profile))
    root = Path(__file__).resolve().parent
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    extension = Path.home() / "Library/Application Support/Sente Browser/extension"
    if (root / "extension").resolve() != extension.resolve():
        shutil.copytree(root / "extension", extension, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    launcher = directory / "native-host"
    # Keep the runtime independent of Downloads or the extracted release folder.
    for name in ("host.py", "cli.py"):
        destination = directory / name
        if (root / name).resolve() != destination.resolve():
            shutil.copy2(root / name, destination)
        destination.chmod(0o600)
    launcher.write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + " " + shlex.quote(str(directory / "host.py")) + ' "$@"\n')
    launcher.chmod(0o700)
    manifest = {"name": "io.teai.sente_browser", "description": "Sente local browser bridge",
                "path": str(launcher), "type": "stdio",
                "allowed_origins": ["chrome-extension://" + EXTENSION_ID + "/"]}
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
