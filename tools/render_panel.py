#!/usr/bin/env python3
"""Render a terminal-style 'sysinfo' panel as a self-typing SVG."""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ACCENT = "#2EFFB8"
BG = "#0d1117"
DIM = "#7d8590"

ROWS = [
    ("role", "CS Student & Founder"),
    ("focus", "Shipping AI-native products"),
    ("stack", "FastAPI · Next.js · Supabase · Postgres"),
    ("now", "Heading to Waterloo CS Co-op, Fall 2026"),
]

WIDTH = 460
ROW_H = 34
HEADER_H = 40
FADE_MS = 350
ROW_STAGGER_MS = 260


def render_svg(rows, animate=True):
    height = HEADER_H + len(rows) * ROW_H + 20
    parts = [
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg">',
        "<defs><style>",
        f".label {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {DIM}; }}",
        f".value {{ font-family: 'Courier New', monospace; font-size: 14px; fill: {ACCENT}; }}",
        f".header {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {DIM}; }}",
        "</style></defs>",
        f'<rect width="100%" height="100%" fill="{BG}" rx="6"/>',
        f'<rect x="0" y="0" width="100%" height="{HEADER_H}" fill="#161b22" rx="6"/>',
        '<circle cx="18" cy="20" r="5" fill="#ff5f56"/>',
        '<circle cx="34" cy="20" r="5" fill="#ffbd2e"/>',
        '<circle cx="50" cy="20" r="5" fill="#27c93f"/>',
        f'<text x="{WIDTH - 14}" y="24" text-anchor="end" class="header">sysinfo.sh</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = HEADER_H + 30 + i * ROW_H
        parts.append('<g opacity="0">' if animate else "<g>")
        parts.append(f'<text x="16" y="{y}" class="label">{escape(label)}</text>')
        parts.append(f'<text x="110" y="{y}" class="value">{escape(value)}</text>')
        if animate:
            begin = i * ROW_STAGGER_MS
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin}ms" dur="{FADE_MS}ms" fill="freeze"/>'
            )
        parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    preview = os.environ.get("PREVIEW") == "1"
    svg = render_svg(ROWS, animate=not preview)
    Path("sysinfo.svg").write_text(svg)
    print(f"wrote sysinfo.svg (preview={preview})")


if __name__ == "__main__":
    main()
