#!/usr/bin/env python3
"""Validate the @tank/professional-programmer skill package."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


SKILL_NAME = "@tank/professional-programmer"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def warn(message: str) -> None:
    print(f"WARN: {message}")


def read_text(path: Path) -> str:
    if not path.exists():
        fail(f"missing required file: {path}")
    return path.read_text(encoding="utf-8")


def parse_frontmatter(skill_text: str) -> dict[str, str]:
    if not skill_text.startswith("---\n"):
        fail("SKILL.md is missing YAML frontmatter")
    parts = skill_text.split("---\n", 2)
    if len(parts) < 3:
        fail("SKILL.md frontmatter is not closed")
    frontmatter = parts[1]
    result: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if line.startswith("name:"):
            result["name"] = line.split(":", 1)[1].strip().strip('"')
    return result


def skill_body_line_count(skill_text: str) -> int:
    parts = skill_text.split("---\n", 2)
    if len(parts) < 3:
        return len(skill_text.splitlines())
    return len(parts[2].strip("\n").splitlines())


def reference_paths_from_skill(skill_text: str) -> set[str]:
    return set(re.findall(r"`(references/[^`]+\.md)`", skill_text))


def validate_manifest(root: Path) -> None:
    manifest_path = root / "tank.json"
    manifest = json.loads(read_text(manifest_path))
    if manifest.get("name") != SKILL_NAME:
        fail(f"tank.json name must be {SKILL_NAME}")
    if "atoms" in manifest:
        fail("tank.json must not contain atoms for the initial instruction-only package")
    if not re.match(r"^\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?(\+[A-Za-z0-9.]+)?$", manifest.get("version", "")):
        fail("tank.json version must be semver")
    if manifest.get("repository") != "https://github.com/tankpkg/skills":
        fail("tank.json repository must be https://github.com/tankpkg/skills")
    permissions = manifest.get("permissions")
    if not permissions:
        fail("tank.json permissions are required")
    if permissions.get("network", {}).get("outbound") != []:
        fail("network.outbound must be empty")
    if permissions.get("filesystem", {}).get("read") != ["**/*"]:
        fail("filesystem.read must be ['**/*']")
    if permissions.get("filesystem", {}).get("write") != []:
        fail("filesystem.write must be empty")
    if permissions.get("subprocess") is not False:
        fail("subprocess must be false")


def validate_skill(root: Path) -> set[str]:
    skill_path = root / "SKILL.md"
    skill_text = read_text(skill_path)
    frontmatter = parse_frontmatter(skill_text)
    if frontmatter.get("name") != SKILL_NAME:
        fail(f"SKILL.md name must be {SKILL_NAME}")
    trigger_count = len(re.findall(r'"[^"]+"', skill_text.split("---\n", 2)[1]))
    if trigger_count < 10:
        fail(f"SKILL.md description must include at least 10 quoted trigger phrases, found {trigger_count}")
    for section in ["## Core Philosophy", "## Quick-Start: Common Problems", "## Decision Trees", "## Reference Index"]:
        if section not in skill_text:
            fail(f"SKILL.md missing required section: {section}")
    body_lines = skill_body_line_count(skill_text)
    if body_lines > 200:
        fail(f"SKILL.md body exceeds 200 lines: {body_lines}")
    references = reference_paths_from_skill(skill_text)
    if not references:
        fail("SKILL.md does not list reference files")
    return references


def validate_ledger(root: Path, allow_blocked: bool) -> None:
    ledger_path = root / "assets" / "source-ledger.csv"
    with ledger_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    expected_fields = [
        "item_number",
        "title",
        "author",
        "main_page_url",
        "medium_step_url",
        "discovered_medium_step_url",
        "medium_read_status",
        "canonical_source_url",
        "coverage_status",
        "notes",
    ]
    if fields != expected_fields:
        fail(f"source-ledger.csv fields must be {expected_fields}, found {fields}")
    if len(rows) != 97:
        fail(f"source-ledger.csv must have exactly 97 rows, found {len(rows)}")
    required = {"item_number", "title", "author", "main_page_url", "medium_read_status", "canonical_source_url", "coverage_status"}
    allowed_medium = {"read", "missing", "inaccessible", "paywalled", "duplicate", "not-applicable"}
    allowed_coverage = {"covered-from-medium-and-canonical", "covered-from-canonical", "blocked-needs-review"}
    for index, row in enumerate(rows, start=1):
        for field in required:
            if not row.get(field):
                fail(f"ledger row {index} missing {field}")
        if row.get("medium_read_status") not in allowed_medium:
            fail(f"ledger row {index} has invalid medium_read_status: {row.get('medium_read_status')}")
        if row.get("coverage_status") not in allowed_coverage:
            fail(f"ledger row {index} has invalid coverage_status: {row.get('coverage_status')}")
        if row.get("medium_read_status") == "read" and not row.get("medium_step_url") and not row.get("discovered_medium_step_url"):
            fail(f"ledger row {index} marked read without a Medium URL")
        if not row.get("canonical_source_url", "").startswith("https://raw.githubusercontent.com/97-things/"):
            fail(f"ledger row {index} canonical_source_url must be raw 97-things GitHub URL")
        if row.get("coverage_status") == "blocked-needs-review" and not allow_blocked:
            fail(f"ledger row {index} is blocked-needs-review")


def validate_references(root: Path, listed_refs: set[str]) -> None:
    banned_reference_phrases = [
        "Operational Catalog",
        "Assessment Questions",
        "Review Prompts",
        "Additional Application Notes",
        "Failure to avoid: treating the scenario as a generic best-practice reminder",
        "If you see ",
        "Step-by-Step Procedure",
        "Anti-Pattern Corrections",
        "Review Questions",
        "Routing Matrix",
        "Scenario Playbook",
        "Completion Signals",
        "Boundary Questions",
        "Topic-Specific Notes",
        "Questions",
        "A recommendation from this reference is complete",
        "guidance note",
        "Applied Guidance Notes",
        "Verification Focus",
        "This case matters because",
        "Detailed Application Cases",
    ]
    for ref in sorted(listed_refs):
        path = root / ref
        text = read_text(path)
        lines = text.splitlines()
        if not lines or not lines[0].startswith("# "):
            fail(f"{ref} must start with an H1")
        if text.startswith("---"):
            fail(f"{ref} must not contain YAML frontmatter")
        if not any(line.startswith("Sources:") for line in lines[:5]):
            fail(f"{ref} must include Sources near the top")
        line_count = len(lines)
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < 70:
            fail(f"{ref} is too thin for a layered reference, found {len(non_empty_lines)} non-empty lines")
        if line_count > 450:
            fail(f"{ref} exceeds 450 lines, found {line_count}")
        if "\n\n\n" in text:
            fail(f"{ref} contains excessive consecutive blank lines")
        for phrase in banned_reference_phrases:
            if phrase in text:
                fail(f"{ref} contains banned filler/scaffold phrase: {phrase}")

    actual_refs = {str(path.relative_to(root)) for path in (root / "references").glob("*.md")}
    unlisted = actual_refs - listed_refs
    if unlisted:
        fail(f"reference files not listed in SKILL.md: {sorted(unlisted)}")


def validate_evals(root: Path) -> None:
    cases_dir = root / "assets" / "evals" / "cases"
    expected_dir = root / "assets" / "evals" / "expected"
    cases = {path.stem for path in cases_dir.glob("*.md")}
    expected = {path.stem for path in expected_dir.glob("*.json")}
    if len(cases) < 30:
        fail(f"expected at least 30 eval cases, found {len(cases)}")
    index_cases = [name for name in cases if "index" in name]
    if index_cases:
        fail(f"eval cases must not include index placeholders: {index_cases}")
    if cases != expected:
        fail(f"eval case/expected mismatch: missing expected={sorted(cases - expected)}, missing cases={sorted(expected - cases)}")
    for path in cases_dir.glob("*.md"):
        case_text = read_text(path).strip()
        if len(case_text.split()) < 15:
            fail(f"{path} is too thin to be a meaningful eval case")
        if "The expected response should" in case_text:
            fail(f"{path} contains meta-instructions instead of scenario input")
        if "Context: Treat this as a realistic review prompt" in case_text:
            fail(f"{path} contains repeated eval context boilerplate")
    for path in expected_dir.glob("*.json"):
        data = json.loads(read_text(path))
        for key in ["primaryPrinciples", "tradeoff", "recommendedAction", "delegateTo", "verificationRequired", "mustNotDo"]:
            if key not in data:
                fail(f"{path} missing key {key}")
        if not data.get("primaryPrinciples") or not data.get("verificationRequired") or not data.get("mustNotDo"):
            fail(f"{path} must have non-empty principles, verification, and mustNotDo")


def validate_attribution(root: Path) -> None:
    attribution = read_text(root / "assets" / "ATTRIBUTION.md")
    required_phrases = ["CC BY-NC-SA 3.0", "original synthesis", "does not include copied source prose"]
    for phrase in required_phrases:
        if phrase not in attribution:
            fail(f"ATTRIBUTION.md must mention: {phrase}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-blocked", action="store_true")
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root)

    validate_manifest(root)
    listed_refs = validate_skill(root)
    validate_ledger(root, args.allow_blocked)
    validate_references(root, listed_refs)
    validate_evals(root)
    validate_attribution(root)
    print("professional-programmer package validation passed")


if __name__ == "__main__":
    main()
