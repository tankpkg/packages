#!/usr/bin/env python3
"""
revise.py — Apply auto-fixable findings to campaign.json, emit campaign_v{N+1}.json
plus a DIFF.md showing the before/after.

Reads:  campaign.json + findings.json
Writes: campaign_v{N+1}.json + DIFF.md

The user supplies an `--apply` flag listing which mutation kinds to apply
(or `--apply all` for every auto_fixable=true finding). Defaults to "all".

Usage:
    python3 revise.py --campaign campaign.json --findings findings.json \
                      --apply all --out campaign_v2.json --diff DIFF.md
"""

from __future__ import annotations
import argparse
import copy
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Mutation handlers
# ---------------------------------------------------------------------------

def find_campaign(doc: dict, name: str) -> dict | None:
    for c in doc.get("campaigns", []):
        if c.get("name") == name:
            return c
    return None


def find_ad_group(doc: dict, campaign_name: str, ag_name: str) -> dict | None:
    c = find_campaign(doc, campaign_name)
    if not c:
        return None
    for g in c.get("ad_groups", []):
        if g.get("name") == ag_name:
            return g
    return None


def mut_add_negative(doc: dict, m: dict) -> str:
    """Add a negative keyword at the ad-group, campaign, or account level."""
    text = m["text"]
    match = m.get("match", "Negative Exact")
    c_name = m.get("campaign")
    g_name = m.get("ad_group")

    if c_name and g_name:
        g = find_ad_group(doc, c_name, g_name)
        if g is None:
            return f"skipped: ad group {c_name!r}>{g_name!r} not found"
        # Dedupe
        for n in g.setdefault("negatives", []):
            if n["text"].lower() == text.lower() and n["match"] == match:
                return f"skipped: negative {text!r} already exists"
        g["negatives"].append({"text": text, "match": match})
        return f"added negative {text!r} ({match}) to {c_name}>{g_name}"

    if c_name and not g_name:
        c = find_campaign(doc, c_name)
        if c is None:
            return f"skipped: campaign {c_name!r} not found"
        existing = [n.lower() for n in c.setdefault("campaign_negatives", [])]
        if text.lower() in existing:
            return f"skipped: campaign negative {text!r} already exists"
        c["campaign_negatives"].append(text)
        return f"added campaign negative {text!r} to {c_name}"

    # Account-level
    existing = [n.lower() for n in doc.setdefault("account_negatives", [])]
    if text.lower() in existing:
        return f"skipped: account negative {text!r} already exists"
    doc["account_negatives"].append(text)
    return f"added account-level negative {text!r}"


def mut_add_keyword(doc: dict, m: dict) -> str:
    g = find_ad_group(doc, m["campaign"], m["ad_group"])
    if g is None:
        return f"skipped: ad group {m['campaign']!r}>{m['ad_group']!r} not found"
    new_text = m["text"]
    for kw in g.get("keywords", []):
        if kw["text"].lower() == new_text.lower():
            return f"skipped: keyword {new_text!r} already exists"
    g.setdefault("keywords", []).append({
        "text": new_text,
        "match": m.get("match", "Exact"),
        "tag": m.get("tag", "HOT"),
        "max_cpc": None,
    })
    return f"added keyword {new_text!r} ({m.get('match')}) to {m['campaign']}>{m['ad_group']}"


def mut_raise_max_cpc(doc: dict, m: dict) -> str:
    c = find_campaign(doc, m["campaign"])
    if c is None:
        return f"skipped: campaign {m['campaign']!r} not found"
    factor = m.get("factor", 1.20)
    # Cap to +50% per cycle
    factor = min(factor, 1.50)
    scope = m.get("scope", "top_cvr_keywords")
    changed = 0
    for g in c.get("ad_groups", []):
        if g.get("max_cpc"):
            old = g["max_cpc"]
            g["max_cpc"] = round(old * factor, 2)
            changed += 1
    return f"raised max_cpc on {changed} ad groups in {m['campaign']} by ×{factor}"


def mut_bid_adjust(doc: dict, m: dict) -> str:
    """Apply device-level bid adjustment metadata to all campaigns or to one."""
    pct = m["pct"]
    device = m.get("device", "mobile")
    if m.get("scope") == "account":
        targets = doc.get("campaigns", [])
    else:
        c = find_campaign(doc, m.get("campaign", ""))
        if c is None:
            return f"skipped: campaign {m.get('campaign')!r} not found"
        targets = [c]
    for c in targets:
        c.setdefault("bid_adjustments", {})[device] = pct
    return f"applied {device} bid adjustment {pct:+.0%} to {len(targets)} campaign(s)"


