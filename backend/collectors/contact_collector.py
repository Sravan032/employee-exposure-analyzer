"""
Contact Exposure Collector  (SIMULATED)
-------------------------------------------
Two things happen here, both grounded in real OSINT technique but
simulated for this demo:

1. Email pattern inference: many organizations use a predictable
   `firstname.lastname@company.com` convention, which is often confirmed
   publicly via press releases, GitHub commit metadata, or conference
   listings. We only *construct the plausible address*, we do not verify
   deliverability, send mail, or attempt to access any mailbox.

2. Phone number exposure: simulates whether a number was found in a
   public directory / press listing. In production this would be sourced
   from something like a public company directory page the org itself
   published -- never from a data broker or breach dump.
"""
from __future__ import annotations
import hashlib
import re


def _guess_domain(organization: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", organization.lower())
    return f"{slug}.com"


def collect(full_name: str, organization: str) -> dict:
    parts = full_name.lower().split()
    first, last = (parts[0], parts[-1]) if len(parts) > 1 else (parts[0], "")
    domain = _guess_domain(organization)
    inferred_email = f"{first}.{last}@{domain}" if last else f"{first}@{domain}"

    h = int(hashlib.sha256(f"contact{full_name}{organization}".encode()).hexdigest(), 16)
    email_confirmed_public = (h % 10) < 5   # ~50% chance seen in a real public source
    phone_exposed = (h % 10) < 2            # ~20% chance a phone number is publicly indexed

    result = {
        "source": "contact_exposure",
        "provider": "simulated",
        "inferred_email": inferred_email,
        "email_publicly_confirmed": email_confirmed_public,
        "phone_publicly_indexed": phone_exposed,
    }
    if phone_exposed:
        result["phone_hint"] = "Partial number found in a public business directory listing"
    return result
