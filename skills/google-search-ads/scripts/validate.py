#!/usr/bin/env python3
"""
validate.py — Two-pass validator for campaign.json + emitted CSVs.

Pass 1 validates the logical campaign.json against Google's rules.
Pass 2 validates the emitted CSV files against Editor's strict file format.

Exits 0 only if zero ERRORs (WARNs are OK).

Usage:
    python3 validate.py --in campaign.json --csv-dir ./out/ --report validation-report.md
    python3 validate.py --in campaign.json --strict        # treat WARNs as errors too
"""

from __future__ import annotations
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Finding type
# ---------------------------------------------------------------------------

class Finding:
    __slots__ = ("severity", "rule", "location", "message", "fix")

    def __init__(self, severity: str, rule: str, location: str, message: str, fix: str = ""):
        if severity not in {"ERROR", "WARN", "INFO"}:
            raise ValueError(
                f"severity must be one of ERROR/WARN/INFO, got {severity!r}"
            )
        self.severity = severity
        self.rule = rule
        self.location = location
        self.message = message
        self.fix = fix

    def __str__(self):
        out = f"[{self.severity}] [{self.rule}] {self.location}\n      {self.message}"
        if self.fix:
            out += f"\n      Fix: {self.fix}"
        return out

    def to_dict(self):
        return {
            "severity": self.severity, "rule": self.rule,
            "location": self.location, "message": self.message, "fix": self.fix,
        }


# ---------------------------------------------------------------------------
# Constants from references/02-csv-schema.md
# ---------------------------------------------------------------------------

BID_STRATEGIES = {
    "Manual CPC", "Enhanced CPC",
    "Target CPA", "Target ROAS",
    "Maximize conversions", "Maximize conversion value",
    "Target impression share",
}
MATCH_TYPES_POSITIVE = {"Broad", "Phrase", "Exact"}
MATCH_TYPES_NEGATIVE = {"Negative Broad", "Negative Phrase", "Negative Exact"}
ALLOWED_NETWORKS = {"Google search", "Search partners"}
FORBIDDEN_NETWORK_SUBSTRINGS = {"display"}  # case-insensitive

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # symbols & pictographs + misc
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport
    "\U0001F1E0-\U0001F1FF"  # flags
    "\u2600-\u27BF"           # misc symbols & dingbats
    "]"
)
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
REPEATED_PUNCT_RE = re.compile(r"([!?>])\1{2,}")
DOUBLE_SPACE_RE = re.compile(r"\s{2,}")
ALLCAPS_WORD_RE = re.compile(r"\b[A-Z]{4,}\b")
PATH_VALID_RE = re.compile(r"^[A-Za-z0-9-]*$")
REPEATED_WORD_RE = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Pass 1 — validate campaign.json
# ---------------------------------------------------------------------------

def validate_meta(meta: dict) -> Iterator[Finding]:
    if not isinstance(meta.get("geo"), list):
        yield Finding("ERROR", "meta.geo", "campaign.json:meta.geo",
                      "Geo must be a list", "Set meta.geo = [\"21167\", ...]")
        return
    for g in meta["geo"]:
        if not isinstance(g, str) or not g.isdigit():
            yield Finding("ERROR", "meta.geo.numeric",
                          f"campaign.json:meta.geo={g!r}",
                          "Geo entries must be numeric Geo Target ID strings",
                          "Look up at developers.google.com/google-ads/api/data/geotargets")

    if meta.get("language") and not re.match(r"^[a-z]{2}$", meta["language"]):
        yield Finding("ERROR", "meta.language",
                      f"campaign.json:meta.language={meta['language']!r}",
                      "Language must be 2-letter ISO 639-1 code",
                      "Use 'en', not 'english'")


