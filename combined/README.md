# TrustScan — AI Cyber Threat Intelligence Platform

Combined monorepo:

```
combined/
├── backend/       FastAPI + async SQLAlchemy + Redis + websockets (Python 3.12+)
└── frontend/      TanStack Start + React 19 + Tailwind 4 + Framer Motion
```

## One-command dev

Terminal 1 — **backend**:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # edit to add any API keys (all optional in dev)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs
```

Terminal 2 — **frontend**:

```bash
cd frontend
bun install        # or: npm install / pnpm install
bun run dev        # Vite dev server → http://localhost:8080
```

The Vite dev server proxies `/api/*` to `http://localhost:8000` (configurable via
`TRUSTSCAN_API_URL`) so CORS is never an issue in local development.

## API keys — **all free, no card required**

Every key is optional in development — the backend runs with zero keys,
falls back to rule-based scoring and a deterministic AI report, and always
renders the PDF report (which is fully local, no external service).

To enable external providers, add these to `backend/.env`:

| Purpose | Env var | Cost | Card? |
| --- | --- | --- | --- |
| Google Safe Browsing (URL / domain reputation) | `GOOGLE_SAFE_BROWSING_API_KEY` | Free | No |
| AbuseIPDB (IP abuse reputation) | `ABUSEIPDB_API_KEY` | Free (1k/day) | No |
| IPQualityScore (IP / URL / email fraud) | `IPQS_API_KEY` | Free (5k/month) | No |
| Claude Sonnet via Puter.js relay | `PUTER_AUTH_TOKEN` | Free | No |
| SMTP (email OTP delivery) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | Depends on provider | — |

Paid / card-required services (Gemini, Anthropic direct, Scamalytics, Gamma,
Leonardo) are **intentionally not used** — everything ships free.

See [`backend/README.md`](./backend/README.md) for the full spec (architecture,
security model, API surface, scoring rules, deployment).

## Directory layout at a glance

```
backend/app/
  api/v1/           REST + websocket routers (auth, scans, intelligence, admin, ws)
  core/             config (Pydantic v2), exceptions, lifespan
  auth/             JWT + email OTP service + FastAPI deps
  cache/            Redis adapter with in-memory fallback + typed key namespaces
  database/         async SQLAlchemy 2.0 engine + base
  models/           User, Session, OTP, Device, Scan, ScanResult, AIReport, Indicator, AuditLog
  schemas/          Pydantic request/response DTOs
  scans/            URL + domain + IP analyzers, orchestrator, scoring engine
  intelligence/     Provider plugin system + concrete providers
  reputation/       Weighted aggregation across providers
  phishing/         Heuristic detector (typosquat / homograph / entropy)
  dns/              Async DNS resolver (A, MX, NS, TXT, SPF, DKIM, DMARC)
  ai/               Google + Claude orchestrator + prompts + fallback
  websocket/        In-process broadcast manager
  tasks/            Background task runner (ARQ/Celery ready)
  middleware/       request_id, rate_limit, security_headers
  security/         SSRF guard + input sanitizer
  telemetry/        Structured JSON logger
  monitoring/       /health, /health/ready, metrics
```

## Smoke test

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/v1/scans \
     -H 'content-type: application/json' \
     -d '{"target":"https://example.com"}' | head -c 400
```
