#!/usr/bin/env python3
"""Sum lines added/removed (by you) across all your owned repos.

Uses GitHub's pre-computed contributor-stats endpoint rather than walking
commit history ourselves - much cheaper, but can return 202 (still
computing) on a repo's first request, so we retry briefly. Some repos also
return an empty body instead of [] - guarded against below.
"""
import json
import os
import subprocess
import time
from pathlib import Path

import httpx

USERNAME = os.environ.get("GH_USERNAME")

REPOS_QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 50, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes { name }
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


def list_repo_names(username, token):
    headers = {"Authorization": f"bearer {token}"}
    names = []
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
        repos = data["data"]["user"]["repositories"]
        names.extend(r["name"] for r in repos["nodes"])
        if repos["pageInfo"]["hasNextPage"]:
            after = repos["pageInfo"]["endCursor"]
        else:
            break
    return names


def fetch_contributor_stats(username, repo, token, retries=4):
    url = f"https://api.github.com/repos/{username}/{repo}/stats/contributors"
    headers = {
        "Authorization": f"bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    for attempt in range(retries):
        resp = httpx.get(url, headers=headers, timeout=20)
        if resp.status_code == 202:
            time.sleep(2)
            continue
        resp.raise_for_status()
        if not resp.content:
            return []  # empty repo - nothing to compute stats from
        try:
            return resp.json() or []
        except ValueError:
            return []  # non-JSON body, treat as no data rather than crash
    return []


def main():
    if not USERNAME:
        raise SystemExit("set GH_USERNAME before running this script")
    token = get_token()

    repo_names = list_repo_names(USERNAME, token)
    additions = deletions = 0

    for repo in repo_names:
        contributors = fetch_contributor_stats(USERNAME, repo, token)
        for c in contributors:
            author = c.get("author") or {}
            if author.get("login", "").lower() != USERNAME.lower():
                continue
            for week in c.get("weeks", []):
                additions += week.get("a", 0)
                deletions += week.get("d", 0)

    out_path = Path("assets/loc.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"additions": additions, "deletions": deletions}, indent=2))
    print(f"wrote {out_path}: +{additions} / -{deletions} across {len(repo_names)} repos")


if __name__ == "__main__":
    main()
