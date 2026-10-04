#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/paper"
command -v pdflatex >/dev/null || { echo 'pdflatex is required to rebuild the PDF.' >&2; exit 2; }
rm -f BELIEFWEAVE.aux BELIEFWEAVE.log BELIEFWEAVE.out BELIEFWEAVE.toc
pdflatex -interaction=nonstopmode -halt-on-error BELIEFWEAVE.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error BELIEFWEAVE.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error BELIEFWEAVE.tex >/dev/null
printf 'Built %s\n' "$ROOT/paper/BELIEFWEAVE.pdf"
