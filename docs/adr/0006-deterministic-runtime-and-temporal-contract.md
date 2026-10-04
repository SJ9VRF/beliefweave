# ADR 0006 — Deterministic runtime selection and canonical time

## Decision

`PersonalMemoryEngine` starts in the dependency-free deterministic core profile. Optional learned components are enabled only with `enable_ml=True`; merely installing scikit-learn/joblib must not change application behavior.

External timestamps are validated before persistence and canonicalized to aware UTC ISO-8601. Semantically identical offsets therefore hash identically for idempotent ingest. Invalid timestamps fail fast with a typed `TemporalValueError` instead of being stored as opaque strings.

The demo API maps domain errors by type: idempotency conflict → 409, hard-forgotten retry → 410, invalid time → 422. Remote demo access fails closed unless a demo token is configured.

## Why

Environment-dependent component selection makes reproduction fragile, while unvalidated timestamps can silently corrupt recency, expiry, and ordering. String-matched exceptions and unauthenticated export/delete endpoints are also inappropriate even for a polished reference service.

## Boundary

The demo token is not production authentication. Real deployments still need identity, authorization, TLS, key lifecycle, tenant isolation, audit policy, and abuse controls.
