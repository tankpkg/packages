#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CASE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$ROOT/scripts"
ASSETS="$ROOT/assets"
OUT="$CASE/out"
rm -rf "$OUT"; mkdir -p "$OUT"

python3 "$SCRIPTS/plan.py" --brief "$CASE/brief.json" --out "$OUT/campaign.json" --geo-csv "$ASSETS/geo-targets-seed.csv"
python3 "$SCRIPTS/csv_emit.py" --in "$OUT/campaign.json" --out-dir "$OUT/csvs"
python3 "$SCRIPTS/validate.py" --in "$OUT/campaign.json" --csv-dir "$OUT/csvs" --report "$OUT/validation-report.md"

python3 <<PY
import json, pathlib
out = pathlib.Path("$OUT")
doc = json.loads((out / "campaign.json").read_text())
assert len(doc["campaigns"]) == 2, f"expected 2 campaigns (brand + non-brand), got {len(doc['campaigns'])}"
brand = doc["campaigns"][0]
assert brand["bid_strategy"] == "Manual CPC", f"new account must default Manual CPC; got {brand['bid_strategy']}"
assert "Display" not in ";".join(doc["campaigns"][0]["networks"]), "must NOT include Display Network"
assert doc["meta"]["geo"] == ["1026339"], f"San Francisco should resolve to 1026339, got {doc['meta']['geo']}"

# Validation report must be PASS
report = (out / "validation-report.md").read_text()
assert "Status: **PASS**" in report, f"validate failed:\n{report[:1500]}"

# CSVs exist and have headers
for f in ("Campaigns.csv","AdGroups.csv","Keywords.csv","NegativeKeywords.csv","RSAs.csv","Locations.csv"):
    p = out / "csvs" / f
    assert p.exists(), f"missing {f}"
    assert p.read_text().count(",") > 0, f"{f} has no header"

print("e01: all assertions passed")
PY
