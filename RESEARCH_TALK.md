# 8–10 minute research talk: “Your User Is Not a Vector Database”

**0:00–1:00 — Problem.** Most memory stacks optimize “find similar old text.” Personal AI needs “what is true about this user now?”

**1:00–2:15 — Formulation.** Separate events, observations, memories, and current state. Treat memory as temporal state estimation.

**2:15–3:30 — Architecture.** Show the lifecycle: write policy, typed store, provenance, temporal validity, conflict resolver, materialized user state, retrieval.

**3:30–4:45 — Why naive memory fails.** Preference reversal, temporary constraints, context-dependent tone, third-party attribution.

**4:45–6:00 — MemWorldBench.** 100k longitudinal synthetic interactions + 360 hard regression scenarios; explain why controlled benchmarks are useful but insufficient.

**6:00–7:00 — Results.** Show reversal-time retirement and expiry ablations. Emphasize that terminal accuracy alone hid the stale-belief problem.

**7:00–8:00 — Failure analysis.** Historical-time expiry bug and third-party poisoning caught by tests; remaining semantic and calibration weaknesses.

**8:00–9:00 — Product surface.** Memory inspector, edit/delete/correct, provenance, timeline, “why do you remember this?”

**9:00–10:00 — Next step.** Human-authored longitudinal benchmark + learned extraction/conflict scoring + calibrated uncertainty + downstream utility.
