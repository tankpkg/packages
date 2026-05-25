#!/usr/bin/env python3
"""
diagnose.py — Diagnose performance issues from a normalized report.

Implements the rules in references/03-diagnose-playbook.md.

Each rule emits a Finding with severity, confidence, recommendation,
auto_fixable flag, and (when applicable) a structured mutation suggestion
that revise.py can consume.

Usage:
    python3 diagnose.py --report report.json --campaign campaign.json \
        --benchmarks ../assets/benchmarks.json --out findings.json
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Severity weights
# ---------------------------------------------------------------------------

SEVERITY_WEIGHT = {"critical": 10, "high": 5, "medium": 2, "low": 1}


def confidence_from_sample(clicks: float, impressions: float) -> float:
    """Crude confidence proxy: more data → higher confidence (0..1)."""
    if clicks is None and impressions is None:
        return 0.3
    c = clicks or 0
    i = impressions or 0
    score = 0.0
    if c >= 100:
        score += 0.5
    elif c >= 30:
        score += 0.3
    elif c >= 10:
        score += 0.15
    if i >= 5000:
        score += 0.5
    elif i >= 1000:
        score += 0.3
    elif i >= 200:
        score += 0.15
    return min(1.0, score)


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------

def make_finding(severity, rule, target, message, recommendation,
                 auto_fixable=False, mutation=None,
                 confidence=0.5, evidence=None):
    return {
        "severity": severity,
        "rule": rule,
        "target": target,
        "message": message,
        "recommendation": recommendation,
        "auto_fixable": auto_fixable,
        "mutation": mutation,                # consumed by revise.py
        "confidence": round(confidence, 2),
        "score": SEVERITY_WEIGHT[severity] * round(confidence, 2),
        "evidence": evidence or {},
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe(d, key, default=0):
    v = d.get(key)
    return v if isinstance(v, (int, float)) else default


def index_keywords(campaign_doc: dict) -> set[str]:
    """All positive keyword phrases (normalized lower) across the doc."""
    out = set()
    for c in campaign_doc.get("campaigns", []):
        for g in c["ad_groups"]:
            for kw in g.get("keywords", []):
                t = kw.get("text", "").lower().strip("[]\"")
                if t:
                    out.add(t)
    return out


# ---------------------------------------------------------------------------
# Rule implementations
# ---------------------------------------------------------------------------

def rule_search_term_burn(bundle: dict, _doc: dict, _bench: dict):
    """Search terms with high clicks and 0 conversions → make negative."""
    for st in bundle.get("search_terms", []):
        clicks = safe(st, "clicks")
        conv = safe(st, "conversions")
        term = st.get("search_term") or ""
        if clicks >= 10 and conv == 0 and term:
            yield make_finding(
                "critical", "search_term_burn",
                target=f"{st.get('campaign','?')}>{st.get('ad_group','?')}>{term!r}",
                message=f"Search term '{term}' has {clicks} clicks and 0 conversions.",
                recommendation=f"Add '{term}' as a Negative Exact keyword.",
                auto_fixable=True,
                mutation={
                    "kind": "add_negative",
                    "campaign": st.get("campaign"),
                    "ad_group": st.get("ad_group"),
                    "text": term,
                    "match": "Negative Exact",
                },
                confidence=confidence_from_sample(clicks, st.get("impressions")),
                evidence={"clicks": clicks, "conversions": conv, "cost": safe(st, "cost")},
            )


def rule_missed_opportunity(bundle: dict, doc: dict, _bench: dict):
    """Search term with ≥5 conversions but not a keyword → promote."""
    existing = index_keywords(doc)
    for st in bundle.get("search_terms", []):
        conv = safe(st, "conversions")
        term = (st.get("search_term") or "").lower()
        if not term:
            continue
        if conv >= 5 and term not in existing:
            yield make_finding(
                "critical", "missed_opportunity",
                target=f"{st.get('campaign','?')}>{st.get('ad_group','?')}>{term!r}",
                message=f"Search term '{term}' has {conv} conversions but is not a keyword.",
                recommendation=f"Promote '{term}' to Exact keyword in best-matching ad group.",
                auto_fixable=True,
                mutation={
                    "kind": "add_keyword",
                    "campaign": st.get("campaign"),
                    "ad_group": st.get("ad_group"),
                    "text": f"[{term}]",
                    "match": "Exact",
                    "tag": "HOT",
                },
                confidence=confidence_from_sample(safe(st, "clicks"), safe(st, "impressions")),
                evidence={"conversions": conv, "clicks": safe(st, "clicks")},
            )


def rule_conversion_tracking_break(bundle: dict, _doc: dict, _bench: dict):
    """Many clicks, zero conversions account-wide → tracking probably broken."""
    total_clicks = sum(safe(r, "clicks") for r in bundle.get("campaign", []))
    total_conv = sum(safe(r, "conversions") for r in bundle.get("campaign", []))
    if total_clicks >= 500 and total_conv == 0:
        yield make_finding(
            "critical", "conversion_tracking_break",
            target="account",
            message=f"{total_clicks} clicks across all campaigns but 0 conversions.",
            recommendation="Verify conversion tracking is firing. Compare to CRM/Stripe receipts.",
            auto_fixable=False,
            confidence=0.95,
            evidence={"total_clicks": total_clicks, "total_conversions": total_conv},
        )


def rule_lost_is_budget(bundle: dict, _doc: dict, _bench: dict):
    for c in bundle.get("campaign", []):
        lis = safe(c, "lost_is_budget")
        if lis is None:
            continue
        if lis > 0.30:
            yield make_finding(
                "high", "lost_is_budget",
                target=f"campaign:{c.get('campaign')}",
                message=f"Search lost IS (budget) = {lis:.0%}. Campaign is budget-capped.",
                recommendation="Raise daily budget OR pause low-CVR keywords to free room.",
                auto_fixable=False,  # propose only; user decides budget
                confidence=confidence_from_sample(safe(c, "clicks"), safe(c, "impressions")),
                evidence={"lost_is_budget": lis},
            )


def rule_lost_is_rank(bundle: dict, _doc: dict, _bench: dict):
    for c in bundle.get("campaign", []):
        lir = safe(c, "lost_is_rank")
        if lir is None:
            continue
        if lir > 0.30:
            yield make_finding(
                "high", "lost_is_rank",
                target=f"campaign:{c.get('campaign')}",
                message=f"Search lost IS (rank) = {lir:.0%}. Bidding too low or QS issue.",
                recommendation="Raise Max CPC on top-CVR keywords by ~20%, inspect QS sub-components.",
                auto_fixable=True,
                mutation={
                    "kind": "raise_max_cpc",
                    "campaign": c.get("campaign"),
                    "factor": 1.20,
                    "scope": "top_cvr_keywords",
                },
                confidence=confidence_from_sample(safe(c, "clicks"), safe(c, "impressions")),
                evidence={"lost_is_rank": lir},
            )


def rule_sub_benchmark_ctr(bundle: dict, _doc: dict, bench: dict):
    bench_ctr = bench.get("ctr", 0.06)
    threshold = bench_ctr * 0.7
    for g in bundle.get("ad_group", []):
        ctr = safe(g, "ctr")
        impr = safe(g, "impressions")
        if impr < 500 or ctr is None:
            continue
        if ctr < threshold:
            yield make_finding(
                "high", "sub_benchmark_ctr",
                target=f"{g.get('campaign')}>{g.get('ad_group')}",
                message=f"Ad-group CTR {ctr:.1%} below benchmark × 0.7 ({threshold:.1%}).",
                recommendation="Rewrite RSA headlines using rising-query language from STR; "
                               "consider tightening ad-group theme.",
                auto_fixable=False,
                confidence=confidence_from_sample(safe(g, "clicks"), impr),
                evidence={"ctr": ctr, "benchmark": bench_ctr},
            )


def rule_qs_subcomponent_fail(bundle: dict, _doc: dict, _bench: dict):
    for k in bundle.get("keyword", []):
        impr = safe(k, "impressions")
        if impr < 100:
            continue
        for sub in ("exp_ctr", "ad_relevance", "lp_experience"):
            v = k.get(sub)
            if isinstance(v, str) and v.lower().startswith("below"):
                yield make_finding(
                    "high", f"qs_subcomponent_{sub}",
                    target=f"{k.get('campaign')}>{k.get('ad_group')}>{k.get('keyword')!r}",
                    message=f"Keyword {k.get('keyword')!r}: {sub} = '{v}'.",
                    recommendation={
                        "exp_ctr":      "Move keyword to better-themed ad group OR rewrite RSA headlines",
                        "ad_relevance": "Add the keyword's phrase verbatim as one headline",
                        "lp_experience": "Improve landing page: relevance, speed, mobile, trust signals",
                    }[sub],
                    auto_fixable=False,
                    confidence=confidence_from_sample(safe(k, "clicks"), impr),
                    evidence={sub: v},
                )


def rule_mobile_drag(bundle: dict, _doc: dict, _bench: dict):
    """If we have device-segmented data."""
    # The default UI report doesn't include device segmentation unless the
    # user added it. We look for rows with a device column.
    mobile = [r for r in bundle.get("campaign", []) if (r.get("device") or "").lower() == "mobile"]
    desktop = [r for r in bundle.get("campaign", []) if (r.get("device") or "").lower() == "computer"]
    if not mobile or not desktop:
        return
    m_clicks = sum(safe(r, "clicks") for r in mobile)
    d_clicks = sum(safe(r, "clicks") for r in desktop)
    m_conv = sum(safe(r, "conversions") for r in mobile)
    d_conv = sum(safe(r, "conversions") for r in desktop)
    if m_clicks < 100 or d_clicks < 100:
        return
    m_cvr = m_conv / m_clicks if m_clicks else 0
    d_cvr = d_conv / d_clicks if d_clicks else 0
    if d_cvr > 0 and m_cvr < 0.5 * d_cvr:
        yield make_finding(
            "high", "mobile_drag",
            target="account:devices",
            message=f"Mobile CVR {m_cvr:.1%} is < 50% of Desktop CVR {d_cvr:.1%}.",
            recommendation="Apply −50% mobile bid adjustment (McDonald Gotcha #5).",
            auto_fixable=True,
            mutation={"kind": "bid_adjust", "scope": "account", "device": "mobile", "pct": -0.50},
            confidence=0.85,
            evidence={"mobile_cvr": m_cvr, "desktop_cvr": d_cvr},
        )


def rule_hagakure(_bundle: dict, doc: dict, _bench: dict):
    for c in doc.get("campaigns", []):
        for g in c["ad_groups"]:
            n = len(g.get("keywords", []))
            if n > 20:
                yield make_finding(
                    "medium", "hagakure",
                    target=f"{c['name']}>{g['name']}",
                    message=f"Ad group has {n} keywords (soft limit: 20).",
                    recommendation="Split into themed sub-ad-groups.",
                    auto_fixable=False,
                    confidence=0.8,
                    evidence={"keyword_count": n},
                )


def rule_pinning_over_restriction(_bundle: dict, doc: dict, _bench: dict):
    for c in doc.get("campaigns", []):
        for g in c["ad_groups"]:
            rsa = g.get("rsa") or {}
            heads = rsa.get("headlines", []) or []
            if not heads:
                continue
            pinned = sum(1 for h in heads if h.get("pin") is not None)
            if pinned / max(1, len(heads)) > 0.5:
                yield make_finding(
                    "medium", "pinning_over_restriction",
                    target=f"{c['name']}>{g['name']}",
                    message=f"{pinned}/{len(heads)} RSA headlines pinned — hampers ML.",
                    recommendation="Unpin non-brand headlines.",
                    auto_fixable=True,
                    mutation={
                        "kind": "unpin_non_brand",
                        "campaign": c["name"],
                        "ad_group": g["name"],
                    },
                    confidence=0.7,
                )


def rule_cpa_over_benchmark(bundle: dict, _doc: dict, bench: dict):
    bench_cpa = bench.get("cpa")
    if not bench_cpa:
        return
    for c in bundle.get("campaign", []):
        conv = safe(c, "conversions")
        cost = safe(c, "cost")
        if conv < 5:
            continue
        cpa = cost / conv if conv else None
        if cpa and cpa > 2.0 * bench_cpa:
            yield make_finding(
                "high", "cpa_over_benchmark",
                target=f"campaign:{c.get('campaign')}",
                message=f"CPA ${cpa:.2f} is > 2× benchmark ${bench_cpa:.2f}.",
                recommendation="Combine the negative-keyword additions and bid raises proposed elsewhere "
                               "and re-assess in 14 days. If still over, scope down to highest-CVR ad groups.",
                auto_fixable=False,
                confidence=confidence_from_sample(safe(c, "clicks"), safe(c, "impressions")),
                evidence={"cpa": cpa, "benchmark_cpa": bench_cpa},
            )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

ALL_RULES = [
    rule_search_term_burn,
    rule_missed_opportunity,
    rule_conversion_tracking_break,
    rule_lost_is_budget,
    rule_lost_is_rank,
    rule_sub_benchmark_ctr,
    rule_qs_subcomponent_fail,
    rule_mobile_drag,
    rule_hagakure,
    rule_pinning_over_restriction,
    rule_cpa_over_benchmark,
]


def diagnose(report: dict, campaign_doc: dict, benchmarks: dict) -> list[dict]:
    bundle = report.get("bundle", {})
    vertical = campaign_doc.get("meta", {}).get("vertical", "default")
    bench = benchmarks.get(vertical, benchmarks.get("default", {}))

    findings = []
    for rule_fn in ALL_RULES:
        try:
            findings.extend(list(rule_fn(bundle, campaign_doc, bench)))
        except Exception as e:
            findings.append(make_finding(
                "medium", "rule_error",
                target=rule_fn.__name__,
                message=f"Rule raised: {e!r}",
                recommendation="File a bug; continue with remaining rules.",
                auto_fixable=False,
                confidence=0.5,
            ))
    findings.sort(key=lambda f: f["score"], reverse=True)
    return findings


def render_report(findings: list[dict]) -> str:
    out = ["# Diagnose Report",
           f"Total findings: **{len(findings)}**\n"]
    groups = {"critical": [], "high": [], "medium": [], "low": []}
    for f in findings:
        groups[f["severity"]].append(f)
    for sev in ("critical", "high", "medium", "low"):
        items = groups[sev]
        if not items:
            continue
        out.append(f"## {sev.upper()} ({len(items)})\n")
        for i, f in enumerate(items, 1):
            out.append(f"{i}. **{f['rule']}** — `{f['target']}`")
            out.append(f"   - {f['message']}")
            out.append(f"   - **Recommendation:** {f['recommendation']}")
            out.append(f"   - Auto-fixable: {'yes' if f['auto_fixable'] else 'no'} | "
                       f"Confidence: {f['confidence']} | Score: {f['score']}")
            if f.get("evidence"):
                out.append(f"   - Evidence: `{f['evidence']}`")
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description="Diagnose performance issues.")
    p.add_argument("--report", required=True, type=Path)
    p.add_argument("--campaign", required=True, type=Path)
    p.add_argument("--benchmarks", required=True, type=Path)
    p.add_argument("--out", type=Path, default=None,
                   help="JSON output (findings list)")
    p.add_argument("--report-md", type=Path, default=None,
                   help="Markdown report output")
    args = p.parse_args(argv)

    report = json.loads(args.report.read_text())
    campaign_doc = json.loads(args.campaign.read_text())
    benchmarks = json.loads(args.benchmarks.read_text())

    findings = diagnose(report, campaign_doc, benchmarks)

    if args.out:
        args.out.write_text(json.dumps(findings, indent=2))
        print(f"wrote {args.out}")
    if args.report_md:
        args.report_md.write_text(render_report(findings))
        print(f"wrote {args.report_md}")
    if not args.out and not args.report_md:
        print(render_report(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