def validate_campaign(c: dict, idx: int) -> Iterator[Finding]:
    loc = f"campaigns[{idx}]({c.get('name', '?')})"

    if c.get("type") != "Search":
        yield Finding("ERROR", "campaign.type", f"{loc}.type",
                      f"Type must be 'Search', got {c.get('type')!r}",
                      "Set type to 'Search'")
    if not isinstance(c.get("daily_budget"), (int, float)) or c["daily_budget"] <= 0:
        yield Finding("ERROR", "campaign.budget", f"{loc}.daily_budget",
                      f"daily_budget must be > 0, got {c.get('daily_budget')!r}",
                      "Set a positive daily budget")
    if c.get("bid_strategy") not in BID_STRATEGIES:
        yield Finding("ERROR", "campaign.bid_strategy", f"{loc}.bid_strategy",
                      f"Unknown bid strategy {c.get('bid_strategy')!r}",
                      f"Use one of: {sorted(BID_STRATEGIES)}")

    if c.get("bid_strategy") == "Target CPA" and not c.get("target_cpa"):
        yield Finding("ERROR", "campaign.tcpa_required", f"{loc}.target_cpa",
                      "bid_strategy=Target CPA requires target_cpa", "Set target_cpa")
    if c.get("bid_strategy") == "Target ROAS" and not c.get("target_roas"):
        yield Finding("ERROR", "campaign.troas_required", f"{loc}.target_roas",
                      "bid_strategy=Target ROAS requires target_roas", "Set target_roas")

    networks = c.get("networks", [])
    if not networks:
        yield Finding("ERROR", "campaign.networks_empty", f"{loc}.networks",
                      "networks cannot be empty (will default to Display per Google's wizard)",
                      "Set networks to ['Google search']")
    for n in networks:
        if any(sub in n.lower() for sub in FORBIDDEN_NETWORK_SUBSTRINGS):
            yield Finding("ERROR", "campaign.networks_display", f"{loc}.networks",
                          f"Network value {n!r} contains 'Display' — McDonald Gotcha #4",
                          "Remove Display from networks; v1 must be Search-only")
        elif n not in ALLOWED_NETWORKS:
            yield Finding("WARN", "campaign.networks_unknown", f"{loc}.networks",
                          f"Unknown network value {n!r}",
                          f"Allowed: {sorted(ALLOWED_NETWORKS)}")

    if c.get("bid_strategy") in {"Manual CPC", "Enhanced CPC"}:
        for gi, g in enumerate(c.get("ad_groups", [])):
            if not isinstance(g.get("max_cpc"), (int, float)) or g["max_cpc"] <= 0:
                yield Finding("ERROR", "ad_group.max_cpc_required",
                              f"{loc}.ad_groups[{gi}]({g.get('name', '?')}).max_cpc",
                              "Manual/Enhanced CPC strategy requires max_cpc per ad group",
                              "Set max_cpc to a positive value")


