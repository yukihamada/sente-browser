# Sente Browser 0.2.2

Reliability fixes verified against 35 real-browser regression scenarios.

- Complete partial socket writes instead of truncating long input/page responses.
- Reject controls disabled by a parent fieldset; report their state correctly.
- Invalidate old snapshots when a tab is shared again.
- Cancel pending grants/requests when sharing is revoked; discard responses after sharing ends.
- Count Unicode input consistently with the CLI, including emoji.
- Respect field maxlength and revalidate input fields after focus handlers run.

## Update

Download the macOS ZIP, extract it and run `python3 install.py`. Reload the unpacked
extension in Chrome and reload previously shared pages. Share the desired tabs again.
Custom Chrome profiles need `--user-data-dir /path/to/profile` as before.
The bridge supports both the original and Store-issued extension IDs.

## Verification

35/35 real MV3/native-host/CLI scenarios, seven unit/installer tests, and the original
browser integration passed. Tests use isolated profiles and owned localhost pages,
with a test-only localhost permission replacing the toolbar gesture. No real external
form submission or paid API call. Production permissions remain activeTab, scripting
and nativeMessaging. Store availability remains subject to Google's review.

Setup and demo: https://yukihamada.github.io/sente-browser/
