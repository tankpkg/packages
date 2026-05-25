---
name: "@tank/google-search-ads"
description: |
  Closed-loop decision engine for Google Search Ads. Turns business briefs into
  Google Ads Editor-importable CSV bundles, analyzes the user's weekly CSV
  exports against industry benchmarks, and proposes ranked revisions with
  auto-applied fixes. SMB-owner focused. Never emits naked broad match or
  Modified Broad (both validator-blocked). Always Search Network only at v1
  (no Display, no Smart Campaigns, no Performance Max). Bundled scripts:
  plan → csv_emit → validate → normalize_report → diagnose → revise →
  cron_detect.
  Source attribution — Marshall/Todd/Rhodes (Ultimate Guide to Google Ads 6e,
  2020) Ch 4-12; McDonald (Google Ads Workbook 2023) §1-5, §9 including the 6
  Gotchas framework; Google Ads Editor official docs; WordStream industry
  benchmarks; pytrends 12-month signal validation across 35 keywords.

  Trigger phrases: "google ads", "google search ads", "set up google ads",
  "create a google ads campaign", "ppc campaign", "improve my google ads",
  "google ads audit", "google ads not working", "wasted ad spend",
  "fix my google ads", "google ads bulk upload", "google ads editor csv",
  "import campaign google ads", "google search ads json", "weekly google ads check-in",
  "google ads negative keywords", "search terms report analysis", "rsa headlines",
  "responsive search ads", "google ads for small business", "ppc for SMB"
---

# Google Search Ads — Closed-Loop Decision Engine

For SMB owners running their own Google Search Ads. The agent **plans**, the user **imports**, the agent **analyzes**, the agent **revises** — every 7 days.

## Core Philosophy

1. **Editor CSV is the contract.** Skill output is what Google Ads Editor accepts. Never freeform suggestions; always import-ready files.
2. **`campaign.json` is the single source of truth.** CSVs are emitted from it; never edited directly. Roll-back is just `csv_emit.py` on an older version.
3. **Search Network only at v1.** No Display, no Smart Campaigns, no Performance Max. McDonald's Gotchas #3 and #4 are non-negotiable.
4. **Validate before users see it.** Two-pass validator (schema + emitted CSV) catches every known Editor failure mode before the user opens Editor.
5. **The Search Terms Report drives everything.** Weekly review = harvest negatives (burns) + promote winners (missed opportunities). That's where the money is.
6. **Phase out Marshall, lean on McDonald** where they disagree on AI-era tactics. McDonald is 2023 vs Marshall's 2020 — closer to current ground truth.

## The Three Commands

```
plan      Brief → campaign.json + 8 importable CSVs + IMPORT_GUIDE.md
analyze   User's CSV exports → ranked findings vs benchmarks
revise    Findings + previous campaign.json → campaign_v{N+1}.json + DIFF.md + new CSVs
schedule  ASK user, only if host has cron primitive — fall back to .ics + crontab line
```

## Quick-Start: Common Problems

### "Help me set up Google Ads for my business"

