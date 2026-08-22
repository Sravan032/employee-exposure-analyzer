"""
GitHub Collector
-----------------
Uses the REAL, public GitHub REST API (no authentication required for
low-volume, read-only requests against public data). This mirrors what
any anonymous visitor to github.com could see -- nothing private,
nothing behind a login, no scraping of pages that disallow it.

Docs: https://docs.github.com/en/rest
"""
from __future__ import annotations

import requests
from typing import Optional

GITHUB_API = "https://api.github.com"
TIMEOUT = 6


def _get(url: str, params: Optional[dict] = None) -> Optional[dict | list]:
    try:
        resp = requests.get(
            url,
            params=params,
            timeout=TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.RequestException:
        # Network restricted / offline sandbox / rate-limited -> caller falls back gracefully
        return None


def find_candidate_username(full_name: str, organization: str) -> Optional[str]:
    """Search public GitHub users by name + org hint. Best-effort matching only."""
    query = f'{full_name} in:name {organization} in:bio'
    data = _get(f"{GITHUB_API}/search/users", params={"q": query, "per_page": 5})
    if not data or not data.get("items"):
        # retry with a looser query
        data = _get(f"{GITHUB_API}/search/users", params={"q": full_name, "per_page": 5})
    if data and data.get("items"):
        return data["items"][0]["login"]
    return None


def collect(full_name: str, organization: str, github_username: Optional[str] = None) -> dict:
    """
    Returns a normalized dict of publicly visible GitHub OSINT signals.
    If no username is supplied, attempts a best-effort public search.
    """
    username = github_username or find_candidate_username(full_name, organization)

    if not username:
        return {"source": "github", "found": False, "reason": "no_public_match"}

    profile = _get(f"{GITHUB_API}/users/{username}")
    if not profile:
        return {"source": "github", "found": False, "reason": "api_unreachable_or_no_profile"}

    repos = _get(f"{GITHUB_API}/users/{username}/repos", params={"per_page": 100, "sort": "updated"}) or []

    languages: dict[str, int] = {}
    org_mentions = []
    for r in repos:
        lang = r.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
        if r.get("description") and organization.lower() in r["description"].lower():
            org_mentions.append(r["name"])

    top_languages = sorted(languages, key=languages.get, reverse=True)[:6]

    return {
        "source": "github",
        "found": True,
        "username": username,
        "profile_url": profile.get("html_url"),
        "name": profile.get("name"),
        "public_email": profile.get("email"),  # None unless the user opted to show it publicly
        "bio": profile.get("bio"),
        "company_field": profile.get("company"),
        "blog": profile.get("blog"),
        "location": profile.get("location"),
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "top_languages": top_languages,
        "repos_mentioning_org": org_mentions,
        "created_at": profile.get("created_at"),
    }
