const API_BASE = ""; // same-origin (FastAPI serves this file too)

const form = document.getElementById("scan-form");
const runBtn = document.getElementById("run-btn");
const formError = document.getElementById("form-error");

const emptyState = document.getElementById("empty-state");
const loadingState = document.getElementById("loading-state");
const loadingText = document.getElementById("loading-text");
const reportEl = document.getElementById("report");

let currentReportId = null;

const LOADING_MESSAGES = [
  "Querying public code repositories\u2026",
  "Checking research publication indexes\u2026",
  "Scanning public company pages\u2026",
  "Cross-referencing public documents\u2026",
  "Correlating findings\u2026",
  "Scoring exposure risk\u2026",
];

function cycleLoadingText() {
  let i = 0;
  loadingText.textContent = LOADING_MESSAGES[0];
  return setInterval(() => {
    i = (i + 1) % LOADING_MESSAGES.length;
    loadingText.textContent = LOADING_MESSAGES[i];
  }, 900);
}

function setView(view) {
  emptyState.hidden = view !== "empty";
  loadingState.hidden = view !== "loading";
  reportEl.hidden = view !== "report";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  formError.hidden = true;

  const payload = {
    full_name: document.getElementById("full_name").value.trim(),
    organization: document.getElementById("organization").value.trim(),
    github_username: document.getElementById("github_username").value.trim() || null,
    authorized: document.getElementById("authorized").checked,
  };

  if (!payload.authorized) {
    formError.textContent = "Please confirm this is an authorized assessment before running a scan.";
    formError.hidden = false;
    return;
  }

  runBtn.disabled = true;
  setView("loading");
  const tick = cycleLoadingText();

  try {
    const resp = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed (${resp.status})`);
    }

    const report = await resp.json();
    renderReport(report);
    setView("report");
  } catch (err) {
    setView("empty");
    formError.textContent = err.message || "Something went wrong running the scan.";
    formError.hidden = false;
  } finally {
    clearInterval(tick);
    runBtn.disabled = false;
  }
});

document.getElementById("new-scan").addEventListener("click", () => {
  setView("empty");
});

document.getElementById("download-md").addEventListener("click", async () => {
  if (!currentReportId) return;
  const resp = await fetch(`${API_BASE}/api/report/${currentReportId}/markdown`);
  const data = await resp.json();
  const blob = new Blob([data.markdown], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `exposure-report-${currentReportId}.md`;
  a.click();
  URL.revokeObjectURL(url);
});

function renderReport(report) {
  currentReportId = report.report_id;

  document.getElementById("report-id").textContent = `#${report.report_id}`;
  document.getElementById("report-subject-name").textContent = report.subject.full_name;
  document.getElementById("report-subject-org").textContent = report.subject.organization;
  document.getElementById("report-time").textContent = new Date(report.generated_at).toLocaleString();
  document.getElementById("report-duration").textContent = `${report.duration_ms}ms`;

  const stamp = document.getElementById("risk-stamp");
  stamp.className = `stamp stamp--${report.overall_risk.band}`;
  document.getElementById("stamp-band").textContent = `${report.overall_risk.band.toUpperCase()} RISK`;
  document.getElementById("stamp-score").textContent = `${report.overall_risk.score}/100`;

  const tbody = document.getElementById("findings-body");
  tbody.innerHTML = "";
  for (const f of report.findings) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(f.category)}</td>
      <td>${escapeHtml(f.finding)}</td>
      <td><span class="risk-pill risk-pill--${f.level}">${f.level}</span></td>
      <td>${f.evidence ? linkify(f.evidence) : "\u2014"}</td>
    `;
    tbody.appendChild(tr);
  }

  const socialList = document.getElementById("rec-social");
  const leakList = document.getElementById("rec-leak");
  socialList.innerHTML = "";
  leakList.innerHTML = "";
  for (const r of report.recommendations) {
    const li = document.createElement("li");
    li.textContent = r.text;
    if (r.goal === "Social Engineering") socialList.appendChild(li);
    else leakList.appendChild(li);
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function linkify(evidence) {
  const safe = escapeHtml(evidence);
  if (/^https?:\/\//.test(evidence)) {
    return `<a href="${safe}" target="_blank" rel="noopener noreferrer" style="color:inherit;">${safe}</a>`;
  }
  return safe;
}
