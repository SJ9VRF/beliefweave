# Five-minute reviewer path

If you only have five minutes, read these in order:

1. **Paper abstract + Introduction** — `paper/BELIEFWEAVE.pdf`
2. **Main held-out table** — exact USE/ASK/ABSTAIN on BeliefShiftBench-v2
3. **Component ablation** — why time/context/conflict/lifecycle each matter
4. **Counterfactual intervention** — whether memory changes behavior for the right reason
5. **Limitations** — what is not yet established

## The research claim

BeliefWeave does not claim that memory retrieval is solved. It claims that retrieval is an incomplete control surface for personalization. A memory needs a separate authority decision before it changes behavior.

## The strongest evidence

On the frozen 320-case synthetic test split, BeliefWeave reaches 96.9% exact three-way action accuracy (95% bootstrap CI 95.0–98.8), versus 62.5% for temporal+context filtering and 37.5% for retrieval-only. Controlled personalization-intervention fidelity is 98.4%.

## The strongest criticism

The benchmark is still author-constructed and synthetic. The observation router is weak under paraphrase shift, and the authority score is not well calibrated. There is no completed external LongMemEval/PersonaMem model run or human longitudinal study. Those missing studies are the main barrier to a broad NeurIPS-level empirical claim.

## What I would run next

The repository already contains the external adapters and blind human-study kit. The decisive next experiment is a full downstream response study: same histories and model, with memory disabled vs. retrieval-only vs. temporal memory vs. BeliefWeave, evaluated on external benchmark tasks and blind human judgments.

## Specification stress test

Do not stop at the 96.9% frozen primary result. The second 480-case sealed specification audit drops V2 to **53.3%**. V3 closes those exact cases after inspection, so its 100% score is a regression check rather than fresh generalization evidence. The repository also includes 185/185 metamorphic checks per V2/V3 gate and 6/6 killed benchmark mutants.

## Current external boundary

PersonaMem-v3 already studies over-personalization/restraint. The defensible BeliefWeave claim is narrower: explicit memory-level `USE / ASK / ABSTAIN` authority after retrieval, explicit costs, and counterfactual intervention. No LongMemEval-v2, PersonaMem-v3, or human score is claimed yet.

The checked-in PDF is a research manuscript, not a claim of official NeurIPS template compliance; see `submission/NEURIPS_FORMAT_STATUS.md`.

## Runtime/research alignment

The implementation deliberately separates frozen research variants from the production default. `v1` and `v2` remain selectable for exact paper reproduction; new engine instances use `v3` by default. The finite 9,600-state policy audit reports 560 declared-property violations for V1, 146 for V2, and 0 for V3. Treat that as specification assurance, not as independent generalization evidence.

I would also inspect the deletion path. Hard forget is now transactionally provenance-aware: deleting a source event cannot leave sibling memories pointing at a nonexistent event. The checked-in 50-user erasure test and 480-ingest concurrency stress are intended to make that engineering claim inspectable rather than rhetorical.

## Transactionality and result lineage

Two engineering checks are worth looking at if you are reviewing the implementation rather than only the paper. `results/atomicity_fault_injection.json` deliberately crashes an ingest after a memory row is inserted and again during conflict resolution; both cases roll back the complete ingest. `results/experiment_lineage.json` records SHA256 hashes of the code, input manifests, and outputs for the principal reported experiments, so a changed result can be traced to a changed implementation or input rather than inferred from prose.

## Closest-work check
The most important overlap to inspect is OP-Bench/Self-ReCheck, followed by PersonaMem-v3, QUMem, Memora, and Graphiti/Zep. `COMPETITIVE_LANDSCAPE.md` states exactly what those works already cover and what BeliefWeave is still claiming. A fair review should reject any broader “first restraint” or generic temporal-memory claim.

## Runtime semantics worth checking

The default engine is deliberately deterministic even when optional ML packages happen to be installed. Learned local components require explicit `enable_ml=True`; this keeps deployment semantics independent of ambient environment state. External timestamps are canonicalized before both persistence and idempotency hashing. User correction creates a new verified version with an event trail rather than mutating the previous record, and hard-forget leaves only a hashed, content-free replay tombstone so a stale retry cannot resurrect deleted data. The demo token is only a transport guard for the reference service, not a production identity/authorization claim.

## Data-lifecycle and crash-recovery checks

If you are reviewing the runtime rather than only the research claim, inspect `results/privacy_inventory.json` and `results/database_resilience.json`. The first distinguishes complete user erasure from replay-safe guarded erasure and verifies that exports include stored control metadata. Telemetry user correlation is HMAC-keyed rather than an unkeyed digest. The second uses independent processes against one SQLite database and separately kills an interpreter inside an uncommitted event+memory transaction; recovery leaves no partial rows. These are deliberately scoped local-reference guarantees, not legal-compliance or distributed-storage claims.
