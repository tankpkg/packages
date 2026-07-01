#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CASE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$ROOT/scripts"
OUT="$CASE/out"
rm -rf "$OUT"; mkdir -p "$OUT"

# Validate the deliberately-broken campaign.json
# Expect validate.py to FAIL (exit 1) with the right error rules detected.
set +e
python3 "$SCRIPTS/validate.py" --in "$CASE/campaign-bad.json" --report "$OUT/validation-report.md" > "$OUT/validate.stdout" 2>&1
exit_code=$?
set -e

python3 <<PY
import pathlib, sys
out = pathlib.Path("$OUT")
report = (out / "validation-report.md").read_text()
# Must FAIL
if "Status: **FAIL**" not in report:
    print("validate.py did NOT fail on a deliberately bad campaign:")
    print(report[:2000])
    sys.exit(1)

# Must detect ALL of these specific rules:
required_rules = [
    "campaign.networks_display",   # Display Network present
    "kw.naked_broad",              # broad without confirmation
    "kw.modified_broad",           # +keyword syntax
    "ag.dup_keyword",              # duplicate keyword
    "rsa.too_few_headlines",       # only 2 headlines
    "rsa.too_few_descs",           # only 1 description
    "adtext.allcaps",              # "BUY OUR WIDGETS NOW"
    "adtext.repeated_punct",       # "!!!"
    "adtext.too_long",             # path1 31 chars + headline > 30 chars
    "rsa.path1_too_long",          # path1 too long
    "adtext.clickhere",            # "Click here"
]

missing = [r for r in required_rules if r not in report]
if missing:
    print(f"validate.py missed these expected rules: {missing}")
    print("---report---")
    print(report)
    sys.exit(1)

print("e03: all expected validation rules detected")
print(f"  rules verified: {required_rules}")
PY
