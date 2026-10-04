#!/usr/bin/env python3
"""Small dependency-free style contract for the critical runtime path.

This is intentionally narrower than a general formatter/linter. It prevents the
specific readability regressions found during review without requiring network
access or a third-party lint dependency to audit the release.
"""

from __future__ import annotations

import io
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITICAL = [
    ROOT / "pwm" / "belief_governance.py",
    ROOT / "pwm" / "engine.py",
    ROOT / "pwm" / "memory" / "schema.py",
    ROOT / "pwm" / "memory" / "store.py",
    ROOT / "pwm" / "memory" / "retriever.py",
    ROOT / "pwm" / "events" / "store.py",
    ROOT / "beliefweave" / "__init__.py",
]
MAX_LINE = 119


def semicolon_lines(path: Path) -> list[int]:
    text = path.read_text(encoding="utf-8")
    out: list[int] = []
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.OP and tok.string == ";":
            out.append(tok.start[0])
    return sorted(set(out))


def main() -> int:
    failures: list[str] = []
    for path in CRITICAL:
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if len(line) > MAX_LINE:
                failures.append(f"{rel}:{lineno}: line length {len(line)} > {MAX_LINE}")
        for lineno in semicolon_lines(path):
            failures.append(f"{rel}:{lineno}: semicolon-separated statements are not allowed")
    if failures:
        print("CORE STYLE CHECK: FAIL")
        print("\n".join(failures))
        return 1
    print(f"CORE STYLE CHECK: PASS ({len(CRITICAL)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
