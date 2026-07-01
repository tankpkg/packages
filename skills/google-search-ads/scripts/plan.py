#!/usr/bin/env python3
"""
plan.py — Generate campaign.json from a structured business brief.

Takes a brief.json (filled by the user via the prompt template) and emits
a campaign.json conforming to the schema in references/02-csv-schema.md.

Usage:
    python3 plan.py --brief brief.json --out campaign.json
    python3 plan.py --brief brief.json --out campaign.json --geo-csv ../assets/geo-targets-seed.csv
"""

from __future__ import annotations
import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Brief schema (what the user fills in via the prompt template)
# ---------------------------------------------------------------------------
#
# {
#   "business_name": "Acme Plumbing",
#   "one_line_description": "24/7 emergency plumbing in San Francisco",
#   "ideal_customer": "Homeowners with urgent plumbing problems",
#   "usp_elements": {
#       "buyer": null,
#       "what": "Licensed master plumbers, not subcontractors",
#       "angle": "Average response time 32 minutes",
#       "what_not": "We don't do new construction; emergencies only",
#       "time": "On-site within 60 minutes guaranteed",
#       "guarantee": "Fixed first time or it's free"
#   },
#   "primary_conversion": "Phone call OR online booking",
#   "customer_value": 350.00,            // per-customer lifetime or per-sale
#   "geo_targets": ["San Francisco, CA"],
#   "monthly_budget": 1500.00,
#   "currently_running_ads": false,
#   "competitors_bid_on_brand": false,
#   "competitors": [
#       {"name": "Roto-Rooter", "site": "https://rotorooter.com"},
#       {"name": "Mike Diamond", "site": "https://mikediamondservices.com"}
#   ],
#   "device_focus": "both",              // desktop | mobile | both
#   "vertical": "home_services",
#   "language": "en",
#   "currency": "USD"
# }


BID_STRATEGY_BY_CONV_VOLUME = [
    (0,    "Manual CPC"),
    (50,   "Enhanced CPC"),
    (100,  "Target CPA"),
]


