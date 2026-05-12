# TrustScan Backend

Enterprise-grade AI cyber threat intelligence platform — FastAPI, async
SQLAlchemy 2.0, Pydantic v2, Redis cache, websocket progress streaming, and
pluggable intelligence providers.

## Features

| Domain | What it does |
| --- | --- |
| URL / website analysis | HTTPS, full TLS cert, security headers, redirect chain, suspicious HTML patterns |
| Domain intelligence | WHOIS age, registrar, nameservers, MX/SPF/DKIM/DMARC, suspicious TLDs |
| IP intelligence | ASN, geolocation, abuse score, VPN/proxy/Tor (via providers) |
| Phishing detection | Typosquatting (Levenshtein), homographs, brand impersonation, entropy, shorteners |
| Reputation aggregation | Weighted merge across every enabled provider with confidence scoring |
| AI threat explanation | Google Gemini + Anthropic Claude orchestration, deterministic fallback |
| Trust scoring engine | Modular weighted rules table (edit `app/scans/scorer.py`) |
| Realtime progress | Websocket channel per scan — 9 pipeline stages streamed live |
| Email-OTP auth | No passwords, hashed OTPs, cooldown, JWT + rotating refresh tokens |
| API security | SSRF guard, private IP block, rate limiting, security headers, CORS, request IDs |
| Caching | Redis or in-memory fallback, namespaced keys, tunable TTLs |
| Monitoring | `/health`, `/health/ready`, structured JSON logs, admin metrics endpoint |

## Architecture

```
app/
├── api/v1/              REST + websocket routers (auth, scans, intelligence, ws, admin)
├── core/                config, exceptions, lifespan
├── auth/                JWT, OTP generation, email delivery, FastAPI deps
├── cache/               Redis/memory cache + namespaced keys
├── database/            Async SQLAlchemy engine, base, session factory
├── models/              Users, sessions, OTP, scans, AI reports, indicators, audit
├── schemas/             Pydantic request/response models
├── scans/               URL + domain + IP analyzers, scoring engine, orchestrator
├── intelligence/        Provider interface + concrete providers (GSB, AbuseIPDB, IPQS, Scamalytics)
├── reputation/          Aggregator (weighted merge, per-target caching)
├── phishing/            Heuristic detector (typosquat / homograph / entropy)
├── dns/                 Async DNS resolver (A/MX/NS/TXT, SPF/DKIM/DMARC)
├── ai/                  Google + Claude providers, orchestrator, prompts
├── websocket/           Connection manager + broadcast
├── tasks/               Lightweight background task runner (ARQ/Celery ready)
├── middleware/          request_id, rate_limit, security_headers
├── security/            SSRF, sanitizer
├── telemetry/           Structured logger
├── monitoring/          /health + metrics
└── main.py              FastAPI app factory
```

## Quick start

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # edit to add API keys

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000/docs
```

In dev the database is SQLite (`./trustscan.db`), the cache is in-memory, and
OTP codes are logged to stdout (no SMTP required).

## Configuration

Every setting is documented inline in `.env.example`. Highlights:

### Required in production

| Key | Purpose |
| --- | --- |
| `SECRET_KEY` | JWT signing / OTP hashing — set to a long random string |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/trustscan` |
| `REDIS_URL` | `redis://host:6379/0` — omit to use the in-memory fallback |
| `CORS_ORIGINS` | Comma-separated frontend origins |
| SMTP\_\* | To actually deliver OTPs |

### Intelligence provider API keys — **all 100% free, no credit card**

Every provider key is optional. Missing keys disable the provider at runtime;
the rest still run. Scores degrade gracefully.

| Provider | Env var | Free tier | Card required? |
| --- | --- | --- | --- |
| Google Safe Browsing | `GOOGLE_SAFE_BROWSING_API_KEY` | 10,000 req/day | No |
| AbuseIPDB | `ABUSEIPDB_API_KEY` | 1,000 checks/day | No |
| IPQualityScore | `IPQS_API_KEY` | 5,000 lookups/month | No |

Sign-up links are in `.env.example`.

Add a new provider in three steps:

1. Create `app/intelligence/providers/<name>.py` subclassing `Provider`.
2. Register it in `app/intelligence/registry.py`.
3. Add the env var it reads to `app/core/config.py` + `.env.example`.

### AI — **free via Puter.js relay to Claude Sonnet**

The orchestrator uses Puter.js as a free relay for Claude. No Anthropic
account, no billing, no card. When `PUTER_AUTH_TOKEN` is blank the backend
falls back to a deterministic rule-based report so the UI never breaks.

| Provider | Env var | Model env var | Cost |
| --- | --- | --- | --- |
| Claude (via Puter.js) | `PUTER_AUTH_TOKEN` | `AI_MODEL_CLAUDE` (default `claude-sonnet-4-5`) | Free |

Grab the token from your Puter browser console:

```js
puter.auth.getAuthToken()   // paste output into .env
```

