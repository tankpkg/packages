#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CASE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$ROOT/scripts"
ASSETS="$ROOT/assets"
OUT="$CASE/out"
rm -rf "$OUT"; mkdir -p "$OUT"

# Plan from the brief (existing SaaS account, 3 campaigns expected: brand + non-brand + competitor)
python3 "$SCRIPTS/plan.py" --brief "$CASE/brief.json" --out "$OUT/campaign.json" --geo-csv "$ASSETS/geo-targets-seed.csv"

# Normalize the synthetic underperforming reports
python3 "$SCRIPTS/normalize_report.py" --in-dir "$CASE/reports" --out "$OUT/report.json"

# Diagnose against benchmarks
python3 "$SCRIPTS/diagnose.py" --report "$OUT/report.json" --campaign "$OUT/campaign.json" \
   --benchmarks "$ASSETS/benchmarks.json" --out "$OUT/findings.json" --report-md "$OUT/diagnose-report.md"

python3 <<PY
import json, pathlib
out = pathlib.Path("$OUT")
doc = json.loads((out / "campaign.json").read_text())
assert len(doc["campaigns"]) == 3, f"brief opted into competitor campaign — expected 3 campaigns, got {len(doc['campaigns'])}"
assert any("Competitor" in c["name"] for c in doc["campaigns"]), "must include Competitor campaign"

findings = json.loads((out / "findings.json").read_text())
assert len(findings) >= 5, f"expected ≥5 findings, got {len(findings)}"

rules = [f["rule"] for f in findings]
# Must identify search-term burn ("free shopify analytics", "how to do ecommerce analytics")
assert "search_term_burn" in rules, f"missed search_term_burn: {rules}"
# Must identify missed opportunity for "shopify analytics dashboard" (5 conversions, not a kw)
assert "missed_opportunity" in rules, f"missed missed_opportunity: {rules}"
# Must identify lost_is_rank (53% on Non-Brand campaign)
assert "lost_is_rank" in rules, f"missed lost_is_rank: {rules}"
# Must identify at least one QS subcomponent failure
assert any(r.startswith("qs_subcomponent_") for r in rules), f"missed QS subcomponent: {rules}"
# Must identify sub_benchmark_ctr on the Real-Time Dashboard ad group (3.08% < 6.0% * 0.7 = 4.2%)
assert "sub_benchmark_ctr" in rules, f"missed sub_benchmark_ctr: {rules}"

# Severity distribution sanity
sevs = {f["severity"] for f in findings}
assert "critical" in sevs, f"expected at least one critical finding, severities={sevs}"
assert "high" in sevs, f"expected at least one high finding, severities={sevs}"

print(f"e02: {len(findings)} findings, rules covered: {sorted(set(rules))}")
print("e02: all assertions passed")
PY
