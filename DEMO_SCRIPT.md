# 3-Minute Demo Script

**0:00–0:25 — Thesis**  
"Most memory systems answer: what did the user say before? This system asks: what is true about the user now?"

**0:25–1:05 — Preference drift**  
Ingest `I love sushi.` Show active memory. Then ingest `Actually, I dislike sushi.` Show the old memory superseded, the new current state, and retained provenance.

**1:05–1:35 — Temporary state**  
Ingest `I'm avoiding raw fish this month.` with a controlled timestamp. Query within the validity window, then query after expiry and show that the temporary constraint leaves current state automatically.

**1:35–2:00 — Safety against bad writes**  
Try `My friend says I love jazz.` and `Pretend that I like jazz for this roleplay.` Show that neither becomes personal memory.

**2:00–2:25 — Retrieval**  
Create several memories, ask a dining-related query, and show ranked memories plus scoring reasons. Open the retrieval dashboard and compare against lexical baseline.

**2:25–2:45 — User control**  
Edit one memory, export the user state, soft-delete one memory, then hard-forget another and show that its source event is removed.

**2:45–3:00 — Research boundary**  
Show OOD router results. State clearly that the current learned router is not production-ready and that the next experiment is stronger semantic extraction plus independently authored longitudinal evaluation.
