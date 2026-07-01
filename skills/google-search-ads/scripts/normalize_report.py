#!/usr/bin/env python3
"""
normalize_report.py — Convert Google Ads UI CSV report exports into a
single unified internal JSON for diagnose.py.

Accepts any of:
  - campaign-report.csv
  - ad-group-report.csv
  - search-terms-report.csv
  - keyword-report.csv (Search keywords)
  - ad-report.csv (RSAs)
  - asset-report.csv (extensions)

Column headers are matched fuzzy (case-insensitive, whitespace-insensitive,
ignores trailing-period from "Avg. CPC", etc.).

Usage:
    python3 normalize_report.py --in-dir ./reports/ --out report.json
"""

from __future__ import annotations
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Column name fuzzing
# ---------------------------------------------------------------------------

def normalize_header(h: str) -> str:
    """Normalize a column header for fuzzy matching."""
    return re.sub(r"[^a-z0-9]+", "", h.lower().strip())


# Canonical metric names → list of possible UI column names
CANONICAL_COLUMNS = {
    "campaign":       ["campaign", "campaignname"],
    "ad_group":       ["adgroup", "adgroupname"],
    "keyword":        ["keyword", "keywordtext", "searchkeyword"],
    "match_type":     ["matchtype", "keywordmatchtype", "type"],
    "search_term":    ["searchterm", "searchterms"],
    "added_excluded": ["addedexcluded", "added/excluded"],
    "impressions":    ["impressions", "impr"],
    "clicks":         ["clicks"],
    "ctr":            ["ctr", "clickthroughrate"],
    "avg_cpc":        ["avgcpc", "averagecpc"],
    "cost":           ["cost", "spend"],
    "conversions":    ["conversions", "conv"],
    "cost_per_conv":  ["costperconv", "costconv", "costconversion", "costperconversion"],
    "conv_rate":      ["convrate", "conversionrate"],
    "conv_value":     ["convvalue", "conversionvalue", "allconvvalue"],
    "value_per_cost": ["valuepercost", "convvaluepercost", "roas"],
    "impr_share":     ["searchimprshare", "imprshare", "impressionshare"],
    "lost_is_budget": ["searchlostisbudget", "lostisbudget"],
    "lost_is_rank":   ["searchlostisrank", "lostisrank"],
    "top_is":         ["searchtopis", "topimprshare", "topis"],
    "abs_top_is":     ["searchabstopis", "absolutetopimprshare", "abstopis"],
    "quality_score":  ["qualityscore", "qs"],
    "exp_ctr":        ["expectedctr", "expctr"],
    "ad_relevance":   ["adrelevance"],
    "lp_experience":  ["landingpageexperience", "lpexperience"],
    "ad_strength":    ["adstrength"],
    "device":         ["device", "devicetype"],
}


def build_column_map(headers: list[str]) -> dict[str, int]:
    """Return {canonical_name: column_index} for headers present."""
    norm_to_idx = {normalize_header(h): i for i, h in enumerate(headers)}
    out = {}
    for canonical, candidates in CANONICAL_COLUMNS.items():
        for cand in candidates:
            if cand in norm_to_idx:
                out[canonical] = norm_to_idx[cand]
                break
    return out


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------

def to_float(v: str) -> Optional[float]:
    """Parse number from UI strings like '1,234.56', '5.20%', '$3.45', '< 10%'."""
    if v is None:
        return None
    s = str(v).strip()
    if not s or s in {"--", "-", "N/A"}:
        return None
    s = s.lstrip("<>").strip()
    s = s.replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    pct = s.endswith("%")
    if pct:
        s = s[:-1]
    try:
        v = float(s)
        if pct:
            v /= 100.0
        return v
    except ValueError:
        return None


def to_int(v: str) -> Optional[int]:
    f = to_float(v)
    return int(f) if f is not None else None


def to_str(v: str) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Report-type detection
# ---------------------------------------------------------------------------

