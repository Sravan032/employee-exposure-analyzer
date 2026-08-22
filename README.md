# Employee Exposure Analyzer

An OSINT-based tool that aggregates an employee's **publicly available**
digital footprint across multiple sources, correlates it, assigns a
security risk score, and produces an exposure report with mitigation
recommendations — built for **authorized** internal security assessments
and employee security-awareness programs.

> **Ethical scope.** This tool only ever queries public APIs or simulates
> public-source lookups. It never scrapes login-walled pages, never uses
> data brokers or breach dumps, never contacts the subject, and requires
> the caller to explicitly confirm the lookup is authorized before it runs.

---

## 1. Architecture

```
 User input (name + org)
        │
        ▼
 ┌─────────────────────────────────────────────┐
 │                Collectors                    │
 │  github_collector       -> REAL GitHub REST API
 │  publications_collector -> REAL arXiv API (falls back to
 │                              a labeled simulation offline)
 │  company_collector      -> simulated "team page" lookup
 │  documents_collector    -> simulated public-document lookup
 │  contact_collector      -> simulated email/phone exposure
 └─────────────────────────────────────────────┘
        │  raw per-source JSON
        ▼
 ┌─────────────────────────────────────────────┐
 │           Correlation Engine                  │
 │  Normalizes all sources into one Finding list  │
 │  (category, finding, evidence, risk_key)       │
 └─────────────────────────────────────────────┘
        │
        ▼
 ┌─────────────────────────────────────────────┐
 │           Risk Scoring Engine                 │
 │  Predefined weight table -> per-finding level  │
 │  Weighted sum -> normalized 0-100 overall score│
 └─────────────────────────────────────────────┘
        │
        ▼
 ┌─────────────────────────────────────────────┐
 │        Recommendations Engine                 │
 │  risk_key -> social-engineering / leakage      │
 │  mitigation guidance                           │
 └─────────────────────────────────────────────┘
        │
        ▼
   Exposure Report (JSON + Markdown) -> Dashboard
```

Two collectors call **real public APIs**:
- **GitHub** (`api.github.com`) — public profile, public repos, languages, bio, location.
- **arXiv** (`export.arxiv.org`) — public research publications by author name.

Three collectors are **clearly labeled simulations** (`provider: "simulated"`
in their output) standing in for capabilities that need a paid search API
in production (company site indexing, public-document discovery, phone/email
directory exposure). Swap-in points are documented in each collector's
docstring.

## 2. Risk scoring criteria (predefined, auditable)

| risk_key            | Weight | Level    | Meaning |
|----------------------|:------:|----------|---------|
| `github_profile`     | 1 | Low      | Public code-repository presence |
| `tech_stack`         | 1 | Low      | Public technology/skill footprint |
| `org_affiliation`    | 1 | Low      | Confirmed organizational affiliation |
| `publication`        | 1 | Low      | Authored public research |
| `email_inferred`     | 1 | Low      | Email guessable from naming convention |
| `location_disclosed` | 2 | Medium   | Approximate location public |
| `public_document`    | 2 | Medium   | Named in a public document |
| `email_disclosed`    | 2 | Medium   | Email confirmed public |
| `phone_exposed`      | 3 | High     | Phone number publicly indexed |

Overall score = sum of finding weights, normalized to 0–100 (ceiling = 14),
bucketed into **Low (<35) / Medium (35–69) / High (≥70)**. See
`backend/engine/risk_scoring.py` for the exact, editable table.

## 3. Running it

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open **http://localhost:8000** — the dashboard is served by the same
FastAPI app (no separate frontend server needed).

## 4. API

| Method | Path | Description |
|---|---|---|
| POST | `/api/analyze` | Run a scan. Body: `{full_name, organization, github_username?, authorized}`. `authorized: true` is required. |
| GET  | `/api/report/{id}` | Fetch a previously generated report (JSON). |
| GET  | `/api/report/{id}/markdown` | Export the report as Markdown. |

## 5. Extending it

- Add a real search-API-backed `company_collector` / `documents_collector` (Google Programmable Search / Bing Web Search, scoped `site:` queries).
- Add a `linkedin` collector *only* via an authorized, ToS-compliant data source (e.g. an internal HR directory export) — do not scrape LinkedIn directly.
- Persist reports in a real database instead of the in-memory `REPORTS` dict.
- Add authentication/audit logging in front of `/api/analyze` for real deployments, since this tool surfaces sensitive-enough aggregated data that access itself should be logged.
