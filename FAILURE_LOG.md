# Failure Log

## F001 — Persistence placeholder mismatch
**Observed:** initial SQL insert did not match the memory schema.  
**Resolution:** synchronized persistence schema and added regression tests.

## F002 — Historical-time expiry bug
**Observed:** simulated historical temporary memories expired immediately because state materialization used wall-clock time.  
**Root cause:** time was not an explicit dependency of state operations.  
**Resolution:** made active-memory lookup, state materialization, and retrieval time-aware.

## F003 — Third-party attribution poisoning
**Observed:** “My friend says I love sushi” was incorrectly stored as the user's preference.  
**Resolution:** added provenance-sensitive third-party guards and a regression test.  
**Remaining risk:** arbitrary reported speech and quotations still require a stronger semantic attribution model.

## F004 — Non-discriminative terminal metric
**Observed:** both append-only and world-state baselines achieved the same final food preference accuracy when a new positive preference was explicitly restated.  
**Resolution:** added a reversal-time probe measuring retirement of the obsolete belief before the new preference is stated.

## Known open failures
- paraphrases outside the rule set may be missed;
- semantic conflicts such as ingredient/category relations are only lightly modeled;
- sarcasm, roleplay, nested quotation, and hypothetical contexts are incomplete;
- confidence is not calibrated on human labels;
- retrieval is lexical rather than embedding-based.

## F005 — Authority-ablation stale-case time inversion
**Observed:** the authority ablation labeled a memory as stale while its `valid_until` was later than the benchmark's synthetic `NOW`, producing false personalization inside the test fixture.  
**Root cause:** benchmark labels and temporal ground truth were inconsistent.  
**Resolution:** moved the stale fixture before synthetic `NOW`, kept the temporal check explicit, and reran the full release suite.
