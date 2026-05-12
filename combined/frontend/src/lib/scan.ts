/**
 * Live scan client — calls the TrustScan FastAPI backend (v1) and adapts the
 * response to the shape the UI expects.
 *
 *   POST /api/v1/scans          { target }  → ScanDetail
 *   WS   /api/v1/ws/scans/:id                → scan_progress events
 *
 * In dev the Vite proxy forwards /api/* to http://localhost:8000.
 * In prod set VITE_TRUSTSCAN_API to the backend origin (no trailing slash).
 */

export type ScanResult = {
  target: string;
  score: number;
  verdict: "Trusted" | "Suspicious" | "High risk" | "Critical";
  fraudScore: number;
  ssl: { valid: boolean; issuer: string; expires: string; grade: string };
  whois: { registrar: string; created: string; country: string; ageDays: number };
  ip: { address: string; asn: string; org: string; country: string; abuse: number };
  blacklists: { name: string; listed: boolean }[];
  indicators: { label: string; status: "ok" | "warn" | "bad" }[];
  ai: string;
};

// ── Backend v1 response shape ───────────────────────────────────────────────
type V1Indicator = {
  kind: string;
  label: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  score_delta: number;
  description?: string | null;
};

type V1AI = {
  provider: string;
  model?: string | null;
  summary?: string | null;
  exec_summary?: string | null;
  risk_description?: string | null;
  remediation?: string | null;
};

type V1ScanDetail = {
  id: string;
  target: string;
  target_type: "url" | "ip" | "domain" | "email";
  normalized_target: string;
  status: string;
  trust_score: number | null;
  fraud_probability: number | null;
  threat_level: string | null;
  verdict: "Trusted" | "Suspicious" | "High risk" | "Critical" | null;
  confidence: number | null;
  created_at: string;
  completed_at?: string | null;
  payload: Record<string, any>;
  indicators: V1Indicator[];
  ai_report?: V1AI | null;
};

const API_BASE = ((import.meta as any).env?.VITE_TRUSTSCAN_API || "").replace(/\/$/, "");
const v1 = (p: string) => `${API_BASE}/api/v1${p}`;

// ── adapters ─────────────────────────────────────────────────────────────────
function verdictFromScore(score: number): ScanResult["verdict"] {
  if (score >= 85) return "Trusted";
  if (score >= 65) return "Suspicious";
  if (score >= 40) return "High risk";
  return "Critical";
}

function sslGrade(score: number, valid: boolean, hsts: boolean): string {
  if (!valid) return "F";
  if (score >= 90 && hsts) return "A+";
  if (score >= 80) return "A";
  if (score >= 65) return "B";
  if (score >= 50) return "C";
  return "D";
}

function severityToStatus(sev?: string): "ok" | "warn" | "bad" {
  if (!sev || sev === "info") return "ok";
  if (sev === "low" || sev === "medium") return "warn";
  return "bad";
}

