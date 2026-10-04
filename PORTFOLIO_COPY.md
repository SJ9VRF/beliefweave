# Portfolio Copy

## Card
**BeliefWeave — Governing When Memory May Change Behavior — Memory for users who change.**  
A temporal, uncertainty-aware memory architecture that models evolving preferences, goals, constraints, and commitments as a current user state—not a pile of retrieved chat snippets.

## One-line research claim
Personal memory is better framed as temporal belief-state estimation over an evolving person than as document retrieval over conversation history.

## What I built
A reproducible memory engine with provenance, expiry, conservative conflict resolution, user-controlled correction/deletion, longitudinal simulation, adversarial evaluation, retrieval benchmarking, and an interactive inspector.

## Interview hook
"The most important bug I found was that naive conflict logic treated `I like sushi` followed by `I like jazz` as preference drift. That forced the architecture to become additive-by-default and destructive only when there is explicit structural evidence of replacement."
