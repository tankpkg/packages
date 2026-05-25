# @tank/google-search-ads — Evaluation suite

Three test cases that exercise the full plan → emit → validate → analyze → revise loop.

## Test cases

| ID | Scenario | What it proves |
|---|---|---|
| `e01-plumber-new` | Brand new SMB plumber, no existing ads | plan.py + validate.py pass on a clean greenfield brief |
| `e02-ecom-saas-underperform` | SaaS account already running, sub-benchmark CTR + IS-rank-lost | diagnose.py identifies the right issues at the right severity |
| `e03-broad-match-disaster` | Account with naked broad matches and "free"/"jobs" search-term burn | revise.py correctly adds negatives + promotes missed opportunities |

## How to run

```
bash run-all.sh
```

Each test writes its outputs into `evals/e01-*/out/`, `evals/e02-*/out/`, etc., and emits a `RESULT.md` per case with PASS/FAIL on each assertion.

## Assertion model

For every case, the harness checks:

1. **Exit code** — every script must exit 0 (or the expected non-zero for `validate.py --strict` cases).
2. **Required artifacts** — the expected files must exist with non-zero size.
3. **Content assertions** — domain-specific checks defined per case (e.g., "campaign count = 2", "at least one critical finding fired").

PASS if all assertions hold. The harness uses Python `assert` statements with descriptive messages; failures stop the test.
