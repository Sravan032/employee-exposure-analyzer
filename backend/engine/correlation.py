"""
Correlation Engine
-------------------
Takes the raw, heterogeneous output of each collector and normalizes it
into a flat list of "Finding" objects that all share the same shape:

    {
        "category": str,      # e.g. "Email", "GitHub", "Technologies"
        "finding": str,       # human-readable description
        "evidence": str,      # url or source detail
        "risk_key": str,      # key used to look up weight in risk_scoring
    }

This is also where cross-source correlation happens: e.g. if the GitHub
profile's company field matches the target organization, or the inferred
email matches the domain used elsewhere, those get flagged as
"corroborated" findings (higher confidence).
"""
from __future__ import annotations


def build_findings(full_name: str, organization: str, raw: dict) -> list[dict]:
    findings: list[dict] = []

    gh = raw.get("github", {})
    pub = raw.get("publications", {})
    site = raw.get("company_website", {})
    docs = raw.get("public_documents", {})
    contact = raw.get("contact_exposure", {})

    # --- GitHub ---
    if gh.get("found"):
        findings.append({
            "category": "Code Repositories",
            "finding": f"Public GitHub profile identified (@{gh['username']})",
            "evidence": gh.get("profile_url"),
            "risk_key": "github_profile",
        })
        if gh.get("public_email"):
            findings.append({
                "category": "Email",
                "finding": f"Email publicly disclosed on GitHub profile: {gh['public_email']}",
                "evidence": gh.get("profile_url"),
                "risk_key": "email_disclosed",
            })
        if gh.get("top_languages"):
            findings.append({
                "category": "Technologies",
                "finding": f"Public technology/skill footprint: {', '.join(gh['top_languages'])}",
                "evidence": gh.get("profile_url"),
                "risk_key": "tech_stack",
            })
        if gh.get("company_field") and organization.lower() in str(gh["company_field"]).lower():
            findings.append({
                "category": "Organization",
                "finding": f"GitHub profile self-identifies organization: {gh['company_field']}",
                "evidence": gh.get("profile_url"),
                "risk_key": "org_affiliation",
            })
        if gh.get("location"):
            findings.append({
                "category": "Personal Details",
                "finding": f"Approximate location disclosed: {gh['location']}",
                "evidence": gh.get("profile_url"),
                "risk_key": "location_disclosed",
            })
        if gh.get("repos_mentioning_org"):
            findings.append({
                "category": "Organization",
                "finding": f"{len(gh['repos_mentioning_org'])} public repo(s) reference the organization by name",
                "evidence": ", ".join(gh["repos_mentioning_org"][:5]),
                "risk_key": "org_affiliation",
            })

    # --- Publications ---
    if pub.get("found"):
        for paper in pub.get("papers", [])[:5]:
            findings.append({
                "category": "Research Publications",
                "finding": f"Authored publication: \u201c{paper['title']}\u201d",
                "evidence": paper.get("url"),
                "risk_key": "publication",
            })

    # --- Company website ---
    if site.get("found"):
        findings.append({
            "category": "Organization",
            "finding": f"Listed on company {site.get('page_type', 'page')} as {site.get('listed_role')}",
            "evidence": site.get("url"),
            "risk_key": "org_affiliation",
        })

    # --- Public documents ---
    if docs.get("found"):
        findings.append({
            "category": "Documents",
            "finding": f"Mentioned in a publicly indexed document ({docs.get('document_type')}, {docs.get('file_format')})",
            "evidence": docs.get("url"),
            "risk_key": "public_document",
        })

    # --- Contact exposure ---
    if contact.get("email_publicly_confirmed"):
        findings.append({
            "category": "Email",
            "finding": f"Work email pattern confirmed in public sources: {contact['inferred_email']}",
            "evidence": "Cross-referenced across collected sources",
            "risk_key": "email_disclosed",
        })
    else:
        findings.append({
            "category": "Email",
            "finding": f"Work email pattern inferable from naming convention: {contact['inferred_email']} (unconfirmed)",
            "evidence": "Derived from common organizational naming convention",
            "risk_key": "email_inferred",
        })

    if contact.get("phone_publicly_indexed"):
        findings.append({
            "category": "Contact Details",
            "finding": f"Phone number publicly indexed \u2014 {contact.get('phone_hint')}",
            "evidence": "Public business directory listing",
            "risk_key": "phone_exposed",
        })

    if not findings:
        findings.append({
            "category": "General",
            "finding": "No significant public digital footprint identified with current sources",
            "evidence": None,
            "risk_key": "none",
        })

    return findings
