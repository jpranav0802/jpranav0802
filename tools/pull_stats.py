#!/usr/bin/env python3
"""Pull real GitHub stats: repo count, total stars, followers, all-time commits."""
import json
import os
import subprocess
from pathlib import Path

import httpx

USERNAME = os.environ.get("GH_USERNAME")

REPOS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes { stargazerCount }
    }
  }
}
"""


def get_token():
    token = os.environ.get("STATS_TOKEN")
    if token:
        return token
    # Local fallback: reuse the token from your already-authenticated gh CLI.
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def fetch_repo_stats(username, token):
    headers = {"Authorization": f"bearer {token}"}
    followers = total_repos = total_stars = 0
    after = None
    while True:
        resp = httpx.post(
            "https://api.github.com/graphql",
            json={"query": REPOS_QUERY, "variables": {"login": username, "after": after}},
            headers=headers,
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise SystemExit(f"GraphQL errors: {data['errors']}")
        user = data["data"]["user"]
        followers = user["followers"]["totalCount"]
        repos = user["repositories"]
        total_repos = repos["totalCount"]
        total_stars += sum(r["stargazerCount"] for r in repos["nodes"])
        if repos["pageInfo"]["hasNextPage"]:
            after = repos["pageInfo"]["endCursor"]
        else:
            break
    return {"repos": total_repos, "stars": total_stars, "followers": followers}


def fetch_commit_count(username, token):
    resp = httpx.get(
        "https://api.github.com/search/commits",
        params={"q": f"author:{username}"},
        headers={
            "Authorization": f"bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json().get("total_count", 0)


def main():
    if not USERNAME:
        raise SystemExit("set GH_USERNAME before running this script")
    token = get_token()

    stats = fetch_repo_stats(USERNAME, token)
    stats["commits"] = fetch_commit_count(USERNAME, token)

    out_path = Path("assets/stats.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(stats, indent=2))
    print(f"wrote {out_path}: {stats}")


if __name__ == "__main__":
    main()
