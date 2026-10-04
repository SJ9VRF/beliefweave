# NeurIPS format status

The checked-in PDF is the **research manuscript**, not a claim of official NeurIPS formatting compliance.

The repository deliberately does not invent or recreate `neurips_2026.sty`. `scripts/check_neurips_submission_readiness.py` verifies whether the official style is present and actually loaded. Until that check reports `ready_for_official_neurips_template_submission: true`, the release should not be described as template-ready.

Current scientific content is organized to fit a nine-page main-text budget, but the final submission source must be rebuilt with the official conference style and no custom margin/font overrides.
