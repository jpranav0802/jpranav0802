#!/usr/bin/env python3
"""Convert assets/photo-ready.png into a self-drawing ASCII portrait.svg."""
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

GLYPHS = " '.,:;~+*xXO#"
ACCENT = "#2EFFB8"
BG = "#0d1117"

COLS = 80
CHAR_W = 8.6
CHAR_H = 15
FONT_SIZE = 15
ROW_STAGGER_MS = 40
ROW_FADE_MS = 220


def image_to_rows(path, cols=COLS):
    img = Image.open(path).convert("L")
    w, h = img.size
    rows = max(1, round(cols * (h / w) * 0.55))
    img = img.resize((cols, rows))
    pixels = list(img.getdata())
    lines = []
    n = len(GLYPHS) - 1
    for r in range(rows):
        row_pixels = pixels[r * cols:(r + 1) * cols]
        line = "".join(GLYPHS[min(n, int((255 - p) / 255 * n))] for p in row_pixels)
        lines.append(line)
    return lines


def render_svg(lines):
    width = COLS * CHAR_W
    height = len(lines) * CHAR_H + 20
    parts = [
        f'<svg viewBox="0 0 {width:.0f} {height:.0f}" xmlns="http://www.w3.org/2000/svg">',
        "<defs>",
        f"<style>text {{ font-family: 'Courier New', monospace; font-size: {FONT_SIZE}px; "
        f"fill: {ACCENT}; white-space: pre; }}</style>",
        "</defs>",
        f'<rect width="100%" height="100%" fill="{BG}" rx="6"/>',
    ]
    # Fade each row in directly on the <text> element (opacity animate on a
    # leaf shape, not a clipPath or <g> wrapper) - this is the pattern that
    # actually survives GitHub's <img>-embedded SVG rendering.
    for i, line in enumerate(lines):
        y = (i + 1) * CHAR_H
        begin = i * ROW_STAGGER_MS
        parts.append(
            f'<text x="4" y="{y}" opacity="0">{escape(line)}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin}ms" '
            f'dur="{ROW_FADE_MS}ms" fill="freeze"/></text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    src = "assets/photo-ready.png"
    if not Path(src).exists():
        raise SystemExit(f"missing {src} - run tools/clean_photo.py first")
    lines = image_to_rows(src)
    Path("portrait.svg").write_text(render_svg(lines))
    print(f"wrote portrait.svg ({len(lines)} rows x {COLS} cols)")


if __name__ == "__main__":
    main()
