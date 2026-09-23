# Sente Browser 0.2.1

Native bridge compatibility for Chrome Web Store item
`jnnfblhbdlgofcadhgaicafimchnbdnl`. Store availability is subject to review;
this release provides a working macOS download now.

- Uses the store-issued public key for unpacked/Store identity consistency.
- Native host accepts only the exact Store ID and the original 0.2.0 ID.
- Store ZIP omits `manifest.key`, as required by the upload validator.
- Existing 0.2.0 users: rerun `python3 install.py` from this release to update the bridge.
- macOS ZIP includes the extension, bridge, CLI and installer. An AI client capable
  of running the CLI is required; the extension alone does not run a model.

Verification: six unit/installer tests plus real MV3/native-host/CLI integration
passed with the store-issued ID. Key-derived ID equals the host origin.

Setup and demo: https://yukihamada.github.io/sente-browser/
