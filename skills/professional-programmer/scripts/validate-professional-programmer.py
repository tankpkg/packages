#!/usr/bin/env python3
"""Validate the @tank/professional-programmer skill package."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SKILL_NAME = "@tank/professional-programmer"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


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


MIN_NON_EMPTY_LINES = 150
MAX_LINES = 550
MIN_CODE_BLOCKS = 4
REQUIRED_REFERENCE_SECTIONS = [
    "### Anti-pattern",
    "### Better approach",
]
REQUIRED_REFERENCE_SECTION_ALTERNATIVES = [
    ("### Why this wins", "### Why correctness wins", "### Why security wins", "### Why simplicity wins", "### Why clarity wins", "### Why readability wins", "### Why critical tests win"),
    ("### Why the alternative loses", "### When speed legitimately wins", "### When convenience legitimately wins", "### When extensibility legitimately wins", "### When DRY legitimately wins", "### When performance legitimately wins", "### When deadlines legitimately win"),
]
BANNED_REFERENCE_PHRASES = [
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
        "A recommendation from this reference is complete",
        "guidance note",
        "Applied Guidance Notes",
        "Verification Focus",
        "This case matters because",
        "Detailed Application Cases",
    ]


def count_fenced_code_blocks(text: str) -> int:
    fence_count = sum(1 for line in text.splitlines() if line.startswith("```"))
    return fence_count // 2


def validate_references(root: Path, listed_refs: set[str]) -> None:
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
        if len(non_empty_lines) < MIN_NON_EMPTY_LINES:
            fail(f"{ref} is too thin: needs at least {MIN_NON_EMPTY_LINES} non-empty lines, found {len(non_empty_lines)}")
        if line_count > MAX_LINES:
            fail(f"{ref} exceeds {MAX_LINES} lines, found {line_count}")
        if "\n\n\n" in text:
            fail(f"{ref} contains excessive consecutive blank lines")
        code_blocks = count_fenced_code_blocks(text)
        if code_blocks < MIN_CODE_BLOCKS:
            fail(f"{ref} needs at least {MIN_CODE_BLOCKS} fenced code blocks for concrete examples, found {code_blocks}")
        for required_section in REQUIRED_REFERENCE_SECTIONS:
            if required_section not in text:
                fail(f"{ref} missing required section: {required_section}")
        for alternatives in REQUIRED_REFERENCE_SECTION_ALTERNATIVES:
            if not any(alt in text for alt in alternatives):
                fail(f"{ref} missing one of required sections: {alternatives}")
        for phrase in BANNED_REFERENCE_PHRASES:
            if phrase in text:
                fail(f"{ref} contains banned filler/scaffold phrase: {phrase}")

    actual_refs = {str(path.relative_to(root)) for path in (root / "references").glob("*.md")}
    unlisted = actual_refs - listed_refs
    if unlisted:
        fail(f"reference files not listed in SKILL.md: {sorted(unlisted)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root)

    validate_manifest(root)
    listed_refs = validate_skill(root)
    validate_references(root, listed_refs)
    print("professional-programmer package validation passed")


if __name__ == "__main__":
    main()
