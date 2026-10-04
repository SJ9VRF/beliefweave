# ADR 0005 — Keep the core runtime optional-ML and telemetry-backend neutral

## Context

The research package includes local TF-IDF and lightweight learned routing/conflict components. Requiring scikit-learn and joblib for every installation makes the production-facing memory contract harder to audit and turns packaging convenience into an architectural dependency. At the same time, adding a logging framework to the reference runtime risks coupling memory semantics to infrastructure and accidentally logging user content.

## Decision

`pip install beliefweave` has no third-party runtime dependency. The engine starts with the deterministic rule-based extractor, lexical retriever, and deterministic conflict resolver. `beliefweave[ml]` enables the optional local ML path. The active path is exposed through `runtime_capabilities()`.

Operational instrumentation is an optional observer callback. Emitted records contain operation metadata and counts, but never raw interaction text, memory values, or context. User identity is represented only by a short one-way correlation hash. Observer exceptions are swallowed so telemetry cannot change memory correctness.

## Consequences

- The smallest runtime is easy to install and audit.
- Research ML components remain available without defining the public API.
- Deployments can attach their own tracing/logging backend.
- The reference implementation makes a narrow privacy promise about its own observer payload; it does not claim end-to-end logging compliance for host applications.