def validate_keyword(kw: dict, where: str, broad_confirmed: bool) -> Iterator[Finding]:
    text = kw.get("text", "")
    match = kw.get("match", "")

    if not text:
        yield Finding("ERROR", "kw.empty", where, "Keyword text is empty", "Remove or fill in")
        return
    if len(text) > 80:
        yield Finding("ERROR", "kw.too_long", where,
                      f"Keyword text > 80 chars ({len(text)})", "Shorten the keyword")
    word_count = len(text.split())
    if word_count > 10:
        yield Finding("ERROR", "kw.too_many_words", where,
                      f"Keyword has {word_count} words (Google limit: 10)",
                      "Split or shorten")

    if text.startswith("+"):
        yield Finding("ERROR", "kw.modified_broad", where,
                      f"Modified Broad (+) is discontinued: {text!r}",
                      "Use Phrase (\"...\") or Exact ([...]) instead")

    valid_match = MATCH_TYPES_POSITIVE | MATCH_TYPES_NEGATIVE
    if match not in valid_match:
        yield Finding("ERROR", "kw.bad_match", where,
                      f"Unknown match type {match!r}",
                      f"Use one of: {sorted(valid_match)}")

    # Wrapping vs match-type consistency
    is_bracket = text.startswith("[") and text.endswith("]")
    is_quote = text.startswith('"') and text.endswith('"')
    is_naked = not is_bracket and not is_quote

    if match in {"Exact", "Negative Exact"} and not is_bracket:
        yield Finding("ERROR", "kw.exact_wrapping", where,
                      f"Exact-match keyword must be wrapped in [] — got {text!r}",
                      "Wrap as [...]")
    if match in {"Phrase", "Negative Phrase"} and not is_quote:
        yield Finding("ERROR", "kw.phrase_wrapping", where,
                      f"Phrase-match keyword must be wrapped in \"\" — got {text!r}",
                      "Wrap as \"...\"")
    if match == "Broad" and is_naked and not broad_confirmed:
        yield Finding("ERROR", "kw.naked_broad", where,
                      f"Naked broad-match keyword {text!r} without explicit confirmation "
                      "(McDonald Gotcha #2: broad match expands aggressively via BERT and "
                      "burns budget on irrelevant traffic).",
                      "Wrap in [] (Exact) or \"\" (Phrase), or set broad_confirmed=true at "
                      "the ad-group or campaign level if you really intend Broad")


def validate_rsa(rsa: dict, where: str) -> Iterator[Finding]:
    if not rsa:
        yield Finding("ERROR", "rsa.missing", where, "Ad group has no RSA",
                      "Add an RSA with ≥3 headlines and ≥2 descriptions")
        return

    final_url = rsa.get("final_url", "")
    if not final_url:
        yield Finding("ERROR", "rsa.no_url", f"{where}.final_url",
                      "Missing final_url", "Set the landing-page URL")
    else:
        parsed = urlparse(final_url)
        if parsed.scheme not in {"https", "http"}:
            yield Finding("ERROR", "rsa.bad_url_scheme", f"{where}.final_url",
                          f"final_url must be HTTPS, got {final_url!r}",
                          "Use https:// prefix")
        if len(final_url) > 1024:
            yield Finding("ERROR", "rsa.url_too_long", f"{where}.final_url",
                          f"final_url > 1024 chars ({len(final_url)})", "Shorten URL")

    for path_field in ("path1", "path2"):
        v = rsa.get(path_field, "") or ""
        if len(v) > 15:
            yield Finding("ERROR", f"rsa.{path_field}_too_long", f"{where}.{path_field}",
                          f"{path_field} > 15 chars: {v!r}", "Shorten to ≤15 chars")
        if v and not PATH_VALID_RE.match(v):
            yield Finding("ERROR", f"rsa.{path_field}_invalid", f"{where}.{path_field}",
                          f"{path_field} has invalid chars: {v!r}",
                          "Use only alphanumeric + hyphen")

    headlines = rsa.get("headlines", []) or []
    descriptions = rsa.get("descriptions", []) or []

    if len(headlines) < 3:
        yield Finding("ERROR", "rsa.too_few_headlines", f"{where}.headlines",
                      f"RSA needs ≥3 headlines, got {len(headlines)}",
                      "Add more headlines (up to 15)")
    if len(headlines) > 15:
        yield Finding("ERROR", "rsa.too_many_headlines", f"{where}.headlines",
                      f"RSA allows ≤15 headlines, got {len(headlines)}",
                      "Remove extras")
    if len(descriptions) < 2:
        yield Finding("ERROR", "rsa.too_few_descs", f"{where}.descriptions",
                      f"RSA needs ≥2 descriptions, got {len(descriptions)}",
                      "Add more descriptions (up to 4)")
    if len(descriptions) > 4:
        yield Finding("ERROR", "rsa.too_many_descs", f"{where}.descriptions",
                      f"RSA allows ≤4 descriptions, got {len(descriptions)}",
                      "Remove extras")

    # Validate each text element
    for i, h in enumerate(headlines):
        yield from validate_ad_text(h.get("text", ""), f"{where}.headlines[{i}]", limit=30)
    for i, d in enumerate(descriptions):
        yield from validate_ad_text(d.get("text", ""), f"{where}.descriptions[{i}]", limit=90)

    # Pin overlap
    pin_counts = {1: 0, 2: 0, 3: 0}
    pinned_total = 0
    for h in headlines:
        p = h.get("pin")
        if p in pin_counts:
            pin_counts[p] += 1
            pinned_total += 1
    if pinned_total > 0 and pinned_total / max(1, len(headlines)) > 0.5:
        yield Finding("WARN", "rsa.over_pinning", f"{where}.headlines",
                      f"Pinning ratio {pinned_total}/{len(headlines)} > 50% — hampers ML",
                      "Unpin non-brand headlines")
    for pos, n in pin_counts.items():
        if n > 2:
            yield Finding("WARN", "rsa.pin_stack", f"{where}.headlines",
                          f"{n} headlines pinned to position {pos} (recommend ≤2)",
                          "Unpin some")


