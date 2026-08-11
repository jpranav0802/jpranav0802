#!/usr/bin/env python3
"""Draw assets/contributions.json as a self-revealing contribution grid."""
import json
from datetime import datetime
from pathlib import Path

LEVELS = ["#1a1a2e", "#0f3d3e", "#0f766e", "#14b8a6", "#2effc9"]
BG = "#0d1117"
DIM = "#7d8590"

CELL = 11
GAP = 3
COL_STAGGER_MS = 60
CELL_FADE_MS = 220


def build_weeks(days):
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    lead_pad = (first.weekday() + 1) % 7  # align to a Sunday-first grid
    padded = [None] * lead_pad + days
    return [padded[i:i + 7] for i in range(0, len(padded), 7)]


def render_svg(data):
    weeks = build_weeks(data["days"])
    width = len(weeks) * (CELL + GAP) + 40
    height = 7 * (CELL + GAP) + 70

    parts = [
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        "<defs><style>",
        f".stats {{ font-family: 'Courier New', monospace; font-size: 13px; fill: {DIM}; }}",
        f".legend {{ font-family: 'Courier New', monospace; font-size: 11px; fill: {DIM}; }}",
        "</style></defs>",
        f'<rect width="100%" height="100%" fill="{BG}" rx="6"/>',
    ]

    ox, oy = 20, 20
    for wi, week in enumerate(weeks):
        begin = wi * COL_STAGGER_MS
        for di, day in enumerate(week):
            if day is None:
                continue
            x, y = ox + wi * (CELL + GAP), oy + di * (CELL + GAP)
            color = LEVELS[min(day["level"], len(LEVELS) - 1)]
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin}ms" dur="{CELL_FADE_MS}ms" fill="freeze"/></rect>'
            )

    legend_y = height - 34
    parts.append(f'<text x="{ox}" y="{legend_y}" class="legend">Less</text>')
    lx = ox + 40
    for i, color in enumerate(LEVELS):
        parts.append(f'<rect x="{lx + i * 16}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{lx + len(LEVELS) * 16 + 6}" y="{legend_y}" class="legend">More</text>')

    stats_y = height - 12
    stats_line = (
        f'{data["total"]} contributions this year · '
        f'{data["current_streak"]}-day streak (best {data["longest_streak"]}) · '
        f'busiest day: {data["busiest_weekday"]}'
    )
    parts.append(f'<text x="{ox}" y="{stats_y}" class="stats">{stats_line}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    data = json.loads(Path("assets/contributions.json").read_text())
    Path("graph.svg").write_text(render_svg(data))
    print("wrote graph.svg")


if __name__ == "__main__":
    main()
