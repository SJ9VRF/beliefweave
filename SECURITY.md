# Security and privacy status

This repository is a research prototype. Do not deploy it as a production personal-memory service without additional controls.

Missing production controls include authentication, per-user authorization, encryption at rest, secret management, rate limiting, abuse monitoring, retention governance, consent UX, audit logging, and formal privacy review.

Implemented research safeguards include third-party attribution guards, role-play/hypothetical filtering, temporal expiry, provenance, user correction, soft deletion, hard forgetting that purges the memory row and source events, and structural gates that prevent learned conflict classification from overwriting structurally unrelated memory types.

See `THREAT_MODEL.md` for the detailed research threat model.

## Demo transport boundary

The bundled FastAPI app is a **local/demo service**, not a production identity boundary. Without `BELIEFWEAVE_DEMO_TOKEN`, `/api/*` requests are accepted only from loopback clients. The provided `docker-compose.yml` refuses to start unless a demo bearer token is explicitly configured. This prevents accidental unauthenticated public export/delete endpoints, but it is still only a coarse demo guard: production deployments need real identity, per-user authorization, key rotation, TLS termination, rate limits, audit policy, and tenant isolation.

## User-level erasure and telemetry correlation

BeliefWeave exposes two intentionally different user-level deletion semantics. Full erasure removes events, memories, and idempotency receipts; after that operation there is no retained replay marker, so an old client request can no longer be recognized. Guarded erasure keeps only hashed, scrubbed idempotency tombstones to prevent stale retries from recreating deleted content. Guarded erasure is therefore **not** described as complete erasure.

Optional observer events use HMAC-SHA256 user-correlation tokens. Without a caller-provided HMAC key, the secret is random per engine instance and correlation is process-local. Raw user IDs, interaction text, memory values, and context are not included in observer payloads. This is a telemetry minimization measure, not an anonymity guarantee.
