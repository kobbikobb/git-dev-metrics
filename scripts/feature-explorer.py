#!/usr/bin/env python3
"""
Feature Explorer
Fetches recent GitHub issues, asks Gemini to suggest new features,
and creates them as issues via the GitHub API.

Required env vars:
  GEMINI_API_KEY    - Google AI Studio free tier works fine
  GH_TOKEN          - GitHub token with issues:write
  GITHUB_REPOSITORY - owner/repo (set automatically in Actions)
"""

import json
import os
import urllib.error
import urllib.request

GEMINI_MODEL = "gemini-2.0-flash"
MAX_EXISTING_ISSUES = 20
LABEL = "explorer:feature"


def env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise SystemExit(f"Missing required env var: {key}")
    return val


def gh_request(path: str, method: str = "GET", body: dict | None = None) -> dict:
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {env('GH_TOKEN')}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"GitHub {e.code} {path}: {e.read().decode()}")


def get_recent_issues(repo: str) -> list[str]:
    issues = gh_request(f"/repos/{repo}/issues?state=all&per_page={MAX_EXISTING_ISSUES}")
    return [i["title"] for i in issues]


def ensure_label(repo: str):
    try:
        gh_request(
            f"/repos/{repo}/labels",
            method="POST",
            body={"name": LABEL, "color": "0075ca", "description": "AI suggested feature"},
        )
        print(f"Created label: {LABEL}")
    except SystemExit as e:
        if "422" not in str(e):  # 422 = already exists
            raise


def create_issue(repo: str, title: str, body: str):
    issue = gh_request(
        f"/repos/{repo}/issues",
        method="POST",
        body={"title": title, "body": body, "labels": [LABEL]},
    )
    print(f"Created #{issue['number']}: {title}")


def suggest_features(existing_titles: list[str]) -> list[dict]:
    existing = (
        "\n".join(f"- {t}" for t in existing_titles) if existing_titles else "(none yet)"
    )

    prompt = f"""You are a Feature Explorer for a software project.
Analyze the existing GitHub issues below and identify 1-3 valuable feature gaps not already covered.

Existing issues:
{existing}

Return ONLY a JSON array. No markdown, no explanation.
Schema: [{{"title": "Short feature title", "body": "Clear description and why it's valuable"}}]"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["title", "body"],
                },
            },
        },
    }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={env('GEMINI_API_KEY')}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Gemini {e.code}: {e.read().decode()}")

    text = data["candidates"][0]["content"]["parts"][0]["text"]
    features = json.loads(text)

    if not isinstance(features, list):
        raise SystemExit("Gemini did not return an array")

    return features


def main():
    repo = env("GITHUB_REPOSITORY")
    print(f"Running Feature Explorer on {repo}")

    existing = get_recent_issues(repo)
    print(f"Found {len(existing)} existing issues")

    features = suggest_features(existing)
    print(f"Gemini suggested {len(features)} feature(s)")

    ensure_label(repo)

    for f in features:
        create_issue(repo, f["title"], f["body"])

    print("Done.")


if __name__ == "__main__":
    main()
