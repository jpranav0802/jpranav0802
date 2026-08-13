#!/usr/bin/env python3
"""Aggregate language byte-share across all owned, non-fork repos."""
import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

import httpx

USERNAME = os.environ.get("GH_USERNAME")

LANGUAGES_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 50, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
    }
  }
}
"""


def get_token():
    token = os.environ.get("STATS_TOKEN")
    if token:
        return token
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def fetch_languages(username, token):
    headers = {"Authorization": f"bearer {token}"}
    totals = defaultdict(int)
    colors = {}
    after = None
    while True:
        resp = httpx.post(
            "https://api.github.com/graphql",
            json={"query": LANGUAGES_QUERY, "variables": {"login": username, "after": after}},
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise SystemExit(f"GraphQL errors: {data['errors']}")
        repos = data["data"]["user"]["repositories"]
        for repo in repos["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                totals[name] += edge["size"]
                colors[name] = edge["node"]["color"]
        if repos["pageInfo"]["hasNextPage"]:
            after = repos["pageInfo"]["endCursor"]
        else:
            break
    return totals, colors


def main():
    if not USERNAME:
        raise SystemExit("set GH_USERNAME before running this script")
    token = get_token()

    totals, colors = fetch_languages(USERNAME, token)
    grand_total = sum(totals.values())
    if grand_total == 0:
        raise SystemExit("no language bytes found - do your repos have any code in them?")

    languages = sorted(
        (
            {
                "name": name,
                "color": colors.get(name, "#888888"),
                "percent": round(size / grand_total * 100, 1),
            }
            for name, size in totals.items()
        ),
        key=lambda x: x["percent"],
        reverse=True,
    )[:6]  # top 6 keeps the panel readable

    out_path = Path("assets/languages.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(languages, indent=2))
    print(f"wrote {out_path}:")
    for lang in languages:
        print(f"  {lang['name']}: {lang['percent']}%")


if __name__ == "__main__":
    main()