def load_geo_seed(geo_csv_path: Path) -> dict[str, str]:
    """Return {lowercased_name: id} lookup from the seed CSV."""
    lookup = {}
    with open(geo_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["Criterion ID"].strip()
            for key in (row["Name"], row["Canonical Name"]):
                lookup[key.strip().lower()] = cid
    return lookup


def resolve_geo(geo_string: str, lookup: dict[str, str]) -> Optional[str]:
    """Resolve a freeform geo string to a numeric Geo Target ID."""
    s = geo_string.strip().lower()
    if s.isdigit():
        return s  # already an ID
    if s in lookup:
        return lookup[s]
    # Try prefix match (e.g. "San Francisco, CA" -> "san francisco, ca, united states")
    for k, v in lookup.items():
        if k.startswith(s):
            return v
    # Try comma-stripping
    s_nocomma = re.sub(r",.*$", "", s).strip()
    if s_nocomma in lookup:
        return lookup[s_nocomma]
    return None


def slugify(s: str, maxlen: int = 15) -> str:
    """For Path1/Path2 — alphanumeric + hyphen, ≤ maxlen chars."""
    out = re.sub(r"[^a-zA-Z0-9-]+", "-", s).strip("-").lower()
    return out[:maxlen]


def truncate(s: str, maxlen: int) -> str:
    # Use plain ASCII ellipsis (3 dots) instead of U+2026 to avoid
    # NFKC normalization differences across systems.
    if len(s) <= maxlen:
        return s
    if maxlen < 4:
        return s[:maxlen]
    return s[:maxlen - 3].rstrip() + "..."


def headline(s: str) -> str:
    return truncate(s, 30)


def description(s: str) -> str:
    return truncate(s, 90)


def pick_bid_strategy(currently_running: bool, monthly_conversions: int = 0) -> str:
    for threshold, strat in reversed(BID_STRATEGY_BY_CONV_VOLUME):
        if monthly_conversions >= threshold:
            return strat
    return "Manual CPC"


# ---------------------------------------------------------------------------
# Keyword generation — HOT/WARM/COLD per McDonald §3
# ---------------------------------------------------------------------------

DEFAULT_NEGATIVES = [
    "free", "cheap", "diy", "do it yourself",
    "course", "class", "tutorial", "training",
    "jobs", "job", "salary", "career", "internship",
    "wikipedia", "wiki", "meaning", "definition", "synonym",
    "youtube", "reddit", "amazon", "ebay",
]


def generate_keywords(business_name: str, services: list[str], geos: list[str]) -> list[dict]:
    """
    For each service, generate HOT/WARM/COLD keyword candidates.
    Returns a list of {text, match, tag} dicts.
    """
    out = []
    helpers_hot = ["near me", "best", "top rated", "licensed", "emergency", "24/7", "same day"]
    helpers_warm = ["company", "service", "services"]

    for svc in services:
        svc_l = svc.lower().strip()
        # WARM: bare service
        out.append({"text": f'"{svc_l}"', "match": "Phrase", "tag": "WARM"})
        out.append({"text": f"[{svc_l}]", "match": "Exact", "tag": "WARM"})

        # HOT: service + helper word
        for h in helpers_hot:
            out.append({"text": f'[{h} {svc_l}]', "match": "Exact", "tag": "HOT"})
            out.append({"text": f'"{svc_l} {h}"', "match": "Phrase", "tag": "HOT"})

        # HOT: service + geo
        for g in geos:
            g_short = re.sub(r",.*$", "", g).strip().lower()
            out.append({"text": f"[{svc_l} {g_short}]", "match": "Exact", "tag": "HOT"})
            out.append({"text": f'"{svc_l} {g_short}"', "match": "Phrase", "tag": "HOT"})

    # De-duplicate
    seen = set()
    deduped = []
    for kw in out:
        key = (kw["text"], kw["match"])
        if key not in seen:
            seen.add(key)
            deduped.append(kw)
    return deduped


# ---------------------------------------------------------------------------
# RSA generation — Marshall Ch 10 + McDonald §5
# ---------------------------------------------------------------------------

def generate_rsa(business: str, theme: str, usp: dict, geo_short: str, final_url: str) -> dict:
    """Generate one RSA per ad-group theme."""
    headlines = []

    # Headline 1: USP / primary keyword, pinned to position 1
    h1 = headline(f"{theme.title()} in {geo_short}".strip())
    headlines.append({"text": h1, "pin": 1})

    # Headline 2: angle from USP
    if usp.get("angle"):
        headlines.append({"text": headline(usp["angle"]), "pin": None})

    # Headline 3: strong CTA
    headlines.append({"text": headline("Get a Free Quote Today"), "pin": None})

    # Headline 4: time guarantee if present
    if usp.get("time"):
        headlines.append({"text": headline(usp["time"]), "pin": None})

    # Headline 5: what
    if usp.get("what"):
        headlines.append({"text": headline(usp["what"]), "pin": None})

    # Headline 6: guarantee
    if usp.get("guarantee"):
        headlines.append({"text": headline(usp["guarantee"]), "pin": None})

    # Headline 7: business name
    headlines.append({"text": headline(business), "pin": None})

    # Pad to ≥3 (we already have ≥3, but defensive)
    if len(headlines) < 3:
        for filler in ["Trusted Local Experts", "Fast Friendly Service", "Call Now"]:
            headlines.append({"text": headline(filler), "pin": None})

    headlines = headlines[:15]

    descriptions = []
    # Description 1: expand USP - promise + proof
    parts = [usp.get("angle"), usp.get("guarantee")]
    d1 = ". ".join(p for p in parts if p) or f"{business} — trusted local experts."
    descriptions.append({"text": description(d1), "pin": 1})

    # Description 2: CTA + path of least resistance
    d2 = f"Free quote in 60 seconds. Licensed pros standing by. Call or book online today."
    descriptions.append({"text": description(d2), "pin": None})

    # Description 3: time / urgency
    if usp.get("time"):
        descriptions.append({"text": description(f"{usp['time']} or it's free."), "pin": None})

    # Description 4: logical proof
    descriptions.append({"text": description("Hundreds of 5-star reviews from local customers."), "pin": None})

    descriptions = descriptions[:4]

    return {
        "final_url": final_url,
        "path1": slugify(theme),
        "path2": slugify(geo_short) if geo_short else "",
        "headlines": headlines,
        "descriptions": descriptions,
    }


# ---------------------------------------------------------------------------
# Main planner
# ---------------------------------------------------------------------------

def plan(brief: dict, geo_lookup: dict[str, str]) -> dict:
    business = brief["business_name"]
    geos_raw = brief.get("geo_targets", [])
    geo_ids = []
    geo_unresolved = []
    for g in geos_raw:
        gid = resolve_geo(g, geo_lookup)
        if gid:
            geo_ids.append(gid)
        else:
            geo_unresolved.append(g)

    # Daily budget = monthly / 30.4
    daily = round(brief["monthly_budget"] / 30.4, 2)

    # Bid strategy: brand new accounts → Manual CPC
    strat = pick_bid_strategy(brief.get("currently_running_ads", False), 0)

    usp = brief.get("usp_elements", {})

    # Service inference from one_line_description
    services_raw = brief.get("services") or [brief["one_line_description"].split(" in ")[0]]
    services = [s.strip() for s in services_raw if s.strip()]

    # Theme primary geo (short form for ad copy)
    geo_short = re.sub(r",.*$", "", geos_raw[0]).strip() if geos_raw else ""

    # Build account negatives
    account_negatives = list(DEFAULT_NEGATIVES)
    # Add competitor names as negatives in non-brand campaigns (passed below)
    competitor_negatives = [c["name"] for c in brief.get("competitors", [])]

    # Build campaigns ---------------------------------------------------------
    campaigns: list[dict] = []
    placeholder_url = brief.get("landing_page_base", "https://example.com").rstrip("/")

    # 1. Brand campaign (always, even if competitors_bid_on_brand=false — cheap insurance)
    brand_keywords = [
        {"text": f"[{business.lower()}]", "match": "Exact", "tag": "HOT"},
        {"text": f'"{business.lower()}"', "match": "Phrase", "tag": "HOT"},
    ]
    brand_campaign = {
        "name": f"{business} — Brand — Search",
        "type": "Search",
        "subtype": "Standard",
        "status": "Paused",
        "daily_budget": round(daily * 0.05, 2) or 1.00,  # ~5% of total per Marshall Ch 12
        "bid_strategy": strat,
        "target_cpa": None,
        "target_roas": None,
        "max_cpc_ceiling": None,
        "networks": ["Google search"],
        "language": brief.get("language", "en"),
        "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "end_date": None,
        "ad_rotation": "Optimize",
        "campaign_negatives": [],
        "ad_groups": [
            {
                "name": f"{business} - Brand",
                "status": "Enabled",
                "max_cpc": 2.00,
                "keywords": brand_keywords,
                "negatives": [],
                "rsa": generate_rsa(business, business, usp, geo_short, placeholder_url),
                "assets": {
                    "sitelinks": [],
                    "callouts": [usp.get("guarantee"), usp.get("time"), "Free Quote", "Licensed Pros"],
                    "structured_snippets": [],
                    "call_extension": None,
                    "location_extension": False,
                    "price_extensions": [],
                },
            }
        ],
    }
    campaigns.append(brand_campaign)

    # 2. Non-brand campaign — primary revenue driver
    non_brand_daily = round(daily - brand_campaign["daily_budget"], 2)
    keywords_all = generate_keywords(business, services, geos_raw or [""])
    # Group keywords by service for ad-group themes
    ad_groups = []
    for svc in services:
        svc_kw = [k for k in keywords_all if svc.lower() in k["text"].lower()]
        if not svc_kw:
            continue
        # Cap at 20 keywords per ad group (Hagakure soft limit)
        svc_kw = svc_kw[:20]
        ad_groups.append({
            "name": f"{svc.title()} — {geo_short}".strip(" —"),
            "status": "Enabled",
            "max_cpc": 4.00,  # placeholder; user adjusts after Keyword Planner check
            "keywords": svc_kw,
            "negatives": [
                {"text": neg, "match": "Negative Broad"} for neg in DEFAULT_NEGATIVES[:5]
            ] + [
                {"text": comp.lower(), "match": "Negative Phrase"} for comp in competitor_negatives
            ],
            "rsa": generate_rsa(business, svc, usp, geo_short, placeholder_url),
            "assets": {
                "sitelinks": [],
                "callouts": [
                    usp.get("guarantee"),
                    usp.get("time"),
                    "Licensed & Insured",
                    "Free Estimates",
                ],
                "structured_snippets": [
                    {"header": "Services", "values": services[:5]}
                ],
                "call_extension": None,
                "location_extension": True,
                "price_extensions": [],
            },
        })

    if ad_groups:
        non_brand_campaign = {
            "name": f"{business} — Non-Brand — Search — {geo_short or 'All'}",
            "type": "Search",
            "subtype": "Standard",
            "status": "Paused",
            "daily_budget": non_brand_daily,
            "bid_strategy": strat,
            "target_cpa": None,
            "target_roas": None,
            "max_cpc_ceiling": None,
            "networks": ["Google search"],
            "language": brief.get("language", "en"),
            "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "end_date": None,
            "ad_rotation": "Optimize",
            "campaign_negatives": [c.lower() for c in competitor_negatives],
            "ad_groups": ad_groups,
        }
        campaigns.append(non_brand_campaign)

    # 3. Competitor campaign — only if explicitly requested
    if brief.get("competitors") and brief.get("run_competitor_campaign", False):
        comp_kws = []
        for comp in brief["competitors"]:
            cn = comp["name"].lower()
            comp_kws.append({"text": f"[{cn}]", "match": "Exact", "tag": "HOT"})
            comp_kws.append({"text": f'"{cn}"', "match": "Phrase", "tag": "WARM"})
        comp_campaign = {
            "name": f"{business} — Competitor — Search",
            "type": "Search",
            "subtype": "Standard",
            "status": "Paused",
            "daily_budget": round(daily * 0.10, 2),  # ~10%
            "bid_strategy": "Manual CPC",
            "target_cpa": None,
            "target_roas": None,
            "max_cpc_ceiling": None,
            "networks": ["Google search"],
            "language": brief.get("language", "en"),
            "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "end_date": None,
            "ad_rotation": "Optimize",
            "campaign_negatives": [],
            "ad_groups": [
                {
                    "name": "Competitor Brands",
                    "status": "Enabled",
                    "max_cpc": 3.00,
                    "keywords": comp_kws,
                    "negatives": [],
                    "rsa": generate_rsa(business, "alternative", usp, geo_short, placeholder_url),
                    "assets": {
                        "sitelinks": [],
                        "callouts": [usp.get("angle"), "Trusted Alternative", "5-Star Reviews", "Free Quote"],
                        "structured_snippets": [],
                        "call_extension": None,
                        "location_extension": False,
                        "price_extensions": [],
                    },
                }
            ],
        }
        campaigns.append(comp_campaign)

    out = {
        "version": "1.0.0",
        "meta": {
            "business": business,
            "geo": geo_ids,
            "geo_unresolved": geo_unresolved,
            "currency": brief.get("currency", "USD"),
            "language": brief.get("language", "en"),
            "vertical": brief.get("vertical", "default"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "monthly_budget": brief["monthly_budget"],
            "daily_budget_total": daily,
        },
        "account_negatives": account_negatives,
        "campaigns": campaigns,
    }

    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Generate campaign.json from a brief.")
    p.add_argument("--brief", required=True, type=Path, help="Path to brief.json")
    p.add_argument("--out", required=True, type=Path, help="Output campaign.json")
    p.add_argument("--geo-csv", type=Path,
                   default=Path(__file__).resolve().parent.parent / "assets" / "geo-targets-seed.csv",
                   help="Geo seed CSV")
    args = p.parse_args(argv)

    if not args.brief.exists():
        print(f"ERROR: brief not found: {args.brief}", file=sys.stderr)
        return 2
    if not args.geo_csv.exists():
        print(f"ERROR: geo seed CSV not found: {args.geo_csv}", file=sys.stderr)
        return 2

    brief = json.loads(args.brief.read_text())
    geo_lookup = load_geo_seed(args.geo_csv)
    campaign = plan(brief, geo_lookup)

    args.out.write_text(json.dumps(campaign, indent=2))
    print(f"wrote {args.out}")
    if campaign["meta"].get("geo_unresolved"):
        print(f"WARN: {len(campaign['meta']['geo_unresolved'])} geo target(s) could not be resolved.",
              file=sys.stderr)
        for g in campaign["meta"]["geo_unresolved"]:
            print(f"  - {g!r}: look up the numeric ID at "
                  f"https://developers.google.com/google-ads/api/data/geotargets",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
