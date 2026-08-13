#!/usr/bin/env python3
"""Render the full neofetch-style sysinfo panel: joke fields, real GitHub
stats, language breakdown, lines of code, and contact info."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ACCENT = "#2EFFB8"
BG = "#0d1117"
DIM = "#7d8590"
HEADER_BG = "#161b22"
ADD_COLOR = "#3fb950"
DEL_COLOR = "#f85149"

WIDTH = 460
ROW_H = 24
SECTION_GAP = 12
HEADER_H = 40
FADE_MS = 180
ROW_STAGGER_MS = 80


def load_json(path, default):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else default


def build_sections():
    stats = load_json("assets/stats.json", {"repos": 0, "stars": 0, "followers": 0, "commits": 0})
    languages = load_json("assets/languages.json", [])
    loc = load_json("assets/loc.json", {"additions": 0, "deletions": 0})

    sections = []

    sections.append((None, [
        ("OS", "macOS Golden Gate", ACCENT),
        ("Host", "MacBook Pro M4 Pro", ACCENT),
        ("Kernel", "University of Waterloo + Founder Mode", ACCENT),
        ("IDE", "Antigravity + VS Code 1.133", ACCENT),
    ]))

    if languages:
        sections.append(("Languages", [
            (lang["name"], f'{lang["percent"]}%', lang["color"])
            for lang in languages
        ]))

    sections.append(("Contact", [
        ("Email", "jpranav08@gmail.com", ACCENT),
        ("Instagram", "@jpranav08", ACCENT),
        ("LinkedIn", "pranav-jain-10a616276", ACCENT),
    ]))

    sections.append(("GitHub Stats", [
        ("Repos", f'{stats["repos"]:,}', ACCENT),
        ("Stars", f'{stats["stars"]:,}', ACCENT),
        ("Commits", f'{stats["commits"]:,}', ACCENT),
        ("Followers", f'{stats["followers"]:,}', ACCENT),
    ]))

    return sections, loc


def render_svg(sections, loc):
    y = HEADER_H + 26
    row_positions = []
    for header, rows in sections:
        if header:
            row_positions.append(("header", header, y))
            y += ROW_H
        for label, value, color in rows:
            row_positions.append(("row", (label, value, color), y))
            y += ROW_H
        y += SECTION_GAP
    row_positions.append(("loc", None, y))
    height = y + ROW_H + 10

    parts = [
        f'<svg viewBox="0 0 {WIDTH} {height:.0f}" xmlns="http://www.w3.org/2000/svg">',
        "<defs><style>",
        f".label {{ font-family: 'Courier New', monospace; font-size: 12px; fill: {DIM}; }}",
        f".value {{ font-family: 'Courier New', monospace; font-size: 12px; }}",
        f".section {{ font-family: 'Courier New', monospace; font-size: 12px; fill: #e6edf3; font-weight: bold; }}",
        f".header {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {DIM}; }}",
        "</style></defs>",
        f'<rect width="100%" height="100%" fill="{BG}" rx="6"/>',
        f'<rect x="0" y="0" width="100%" height="{HEADER_H}" fill="{HEADER_BG}" rx="6"/>',
        '<circle cx="18" cy="20" r="5" fill="#ff5f56"/>',
        '<circle cx="34" cy="20" r="5" fill="#ffbd2e"/>',
        '<circle cx="50" cy="20" r="5" fill="#27c93f"/>',
        f'<text x="{WIDTH - 14}" y="24" text-anchor="end" class="header">pranav@jpranav0802</text>',
    ]

    for i, (kind, payload, ypos) in enumerate(row_positions):
        begin = i * ROW_STAGGER_MS
        anim_attrs = f'<animate attributeName="opacity" from="0" to="1" begin="{begin}ms" dur="{FADE_MS}ms" fill="freeze"/>'
        if kind == "header":
            parts.append(
                f'<text x="16" y="{ypos}" class="section" opacity="0">{escape(payload)}{anim_attrs}</text>'
            )
        elif kind == "row":
            label, value, color = payload
            parts.append(
                f'<text x="16" y="{ypos}" class="label" opacity="0">{escape(label)}{anim_attrs}</text>'
            )
            parts.append(
                f'<text x="180" y="{ypos}" class="value" fill="{color}" opacity="0">{escape(value)}{anim_attrs}</text>'
            )
        elif kind == "loc":
            parts.append(
                f'<text x="16" y="{ypos}" class="label" opacity="0">Lines of Code{anim_attrs}</text>'
            )
            parts.append(
                f'<text x="180" y="{ypos}" class="value" opacity="0">'
                f'<tspan fill="{ADD_COLOR}">+{loc["additions"]:,}</tspan>'
                f'<tspan fill="{DIM}"> / </tspan>'
                f'<tspan fill="{DEL_COLOR}">-{loc["deletions"]:,}</tspan>'
                f'{anim_attrs}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    sections, loc = build_sections()
    Path("sysinfo.svg").write_text(render_svg(sections, loc))
    print("wrote sysinfo.svg")


if __name__ == "__main__":
    main()
