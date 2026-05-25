# Diagnose Playbook

Sources: McDonald (Workbook 2023) §2 Gotchas + §9 Metrics; Marshall (Ultimate Guide 6e) Ch 7–10. Plus industry CPC/CTR/CVR benchmarks from WordStream and Pieprzyk (Google Ads Playbook 2024 — secondary).

Covers: how to read the CSV exports the user provides, what each signal means, and the ordered ranking of findings. This is what `scripts/diagnose.py` implements.

## What the user uploads (input contract)

The skill expects the user to export, from Google Ads UI, last-N-days CSVs of:

| File | Source UI path | Required columns (minimum) |
|---|---|---|
| Campaign report | Insights & reports → Predefined reports → Campaign | Campaign, Impressions, Clicks, CTR, Avg. CPC, Cost, Conversions, Cost / conv., Conv. rate, Search Impr. share, Search lost IS (budget), Search lost IS (rank), Search top IS, Search abs. top IS |
| Ad group report | Insights & reports → Predefined reports → Ad group | Campaign, Ad group, [same metrics as Campaign report] |
| Keyword report (Search keywords) | Insights & reports → Predefined reports → Search keyword | Campaign, Ad group, Keyword, Match type, Quality Score (and the 3 sub-components), Impressions, Clicks, CTR, Avg. CPC, Conversions, Cost / conv., Conv. rate |
| Search terms report | Insights & reports → Predefined reports → Search terms | Search term, Match type, Added/Excluded, Campaign, Ad group, Keyword, Impressions, Clicks, CTR, Avg. CPC, Conversions, Cost / conv., Conv. rate |
| Ad / RSA report | Insights & reports → Predefined reports → Ad | Campaign, Ad group, Ad strength (RSA), Headlines, Descriptions, Impressions, Clicks, CTR, Conversions |
| Asset report (optional) | Insights & reports → Predefined reports → Assets | Campaign, Asset type, Asset text, Performance label |

`scripts/normalize_report.py` accepts CSVs in any column order; it maps based on header names (case-insensitive).

## The metric stack (from McDonald §9)

| Metric | Why it matters | Lies when |
|---|---|---|
| Impressions | How often ads showed | Easy to inflate with broad match |
| Clicks | How often ads were clicked | Inflated by click fraud + curiosity |
| CTR | Clicks / Impressions | High CTR + low CVR = "free pizza" ad |
| Avg. CPC | Paid per click | Reserve Price floor distorts at low volume |
| Conversions | The thing you want | Misconfigured pixels destroy this |
| Cost / conv. (CPA) | Cost to acquire one | The number that pays the bills |
| Value / conv. | Revenue or points per conv | Required for ROAS |
| ROAS | Revenue ÷ cost | The ecom north star |
| Search Impr. share | Eligibility share | High = you own the niche |
| Search lost IS (budget) | Lost impressions due to budget cap | Tells you when to raise budget |
| Search lost IS (rank) | Lost impressions due to bid/QS | Tells you when to raise bids or improve QS |
| Top IS / Abs. top IS | Top-of-page share | Brand-defense quality indicator |

## Quality Score: ignore the composite, read the sub-components

Quality Score's 1–10 composite is mostly diagnostic theater. The actionable sub-components per keyword:

| Sub-component | If "Below average" → fix |
|---|---|
| Expected CTR | Keyword theme too loose, or ad copy doesn't reflect the keyword. Move keyword to better-themed ad group OR rewrite RSA headlines to include the keyword phrase. |
| Ad Relevance | Ad copy doesn't reflect the keyword. Add the keyword's exact phrase as one headline. |
| Landing Page Experience | LP mismatch, LP slow, LP not mobile-friendly. Apply Marshall Ch 11 LP checklist. |

## Industry benchmarks (assets/benchmarks.json)

Default benchmarks the diagnose engine compares against. SMB-tier numbers, US/EN, 2023–2024 averages. Override per industry via `assets/benchmarks.json` keys.

