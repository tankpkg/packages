#!/usr/bin/env python3
"""Check a design bible for structure, enforceable values, and vague wording.

Usage:
    uv run scripts/check_bible.py path/to/DESIGN-BIBLE.md

Errors (exit code 1):
    missing required section, unfilled placeholder, invalid hex value,
    palette without any valid hex value

Warnings (exit code 0):
    missing version line, short or long do-not-do list, anchor length outside
    40 to 250 words, no reference IDs, fewer than three cross-context checks,
    vague quality words without a physical property beside them

The script reads only the file it is given. It has no dependencies beyond the
Python standard library.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SECTIONS = [
    "Thematic statement",
    "Palette",
    "Light",
    "Lens",
    "Rendering",
    "Subjects",
    "Do-not-do",
    "Reference set",
    "Style anchors",
    "Cross-context check",
]

VAGUE_WORDS = [
    "beautiful",
    "stunning",
    "amazing",
    "epic",
    "awesome",
    "gorgeous",
    "nice",
    "pretty",
    "moody",
    "dramatic",
    "cinematic",
    "masterpiece",
    "premium",
    "vintage",
    "cozy",
    "cosy",
    "high quality",
    "highly detailed",
    "ultra detailed",
    "trending",
]

PLACEHOLDER = re.compile(r"\{\{|TODO|<fill")
HEX_TOKEN = re.compile(r"#[0-9A-Za-z]+")
HEX_VALID = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
REFERENCE_ID = re.compile(r"\b[RA]\d{2}\b")
MIDJOURNEY_PARAMETER = re.compile(r"--(sref|sw|sv)\b")
HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
BULLET = re.compile(r"^\s*[-*]\s+\S")
CHECKBOX = re.compile(r"^\s*[-*]\s*\[[ xX]\]")
TABLE_SEPARATOR = re.compile(r"^\|\s*:?-{3,}")
VAGUE = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in VAGUE_WORDS) + r")\b",
    re.IGNORECASE,
)


@dataclass
class Section:
    title: str
    level: int
    start: int
    end: int

    def body(self, lines: list[str]) -> list[str]:
        return lines[self.start + 1 : self.end]


def find_sections(lines: list[str]) -> list[Section]:
    """Split the document by Markdown headings, ignoring headings inside code fences."""
    headings: list[tuple[int, int, str]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))

    sections: list[Section] = []
    for position, (start, level, title) in enumerate(headings):
        end = len(lines)
        for next_start, next_level, _ in headings[position + 1 :]:
            if next_level <= level:
                end = next_start
                break
        sections.append(Section(title=title, level=level, start=start, end=end))
    return sections


def named_section(sections: list[Section], name: str) -> Section | None:
    for section in sections:
        if name.lower() in section.title.lower():
            return section
    return None


def fenced_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if line.lstrip().startswith("```"):
            if current is None:
                current = []
            else:
                blocks.append(current)
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def check_palette(section: Section, lines: list[str]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    table_rows = [line for line in section.body(lines) if line.strip().startswith("|")]
    if not table_rows:
        return [("ERROR", "palette: no table found")]

    valid_hex_count = 0
    header_skipped = False
    for row in table_rows:
        if TABLE_SEPARATOR.match(row.strip()):
            continue
        if not header_skipped:
            header_skipped = True
            continue
        tokens = HEX_TOKEN.findall(row)
        if not tokens:
            findings.append(("WARN", f"palette row has no hex value: {row.strip()[:60]}"))
        for token in tokens:
            if HEX_VALID.match(token):
                valid_hex_count += 1
            else:
                findings.append(("ERROR", f"palette: invalid hex '{token}' in row: {row.strip()[:60]}"))

    if valid_hex_count == 0:
        findings.append(("ERROR", "palette: no valid hex values found"))
    return findings


def check_anchors(section: Section, lines: list[str]) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    blocks = fenced_blocks(section.body(lines))
    if not blocks:
        return [("ERROR", "style anchors: no fenced anchor block found")]
    for number, block in enumerate(blocks, start=1):
        text = " ".join(block)
        if MIDJOURNEY_PARAMETER.search(text):
            continue
        word_count = len(text.split())
        if word_count < 40 or word_count > 250:
            findings.append(("WARN", f"anchor block {number} has {word_count} words; aim for 80 to 200 for prose anchors"))
    return findings


def check(path: Path) -> list[tuple[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    sections = find_sections(lines)
    findings: list[tuple[str, str]] = []

    for name in REQUIRED_SECTIONS:
        if named_section(sections, name) is None:
            findings.append(("ERROR", f"missing required section: {name}"))

    for number, line in enumerate(lines, start=1):
        if PLACEHOLDER.search(line):
            findings.append(("ERROR", f"line {number}: unfilled placeholder"))

    if not any(line.lower().startswith("version:") for line in lines[:20]):
        findings.append(("WARN", "header has no 'Version:' line in the first 20 lines"))

    palette = named_section(sections, "Palette")
    if palette is not None:
        findings.extend(check_palette(palette, lines))

    do_not = named_section(sections, "Do-not-do")
    if do_not is not None:
        items = [line for line in do_not.body(lines) if BULLET.match(line)]
        if len(items) < 3:
            findings.append(("WARN", f"do-not-do list has {len(items)} items; aim for 6 to 12"))
        elif len(items) > 15:
            findings.append(("WARN", f"do-not-do list has {len(items)} items; keep the ones that caused real failures"))

    anchors = named_section(sections, "Style anchors")
    if anchors is not None:
        findings.extend(check_anchors(anchors, lines))

    references = named_section(sections, "Reference set")
    if references is not None and not REFERENCE_ID.search("\n".join(references.body(lines))):
        findings.append(("WARN", "reference set has no IDs such as R01 or A01"))

    cross_context = named_section(sections, "Cross-context check")
    if cross_context is not None:
        checks = [line for line in cross_context.body(lines) if CHECKBOX.match(line)]
        if len(checks) < 3:
            findings.append(("WARN", f"cross-context check has {len(checks)} checkboxes; aim for at least 3"))

    for number, line in enumerate(lines, start=1):
        for match in VAGUE.finditer(line):
            findings.append(
                ("WARN", f"line {number}: vague word '{match.group(1)}'; name a physical property instead")
            )

    return findings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2

    path = Path(argv[1])
    if not path.is_file():
        print(f"ERROR: not a file: {path}")
        return 2

    findings = check(path)
    errors = sum(1 for level, _ in findings if level == "ERROR")
    warnings = len(findings) - errors

    for level, message in findings:
        print(f"{level}: {message}")
    if not findings:
        print("OK: all checks passed")
    print(f"{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
