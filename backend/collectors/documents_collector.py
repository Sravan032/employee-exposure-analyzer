"""
Public Documents Collector  (SIMULATED)
------------------------------------------
Real-world equivalent: search-engine "dorking" against public indexes for
filetype:pdf / filetype:pptx / filetype:xlsx containing the employee's name
and organization (conference programs, procurement/RFP documents, public
council minutes, slide decks left publicly on company sites). This requires
a search API in production; here it is simulated and clearly labeled so the
pipeline can run end-to-end offline.
"""
from __future__ import annotations
import hashlib


def collect(full_name: str, organization: str) -> dict:
    h = int(hashlib.sha256(f"doc{full_name}{organization}".encode()).hexdigest(), 16)
    found = (h % 10) < 4  # ~40% chance a public document mentions them

    if not found:
        return {"source": "public_documents", "found": False, "provider": "simulated"}

    doc_pool = [
        ("Conference speaker program", "PDF"),
        ("Public procurement / vendor contact sheet", "PDF"),
        ("Company slide deck shared publicly", "PPTX"),
        ("Open-source project contributor list", "TXT"),
    ]
    doc_type, fmt = doc_pool[h % len(doc_pool)]

    return {
        "source": "public_documents",
        "found": True,
        "provider": "simulated",
        "document_type": doc_type,
        "file_format": fmt,
        "note": "Name and organizational affiliation appear in a publicly indexed document.",
        "url": "https://example-public-index.org/simulated-document",
    }
