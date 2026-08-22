"""
Employee Exposure Analyzer - Backend API
==========================================
An OSINT-based tool that aggregates PUBLICLY AVAILABLE information about
an employee (with the explicit intent of authorized, defensive security
assessment -- e.g. a company auditing its own staff's public exposure)
and produces a risk-scored exposure report with mitigation guidance.

Ethical scope, by design:
  - Only queries public APIs / simulates public-source lookups.
  - No login-walled scraping, no data brokers, no breach-dump lookups.
  - No credential access, no contact of the target, no automated messaging.
  - Intended for authorized internal security assessments / awareness
    programs, not for surveillance of individuals without organizational
    authorization.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from collectors import (
    github_collector,
    publications_collector,
    company_collector,
    documents_collector,
    contact_collector,
)
from engine import correlation, risk_scoring, recommendations

app = FastAPI(
    title="Employee Exposure Analyzer",
    description="OSINT-based employee digital-footprint & risk exposure tool (ethical/public-source scope).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory report store (demo only -- swap for a DB in production)
REPORTS: dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    full_name: str = Field(..., min_length=2, examples=["Jane Doe"])
    organization: str = Field(..., min_length=2, examples=["Acme Corp"])
    github_username: str | None = Field(default=None, examples=["janedoe-dev"])
    authorized: bool = Field(
        default=False,
        description="Confirms this lookup is an authorized security assessment (e.g. self-audit, "
                     "internal red-team exercise, employee-consented review).",
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    if not req.authorized:
        raise HTTPException(
            status_code=400,
            detail="This tool is scoped to authorized security assessments only. "
                   "Please confirm 'authorized' to proceed.",
        )

    started = time.time()

    raw = {
        "github": github_collector.collect(req.full_name, req.organization, req.github_username),
        "publications": publications_collector.collect(req.full_name, req.organization),
        "company_website": company_collector.collect(req.full_name, req.organization),
        "public_documents": documents_collector.collect(req.full_name, req.organization),
        "contact_exposure": contact_collector.collect(req.full_name, req.organization),
    }

    findings = correlation.build_findings(req.full_name, req.organization, raw)
    scored = risk_scoring.score_findings(findings)
    overall = risk_scoring.overall_score(scored)
    recs = recommendations.build_recommendations(scored)

    report_id = str(uuid.uuid4())[:8]
    report = {
        "report_id": report_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round((time.time() - started) * 1000),
        "subject": {"full_name": req.full_name, "organization": req.organization},
        "sources_queried": list(raw.keys()),
        "raw_sources": raw,
        "findings": scored,
        "overall_risk": overall,
        "recommendations": recs,
    }
    REPORTS[report_id] = report
    return report


@app.get("/api/report/{report_id}")
def get_report(report_id: str):
    report = REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/api/report/{report_id}/markdown")
def get_report_markdown(report_id: str):
    report = REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    lines = [
        f"# Employee Exposure Report",
        f"**Subject:** {report['subject']['full_name']} ({report['subject']['organization']})",
        f"**Generated:** {report['generated_at']}",
        f"**Overall Risk:** {report['overall_risk']['band']} ({report['overall_risk']['score']}/100)",
        "",
        "## Findings",
        "",
        "| Category | Finding | Risk | Evidence |",
        "|---|---|---|---|",
    ]
    for f in report["findings"]:
        evidence = f.get("evidence") or "-"
        lines.append(f"| {f['category']} | {f['finding']} | {f['level']} | {evidence} |")

    lines += ["", "## Recommendations", ""]
    for r in report["recommendations"]:
        lines.append(f"- **[{r['goal']}]** {r['text']}")

    return {"markdown": "\n".join(lines)}


# --- Serve the static frontend dashboard ---------------------------------
# Resolved relative to this file (not the process's working directory) so it
# works the same whether started locally, in Docker, or by a host like
# Render/Railway that may launch uvicorn from a different cwd.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
