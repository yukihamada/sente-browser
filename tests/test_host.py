import io
import base64
import hashlib
import json
from pathlib import Path
import struct
import unittest

from host import MAX_BYTES, EXTENSION_ID, read_frame, write_frame


class HostTests(unittest.TestCase):
    def test_store_key_matches_native_origin(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] / "extension/manifest.json").read_text())
        digest = hashlib.sha256(base64.b64decode(manifest["key"])).hexdigest()[:32]
        ident = "".join(chr(ord("a") + int(n, 16)) for n in digest)
        self.assertEqual(ident, EXTENSION_ID)

    def test_unicode_frame_round_trip(self):
        stream = io.BytesIO()
        value = {"text": "日本語のページ", "ok": True}
        write_frame(stream, value)
        stream.seek(0)
        self.assertEqual(read_frame(stream), value)
        self.assertIsNone(read_frame(stream))

    def test_rejects_oversized_and_truncated_frames(self):
        for data in (struct.pack("<I", MAX_BYTES + 1), b"\x01\x00", struct.pack("<I", 4) + b"{}"):
            with self.assertRaises((ValueError, EOFError)):
                read_frame(io.BytesIO(data))

    def test_handles_partial_reads(self):
        class Slow(io.BytesIO):
            def read(self, count):
                return super().read(min(1, count))
        raw = io.BytesIO()
        write_frame(raw, {"op": "tabs"})
        self.assertEqual(read_frame(Slow(raw.getvalue())), {"op": "tabs"})

    def test_locale_keys_match(self):
        root = Path(__file__).resolve().parents[1] / "extension"
        en = json.loads((root / "_locales/en/messages.json").read_text())
        ja = json.loads((root / "_locales/ja/messages.json").read_text())
        self.assertEqual(set(en), set(ja))
        manifest = json.loads((root / "manifest.json").read_text())
        self.assertNotIn("host_permissions", manifest)
        self.assertNotIn("debugger", manifest["permissions"])


if __name__ == "__main__":
    unittest.main()
