# NeurIPS submission checklist preparation

This file is a pre-submission working checklist. The official NeurIPS checklist must be included from the conference LaTeX template in the final submission PDF.

## Claims and scope
- [x] Main empirical claim is restricted to controlled synthetic authority decisions.
- [x] External/generalized SOTA is not claimed.
- [x] Human utility, trust, and production safety are not claimed without data.
- [x] Post-hoc challenge results are separated from frozen primary test results.

## Reproducibility
- [x] Method and decision rule are specified.
- [x] Primary test manifest is frozen and included.
- [x] Random seeds and deterministic generators are included.
- [x] Main tables are backed by machine-readable result JSON.
- [x] Bootstrap confidence intervals and paired tests are reproducible.
- [x] Cost/threshold sensitivity is included.
- [x] Package tests, environment snapshot, checksums, and build scripts are included.

## Evaluation validity
- [x] Benchmark construction bias is stated.
- [x] Same-family dev/test limitation is stated.
- [x] Separate unseen-composition challenge is reported.
- [x] Failure cases are retained rather than filtered out.
- [x] Calibration weakness is reported.
- [x] External benchmark adapters are included without fabricated scores.
- [x] Human evaluation protocol and power planning are included without fabricated participants.

## Data and responsible use
- [x] Dataset card is included.
- [x] Croissant metadata includes core + minimal RAI fields locally.
- [x] Synthetic-data provenance and limitations are documented.
- [x] No real personal/sensitive user data are present in BeliefShiftBench-v2.
- [ ] Before an Evaluations & Datasets submission: host the dataset at an anonymous reviewer-accessible public URL and run the official Croissant validator.

## Submission-time external actions
- [ ] Replace author identity with the conference-required anonymous form if double-blind submission rules require it.
- [ ] Insert the official NeurIPS style file and official checklist environment.
- [ ] Run external LongMemEval/PersonaMem evaluations if making external-performance claims.
- [ ] Complete the pre-specified human study if making user-preference or trust claims.
- [ ] Provide reviewer-accessible anonymous code/data URLs.
