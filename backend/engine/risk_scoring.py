"""
Risk Scoring Engine
---------------------
Predefined, transparent scoring criteria. Each finding type carries a
fixed weight reflecting its social-engineering / information-leakage
potential. Weights are intentionally simple and documented here so the
scoring is auditable (a core requirement for any security-assessment tool).

Weight scale:
    1 = Low       (background/contextual OSINT, low direct exploitability)
    2 = Medium    (directly useful for phishing / pretexting)
    3 = High      (directly enables targeted social engineering or contact)
    4 = Critical  (credential/secret-level exposure) -- reserved for future collectors

The overall score is the sum of weights, normalized to a 0-100 scale
against a configurable ceiling, then bucketed into a risk band.
"""
from __future__ import annotations

# --- Predefined criteria: risk_key -> (weight, level label) -------------
CRITERIA: dict[str, tuple[int, str]] = {
    "github_profile":     (1, "Low"),
    "tech_stack":         (1, "Low"),
    "org_affiliation":    (1, "Low"),
    "location_disclosed": (2, "Medium"),
    "publication":        (1, "Low"),
    "public_document":    (2, "Medium"),
    "email_inferred":     (1, "Low"),
    "email_disclosed":    (2, "Medium"),
    "phone_exposed":      (3, "High"),
    "none":               (0, "Low"),
}

# Ceiling used to normalize the raw weight sum to a 0-100 scale.
# Tuned so a "typical high-exposure" employee (several medium/high findings)
# lands in the 70-90 range rather than maxing out immediately.
NORMALIZATION_CEILING = 14


def score_finding(risk_key: str) -> dict:
    weight, level = CRITERIA.get(risk_key, (1, "Low"))
    return {"weight": weight, "level": level}


def score_findings(findings: list[dict]) -> list[dict]:
    scored = []
    for f in findings:
        risk = score_finding(f["risk_key"])
        scored.append({**f, **risk})
    return scored


def overall_score(scored_findings: list[dict]) -> dict:
    total_weight = sum(f["weight"] for f in scored_findings)
    normalized = min(100, round((total_weight / NORMALIZATION_CEILING) * 100))

    if normalized >= 70:
        band = "High"
    elif normalized >= 35:
        band = "Medium"
    else:
        band = "Low"

    return {
        "raw_weight_sum": total_weight,
        "score": normalized,
        "band": band,
    }