export function adaptV1(d: V1ScanDetail): ScanResult {
  const p = d.payload || {};
  const urlInfo = p.url || {};
  const domInfo = p.domain || {};
  const whois = domInfo.whois || {};
  const dns = domInfo.dns || {};
  const rep = p.reputation || {};
  const ipInfo = p.ip || {};
  const geo = ipInfo.geo || urlInfo.geo || {};

  const score = Math.round(d.trust_score ?? 0);
  const verdict = d.verdict || verdictFromScore(score);
  const headers = urlInfo.header_flags || {};
  const sslBlock = urlInfo.ssl || {};

  // Build a blacklist-style matrix from the reputation providers.
  const providers = (rep.providers || []) as Array<any>;
  const blacklists: ScanResult["blacklists"] = providers.length
    ? providers.map((x) => ({
        name: String(x.provider || "provider"),
        listed: x.malicious === true,
      }))
    : [
        { name: "Google SB", listed: rep.malicious === true },
        { name: "AbuseIPDB", listed: false },
        { name: "IPQualityScore", listed: false },
        { name: "Scamalytics", listed: false },
      ];

  // UI expects short indicator labels — take the top N by absolute weight.
  const topIndicators = [...(d.indicators || [])]
    .sort((a, b) => Math.abs(b.score_delta || 0) - Math.abs(a.score_delta || 0))
    .slice(0, 8)
    .map((i) => ({ label: i.label, status: severityToStatus(i.severity) }));

  const aiText =
    d.ai_report?.summary ||
    d.ai_report?.exec_summary ||
    topIndicators.map((i) => i.label).join(" · ") ||
    `${d.target} scored ${score}/100 (${verdict}).`;

  return {
    target: d.target,
    score,
    verdict,
    fraudScore: Math.max(1, Math.min(100, Math.round((d.fraud_probability ?? 0) * 100))),
    ssl: {
      valid: !!sslBlock.valid,
      issuer: sslBlock.issuer || (sslBlock.valid ? "Unknown" : "Invalid / missing"),
      expires: sslBlock.expires || "—",
      grade: sslGrade(score, !!sslBlock.valid, !!headers.hsts),
    },
    whois: {
      registrar: whois.registrar || "—",
      created: whois.creation_date || "—",
      country: geo.country_code || geo.country || "—",
      ageDays: whois.age_days ?? 0,
    },
    ip: {
      address: urlInfo.ip || ipInfo.ip || "—",
      asn: geo.asn || "—",
      org: geo.org || urlInfo.server || "—",
      country: geo.country_code || geo.country || "—",
      abuse: Math.max(0, Math.min(100, 100 - score)),
    },
    blacklists,
    indicators: topIndicators.length
      ? topIndicators
      : [{ label: "No indicators fired", status: "ok" }],
    ai: aiText,
  };
}

// ── Live fetch ───────────────────────────────────────────────────────────────
export async function fetchScan(target: string, signal?: AbortSignal): Promise<ScanResult> {
  const res = await fetch(v1("/scans"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ target }),
    signal,
  });
  if (!res.ok) {
    let detail = `Scan failed (${res.status})`;
    try {
      const err = await res.json();
      detail = err?.error?.message || err?.detail || detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  const data = (await res.json()) as V1ScanDetail;
  return adaptV1(data);
}

// ── Progress stream ─────────────────────────────────────────────────────────
export type ScanProgress = {
  scan_id: string;
  stage: string;
  status: string;
  data?: Record<string, any>;
};

export function openScanProgress(
  scanId: string,
  onEvent: (e: ScanProgress) => void,
): () => void {
  const wsBase =
    API_BASE.replace(/^http/, "ws") ||
    `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
  const ws = new WebSocket(`${wsBase}/api/v1/ws/scans/${scanId}`);
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg?.event === "scan_progress" && msg?.payload) onEvent(msg.payload);
    } catch { /* ignore */ }
  };
  return () => {
    try { ws.close(); } catch { /* ignore */ }
  };
}

/** Direct download URL for the 8-page structured PDF report. */
export function reportPdfUrl(scanId: string): string {
  return v1(`/scans/${encodeURIComponent(scanId)}/report.pdf`);
}

// ── Offline fallback — keeps the UI usable without a backend ─────────────────
export function deriveScan(target: string): ScanResult {
  let h = 0;
  for (let i = 0; i < target.length; i++) h = (h * 31 + target.charCodeAt(i)) >>> 0;
  const r = (n: number) => Math.abs((h >> n) % 100);
  const score = Math.max(8, Math.min(99, 30 + (r(2) % 70)));
  const verdict = verdictFromScore(score);
  return {
    target,
    score,
    verdict,
    fraudScore: Math.max(1, Math.min(100, 100 - score)),
    ssl: { valid: score > 50, issuer: "—", expires: "—", grade: score > 80 ? "A" : "C" },
    whois: { registrar: "—", created: "—", country: "—", ageDays: score > 70 ? 4800 : 38 },
    ip: { address: "—", asn: `AS${13000 + (r(13) % 9999)}`, org: "—", country: "—", abuse: 100 - score },
    blacklists: [
      { name: "Google SB", listed: score < 35 },
      { name: "AbuseIPDB", listed: false },
      { name: "IPQualityScore", listed: false },
      { name: "Scamalytics", listed: false },
    ],
    indicators: [{ label: "Offline mode — backend unreachable", status: "warn" }],
    ai: `Offline mode — backend unreachable. Showing placeholder data for ${target}.`,
  };
}
