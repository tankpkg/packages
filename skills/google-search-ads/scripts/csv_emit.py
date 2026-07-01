#!/usr/bin/env python3
"""
csv_emit.py — Emit Google Ads Editor-compatible CSVs from campaign.json.

Produces one file per entity type (the "one entity type per file" rule from
references/02-csv-schema.md). All output is UTF-8 with English column headers.

Usage:
    python3 csv_emit.py --in campaign.json --out-dir ./out/
"""

from __future__ import annotations
import argparse
import csv
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Emit per-entity files
# ---------------------------------------------------------------------------

def emit_campaigns(campaign_doc: dict, out_dir: Path) -> Path:
    path = out_dir / "Campaigns.csv"
    headers = [
        "Campaign", "Campaign Type", "Campaign Status", "Budget", "Budget type",
        "Bid strategy type", "Target CPA", "Target ROAS",
        "Networks", "Language", "Start date", "End date", "Ad rotation",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in campaign_doc["campaigns"]:
            w.writerow([
                c["name"],
                c["type"],
                c["status"],
                c["daily_budget"],
                "Daily",
                c["bid_strategy"],
                c.get("target_cpa") or "",
                c.get("target_roas") or "",
                ";".join(c["networks"]),
                c["language"],
                c.get("start_date") or "",
                c.get("end_date") or "",
                c.get("ad_rotation", "Optimize"),
            ])
    return path


def emit_ad_groups(campaign_doc: dict, out_dir: Path) -> Path:
    path = out_dir / "AdGroups.csv"
    headers = ["Campaign", "Ad group", "Ad Group Status", "Max CPC"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in campaign_doc["campaigns"]:
            for g in c["ad_groups"]:
                w.writerow([
                    c["name"],
                    g["name"],
                    g["status"],
                    g.get("max_cpc") or "",
                ])
    return path


def emit_keywords(campaign_doc: dict, out_dir: Path) -> Path:
    """Positives only. Negatives go to NegativeKeywords.csv per Editor's rules."""
    path = out_dir / "Keywords.csv"
    headers = ["Campaign", "Ad group", "Keyword", "Criterion Type", "Status", "Max CPC"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in campaign_doc["campaigns"]:
            for g in c["ad_groups"]:
                for kw in g["keywords"]:
                    w.writerow([
                        c["name"],
                        g["name"],
                        kw["text"],
                        kw["match"],
                        "Enabled",
                        kw.get("max_cpc") or "",
                    ])
    return path


def emit_negatives(campaign_doc: dict, out_dir: Path) -> Path:
    path = out_dir / "NegativeKeywords.csv"
    headers = ["Campaign", "Ad group", "Keyword", "Criterion Type", "Status"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in campaign_doc["campaigns"]:
            # Campaign-level negatives
            for neg_text in c.get("campaign_negatives", []):
                w.writerow([c["name"], "", neg_text, "Negative Phrase", "Enabled"])
            # Ad-group-level negatives
            for g in c["ad_groups"]:
                for neg in g.get("negatives", []):
                    w.writerow([
                        c["name"],
                        g["name"],
                        neg["text"],
                        neg["match"],
                        "Enabled",
                    ])
        # Account-level negatives (Campaign blank, Ad group blank)
        for neg_text in campaign_doc.get("account_negatives", []):
            w.writerow(["", "", neg_text, "Negative Broad", "Enabled"])
    return path


def emit_rsas(campaign_doc: dict, out_dir: Path) -> Path:
    path = out_dir / "RSAs.csv"
    # 15 headlines + 15 pin positions + 4 descriptions + 4 pin positions
    h_cols = []
    for i in range(1, 16):
        h_cols += [f"Headline {i}", f"Headline {i} position"]
    d_cols = []
    for i in range(1, 5):
        d_cols += [f"Description {i}", f"Description {i} position"]
    headers = [
        "Campaign", "Ad group", "Ad type", "Status",
        "Final URL", "Path 1", "Path 2",
    ] + h_cols + d_cols
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in campaign_doc["campaigns"]:
            for g in c["ad_groups"]:
                rsa = g.get("rsa") or {}
                row = [
                    c["name"],
                    g["name"],
                    "Responsive search ad",
                    "Enabled",
                    rsa.get("final_url", ""),
                    rsa.get("path1", ""),
                    rsa.get("path2", ""),
                ]
                hs = rsa.get("headlines", [])
                for i in range(15):
                    if i < len(hs):
                        row.append(hs[i].get("text", ""))
                        row.append(hs[i].get("pin") if hs[i].get("pin") is not None else "")
                    else:
                        row.append("")
                        row.append("")
                ds = rsa.get("descriptions", [])
                for i in range(4):
                    if i < len(ds):
                        row.append(ds[i].get("text", ""))
                        row.append(ds[i].get("pin") if ds[i].get("pin") is not None else "")
                    else:
                        row.append("")
                        row.append("")
                w.writerow(row)
    return path


def emit_locations(campaign_doc: dict, out_dir: Path) -> Path:
    path = out_dir / "Locations.csv"
    headers = ["Campaign", "Ad group", "Location ID", "Action"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for c in campaign_doc["campaigns"]:
            for gid in campaign_doc["meta"].get("geo", []):
                w.writerow([c["name"], "", gid, "Add"])
    return path


def emit_sitelinks(campaign_doc: dict, out_dir: Path) -> Path | None:
    rows = []
    for c in campaign_doc["campaigns"]:
        for g in c["ad_groups"]:
            for sl in (g.get("assets", {}) or {}).get("sitelinks", []) or []:
                rows.append([c["name"], g["name"], sl.get("text", ""),
                            sl.get("description1", ""), sl.get("description2", ""),
                            sl.get("final_url", "")])
    if not rows:
        return None
    path = out_dir / "Sitelinks.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Campaign", "Ad group", "Sitelink text", "Description 1", "Description 2", "Final URL"])
        w.writerows(rows)
    return path


def emit_callouts(campaign_doc: dict, out_dir: Path) -> Path | None:
    rows = []
    for c in campaign_doc["campaigns"]:
        for g in c["ad_groups"]:
            for co in (g.get("assets", {}) or {}).get("callouts", []) or []:
                if co:  # skip None/empty
                    rows.append([c["name"], g["name"], co])
    if not rows:
        return None
    path = out_dir / "Callouts.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Campaign", "Ad group", "Callout text"])
        w.writerows(rows)
    return path


def emit_structured_snippets(campaign_doc: dict, out_dir: Path) -> Path | None:
    rows = []
    for c in campaign_doc["campaigns"]:
        for g in c["ad_groups"]:
            for ss in (g.get("assets", {}) or {}).get("structured_snippets", []) or []:
                values = ";".join(ss.get("values", []))
                if ss.get("header") and values:
                    rows.append([c["name"], g["name"], ss["header"], values])
    if not rows:
        return None
    path = out_dir / "StructuredSnippets.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Campaign", "Ad group", "Header", "Values"])
        w.writerows(rows)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def emit_all(campaign_doc: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    written.append(emit_campaigns(campaign_doc, out_dir))
    written.append(emit_ad_groups(campaign_doc, out_dir))
    written.append(emit_keywords(campaign_doc, out_dir))
    written.append(emit_negatives(campaign_doc, out_dir))
    written.append(emit_rsas(campaign_doc, out_dir))
    written.append(emit_locations(campaign_doc, out_dir))
    for fn in (emit_sitelinks, emit_callouts, emit_structured_snippets):
        p = fn(campaign_doc, out_dir)
        if p:
            written.append(p)
    return written


def main(argv=None):
    p = argparse.ArgumentParser(description="Emit Google Ads Editor CSVs from campaign.json.")
    p.add_argument("--in", dest="inp", required=True, type=Path, help="campaign.json input")
    p.add_argument("--out-dir", required=True, type=Path, help="Output directory")
    args = p.parse_args(argv)

    if not args.inp.exists():
        print(f"ERROR: input not found: {args.inp}", file=sys.stderr)
        return 2
    doc = json.loads(args.inp.read_text())

    files = emit_all(doc, args.out_dir)
    for fp in files:
        print(f"wrote {fp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
