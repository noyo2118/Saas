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

### Intelligence provider API keys

All provider keys are optional. A provider with a missing key reports
`enabled=False` and is skipped by the aggregator. The others still run.

| Provider | Env var | Supports | Where to get |
| --- | --- | --- | --- |
| Google Safe Browsing | `GOOGLE_SAFE_BROWSING_API_KEY` | url, domain | https://developers.google.com/safe-browsing/v4/get-started |
| AbuseIPDB | `ABUSEIPDB_API_KEY` | ip | https://www.abuseipdb.com/account/api |
| IPQualityScore | `IPQS_API_KEY` | ip, url, email | https://www.ipqualityscore.com/ |
| Scamalytics | `SCAMALYTICS_API_KEY` | ip | https://scamalytics.com/ip/api |

Add a new provider in three steps:

1. Create `app/intelligence/providers/<name>.py` subclassing `Provider`.
2. Register it in `app/intelligence/registry.py`.
3. Add the env var it reads to `app/core/config.py` + `.env.example`.

### AI provider API keys

First enabled provider wins. If none is configured, the orchestrator emits a
deterministic rule-based report so the UI never breaks.

| Provider | Env var | Model env var |
| --- | --- | --- |
| Google Gemini | `GOOGLE_AI_API_KEY` | `AI_MODEL_GOOGLE` (default `gemini-1.5-flash`) |
| Anthropic Claude | `ANTHROPIC_API_KEY` | `AI_MODEL_CLAUDE` (default `claude-3-5-sonnet-latest`) |

Add a new AI provider by subclassing `AIProvider` in `app/ai/providers/` and
prepending it to `_PROVIDERS` in `app/ai/orchestrator.py`.

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