def validate_ad_text(text: str, where: str, limit: int) -> Iterator[Finding]:
    if not text:
        yield Finding("ERROR", "adtext.empty", where, "Ad text is empty",
                      "Remove or fill in")
        return
    if len(text) > limit:
        yield Finding("ERROR", "adtext.too_long", where,
                      f"Length {len(text)} > {limit}", "Shorten")

    if EMOJI_RE.search(text):
        yield Finding("ERROR", "adtext.emoji", where,
                      f"Contains emoji: {text!r}", "Remove emoji")
    if PHONE_RE.search(text):
        yield Finding("ERROR", "adtext.phone", where,
                      f"Looks like a phone number: {text!r}",
                      "Move phone to a Call Extension")
    if "click here" in text.lower():
        yield Finding("WARN", "adtext.clickhere", where,
                      "Contains 'click here' — Google considers it filler",
                      "Use a strong verb instead")
    if REPEATED_PUNCT_RE.search(text):
        yield Finding("ERROR", "adtext.repeated_punct", where,
                      f"Repeated punctuation in {text!r}",
                      "Remove repeated !!! or ???")
    if DOUBLE_SPACE_RE.search(text):
        yield Finding("WARN", "adtext.double_space", where,
                      "Contains double-space", "Normalize whitespace")
    if ALLCAPS_WORD_RE.search(text):
        yield Finding("ERROR", "adtext.allcaps", where,
                      f"Contains ALL-CAPS standalone word in {text!r}",
                      "Use title case")
    if REPEATED_WORD_RE.search(text):
        yield Finding("WARN", "adtext.repeated_word", where,
                      f"Contains repeated consecutive word: {text!r}",
                      "Avoid 'Sale Sale Sale' style")


def validate_ad_group(g: dict, where: str, broad_confirmed: bool) -> Iterator[Finding]:
    if len(g.get("keywords", [])) > 20:
        yield Finding("WARN", "ag.hagakure", f"{where}.keywords",
                      f"Ad group has {len(g['keywords'])} keywords (Hagakure soft limit: 20)",
                      "Split into themed sub-ad-groups")

    # Duplicate keyword check
    seen = set()
    for ki, kw in enumerate(g.get("keywords", [])):
        key = (kw.get("text", "").lower(), kw.get("match", ""))
        if key in seen:
            yield Finding("ERROR", "ag.dup_keyword", f"{where}.keywords[{ki}]",
                          f"Duplicate keyword: {kw.get('text')!r} ({kw.get('match')})",
                          "Remove the duplicate")
        seen.add(key)
        yield from validate_keyword(kw, f"{where}.keywords[{ki}]", broad_confirmed)

    # Negative blocks positive in same ad group?
    pos_texts = {kw.get("text", "").strip("[]\"").lower() for kw in g.get("keywords", [])}
    for ni, neg in enumerate(g.get("negatives", [])):
        ntxt = neg.get("text", "").strip("[]\"").lower()
        if ntxt in pos_texts:
            yield Finding("ERROR", "ag.self_block", f"{where}.negatives[{ni}]",
                          f"Negative keyword {ntxt!r} duplicates a positive in same ad group",
                          "Remove the negative or remove the positive")

    yield from validate_rsa(g.get("rsa", {}), f"{where}.rsa")


