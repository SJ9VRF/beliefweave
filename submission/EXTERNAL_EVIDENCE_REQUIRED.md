# Evidence still required before broad empirical claims

The local artifact supports a controlled mechanism claim. It does **not** yet support a broad claim that BeliefWeave is the best real-world personal-memory system.

Before making that stronger claim, run all of the following without changing the frozen primary method based on test outcomes:

1. LongMemEval using the official data, reader/evaluator path, and benchmark protocol.
2. PersonaMem or an equivalent evolving-profile benchmark with a real model backend.
3. At least one strong external memory implementation (for example a temporal graph or production memory baseline) under matched model/context budgets.
4. End-to-end free-form response generation with at least two model families.
5. Blind human A/B evaluation using the pre-specified protocol.

The external adapters in `benchmark/external/` are scaffolding, not evidence that these runs have already happened.
