# Sente Browser privacy / プライバシー

Updated: 2026-09-23 · Publisher: Enabler Inc. (株式会社イネブラ) · Contact: mail@yukihamada.jp

## English

Sente Browser is an open-source Chrome extension with a local Windows/macOS/Linux bridge.
When you explicitly share an HTTP(S) tab, local tools running as your OS user can
request its visible text, title, URL and interactive-element labels and issue
supported actions. Reading the page can include personal or confidential content
visible on that page. Password field values are not included in snapshots.
Depending on the shared page, content can include personal identifiers, health,
financial information, visible authentication information, communications or
location information. Shared-tab URLs and titles are also passed to the client.

The extension and bridge do not send page content to a server, collect analytics,
read Chrome cookies, or store browsing history. Native-host registration and
runtime files remain on your computer. Unix sockets are restricted to your OS user;
Windows named pipes require an authentication key stored with user-restricted ACLs.
Sharing grants and snapshots are held in memory. Navigation, closing a tab,
extension restart or disconnection revoke grants. You can revoke individual tabs
or stop all sharing from the popup.

**Your AI client is separate:** it may retain page content in conversation history
or send it to its model provider. Review that client's configuration and privacy
policy. This extension does not make cloud AI processing local-only.

Permissions: `activeTab` grants access following your gesture; `scripting` installs
the page reader/action handler in that tab; `nativeMessaging` connects to the local
bridge. No all-sites host permission is requested. Download/site hosting is provided
by GitHub, whose own service privacy policies apply to visits and downloads.

Uninstall the extension in Chrome, remove `io.teai.sente_browser.json` from the
NativeMessagingHosts folders you registered, and remove `~/.local/share/sente-browser`.
This does not erase records kept by your AI client.

## 日本語

先手ブラウザは、Chrome拡張とWindows・macOS・Linux用ローカルブリッジです。明示的に共有した
HTTP(S)タブに対し、同じOSユーザーで動くツールが、表示テキスト・タイトル・URL・
操作要素のラベルを読み取り、対応する操作を実行できます。ページに表示された個人情報や
機密情報も読取内容に含まれ得ます。パスワード欄の値はスナップショットに含めません。

拡張とブリッジ自体は、ページ内容のサーバー送信、アクセス解析、Cookie読取、閲覧履歴保存を
行いません。登録・実行ファイルはパソコンに残ります。Unixソケットは同一OSユーザーに制限され、Windowsの名前付きパイプはユーザー限定ACLで保存した鍵による認証が必要です。
共有許可とスナップショットはメモリ内に保持し、遷移・タブ終了・拡張再起動・切断で失効します。
ポップアップからタブ単位の解除、または全共有の停止ができます。

**AIクライアントは別です。** 会話履歴への保存やモデル提供元への送信を行う場合があります。
利用するクライアントの設定・プライバシーポリシーをご確認ください。

権限はユーザー操作による対象タブへのアクセス、読取/操作コードの注入、ローカルブリッジ接続の
3つです。全サイトへの常時アクセスは要求しません。配布サイト・ダウンロードにはGitHubの
プライバシーポリシーが適用されます。

削除時はChromeで拡張を削除し、登録先NativeMessagingHostsの `io.teai.sente_browser.json` と
`~/.local/share/sente-browser` を削除してください。AIクライアント側の記録は別途管理が必要です。

Windows: remove only `HKEY_CURRENT_USER\Software\Google\Chrome\NativeMessagingHosts\io.teai.sente_browser` from the Registry and `%LOCALAPPDATA%\Sente Browser` from disk.
Windowsでは上記のレジストリキーとフォルダを削除します。
macOSの拡張コピー / macOS extension copy: `~/Library/Application Support/Sente Browser`.
