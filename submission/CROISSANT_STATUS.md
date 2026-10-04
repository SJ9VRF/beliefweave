# Croissant / dataset-hosting status

`benchmark/croissant.json` includes the local core fields and minimal Responsible-AI fields used by this artifact. `scripts/validate_croissant_local.py` checks their presence and basic structure.

One submission-time step cannot be completed inside this offline build: NeurIPS dataset review requires a reviewer-accessible hosted dataset URL and validation with the official Croissant validator. The current `url` is a local file URI by design; it is not represented as externally accessible. Replace it only when the anonymous review hosting location actually exists, then run the official validator and archive its report.
