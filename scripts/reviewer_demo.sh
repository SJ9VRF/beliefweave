#!/usr/bin/env bash
set -euo pipefail
CMD=${PWM_CMD:-pwm}
echo '== BeliefWeave: doctor =='
"$CMD" doctor
echo '== BeliefWeave: end-to-end demo =='
"$CMD" demo
echo '== BeliefWeave: installed-package benchmark =='
"$CMD" benchmark
