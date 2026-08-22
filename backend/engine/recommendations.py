"""
Recommendations Engine
-------------------------
Maps observed risk_keys to concrete, actionable mitigation guidance,
grouped by the two goals requested by the assignment:
  - Reducing social-engineering risk
  - Reducing information leakage
"""
from __future__ import annotations

RECOMMENDATION_MAP: dict[str, dict] = {
    "email_disclosed": {
        "goal": "Information Leakage",
        "text": "Avoid displaying full work email addresses on public profiles (GitHub, forums). "
                 "Use a monitored alias (e.g. contact@company.com) for public-facing correspondence.",
    },
    "email_inferred": {
        "goal": "Social Engineering",
        "text": "Predictable email-naming conventions make phishing targeting trivial. "
                 "Pair with mandatory phishing-resistant MFA and user training on spoofed-sender detection.",
    },
    "phone_exposed": {
        "goal": "Social Engineering",
        "text": "Publicly indexed personal/direct phone numbers enable vishing and SIM-swap pretexting. "
                 "Request removal from public directories and route external inquiries through a front-desk number.",
    },
    "location_disclosed": {
        "goal": "Information Leakage",
        "text": "Precise location data on public profiles can support physical social-engineering "
                 "or targeted surveillance. Consider limiting to city-level or omitting entirely.",
    },
    "tech_stack": {
        "goal": "Social Engineering",
        "text": "Publicly visible technology stack (languages, frameworks, cloud providers) helps attackers "
                 "craft convincing technical pretexts (fake IT tickets, vendor impersonation). "
                 "Reinforce verification procedures for unsolicited technical requests.",
    },
    "org_affiliation": {
        "goal": "Social Engineering",
        "text": "Confirmed organizational affiliation is often combined with other OSINT for pretexting. "
                 "Train staff to verify identity independently before acting on requests that cite internal "
                 "context (project names, org charts, colleague names).",
    },
    "public_document": {
        "goal": "Information Leakage",
        "text": "Audit publicly indexed documents (slide decks, PDFs, spreadsheets) for embedded contact "
                 "details or internal metadata before publishing; strip metadata and review sharing settings.",
    },
    "publication": {
        "goal": "Information Leakage",
        "text": "Research publications are expected to be public, but review author affiliations and "
                 "acknowledgements for internal project names or infrastructure details that shouldn't be public.",
    },
    "github_profile": {
        "goal": "Information Leakage",
        "text": "Review public repositories for accidentally committed secrets (API keys, credentials, internal "
                 "hostnames) using a secret-scanning tool, and confirm profile visibility settings reflect intent.",
    },
}

GENERAL_RECOMMENDATIONS = [
    {"goal": "Social Engineering", "text": "Run periodic security-awareness training that uses this employee's "
                                             "own OSINT footprint as an anonymized case study."},
    {"goal": "Information Leakage", "text": "Establish a quarterly self-OSINT review process so employees can "
                                              "audit and reduce their own public digital footprint."},
]


def build_recommendations(scored_findings: list[dict]) -> list[dict]:
    seen_keys = set()
    recs = []
    for f in scored_findings:
        key = f.get("risk_key")
        if key in RECOMMENDATION_MAP and key not in seen_keys:
            recs.append(RECOMMENDATION_MAP[key])
            seen_keys.add(key)
    recs.extend(GENERAL_RECOMMENDATIONS)
    return recs