def detect_report_type(col_map: dict[str, int], headers: list[str]) -> str:
    norm = {normalize_header(h) for h in headers}
    if "searchterm" in norm or "searchterms" in norm:
        return "search_terms"
    if "keyword" in norm or "keywordtext" in norm:
        if "adstrength" in norm:
            return "ad"
        return "keyword"
    if "adstrength" in norm:
        return "ad"
    if "adgroup" in norm and "campaign" in norm:
        # Distinguish ad-group from campaign by presence of ad_group column
        if "keyword" not in norm and "searchterm" not in norm and "adstrength" not in norm:
            return "ad_group"
        return "ad_group"
    if "campaign" in norm:
        return "campaign"
    return "unknown"


# ---------------------------------------------------------------------------
# Row → record
# ---------------------------------------------------------------------------

def coerce_row(row: list[str], col_map: dict[str, int]) -> dict[str, Any]:
    """Pull canonical fields from row using col_map."""
    rec: dict[str, Any] = {}
    for canon, idx in col_map.items():
        if idx >= len(row):
            continue
        raw = row[idx]
        # Choose a coercion based on canonical name
        if canon in {"campaign", "ad_group", "keyword", "match_type",
                     "search_term", "added_excluded", "quality_score",
                     "exp_ctr", "ad_relevance", "lp_experience",
                     "ad_strength", "device"}:
            # Some QS sub-component columns are "Above average"/"Below average"/numeric
            if canon == "quality_score":
                rec[canon] = to_int(raw) if to_int(raw) is not None else to_str(raw)
            else:
                rec[canon] = to_str(raw)
        elif canon in {"impressions", "clicks", "conversions"}:
            rec[canon] = to_int(raw)
        else:
            rec[canon] = to_float(raw)
    return rec


def load_csv(path: Path) -> tuple[str, list[dict]]:
    """Load one CSV, return (report_type, records)."""
    # Some Google Ads exports have a few preamble lines before the headers.
    # Find the first non-blank line that looks like a CSV header (≥3 columns
    # and at least one canonical word).
    raw_lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    canonical_words = {w for cands in CANONICAL_COLUMNS.values() for w in cands}
    canonical_word_re = re.compile(
        r"\b(" + "|".join(canonical_words) + r")\b", re.IGNORECASE
    )
    header_idx = 0
    for i, line in enumerate(raw_lines):
        if not line.strip():
            continue
        # Naive parse to count fields; reader will handle quotes properly.
        fields = next(csv.reader([line]))
        if len(fields) >= 3 and canonical_word_re.search(line):
            header_idx = i
            break

    body = "\n".join(raw_lines[header_idx:])
    rows = list(csv.reader(body.splitlines()))
    if not rows:
        return ("unknown", [])
    headers = rows[0]
    col_map = build_column_map(headers)
    rtype = detect_report_type(col_map, headers)
    records = []
    for row in rows[1:]:
        if not any(c.strip() for c in row):
            continue
        rec = coerce_row(row, col_map)
        # Skip "Total" / summary rows where Campaign is blank
        if not rec.get("campaign") and not rec.get("search_term"):
            continue
        records.append(rec)
    return (rtype, records)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Normalize Google Ads CSV reports.")
    p.add_argument("--in-dir", required=True, type=Path,
                   help="Directory containing CSV reports")
    p.add_argument("--out", required=True, type=Path, help="Output JSON")
    args = p.parse_args(argv)

    if not args.in_dir.exists() or not args.in_dir.is_dir():
        print(f"ERROR: {args.in_dir} is not a directory", file=sys.stderr)
        return 2

    bundle: dict[str, list[dict]] = {
        "campaign": [],
        "ad_group": [],
        "keyword": [],
        "search_terms": [],
        "ad": [],
        "unknown": [],
    }
    sources: dict[str, list[str]] = {k: [] for k in bundle}

    for csv_path in sorted(args.in_dir.glob("*.csv")):
        rtype, records = load_csv(csv_path)
        bundle.setdefault(rtype, []).extend(records)
        sources.setdefault(rtype, []).append(csv_path.name)
        print(f"  {csv_path.name}: detected as {rtype} ({len(records)} rows)")

    out = {
        "report_period": "last N days",  # caller sets explicit dates
        "bundle": bundle,
        "sources": sources,
    }
    args.out.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
