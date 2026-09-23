"""Generate owned icon artwork and reproducible, allowlisted release archives."""
import hashlib
import json
from pathlib import Path
import zipfile
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def main():
    icons = ROOT / "extension/icons"
    icons.mkdir(exist_ok=True)
    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, 511, 511), radius=120, fill="#c8f2a4")
    draw.line([(145, 355), (360, 140)], fill="#233025", width=48)
    draw.line([(170, 140), (360, 140), (360, 330)], fill="#233025", width=48, joint="curve")
    for size in (16, 32, 48, 128):
        image.resize((size, size), Image.Resampling.LANCZOS).save(icons / f"{size}.png")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    version = json.loads((ROOT / "extension/manifest.json").read_text())["version"]
    extension_files = sorted(p for p in (ROOT / "extension").rglob("*") if p.is_file() and p.suffix in {".json", ".js", ".html", ".css", ".png"})
    for name, paths, base in [
        (f"sente-browser-extension-{version}.zip", extension_files, ROOT / "extension"),
        (f"sente-browser-macos-{version}.zip", extension_files + [ROOT / p for p in ("host.py", "cli.py", "install.py", "README.md", "PRIVACY.md", "LICENSE")], ROOT),
    ]:
        with zipfile.ZipFile(dist / name, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in paths:
                info = zipfile.ZipInfo(str(path.relative_to(base)), date_time=(2026, 9, 23, 0, 0, 0))
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        print(name, (dist / name).stat().st_size)
    checksums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(dist.glob("*.zip")))
    (dist / "SHA256SUMS.txt").write_text(checksums)
    print(checksums)


if __name__ == "__main__":
    main()
