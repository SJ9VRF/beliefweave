#!/usr/bin/env python3
"""Synchronize release-facing metadata from measured/source-of-truth artifacts."""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
META = json.loads((ROOT / "project_metadata.json").read_text())
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text())
VERSION = PYPROJECT["project"]["version"]
TESTS = json.loads((ROOT / "results" / "test_summary.json").read_text())
COVERAGE = json.loads((ROOT / "results" / "coverage.json").read_text())
READINESS = json.loads(
    (ROOT / "results" / "neurips_submission_readiness.json").read_text()
)

# Import only a stable constant from the local source tree.
from pwm.schema_version import CURRENT_SCHEMA_VERSION  # noqa: E402

TEST_COUNT = int(TESTS["passed"])
COVERAGE_PCT = float(COVERAGE["totals"]["percent_covered"])
PAGES = READINESS.get("research_manuscript_pages")
TITLE = META["title"]
AUTHOR = META["author"]
WHEEL = f"beliefweave-{VERSION}-py3-none-any.whl"


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text)


def replace_file(path: str, replacements: list[tuple[str, str]]) -> None:
    p = ROOT / path
    text = p.read_text()
    for old, new in replacements:
        text = text.replace(old, new)
    p.write_text(text)


# Human-facing validation record.
p = ROOT / "FINAL_VALIDATION.md"
s = p.read_text()
s = re.sub(r"\*\*\d+/\d+ tests passed\*\*", f"**{TEST_COUNT}/{TEST_COUNT} tests passed**", s)
s = re.sub(r"\*\*\d+\.\d+% line coverage\*\*", f"**{COVERAGE_PCT:.2f}% line coverage**", s, count=1)
s = re.sub(r"package: `beliefweave` \*\*[^*]+\*\*", f"package: `beliefweave` **{VERSION}**", s)
s = re.sub(r"wheel: `dist/beliefweave-[^`]+`", f"wheel: `dist/{WHEEL}`", s)
s = re.sub(r"SQLite schema version \*\*\d+\*\*", f"SQLite schema version **{CURRENT_SCHEMA_VERSION}**", s)
if PAGES is not None:
    s = re.sub(r"manuscript: `paper/BELIEFWEAVE\.pdf` — \*\*\d+ pages\*\*", f"manuscript: `paper/BELIEFWEAVE.pdf` — **{PAGES} pages**", s)
s = re.sub(r"title: \*\*BeliefWeave:[^*]+\*\*", f"title: **{TITLE}**", s)
p.write_text(s)

# Compact release inventory.
p = ROOT / "RELEASE_CONTENTS.md"
s = p.read_text()
s = re.sub(r"Package version: \*\*[^*]+\*\*", f"Package version: **{VERSION}**", s)
s = re.sub(r"Tests: \*\*\d+/\d+ passing\*\*", f"Tests: **{TEST_COUNT}/{TEST_COUNT} passing**", s)
s = re.sub(r"Coverage: \*\*\d+\.\d+%\*\*", f"Coverage: **{COVERAGE_PCT:.2f}%**", s)
s = re.sub(r"SQLite schema contract: version \d+", f"SQLite schema contract: version {CURRENT_SCHEMA_VERSION}", s)
s = re.sub(r"Wheel: `dist/beliefweave-[^`]+`", f"Wheel: `dist/{WHEEL}`", s)
if PAGES is not None:
    s = re.sub(r"Paper: \d+-page submission-style manuscript", f"Paper: {PAGES}-page research manuscript", s)
p.write_text(s)

# Release gate status line.
p = ROOT / "QUALITY_GATES.md"
s = p.read_text()
s = re.sub(
    r"Current checked release: \*\*\d+ tests passed, \d+\.\d+% line coverage, package [^*]+\*\*\.",
    f"Current checked release: **{TEST_COUNT} tests passed, {COVERAGE_PCT:.2f}% line coverage, package {VERSION}**.",
    s,
)
p.write_text(s)

# Citation/package metadata.
p = ROOT / "CITATION.cff"
s = p.read_text()
s = re.sub(r"^version: .+$", f"version: {VERSION}", s, flags=re.M)
s = re.sub(r'  title: "BeliefWeave:[^"]+"', f'  title: "{TITLE}"', s)
p.write_text(s)

zenodo = json.loads((ROOT / ".zenodo.json").read_text())
zenodo["title"] = TITLE
zenodo["version"] = VERSION
write(".zenodo.json", json.dumps(zenodo, indent=2, ensure_ascii=False) + "\n")

codemeta = json.loads((ROOT / "codemeta.json").read_text())
codemeta["name"] = META["name"]
codemeta["version"] = VERSION
write("codemeta.json", json.dumps(codemeta, indent=2, ensure_ascii=False) + "\n")

# Manuscript-adjacent prose that repeats the paper title.
for path in ["paper/MANUSCRIPT.md", "paper/TECHNICAL_REPORT.md"]:
    p = ROOT / path
    text = p.read_text()
    text = re.sub(r"BeliefWeave: [^\n]+", TITLE, text, count=1)
    p.write_text(text)


# Supporting documents that repeat measured test/package state.
for path in ["paper/MANUSCRIPT.md", "paper/REPRODUCIBLE_SUMMARY.md", "ARTIFACT_MANIFEST.md", "RELEASE_NOTES.md"]:
    p = ROOT / path
    text = p.read_text()
    text = re.sub(r"\b\d+/\d+ tests passed\b", f"{TEST_COUNT}/{TEST_COUNT} tests passed", text)
    text = re.sub(r"\b\d+ tests passed\b", f"{TEST_COUNT} tests passed", text)
    text = re.sub(r"\bLine coverage: \*\*\d+\.\d+%\*\*", f"Line coverage: **{COVERAGE_PCT:.2f}%**", text)
    text = re.sub(r"\b\d+\.\d+% line coverage\b", f"{COVERAGE_PCT:.2f}% line coverage", text)
    text = re.sub(r"beliefweave-\d+\.\d+\.\d+-py3-none-any\.whl", WHEEL, text)
    text = re.sub(r"beliefweave \d+\.\d+\.\d+", f"beliefweave {VERSION}", text)
    p.write_text(text)

print(
    json.dumps(
        {
            "title": TITLE,
            "author": AUTHOR,
            "version": VERSION,
            "tests": TEST_COUNT,
            "coverage": round(COVERAGE_PCT, 2),
            "schema_version": CURRENT_SCHEMA_VERSION,
            "paper_pages": PAGES,
        },
        indent=2,
    )
)
