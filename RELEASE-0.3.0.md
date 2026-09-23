# Sente Browser v0.3.0 — Windows / macOS / Linux

3 OS共通の `sente-browser-desktop-0.3.0.zip` を展開して導入してください。

- Windows 10/11: PowerShellで `py -3 install.py`。ユーザー単位のChrome登録と、認証付き名前付きパイプを使用します。
- macOS / Linux: `python3 install.py`。同一ユーザー専用Unixソケットを使用します。
- 導入ページでOSを選ぶと、コマンド・拡張フォルダ・AIへの依頼文が切り替わります。
- Python 3.9以上、Chrome 120以上、ローカルCLIを実行できるAIクライアントが必要です。
- 既存ユーザーもインストーラーを再実行し、Chromeで拡張を再読み込みしてください。

Download the shared desktop ZIP. Run `py -3 install.py` in Windows PowerShell,
or `python3 install.py` on macOS/Linux, then load the folder printed by the installer
in chrome://extensions. No administrator privileges or TCP listener required.

CI exercises installer relocation, binary Unicode framing, duplicate-host rejection,
local IPC, and real Chromium MV3 → native messaging → CLI on all three operating
systems. The integration fixture uses a localhost-only host grant to replace the
toolbar gesture in headless CI. Manual installation on end-user machines is separate.

Windows Chrome needs Windows Python, not a Linux bridge inside WSL. Linux Snap/
Flatpak browsers, ChromeOS and mobile browsers are not supported. The Chrome Web
Store submission is separate from this downloadable release.
