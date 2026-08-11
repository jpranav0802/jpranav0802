#!/usr/bin/env python3
"""Pull the public contribution calendar for GH_USERNAME and save it as JSON.

No auth needed - this scrapes the same HTML fragment GitHub's own profile
page uses (github.com/users/<name>/contributions).
"""
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx
from lxml import html

USERNAME = os.environ.get("GH_USERNAME")
URL_TMPL = "https://github.com/users/{username}/contributions"


def fetch(username):
    resp = httpx.get(
        URL_TMPL.format(username=username),
        timeout=15,
        headers={"User-Agent": "living-terminal-readme/1.0"},
    )
    resp.raise_for_status()
    return resp.text


def parse(raw_html):
    tree = html.fromstring(raw_html)
    tooltips = {
        tt.get("for"): tt.text_content().strip()
        for tt in tree.xpath("//tool-tip")
        if tt.get("for")
    }
    days = []
    for td in tree.xpath('//td[contains(@class, "ContributionCalendar-day")]'):
        d = td.get("data-date")
        if not d:
            continue
        level = int(td.get("data-level", 0))
        text = tooltips.get(td.get("id"), "")
        m = re.match(r"(No|\d+)\s+contributions?", text)
        count = 0 if not m or m.group(1) == "No" else int(m.group(1))
        days.append({"date": d, "count": count, "level": level})
    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    longest_streak = run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            longest_streak = max(longest_streak, run)
        else:
            run = 0

    by_weekday = defaultdict(int)
    for d in days:
        wd = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%A")
        by_weekday[wd] += d["count"]
    busiest = max(by_weekday, key=by_weekday.get) if by_weekday else None

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_weekday": busiest,
    }


def main():
    if not USERNAME:
        raise SystemExit("set GH_USERNAME before running this script")

    days = parse(fetch(USERNAME))
    if not days:
        raise SystemExit("parsed 0 day cells - GitHub's markup may have changed")

    stats = compute_stats(days)
    out = {
        "username": USERNAME,
        "pulled_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        **stats,
    }

    out_path = Path("assets/contributions.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path} - {stats['total']} contributions, "
          f"{stats['current_streak']}-day current streak")


if __name__ == "__main__":
    main()
