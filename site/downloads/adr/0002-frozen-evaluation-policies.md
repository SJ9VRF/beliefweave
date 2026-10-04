# ADR 0002 — Keep historical authority policies frozen

## Decision
V1 and V2 authority gates remain importable and unchanged for reproduction. The runtime default is V3.

## Why
Post-hoc challenge suites exposed specification gaps. Replacing an old gate in place would make earlier benchmark numbers impossible to reproduce and would blur the line between independent evidence and regression hardening.

## Consequences
- Published internal results remain attributable to the policy that produced them.
- V3 can incorporate challenge-informed fixes without rewriting history.
- Every governed-recall result identifies the gate version used.
