"""
Publications Collector
-----------------------
Primary source: arXiv's public Atom API (no key required, fully public,
explicitly designed for programmatic/automated querying):
  https://export.arxiv.org/api/query

If the arXiv API is unreachable (offline demo / restricted network),
falls back to a clearly-labeled SIMULATED result so the rest of the
pipeline (correlation + scoring) can still be demonstrated end-to-end.
In production, this collector could equally query Google Scholar via an
authorized API, ORCID, Semantic Scholar, or a company's own publications page.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import requests
from typing import Optional

ARXIV_API = "http://export.arxiv.org/api/query"
TIMEOUT = 6
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def _query_arxiv(full_name: str) -> Optional[list[dict]]:
    try:
        resp = requests.get(
            ARXIV_API,
            params={"search_query": f'au:"{full_name}"', "max_results": 5},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        root = ET.fromstring(resp.text)
        entries = []
        for entry in root.findall("atom:entry", ATOM_NS):
            title_el = entry.find("atom:title", ATOM_NS)
            link_el = entry.find("atom:id", ATOM_NS)
            published_el = entry.find("atom:published", ATOM_NS)
            entries.append({
                "title": (title_el.text or "").strip() if title_el is not None else "Untitled",
                "url": link_el.text.strip() if link_el is not None else None,
                "published": published_el.text[:10] if published_el is not None else None,
            })
        return entries
    except (requests.RequestException, ET.ParseError):
        return None


def collect(full_name: str, organization: str) -> dict:
    entries = _query_arxiv(full_name)

    if entries is not None:
        return {
            "source": "publications",
            "found": len(entries) > 0,
            "provider": "arXiv (live public API)",
            "papers": entries,
        }

    # ---- Fallback: labeled simulation (network unavailable in this environment) ----
    seed = sum(ord(c) for c in full_name) % 3
    if seed == 0:
        return {"source": "publications", "found": False, "provider": "simulated", "papers": []}

    simulated_papers = [
        {
            "title": f"Applied {['Machine Learning', 'Cloud Security', 'Distributed Systems'][seed % 3]} Practices at {organization}",
            "url": "https://example-conference.org/proceedings/simulated-entry",
            "published": "2023-04-11",
        }
    ]
    return {
        "source": "publications",
        "found": True,
        "provider": "simulated",
        "papers": simulated_papers,
    }
