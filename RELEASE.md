# Sente Browser 0.2.0

macOS download release with a bilingual setup page and a 26-second real-browser
demonstration. Chrome Web Store listing is not yet available.

## Improvements

- Installer copies both runtime and extension into stable application folders.
- Popup lists shared tabs and supports per-tab revocation.
- Help, privacy policy, app icons and recoverable connection guidance.
- Concurrent connection attempts share one handshake; grant checks retain the live connection.
- Privacy text explains the difference between the local bridge and cloud AI clients.

## Downloads

- **sente-browser-macos-0.2.0.zip**: extension + native bridge + installer + CLI.
- **sente-browser-extension-0.2.0.zip**: extension-only package (requires the bridge).
- **SHA256SUMS.txt**: package hashes.

Start at https://yukihamada.github.io/sente-browser/ for installation and the video.
Requires macOS, Python 3.9+, Chrome 120+, and an AI client that can execute the CLI.

## Evidence

5 unit/installer tests, including moved-download survival and unauthorized-origin
rejection. Real MV3/native-host/CLI integration checks read, Japanese input, click,
password-value exclusion, stale snapshots, per-tab revoke, navigation revoke and stop.
Website checked at 390/1440px in ja/en, including actual MP4 decoding and playback.
No paid API calls or real external form submissions in these tests.

Video uses owned demo data and test-only localhost sharing permission. The production
extension has no broad host permissions. Image-based visual review is unverified in
this session; DOM geometry, text, browser behavior and video decoding are checked.
