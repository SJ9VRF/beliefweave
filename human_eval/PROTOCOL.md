# Blind personalization evaluation protocol

Goal: test whether BeliefWeave reduces inappropriate memory influence while preserving useful personalization.

Each item shows two anonymized assistant responses in randomized order, generated from the same current user request and history. Raters answer:

1. Which response better matches the user's **current** preferences or constraints?
2. Which response relies on outdated or unsupported personal information?
3. Which response feels more intrusive?
4. Should the assistant have asked a clarifying question before personalizing?
5. Overall preference (A / B / tie).

Primary outcomes: pairwise preference rate, stale-memory harm rate, unsupported-personalization rate, clarification appropriateness, and perceived intrusiveness. Report Wilson or bootstrap 95% confidence intervals. For multi-rater subsets, report Krippendorff's alpha or Fleiss' kappa as appropriate.

This repository contains the protocol and analysis code only. No human-subject results are claimed without actual recruitment, consent/ethics review as applicable, and collected judgments.
