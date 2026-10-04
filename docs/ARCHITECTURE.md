# Architecture

BeliefWeave separates raw interaction history from the model's current belief about a user.

```text
User interaction
      ↓
Event Store (immutable interaction evidence)
      ↓
Observation Extraction
      ↓
Write Policy ─────→ IGNORE / ASK / TEMPORARY / WRITE
      ↓
Typed Memory Record
      ↓
Structural Safety Gates
      ↓
Conflict / Update Resolver
      ↓
Temporal Memory Store
      ↓
Current User State Materializer
      ↓
Query-aware Retrieval
      ↓
Personalized downstream behavior
```

## Core invariants

1. **Events are evidence, not truth.** An event can yield zero or more observations.
2. **Observations are candidates, not persistent memory.** A write policy decides persistence.
3. **Additive by default.** A new preference/goal does not erase unrelated existing values.
4. **Destructive updates require evidence.** Corrections, explicit reversals, or compatible state transitions can supersede old memory.
5. **Time is queryable.** State and retrieval accept a reference time, enabling historical snapshots and correct expiry.
6. **Provenance is retained.** Every memory points back to source event IDs.
7. **User control is first class.** Memory can be inspected, corrected, soft-deleted, or hard-forgotten with source-event removal.

## Why a world model rather than a vector store?

A flat vector store answers “what text looks relevant?” A personal world model additionally represents whether a belief is current, temporary, contradicted, context-scoped, uncertain, user-verified, or superseded. Retrieval then operates over active state rather than an undifferentiated archive.

## Learned components

The repository intentionally uses small local models so the full pipeline is reproducible offline:

- observation router: TF-IDF features + classifier
- conflict classifier: local supervised classifier

Both are safety-gated by deterministic structural rules. This is a prototype design choice, not a claim that these lightweight models are sufficient for production semantic understanding.
