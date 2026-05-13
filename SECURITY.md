# Security Policy

Thank you for taking the time to improve the security of TrustScan.

## Supported versions

We patch the `main` branch of `noyo2118/Saas`. If you are running a fork or a
pinned release, please verify the issue reproduces against `main` before
reporting.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Email `security@trustscan.ai` with:

1. A description of the vulnerability.
2. Steps to reproduce (HTTP requests, payloads, sample targets).
3. The impact you believe it has.
4. Whether the issue is already known to you or a third party.

We aim to:

| Stage | Target |
| --- | --- |
| Acknowledge receipt | within 48 hours |
| Initial triage | within 5 business days |
| Fix or mitigation | within 30 days (critical issues: 7 days) |

Responsible disclosure is welcome — once a fix ships we will credit the
reporter (unless anonymity is preferred).

## Scope

### In scope

- Backend authentication, authorisation, session handling.
- SSRF, injection, and deserialisation paths in the scanner engines.
- Rate-limit bypass, account-lockout bypass, token replay.
- Privilege escalation (user → admin).
- Cross-tenant data exposure.
- Cryptographic weaknesses (key material, JWT validation, OTP hashing).

### Out of scope

- Attacks requiring MITM or control of the victim's network.
- Denial-of-service via raw traffic flooding (use Cloudflare / reverse proxy).
- Findings from automated scanners without a proof-of-concept exploit.
- Issues in dependencies already fixed upstream (please file with the upstream).
- Self-XSS requiring manual paste in DevTools.

## Defensive posture

Summary of security controls already present in the codebase:

| Control | Location |
| --- | --- |
| SSRF allowlist (scheme, private/loopback/link-local/metadata IPs) | `app/security/ssrf.py` |
| URL sanitiser (length, control chars, scheme) | `app/security/sanitizer.py` |
| Brute-force lockout per (email, ip) | `app/auth/lockout.py` |
| Email-OTP (HMAC-SHA256 hashed, TTL + attempt cap + resend cooldown) | `app/auth/otp.py` |
| Rotating refresh tokens (SHA-256 digested at rest) | `app/auth/jwt.py` |
| Access-token revocation via `jti` denylist | `app/security/jwt_denylist.py` |
| IP ban list (cache-backed, admin-controlled) | `app/security/ipban.py` |
| Body size limit (default 1 MiB) | `app/middleware/body_limit.py` |
| Content-Type enforcement on mutations | `app/middleware/content_type.py` |
| Trusted-host check (prod) | `app/middleware/trusted_host.py` |
| Per-IP rate limiting (scan / auth / global buckets) | `app/middleware/rate_limit.py` |
| Strict security response headers (CSP, HSTS, permissions, COOP/CORP) | `app/middleware/security.py` |
| Typed + envelope-wrapped error responses (no stack-trace leaks) | `app/core/exceptions.py` |
| Structured audit log on auth events | `app/models/audit_log.py` |
| Request-id tracing on every response | `app/middleware/request_id.py` |
| JWT `iss`+`aud`+`jti` verification with no clock leeway | `app/auth/jwt.py` |
| Payload validation via Pydantic v2 | `app/schemas/**` |
| Parameterised queries (SQLAlchemy 2.0 async ORM) | everywhere |

## Known residual risks

- **DNS rebinding** — SSRF validation resolves the hostname once before HTTP
  starts. A malicious DNS server could respond with a public IP first and a
  private IP second. Mitigation options: run the backend behind an egress
  proxy that blocks RFC1918, or enable a transport-level `socket_options` hook.
  Not exploitable against typical scan targets because our HTTP client only
  follows HTTPS to the originally-resolved address via httpx's connection
  pool — but a custom transport could still be abused. Tracked for v4.3.

- **Side-channel timing on OTP verify** — we use `hmac.compare_digest` for the
  hash comparison, but the row lookup itself is not constant-time. An attacker
  with precise network timing could infer whether an address has an outstanding
  OTP. Mitigation is already in place: the `otp.request` endpoint returns the
  same message whether the email exists or not, and the `otp.verify` lockout
  starts counting after the first failure.

- **Uploaded target content** — the scanner fetches up to 256 KiB of response
  body for pattern matching. The raw body is **never** echoed back to the
  caller — only a list of matched pattern names. This mitigates reflected-XSS
  but depends on the caller not logging the target URL if it contains
  attacker-controlled data.

## Cryptographic notes

- `SECRET_KEY` must be a long random string in production. A default sentinel
  is shipped for development only. Rotate via `.env` and restart all workers.
- OTP codes are hashed with HMAC-SHA256 using `SECRET_KEY`; the plaintext is
  never persisted.
- Refresh tokens are 48-byte URL-safe `secrets` tokens; only SHA-256 digests
  are stored in `user_sessions.refresh_token_hash`.
- Access tokens carry `jti`, `iss`, `aud`, `iat`, `nbf`, `exp` and are verified
  with no clock leeway. Logout inserts the `jti` into a cache-backed denylist
  until the natural expiry.
