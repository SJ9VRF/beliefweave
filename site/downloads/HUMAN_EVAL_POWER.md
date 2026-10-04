# Human evaluation planning

The released human-evaluation kit is intentionally unpopulated: no participant judgment is fabricated.

For a simple blind A/B preference endpoint tested against 50%, a normal-approximation planning calculation gives approximately:

| True preference | Approx. complete pairs for 80% power, two-sided alpha=.05 |
|---:|---:|
| 60% | 194 |
| 65% | 85 |
| 70% | 47 |
| 75% | 29 |

A practical minimum target is **100 complete independent A/B pairs** for a moderate effect, with more if participants contribute repeated judgments. If repeated judgments are collected, analysis should account for participant-level clustering rather than treating every judgment as independent.

Primary pre-specified outcomes: overall preference, stale-memory harm, unsupported personalization, clarification appropriateness, and perceived intrusiveness. Exclusion rules, stopping rules, and any subgroup analyses should be fixed before looking at outcome data.
