# Memory Write Policy — Model Card

The learned proof-of-execution model in `results/write_policy.joblib` is a TF–IDF + logistic-regression classifier trained to distinguish templated memory-worthy self-statements from templated non-personal requests.

It exists to verify an end-to-end learned policy pipeline: dataset → split → training → held-out evaluation → serialization. The data is deliberately simple and separable. Do not interpret the held-out accuracy as production or human-data performance.