| Vertical | CTR | Avg. CPC | CVR | CPA |
|---|---|---|---|---|
| Default (no vertical specified) | 6.0% | $3.00 | 4.5% | $65 |
| Legal | 4.8% | $7.50 | 5.0% | $150 |
| Home services (plumbing, HVAC) | 7.0% | $4.50 | 6.5% | $70 |
| Health & medical | 6.0% | $3.50 | 5.0% | $70 |
| Real estate | 5.0% | $2.00 | 3.0% | $66 |
| Ecommerce | 5.0% | $1.20 | 2.3% | $52 |
| Professional services (B2B) | 5.5% | $5.00 | 5.0% | $100 |
| Education | 6.0% | $2.50 | 4.0% | $62 |
| Travel | 7.5% | $1.80 | 3.5% | $51 |
| Finance & insurance | 6.5% | $4.50 | 5.0% | $90 |

Numbers are starting-point sanity checks, not targets. Each user's account establishes its own baseline after 30 days.

## The diagnostic decision tree

Ordered top-to-bottom by severity. `diagnose.py` checks every rule against every applicable row and emits findings.

### Critical — wasted spend you can fix today

| Rule | Trigger | Recommendation | auto_fixable |
|---|---|---|---|
| Search-term burn | Search term has ≥10 clicks and 0 conversions in last 30 days | Add as `Negative Exact` to its ad group | yes |
| Missed opportunity | Search term has ≥5 conversions and is NOT a keyword in any ad group | Promote to its own `Exact` keyword in the best-matching ad group | yes |
| Conversion-tracking break | Conversions = 0 across all campaigns despite ≥500 clicks in the period | Verify conversion tracking is firing; compare to CRM/Stripe | no — requires user verification |
| Display contamination | Network column in upload shows "Display" anywhere | Re-create campaign as Search-only (McDonald Gotcha #4) | yes |

### High — fix this week

| Rule | Trigger | Recommendation | auto_fixable |
|---|---|---|---|
| Budget-capped | Search lost IS (budget) > 30% | Raise daily budget OR pause low-CVR keywords to free room | partial — propose pause list |
| Bid/QS-capped | Search lost IS (rank) > 30% | Raise Max CPC for top-CVR keywords AND inspect QS sub-components | yes for CPC raise |
| Mobile drag | Mobile CVR < 0.5 × Desktop CVR with ≥100 clicks each | Apply −50% mobile bid adjustment (McDonald Gotcha #5) | yes |
| Sub-benchmark CTR | Ad-group CTR < benchmark × 0.7 with ≥500 impressions | Rewrite RSA headlines: include rising-query language from STR + tighten ad-group theme | partial — propose new RSA |
| QS sub-component fail | Keyword has any sub-component = "Below average" with ≥100 impressions | Move keyword to better-themed ad group OR rewrite RSA per sub-component (see above table) | partial — propose move |
| Pinning over-restriction | Pinning ratio > 50% of RSA headlines | Unpin all non-brand headlines | yes |

### Medium — fix this month

| Rule | Trigger | Recommendation | auto_fixable |
|---|---|---|---|
| Hagakure violation | Ad group has >20 keywords | Split into 2+ themed ad groups | partial — propose split lines |
| Mobile truncation risk | All RSA headlines >25 chars | Add 3+ short variants (≤20 chars) | yes |
| No call extension on phone-led business | User opted phone-led in brief, but call extension absent | Add call extension | yes |
| No sitelinks | Campaign has zero sitelinks attached | Add 4 sitelinks | yes |
| Stale RSA | RSA Ad Strength = "Poor" | Rewrite headlines per dimensions list (Marshall Ch 10 top-10) | partial — propose new RSA |

### Low — track over time

| Rule | Trigger | Recommendation | auto_fixable |
|---|---|---|---|
| Brand bleed | Non-brand campaign receives ≥5% of impressions on brand-name search terms | Move those terms into the brand campaign | yes |
| Cross-group cannibalization | Same search term triggers ads in 2+ ad groups | Add cross-group negatives to enforce ownership | yes |
| Single-keyword whale | One keyword >50% of ad-group spend with sub-benchmark CVR | Move whale to its own ad group with reduced Max CPC | yes |
| Wrong-tag drift | Keyword tagged HOT but CVR < benchmark × 0.5 | Re-tag to WARM or COLD | yes |

## How the ranking works

For each finding, score = severity_weight × confidence:
- severity_weight: critical=10, high=5, medium=2, low=1
- confidence: a 0.0–1.0 score based on sample size (clicks/impressions/conversions vs minimum thresholds)

Findings are sorted descending. Top 5 critical + top 5 high + top 5 medium are surfaced first.

## What `revise.py` does next

1. Take the ranked findings list.
2. Filter to `auto_fixable: yes` (skipping partials by default; user can override).
3. Apply mutations to `campaign.json`:
   - Add negatives
   - Promote search terms to keywords
   - Raise Max CPC for top-CVR keywords (capped at +50% per cycle)
   - Apply device bid adjustments
   - Unpin RSA headlines
4. Re-emit CSVs via `csv_emit.py`.
5. Re-validate via `validate.py`.
6. Emit `DIFF.md` showing the before/after diff in human-readable form.

The user takes `DIFF.md` + the new CSV bundle and re-imports via Google Ads Editor.

## Decision tree summary

```
DIAGNOSE
  |
  v
Load CSVs, normalize column names
  |
  v
Build internal report JSON
  |
  v
For each rule in priority order:
  - test against rows
  - emit finding with severity, confidence, recommendation, auto_fixable
  |
  v
Rank findings (severity_weight × confidence)
  |
  v
Output diagnose-report.md
  |
  v
Ask user: "apply auto-fixable items?"
  |
  v
If yes → REVISE
   - mutate campaign.json
   - re-emit CSVs
   - re-validate
   - emit DIFF.md
```

## Worked example (the "plumber" scenario)

Inputs:
- Vertical: Home services
- Period: last 30 days
- Spend: $1,500
- Total clicks: 320 / Conversions: 12 / CTR 5.0% / CPA $125

Rule firings:
- CTR 5.0% vs benchmark 7.0% × 0.7 = 4.9% → just above threshold, no firing
- CPA $125 vs benchmark $70 → 1.78× over benchmark → high-severity "CPA over-target" finding
- Search lost IS (budget) = 8% → no firing
- Search lost IS (rank) = 41% → high-severity "bid/QS capped" finding
- Search terms scan finds:
  - "plumber free quote" — 18 clicks, 4 conv → keep as is
  - "plumber jobs near me" — 22 clicks, 0 conv → CRITICAL: add `jobs` as account-level Negative Broad
  - "diy drain cleaning" — 14 clicks, 0 conv → CRITICAL: add `diy` as account-level Negative Broad
  - "emergency plumber san francisco" — 9 clicks, 3 conv, NOT a current keyword → CRITICAL: promote to Exact in best-matching ad group
- QS report shows 3 keywords with Ad Relevance = Below average → high-severity finding per keyword

Output ranking:
1. CRITICAL: add `jobs` as Negative Broad (account-level)
2. CRITICAL: add `diy` as Negative Broad (account-level)
3. CRITICAL: promote `emergency plumber san francisco` to Exact keyword
4. HIGH: 41% search lost IS (rank) — raise top-3 keyword Max CPC by 20%
5. HIGH: CPA $125 vs benchmark $70 — combination of above fixes should help; re-check in 14 days
6. HIGH: 3 keywords with Ad Relevance Below average — propose new RSA headlines

Auto-applied (auto_fixable: yes):
- Negatives added
- Promotion applied
- CPC raised
- New RSA proposed (user reviews)

`DIFF.md` shows all changes. User re-imports.

## Source attribution

- McDonald, *Google Ads Workbook 2023*, §2 (Gotchas) and §9 (Metrics).
- Marshall, Todd, Rhodes, *Ultimate Guide to Google Ads 6e* (2020), Ch 7–10.
- Industry benchmarks: WordStream "Google Ads Industry Benchmarks" + Pieprzyk *Google Ads Playbook* (2024, secondary).
