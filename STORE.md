# Chrome Web Store submission — prepared, not submitted

Version: 0.2.1 · Package: `dist/sente-browser-store-0.2.1.zip`
Store item ID: `jnnfblhbdlgofcadhgaicafimchnbdnl`
Publisher: 株式会社イネブラ（Enabler Inc.）. Identity and contact email verified.
Category: Workflow & Planning · Languages: English, Japanese
Website: https://yukihamada.github.io/sente-browser/
Privacy: https://yukihamada.github.io/sente-browser/privacy.html
Support: https://github.com/yukihamada/sente-browser/issues

## Short description

Let Sente read and operate the tab you share, using your current Chrome session.

## Full description (English)

Work from the Chrome tab you already have open. Share a tab with Sente Browser
and let a local AI client read visible text, fill standard text fields, click
controls and scroll — using your current signed-in session.

- Explicit sharing per tab; revoke a single tab or stop everything.
- Sharing ends on navigation, reload, tab closure or disconnection.
- Japanese and English interface.
- No cookie extraction or all-sites host permission.
- Open-source local bridge. No telemetry in the extension.

Requires macOS, Chrome 120+, Python 3.9+ and a separate AI client capable of running
the included command-line interface. Install the native messaging bridge from the
linked website before sharing a tab. The extension itself does not run an AI model.

The local bridge does not transmit page data to a remote server. Your AI client
may retain content or send it to its model provider. Review its settings before
sharing sensitive pages. Password entry, file pickers, iframe/Shadow DOM contents,
rich-text editors and screenshots are not supported in this release.

## 日本語説明

今開いているChromeタブを、先手と一緒に。共有したタブの表示テキストの確認、通常の
入力欄への記入、クリック、スクロールを、現在のログイン状態のまま行えます。

タブごとの明示共有、個別解除、全共有の停止に対応。ページ移動・再読み込み・タブ終了・
切断で共有を解除します。日本語/英語UI、Cookie抽出なし、全サイト常時アクセスなし。

macOS、Chrome 120以上、Python 3.9以上、およびCLIを実行できるAIクライアントが必要です。
ウェブサイトからローカルブリッジを導入してからご利用ください。拡張だけではAIは動作しません。
拡張にテレメトリーはありませんが、AIクライアントが内容を会話履歴やモデル提供元に渡す場合があります。

## Permission justifications

- activeTab: user-triggered read/action access to the explicitly selected tab.
- scripting: inject packaged content.js into that tab to inspect text and execute supported actions.
- nativeMessaging: exchange bounded JSON with io.teai.sente_browser, the user-installed local bridge.
- Remote code: none. All executable extension code is packaged.
- Single purpose: user-authorized tab interaction through a local AI client.

## Data disclosure to complete in console

Be explicit that website content is accessed and transferred to the local client;
that content can contain personal information. Do not claim the entire AI workflow
is local-only. No advertising, sale of data, or unrelated data use. Verify each
current console checkbox against PRIVACY.md before submitting.

## Pending publisher steps

The developer console currently requires the publisher to sign in again. No
registration fee has been paid and no submission or review approval is claimed.
After login: check account eligibility, upload package, review generated listing
ID, fill disclosures, add actual extension screenshots and submit for review.

**Important:** the unpacked ID is `ndpogcpncelkickingfpfdbajchdbnim`. If the store
allocates a different ID, obtain its public key and update manifest key, host
origin and packaging together before submission. Do not publish a store package
that cannot connect to the distributed native host.