def mut_unpin_non_brand(doc: dict, m: dict) -> str:
    """Unpin all headlines whose text does not contain the business name."""
    business = doc.get("meta", {}).get("business", "").lower()
    g = find_ad_group(doc, m["campaign"], m["ad_group"])
    if g is None:
        return f"skipped: ad group {m['campaign']!r}>{m['ad_group']!r} not found"
    rsa = g.get("rsa", {})
    unpinned = 0
    for h in rsa.get("headlines", []):
        if h.get("pin") is not None and business and business not in h.get("text", "").lower():
            h["pin"] = None
            unpinned += 1
    return f"unpinned {unpinned} non-brand headlines in {m['campaign']}>{m['ad_group']}"


MUTATIONS = {
    "add_negative": mut_add_negative,
    "add_keyword":  mut_add_keyword,
    "raise_max_cpc": mut_raise_max_cpc,
    "bid_adjust":   mut_bid_adjust,
    "unpin_non_brand": mut_unpin_non_brand,
}


# ---------------------------------------------------------------------------
# Versioning + diff
# ---------------------------------------------------------------------------

def next_version(campaign_path: Path) -> Path:
    """Pick the next campaign_v{N}.json filename next to campaign.json."""
    parent = campaign_path.parent
    pat = re.compile(r"^campaign_v(\d+)\.json$")
    highest = 0
    for f in parent.iterdir():
        m = pat.match(f.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return parent / f"campaign_v{highest + 1}.json"


def render_diff(before: dict, after: dict, applied: list[str]) -> str:
    """Produce a markdown DIFF.md."""
    before_s = json.dumps(before, indent=2, sort_keys=True).splitlines()
    after_s = json.dumps(after, indent=2, sort_keys=True).splitlines()
    diff = difflib.unified_diff(before_s, after_s, lineterm="", n=3,
                                 fromfile="campaign.json (before)",
                                 tofile="campaign.json (after)")
    out = ["# DIFF — campaign.json changes\n",
           f"## Applied {len(applied)} mutation(s)\n"]
    for a in applied:
        out.append(f"- {a}")
    out.append("\n## Unified diff\n")
    out.append("```diff")
    out.extend(diff)
    out.append("```")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Apply findings to campaign.json.")
    p.add_argument("--campaign", required=True, type=Path)
    p.add_argument("--findings", required=True, type=Path)
    p.add_argument("--apply", default="all",
                   help="Mutation kinds to apply (csv) or 'all'. "
                        "E.g. add_negative,add_keyword")
    p.add_argument("--out", type=Path, default=None,
                   help="Output campaign_vN.json (default: auto-numbered)")
    p.add_argument("--diff", type=Path, default=None,
                   help="DIFF.md output path")
    p.add_argument("--dry-run", action="store_true",
                   help="Print plan without writing files")
    args = p.parse_args(argv)

    if not args.campaign.exists() or not args.findings.exists():
        print("ERROR: input file missing", file=sys.stderr)
        return 2

    doc = json.loads(args.campaign.read_text())
    findings = json.loads(args.findings.read_text())

    # Filter to auto_fixable + chosen kinds
    if args.apply == "all":
        allowed = set(MUTATIONS.keys())
    else:
        allowed = {k.strip() for k in args.apply.split(",") if k.strip()}

    applied: list[str] = []
    before = copy.deepcopy(doc)

    for f in findings:
        if not f.get("auto_fixable"):
            continue
        m = f.get("mutation")
        if not m:
            continue
        kind = m.get("kind")
        if kind not in allowed:
            continue
        handler = MUTATIONS.get(kind)
        if not handler:
            applied.append(f"unknown mutation kind: {kind}")
            continue
        result = handler(doc, m)
        applied.append(f"[{f['severity']}] {f['rule']}: {result}")

    if args.dry_run:
        print(f"would apply {len(applied)} mutations:")
        for a in applied:
            print(f"  - {a}")
        return 0

    out_path = args.out or next_version(args.campaign)
    out_path.write_text(json.dumps(doc, indent=2))
    print(f"wrote {out_path}")

    diff_path = args.diff or out_path.with_name("DIFF.md")
    diff_text = render_diff(before, doc, applied)
    diff_path.write_text(diff_text)
    print(f"wrote {diff_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
