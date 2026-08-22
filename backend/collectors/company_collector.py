"""
Company Website Collector  (SIMULATED)
----------------------------------------
Real-world equivalent: querying a licensed search API (Google Programmable
Search, Bing Web Search) restricted to the target company's domain, e.g.
`site:company.com "Jane Doe"`, then parsing "About us" / "Team" / press-
release pages. That requires a paid API key, so this collector returns a
deterministic SIMULATED finding, clearly labeled, so the pipeline can be
demonstrated without external credentials. Swap in a real search API call
here for production use.
"""
from __future__ import annotations
import hashlib


def collect(full_name: str, organization: str) -> dict:
    h = int(hashlib.sha256(f"{full_name}{organization}".encode()).hexdigest(), 16)
    on_team_page = (h % 10) < 7  # ~70% of employees show up on some company page

    if not on_team_page:
        return {"source": "company_website", "found": False, "provider": "simulated"}

    role_pool = ["Software Engineer", "Data Analyst", "Product Manager", "DevOps Engineer", "Security Analyst"]
    role = role_pool[h % len(role_pool)]

    return {
        "source": "company_website",
        "found": True,
        "provider": "simulated",
        "page_type": "Team / About Us page",
        "listed_role": role,
        "listed_department": "Engineering" if "Engineer" in role else "Business",
        "url": f"https://www.{organization.lower().replace(' ', '')}.example/team",
    }
