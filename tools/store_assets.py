"""Compose store artwork using the actual captured extension popup."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/store"
FONT = "/System/Library/Fonts/Helvetica.ttc"


def text(draw, xy, content, size, color="#edf4e8"):
    draw.text(xy, content, font=ImageFont.truetype(FONT, size), fill=color, spacing=15)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (1280, 800), "#111914")
    draw = ImageDraw.Draw(image)
    text(draw, (65, 65), "SENTE BROWSER", 23, "#c8f2a4")
    text(draw, (65, 180), "Your tab.\nYour next step.", 64)
    text(draw, (65, 390), "Read, fill and click a shared tab.\nKeep your current Chrome session.\nUnshare whenever you choose.", 25, "#afbdad")
    text(draw, (65, 660), "macOS + Python + a CLI-capable AI client\nActual extension UI / local test page", 19, "#afbdad")
    popup = Image.open(OUT / "popup.png").convert("RGB")
    popup.thumbnail((430, 650))
    image.paste(popup, (770, 75))
    image.save(OUT / "screenshot.png")
    tile = Image.new("RGB", (440, 280), "#111914")
    draw = ImageDraw.Draw(tile)
    icon = Image.open(ROOT / "extension/icons/128.png").convert("RGBA")
    icon.thumbnail((58, 58))
    tile.paste(icon, (30, 28), icon)
    text(draw, (30, 112), "Sente Browser", 35)
    text(draw, (30, 172), "Your tab. Your next step.", 21, "#c8f2a4")
    text(draw, (30, 229), "macOS / Chrome / Local bridge", 16, "#afbdad")
    tile.save(OUT / "tile.png")
    for name, size in (("screenshot.png", (1280, 800)), ("tile.png", (440, 280))):
        asset = Image.open(OUT / name)
        assert asset.mode == "RGB" and asset.size == size
    print("PASS: store screenshot 1280x800, tile 440x280, RGB without alpha")


if __name__ == "__main__":
    main()