Add another AI provider by subclassing `AIProvider` in `app/ai/providers/` and
prepending it to `_PROVIDERS` in `app/ai/orchestrator.py`.

### PDF intelligence reports

`GET /api/v1/scans/{id}/report.pdf` renders an **8-page VirusTotal-style PDF**
from the real scan payload. Zero AI in the document itself — every value is
pulled directly from the scan result:

1. **Cover** — target, verdict, trust score, timestamps
2. **Executive summary** — severity counters, top 10 indicators, module coverage
3. **TLS / SSL** — certificate chain, cipher, SAN, expiry
4. **Domain intelligence** — WHOIS, registrar, DNS (A/MX/NS/SPF/DMARC/DKIM)
5. **Reputation matrix** — per-provider verdicts, aggregate score, VPN/proxy/Tor
6. **Phishing heuristics** — every fired heuristic with severity + score delta
7. **HTTP response** — security headers, redirect chain, body patterns
8. **Indicator log** — full scoring rule audit trail

Rendered with `reportlab` (pure Python, no external service, no API key).

## API surface (v1)

Base URL: `/api/v1`. All responses wrap errors in `{ ok: false, error: { code, message, trace_id } }`.

### Auth

- `POST /auth/otp/request` — issue an OTP to an email
- `POST /auth/otp/verify` — verify code, receive JWT + refresh token
- `POST /auth/refresh` — rotate refresh, mint new access
- `POST /auth/logout` — revoke a refresh token
- `GET /auth/me` — current user

### Scans

- `POST /scans` — run an orchestrated scan (target: URL / IP / domain / email)
- `GET /scans` — list recent scans
- `GET /scans/{id}` — full scan detail with indicators + AI report
- `GET /scans/{id}/report.pdf` — download an 8-page structured PDF report
- `DELETE /scans/{id}` — delete a scan

### Direct intelligence

- `GET /url/analyze?target=` — URL + phishing heuristics
- `GET /ip/analyze?target=` — IP geo + reputation
- `GET /domain/analyze?target=` — WHOIS + DNS
- `GET /domain/dns?target=` — raw DNS records
- `GET /reputation/{url|ip|domain}?target=`
- `GET /intelligence/providers` — introspection of enabled providers

### Websockets

- `WS /api/v1/ws/scans/{scan_id}` — progress stream for a specific scan
- `WS /api/v1/ws/threats` — global threat feed (heartbeat)

### Admin

- `GET /admin/stats` — scan counters, provider status (admin only)
- `GET /admin/metrics` — in-memory counters/gauges

## Security model

- **SSRF guard** — resolves hostnames and blocks loopback, RFC1918, link-local, multicast, reserved, metadata endpoints (169.254.169.254 etc.). Applied to every scanner call.
- **Scheme allowlist** — only `http`/`https`.
- **Rate limiting** — per-IP buckets for scan / auth / global, backed by the cache.
- **Security headers** — nosniff, X-Frame-Options DENY, strict referrer, permissions policy, HSTS on HTTPS.
- **OTP** — HMAC-SHA256 hashed with `SECRET_KEY`, 6 digits, 5-minute TTL, 5-attempt cap, 60s resend cooldown.
- **JWT** — HS256 access (30 min default), rotating refresh (SHA256-hashed at rest, 30-day TTL).
- **Audit log** — append-only table for auth events.

## Scoring engine

Every scoring rule lives in `app/scans/scorer.RULES` — a single list of
`Rule(kind, label, severity, weight, predicate, description)`. Edit weights or
add a rule without touching branching logic.

Output fields:
- `trust_score` — 0..100, higher = safer
- `fraud_probability` — 0..1
- `threat_level` — `low | moderate | high | critical`
- `verdict` — `Trusted | Suspicious | High risk | Critical`
- `confidence` — 0..1, mixes rules-fired ratio + reputation confidence

## Realtime pipeline

Each POST `/scans` call streams these events on `ws /ws/scans/{id}`:

1. `validate`    — target sanitized + SSRF-checked
2. `dispatch`    — parallel analyzers launched (URL, DNS, WHOIS, reputation, phishing, IP)
3. `aggregate`   — merged
4. `score`       — scoring engine → `trust_score`, `verdict`, `threat_level`
5. `ai`          — provider chosen + narrative emitted
6. `complete`    — final payload cached

## Deployment

Run behind a reverse proxy (Traefik / nginx / Caddy). The Dockerfile sketch:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV APP_ENV=production LOG_JSON=true
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop", "--http", "httptools", "--workers", "4"]
```

For migrations use Alembic (already in requirements.txt):

```bash
alembic init migrations
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Testing the stack locally

```bash
# start backend
uvicorn app.main:app --reload

# in another shell — real scan
curl -s -X POST http://localhost:8000/api/v1/scans \
     -H 'content-type: application/json' \
     -d '{"target":"https://example.com"}' | jq
```