1. Run prompt `prompts/plan-brief.md` — 11 questions.
2. Save user answers as `brief.json` (template in `assets/brief-template.json`).
3. `scripts/plan.py --brief brief.json --out campaign.json` → produces `campaign.json`.
4. `scripts/csv_emit.py --in campaign.json --out-dir out/` → 8 CSV files.
5. `scripts/validate.py --in campaign.json --csv-dir out/` → must exit 0 before handoff.
6. Hand `out/` directory + `assets/IMPORT_GUIDE.md` to user.
7. Run `scripts/cron_detect.py` to see if host has a scheduler.
8. ASK the user (don't assume): "Want me to schedule a weekly check-in?"

### "My Google Ads are wasting money"

1. Ask the user to export the 5 CSVs listed in `prompts/weekly-checkin.md` (Campaign, Ad group, Search terms, Keyword with QS columns, Ad).
2. `scripts/normalize_report.py --in-dir reports/ --out report.json`.
3. `scripts/diagnose.py --report report.json --campaign campaign.json --benchmarks assets/benchmarks.json --out findings.json --report-md diagnose-report.md`.
4. Show user the diagnose report (sorted by severity × confidence score).
5. Ask: "Apply the auto-fixable items?" — never auto-apply without confirmation.
6. `scripts/revise.py --campaign campaign.json --findings findings.json --apply all` → produces `campaign_v{N+1}.json` + `DIFF.md`.
7. Re-emit CSVs from the new version; re-validate.
8. Hand new bundle to user for re-import.

### "I imported the CSVs but Editor says 'Ambiguous row type'"

Don't combine entity files. Each CSV must hold one entity type only (Campaigns, AdGroups, Keywords, etc.). Re-emit via `csv_emit.py` — it always emits one file per entity. If the error persists, run `validate.py` with `--csv-dir` and read the validation report.

### "I want to revert a revision"

Every revise step keeps `campaign_v{N}.json` files. To revert:

```
python3 scripts/csv_emit.py --in campaign_v{N-1}.json --out-dir rollback/
# Import rollback/ in Editor — it overrides the current state
```

## Decision Trees

### When to use which command

| User asks | Run |
|---|---|
| "Set up ads for [business]" | plan + csv_emit + validate (handoff) |
| "Audit / improve / fix my ads" | normalize_report + diagnose (show findings) → ask before revise |
| "Apply the fixes" / "Yes, go ahead" | revise + csv_emit + validate (handoff) |
| "Roll back" | csv_emit on `campaign_v{N-1}.json` |
| "Schedule weekly review" | cron_detect → if found, call its `_tool_call` with payload; else emit .ics |

### Bid-strategy ramp (from references/01-plan-workflow.md)

| Account state | Strategy |
|---|---|
| Brand new, 0 conversions | Manual CPC |
| 1–49 conversions / month / campaign | Manual CPC |
| 50–99 conv / mo / camp | Enhanced CPC |
| 100+ conv with lead gen | Target CPA |
| 100+ conv with ecom + wide price range | Target ROAS |

### "Should I emit a competitor campaign?"

| Signal | Decision |
|---|---|
| User named competitors AND opted in via `run_competitor_campaign: true` | Yes — 10% of budget |
| User named competitors but didn't opt in | No (default) — list them as account negatives in non-brand instead |
| User has no listed competitors | No |

## Hard Rules (Validator-Enforced)

| Rule | Source |
|---|---|
| No naked broad-match keywords without explicit `broad_confirmed: true` | McDonald Gotcha #2 |
| No Modified Broad (`+keyword`) — discontinued since 2021 | Google deprecation |
| No `Display Network` in `Networks` column | McDonald Gotcha #4 |
| RSA has 3–15 headlines (≤30 chars each) and 2–4 descriptions (≤90 chars each) | Google ad spec |
| Path 1, Path 2 ≤15 chars, alphanumeric + hyphen | Google ad spec |
| Match-type wrapping matches Criterion Type (`[...]` for Exact, `"..."` for Phrase) | Editor strict parse |
| Each emitted CSV holds one entity type only | Editor "Ambiguous row type" prevention |
| Geo cells in `Locations.csv` are numeric IDs only | Editor "Unknown location" prevention |
| Headers in English, case-insensitive | Editor multilingual rejection |
| Multi-value cells use `;` (semicolon) not `,` | Editor strict parse |

`scripts/validate.py` enforces all of these. ALWAYS run it before handing CSVs to the user.

## Reference Files

| File | Contents |
|---|---|
| `references/01-plan-workflow.md` | 11-question brief, prerequisites, USP six elements, HOT/WARM/COLD keyword tagging, RSA generation rules, campaign-separation matrix |
| `references/02-csv-schema.md` | `campaign.json` schema, full per-entity CSV column layouts, validator Pass 1 + Pass 2 rule tables with severities |
| `references/03-diagnose-playbook.md` | Industry benchmarks, diagnostic decision tree (search term burn / missed opportunity / lost IS / QS sub-components / etc), worked plumber example |
| `references/04-cron-integration.md` | Host capability detection, OpenClaw/Hermes/Agentic OS/generic payload shapes, .ics + crontab fallback |

## Bundled scripts

| Script | Purpose |
|---|---|
| `scripts/plan.py` | brief.json → campaign.json |
| `scripts/csv_emit.py` | campaign.json → 8 Editor-compatible CSVs |
| `scripts/validate.py` | Two-pass validator: schema + emitted CSVs. Exit 0 only on zero ERRORs. |
| `scripts/normalize_report.py` | User's UI CSV exports → unified `report.json` |
| `scripts/diagnose.py` | report.json + campaign.json + benchmarks → ranked findings |
| `scripts/revise.py` | Findings → `campaign_v{N+1}.json` + DIFF.md |
| `scripts/cron_detect.py` | Detect host scheduler; emit payload or fallback |

## Bundled assets

| Asset | Purpose |
|---|---|
| `assets/brief-template.json` | Skeleton for the 11-question interrogation |
| `assets/benchmarks.json` | Industry CTR/CPC/CVR/CPA medians (default + 9 verticals) |
| `assets/geo-targets-seed.csv` | 86 Geo Target IDs (top countries + US states + major cities). Fallback to https://developers.google.com/google-ads/api/data/geotargets for anything missing. |
| `assets/IMPORT_GUIDE.md` | Step-by-step Editor import instructions for the user |

## Prompts

| Prompt | When |
|---|---|
| `prompts/plan-brief.md` | First-time setup. Use verbatim — it lists the prerequisites the user MUST satisfy. |
| `prompts/weekly-checkin.md` | Triggered by cron OR by user request. Lists the 5 reports + UI paths. |

## What this skill does NOT do (anti-scope)

- Display Network, Performance Max, Smart Campaigns, Shopping, YouTube, App campaigns — out of scope.
- Direct Google Ads API write access (developer token gate). Editor CSV bulk import is the supported path.
- Auto-scraping the user's actual account performance — user uploads CSVs explicitly.
- Auto-applying fixes without user confirmation. Always show DIFF.md first.
- Replacing human judgment on USP, brand voice, or unique offer crafting — the skill mechanizes the boring parts.