def validate_pass1(doc: dict) -> list[Finding]:
    findings: list[Finding] = []
    findings += list(validate_meta(doc.get("meta", {})))

    # Cross-campaign duplicate-final-url check
    url_to_locations: dict[str, list[str]] = {}

    for ci, c in enumerate(doc.get("campaigns", [])):
        findings += list(validate_campaign(c, ci))
        for gi, g in enumerate(c.get("ad_groups", [])):
            where = f"campaigns[{ci}]({c.get('name')}).ad_groups[{gi}]({g.get('name')})"
            broad_confirmed = c.get("broad_confirmed") or g.get("broad_confirmed", False)
            findings += list(validate_ad_group(g, where, broad_confirmed))
            url = (g.get("rsa") or {}).get("final_url")
            if url:
                url_to_locations.setdefault(url, []).append(where)

    # Multiple ad groups sharing one final URL
    for url, locs in url_to_locations.items():
        if len(locs) > 1:
            findings.append(Finding(
                "WARN", "rsa.shared_url", locs[0],
                f"final_url {url!r} is used by {len(locs)} ad groups — "
                "McDonald Gotcha #1: same LP for different intents = sloppy mapping",
                "Create a dedicated LP per ad-group theme"))

    return findings


# ---------------------------------------------------------------------------
# Pass 2 — validate emitted CSVs
# ---------------------------------------------------------------------------

ENTITY_FILES = {
    "Campaigns.csv": "campaign",
    "AdGroups.csv": "adgroup",
    "Keywords.csv": "keyword",
    "NegativeKeywords.csv": "negkeyword",
    "RSAs.csv": "rsa",
    "Locations.csv": "location",
    "Sitelinks.csv": "sitelink",
    "Callouts.csv": "callout",
    "StructuredSnippets.csv": "structured_snippet",
}


