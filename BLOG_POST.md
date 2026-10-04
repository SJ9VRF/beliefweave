# When Memory Should Not Be Trusted

## BeliefWeave and the difference between relevance and authority

I started this project with a failure mode that bothered me: a personal assistant can retrieve exactly the right memory and still make the wrong decision.

Suppose it remembers that a user once preferred sushi. That memory is obviously relevant to a dinner recommendation. But relevance is not enough. The preference might be stale, context-specific, weakly inferred, contradicted by newer evidence, or not even about the user.

That led me to split memory use into two decisions. Retrieval answers **what is related**. BeliefWeave then asks a second question: **is this memory strong enough to change behavior?**

A retrieved belief is routed to one of three outcomes:

- **USE** when the evidence is current and strong enough;
- **ASK** when clarification is safer than guessing;
- **ABSTAIN** when the memory should not influence the response.

The gate considers provenance, confidence, temporal validity, context, user verification, and unresolved conflict. The goal is not to use more memory. It is to avoid confidently personalizing from the wrong memory.

This also changed how I evaluate the system. Retrieval accuracy still matters, but it is not the end metric. I care about whether removing a memory changes the decision when it should, and about the cost of false personalization when it should not. BeliefShiftBench was built around exactly those cases.

The current evidence is deliberately narrow: synthetic longitudinal users, controlled hard cases, retrieval tests, and local stress runs. It tells me the mechanism is behaving the way I designed it to behave. It does not yet tell me how useful it is to real users.

That is the next experiment I would run: a longitudinal study where preferences genuinely change over time, with independent annotators deciding whether each remembered belief should be used, clarified, or ignored.

The idea I want to keep testing is simple: **a memory can be relevant without having earned the right to influence behavior.**

— Aura Yavary