def validate_pass2(csv_dir: Path, campaign_doc: dict) -> list[Finding]:
    findings: list[Finding] = []
    if not csv_dir.exists() or not csv_dir.is_dir():
        return findings

    valid_campaigns = {c["name"] for c in campaign_doc.get("campaigns", [])}
    valid_ag_pairs = {
        (c["name"], g["name"])
        for c in campaign_doc.get("campaigns", [])
        for g in c["ad_groups"]
    }

    for filename in ENTITY_FILES:
        path = csv_dir / filename
        if not path.exists():
            continue

        # UTF-8 decoding check
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(
                "ERROR", "csv.encoding", str(path),
                "File is not valid UTF-8",
                "Re-emit with UTF-8 encoding"))
            continue

        # File size limit
        if len(raw) > 50 * 1024 * 1024:
            findings.append(Finding(
                "ERROR", "csv.too_big", str(path),
                f"File > 50MB ({len(raw)} bytes)",
                "Split into smaller bulk imports"))

        # Parse rows
        rows = list(csv.reader(text.splitlines()))
        if not rows:
            findings.append(Finding(
                "ERROR", "csv.empty", str(path),
                "File has no rows", "Re-emit"))
            continue

        header = rows[0]
        header_len = len(header)
        # Header English check (very loose — at least ASCII)
        for h in header:
            if not re.match(r"^[\x20-\x7E]+$", h):
                findings.append(Finding(
                    "ERROR", "csv.non_english_header", f"{path}:1",
                    f"Header {h!r} contains non-ASCII chars",
                    "Use English headers"))

        # Ragged rows
        for ri, row in enumerate(rows[1:], start=2):
            if row and len(row) < header_len:
                findings.append(Finding(
                    "ERROR", "csv.ragged", f"{path}:{ri}",
                    f"Row has {len(row)} fields, header has {header_len}",
                    "Pad with empty fields"))

        # Per-file rules
        if filename == "Campaigns.csv":
            idx_nets = header.index("Networks") if "Networks" in header else -1
            idx_name = header.index("Campaign") if "Campaign" in header else -1
            for ri, row in enumerate(rows[1:], start=2):
                if idx_nets >= 0 and idx_nets < len(row):
                    nets_value = row[idx_nets]
                    if any(sub in nets_value.lower() for sub in FORBIDDEN_NETWORK_SUBSTRINGS):
                        findings.append(Finding(
                            "ERROR", "csv.networks_display", f"{path}:{ri}",
                            f"Networks cell {nets_value!r} contains 'Display'",
                            "Remove Display — v1 must be Google search only"))
                    if "," in nets_value:
                        findings.append(Finding(
                            "ERROR", "csv.networks_comma", f"{path}:{ri}",
                            f"Networks cell uses commas: {nets_value!r}",
                            "Use semicolons as separator"))
                if idx_name >= 0 and idx_name < len(row) and row[idx_name] not in valid_campaigns:
                    findings.append(Finding(
                        "WARN", "csv.campaign_not_in_json", f"{path}:{ri}",
                        f"Campaign {row[idx_name]!r} not in campaign.json",
                        "Re-emit from authoritative campaign.json"))

        elif filename == "AdGroups.csv":
            idx_c = header.index("Campaign") if "Campaign" in header else -1
            idx_g = header.index("Ad group") if "Ad group" in header else -1
            for ri, row in enumerate(rows[1:], start=2):
                if idx_c >= 0 and idx_g >= 0:
                    cn = row[idx_c] if idx_c < len(row) else ""
                    gn = row[idx_g] if idx_g < len(row) else ""
                    if cn and cn not in valid_campaigns:
                        findings.append(Finding(
                            "ERROR", "csv.orphan_adgroup", f"{path}:{ri}",
                            f"Ad group {gn!r} references missing campaign {cn!r}",
                            "Add the campaign or fix the reference"))

        elif filename == "Keywords.csv":
            idx_c = header.index("Campaign") if "Campaign" in header else -1
            idx_g = header.index("Ad group") if "Ad group" in header else -1
            idx_kw = header.index("Keyword") if "Keyword" in header else -1
            idx_t = header.index("Criterion Type") if "Criterion Type" in header else -1
            for ri, row in enumerate(rows[1:], start=2):
                cn = row[idx_c] if idx_c >= 0 and idx_c < len(row) else ""
                gn = row[idx_g] if idx_g >= 0 and idx_g < len(row) else ""
                kw_text = row[idx_kw] if idx_kw >= 0 and idx_kw < len(row) else ""
                ctype = row[idx_t] if idx_t >= 0 and idx_t < len(row) else ""

                if cn and gn and (cn, gn) not in valid_ag_pairs:
                    findings.append(Finding(
                        "ERROR", "csv.orphan_keyword", f"{path}:{ri}",
                        f"Keyword {kw_text!r} references missing ad group ({cn!r},{gn!r})",
                        "Add the ad group or fix the reference"))

                # Wrapping vs Criterion Type case-sensitive
                if ctype not in (MATCH_TYPES_POSITIVE | MATCH_TYPES_NEGATIVE | {"Campaign negative"}):
                    findings.append(Finding(
                        "ERROR", "csv.criterion_type_case", f"{path}:{ri}",
                        f"Criterion Type {ctype!r} is case-sensitive — got wrong case or unknown value",
                        f"Use exactly one of: {sorted(MATCH_TYPES_POSITIVE | MATCH_TYPES_NEGATIVE)}"))

                is_bracket = kw_text.startswith("[") and kw_text.endswith("]")
                is_quote = kw_text.startswith('"') and kw_text.endswith('"')
                if ctype in {"Exact", "Negative Exact"} and not is_bracket:
                    findings.append(Finding(
                        "ERROR", "csv.exact_no_brackets", f"{path}:{ri}",
                        f"Exact keyword without []: {kw_text!r}",
                        "Wrap in []"))
                if ctype in {"Phrase", "Negative Phrase"} and not is_quote:
                    findings.append(Finding(
                        "ERROR", "csv.phrase_no_quotes", f"{path}:{ri}",
                        f"Phrase keyword without quotes: {kw_text!r}",
                        "Wrap in \"\""))
                if kw_text.startswith("+"):
                    findings.append(Finding(
                        "ERROR", "csv.modified_broad", f"{path}:{ri}",
                        f"Modified Broad (+) is discontinued: {kw_text!r}",
                        "Use Phrase or Exact instead"))

        elif filename == "Locations.csv":
            idx_id = header.index("Location ID") if "Location ID" in header else -1
            for ri, row in enumerate(rows[1:], start=2):
                if idx_id >= 0 and idx_id < len(row):
                    v = row[idx_id]
                    if v and not v.isdigit():
                        findings.append(Finding(
                            "ERROR", "csv.location_not_numeric", f"{path}:{ri}",
                            f"Location ID {v!r} must be numeric",
                            "Look up at developers.google.com/google-ads/api/data/geotargets"))

    return findings


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def render_report(findings: list[Finding]) -> str:
    errs = [f for f in findings if f.severity == "ERROR"]
    warns = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]
    status = "PASS" if not errs else "FAIL"
    out = [f"# Validation Report",
           f"Status: **{status}** ({len(errs)} errors, {len(warns)} warnings, {len(infos)} info)\n"]

    if errs:
        out.append("## ERRORS (must fix before import)\n")
        for i, f in enumerate(errs, 1):
            out.append(f"{i}. **{f.rule}** — `{f.location}`")
            out.append(f"   - {f.message}")
            if f.fix:
                out.append(f"   - **Fix:** {f.fix}")
            out.append("")
    if warns:
        out.append("## WARNINGS (will import but may cause silent issues)\n")
        for i, f in enumerate(warns, 1):
            out.append(f"{i}. **{f.rule}** — `{f.location}`")
            out.append(f"   - {f.message}")
            if f.fix:
                out.append(f"   - **Fix:** {f.fix}")
            out.append("")
    if infos:
        out.append("## INFO\n")
        for i, f in enumerate(infos, 1):
            out.append(f"{i}. **{f.rule}** — {f.message}")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Validate campaign.json + emitted CSVs.")
    p.add_argument("--in", dest="inp", required=True, type=Path)
    p.add_argument("--csv-dir", type=Path, default=None,
                   help="Optional CSV directory for Pass 2")
    p.add_argument("--report", type=Path, default=None,
                   help="Write report to file (default: stdout)")
    p.add_argument("--strict", action="store_true",
                   help="Treat WARNs as errors for exit-code purposes")
    p.add_argument("--json", action="store_true",
                   help="Output findings as JSON instead of markdown")
    args = p.parse_args(argv)

    if not args.inp.exists():
        print(f"ERROR: input not found: {args.inp}", file=sys.stderr)
        return 2

    doc = json.loads(args.inp.read_text())
    findings = validate_pass1(doc)
    if args.csv_dir:
        findings += validate_pass2(args.csv_dir, doc)

    if args.json:
        out = json.dumps([f.to_dict() for f in findings], indent=2)
    else:
        out = render_report(findings)

    if args.report:
        args.report.write_text(out)
        print(f"wrote {args.report}")
    else:
        print(out)

    bad = sum(1 for f in findings if f.severity == "ERROR")
    if args.strict:
        bad += sum(1 for f in findings if f.severity == "WARN")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
