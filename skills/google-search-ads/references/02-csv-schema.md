# CSV Schema & Validator Rules

Sources: Google Ads Editor Help (support.google.com/google-ads/editor/answer/56368, 57747, 30564), brightbuilders.co empirical findings, Marshall Ch 6–10, McDonald §2 (Gotchas), §4.

Covers: the internal `campaign.json` schema, the Google Ads Editor CSV file format, the strict rules that make imports succeed, and every validator rule with its severity.

## The internal data model: `campaign.json`

This is the single source of truth. CSVs are EMITTED from it; never edit CSVs and back-port. The schema:

```json
{
  "version": "1.0.0",
  "meta": {
    "business": "string — Q1 from the brief",
    "geo": ["string", ...],         // numeric Geo Target IDs as strings
    "currency": "USD",
    "language": "en",               // 2-letter ISO 639-1
    "created_at": "ISO 8601 UTC"
  },
  "account_negatives": ["string", ...],
  "campaigns": [
    {
      "name": "string — Editor-unique campaign name",
      "type": "Search",
      "subtype": "Standard",
      "status": "Paused",           // Always import paused, user enables in UI
      "daily_budget": 50.00,        // numeric, > 0
      "bid_strategy": "Manual CPC", // one of fixed enum (see below)
      "target_cpa": null,           // required if bid_strategy is Target CPA
      "target_roas": null,          // required if bid_strategy is Target ROAS
      "max_cpc_ceiling": null,      // optional for portfolio strategies
      "networks": ["Google search"],// subset of {Google search, Search partners}
      "language": "en",
      "start_date": "2026-05-25",   // YYYY-MM-DD
      "end_date": null,
      "ad_rotation": "Optimize",
      "campaign_negatives": ["string", ...],
      "ad_groups": [
        {
          "name": "string — campaign-unique ad-group name",
          "status": "Enabled",
          "max_cpc": 4.50,          // required if campaign uses Manual CPC
          "keywords": [
            { "text": "string", "match": "Exact|Phrase|Broad", "max_cpc": null, "tag": "HOT|WARM|COLD" }
          ],
          "negatives": [
            { "text": "string", "match": "Negative Exact|Negative Phrase|Negative Broad" }
          ],
          "rsa": {
            "final_url": "https://...",
            "path1": "string",        // ≤15 chars, alphanumeric + hyphen
            "path2": "string",        // ≤15 chars, alphanumeric + hyphen
            "headlines": [
              { "text": "string", "pin": 1|2|3|null }
            ],
            "descriptions": [
              { "text": "string", "pin": 1|2|3|4|null }
            ]
          },
          "assets": {
            "sitelinks": [
              { "text": "string", "description1": "string?", "description2": "string?", "final_url": "https://..." }
            ],
            "callouts": ["string", ...],
            "structured_snippets": [
              { "header": "Services|Types|Brands|...", "values": ["string", ...] }
            ],
            "call_extension": { "phone": "string?", "country_code": "US?" },
            "location_extension": true|false,
            "price_extensions": [...]   // optional
          }
        }
      ]
    }
  ]
}
```

## Mapping campaign.json → Google Ads Editor CSV files

Google Ads Editor refuses to import a CSV that mixes entity types ("Ambiguous row type" error). The skill MUST emit ≥5 separate files per campaign batch:

| File | Entity | Required columns |
|---|---|---|
| `Campaigns.csv` | One row per campaign | Campaign, Campaign Type, Campaign Status, Budget, Budget type, Bid strategy type, Networks, Language, Start date |
| `AdGroups.csv` | One row per ad group | Campaign, Ad group, Ad Group Status, Max CPC |
| `Keywords.csv` | One row per keyword (positives and negatives) | Campaign, Ad group, Keyword, Criterion Type, Status, Max CPC (optional) |
| `RSAs.csv` | One row per RSA | Campaign, Ad group, Status, Final URL, Path 1, Path 2, Headline 1..15, Headline 1 position..15 position, Description 1..4, Description 1 position..4 position |
| `Locations.csv` | One row per geo target (optional but recommended) | Campaign, Location ID, Action |
| `Sitelinks.csv` | One row per sitelink (optional) | Campaign, Ad group (or blank), Sitelink text, Description 1, Description 2, Final URL |
| `Callouts.csv` | One row per callout (optional) | Campaign, Ad group (or blank), Callout text |
| `StructuredSnippets.csv` | One row per snippet (optional) | Campaign, Ad group (or blank), Header, Values (semicolon-separated) |

### File-level rules

- **UTF-8 encoding** (UTF-16 LE also accepted; UTF-8 is the default we emit).
- **English column headers**. Casing and spaces don't matter (`Daily Budget` = `dailybudget` = `DAILY_BUDGET`), but the language must be English.
- **First row = header row**. Always.
- **Multi-value cells** use `;` as separator, not `,` or `|`. Examples: `Google search;Search partners`, `en;es`.
- **No `,` inside cells** unless the cell is quoted with `"..."`.
- **Don't include `#Original` columns** on first-time emit. They are only used for edit-preserving history.

### Match-type encoding rules

| Match | `Keyword` column value | `Criterion Type` column value |
|---|---|---|
| Broad | `plumber san francisco` (no wrapping) | `Broad` |
| Phrase | `"plumber san francisco"` | `Phrase` |
| Exact | `[plumber san francisco]` | `Exact` |
| Negative Broad | `plumber free` (no wrapping) | `Negative Broad` |
| Negative Phrase | `"plumber free"` | `Negative Phrase` |
| Negative Exact | `[plumber free]` | `Negative Exact` |
| Campaign-level negative | as above, but `Ad group` column blank | `Campaign negative` (legacy) — modern: `Negative *` with Ad group blank |

**Modified Broad (`+keyword`) is dead.** Skill must never emit `+` prefixes. (McDonald §2 Gotcha #2.)

### Bid-strategy enum (campaign.json `bid_strategy`)

Allowed values, case-sensitive:
- `Manual CPC`
- `Enhanced CPC`
- `Target CPA`        (requires `target_cpa`)
- `Target ROAS`       (requires `target_roas`)
- `Maximize conversions`
- `Maximize conversion value`
- `Target impression share`

If `Manual CPC` or `Enhanced CPC`: every ad group MUST have `max_cpc > 0`.

### Networks enum

Allowed values for `Networks` cell (semicolon-joined subset):
- `Google search` (the safe v1 default)
- `Search partners` (opt-in only)

Forbidden at v1: `Display Network`, `Display`, anything containing "Display". Emitting these triggers McDonald Gotcha #4.

### Campaign type enum

Only `Search` for this skill. Other Editor values exist (`Search – Mobile app installs`, `Display`, `Shopping`, `Video`, etc.) but the skill rejects them in Pass 1 validation.

## Geo targeting

- Always emit numeric **Geo Target IDs** in `Locations.csv`, not location names.
- Names like "Texas" or "United States" sometimes import as "Unknown."
- Lookup source: `assets/geo-targets-seed.csv` (86 entries) + fallback to Google's CSV at https://developers.google.com/google-ads/api/data/geotargets.
- If user requests a geo not in the seed CSV, the plan step asks them to look up the numeric ID and supply it.

## RSA component limits (validator rules)

| Component | Min | Max | Per-item limit |
|---|---|---|---|
| Headlines | 3 | 15 | ≤30 chars |
| Descriptions | 2 | 4 | ≤90 chars |
| Path 1, Path 2 | 0 each | 1 each | ≤15 chars, alphanumeric + hyphen |
| Final URL | 1 | 1 | ≤1024 chars |
| Headlines pinned to position 1 | 0 | (no hard cap, ≤2 recommended) | — |
| Headlines pinned to position 2 | 0 | ≤2 recommended | — |
| Headlines pinned to position 3 | 0 | ≤2 recommended | — |
| Descriptions pinned to position 1–4 | 0 | (≤2 per position recommended) | — |

## Validator — Pass 1 rules (campaign.json schema)

Each rule lists severity, scope, and the failure surface.

| Rule | Severity | Triggers on |
|---|---|---|
| `meta.geo` is a list of numeric strings | ERROR | location names instead of IDs |
| `meta.language` is a valid 2-letter ISO code | ERROR | `english` instead of `en` |
| `campaign.type` is exactly `Search` | ERROR | other types |
| `campaign.daily_budget > 0` | ERROR | 0 or missing |
| `campaign.bid_strategy` is in the enum | ERROR | unknown strings |
| `bid_strategy == Target CPA` → `target_cpa` is set | ERROR | missing required field |
| `bid_strategy == Target ROAS` → `target_roas` is set | ERROR | missing required field |
| `bid_strategy in {Manual CPC, Enhanced CPC}` → every ad group has `max_cpc > 0` | ERROR | bid required at ad-group level |
| `campaign.networks` does not contain `Display Network` or any "Display*" value | ERROR | McDonald Gotcha #4 |
| Every keyword `text` is non-empty | ERROR | blank keyword |
| Every keyword `text` ≤80 chars AND ≤10 words | ERROR | Google's limits |
| Every keyword `match` is in {Exact, Phrase, Broad} + Negative variants | ERROR | case-sensitive enum |
| No naked broad-match keyword without an explicit Broad confirmation flag in campaign.json | ERROR | McDonald Gotcha #2 — naked broad is forbidden by default |
| No keyword text starting with `+` | ERROR | Modified Broad sunset |
| Every RSA has ≥3 headlines | ERROR | Google requires 3+ |
| Every RSA has ≤15 headlines | ERROR | hard max |
| Every RSA has ≥2 descriptions | ERROR | Google requires 2+ |
| Every RSA has ≤4 descriptions | ERROR | hard max |
| Every headline ≤30 chars | ERROR | truncation guaranteed |
| Every description ≤90 chars | ERROR | truncation guaranteed |
| `path1` and `path2` ≤15 chars, alphanumeric + hyphen | ERROR | path validation rules |
| `final_url` is HTTPS and well-formed | ERROR | malformed URLs |
| Headlines pinned to position 1 ≤2 (warn at >2) | WARN | pin overlap may break rotation |
| Pinning ratio across headlines ≤50% | WARN | hampers ML (Marshall Ch 10) |
| No duplicate keyword (text+match) within an ad group | ERROR | Editor deduplicates silently |
| Negative keyword doesn't duplicate a positive in the same ad group | ERROR | self-blocking |
| Ad group has ≤20 keywords | WARN | Hagakure soft limit, McDonald §4 |
| Ad copy contains no ALL CAPS standalone words ≥4 chars | ERROR | Google rejects (`FREE`) |
| Ad copy contains no emoji codepoints | ERROR | Google rejects |
| Ad copy contains no repeated punctuation runs (`!!!`, `>>>`, `???`) | ERROR | Google rejects |
| Ad copy contains no `click here` (case-insensitive) | WARN | wastes space |
| Ad copy contains no phone-number-like patterns | ERROR | must be in call extension |
| Ad copy contains no consecutive duplicated words (`sale sale`, `now now`) | WARN | Google rejects repetition |
| Ad copy contains no double-spaces | WARN | strip + normalize |
| Multiple ad groups share the same `final_url` | WARN | McDonald Gotcha #1 — likely sloppy LP mapping |

## Validator — Pass 2 rules (emitted CSV conformance)

After `csv_emit.py` produces the files, validate each:

| Rule | Severity |
|---|---|
| File is valid UTF-8 (or UTF-16 LE with BOM) | ERROR |
| First row is a header row in English | ERROR |
| One entity type per file (no mixing) | ERROR — "Ambiguous row type" |
| Multi-value cells use `;` (not `,` or `|`) | ERROR |
| Match-type wrapping in `Keyword` column matches `Criterion Type` value | ERROR |
| `Criterion Type` casing exactly one of: `Broad`, `Phrase`, `Exact`, `Negative Broad`, `Negative Phrase`, `Negative Exact`, `Campaign negative` | ERROR |
| `Networks` cell values are from the allowed set, semicolon-separated | ERROR |
| Every `Campaign` referenced in AdGroups.csv exists as a row in Campaigns.csv | ERROR |
| Every `Campaign,Ad group` pair referenced in Keywords.csv exists in AdGroups.csv | ERROR |
| Every `Campaign,Ad group` pair referenced in RSAs.csv exists in AdGroups.csv | ERROR |
| `Locations.csv` uses numeric IDs that resolve in `assets/geo-targets-seed.csv` (warn if not) | WARN |
| No row in any file has fewer fields than the header | ERROR — ragged CSV |
| For RSA file: every `Headline N` value has a matching `Headline N position` column header (even if value blank) | ERROR |
| Total file size ≤ 50MB and total rows ≤ 1,000,000 | ERROR — Google Ads bulk-upload limits |

## Validator output: `validation-report.md`

```
# Validation Report
Status: FAIL (3 errors, 5 warnings, 2 info)

## ERRORS (must fix before import)

1. [Pass 1] campaign[0].networks contains "Display Network" — McDonald Gotcha #4
   File: campaign.json
   Fix: remove "Display Network" from networks list; v1 must be ["Google search"] only

2. [Pass 2] Keywords.csv:14 — naked broad match without explicit Broad confirmation
   Row: ,Acme - Search,Emergency Plumbing,plumber san francisco,,Enabled
   Fix: wrap in [] for Exact or "" for Phrase, OR add explicit broad_confirmed: true in campaign.json

... etc

## WARNINGS (will import but may cause silent issues)

1. [Pass 1] ad_group "Emergency Plumbing" has 23 keywords (Hagakure soft limit: 20)
   Fix: split into sub-themes — possibly "24/7 Emergency" and "Same-Day Plumbing"

... etc

## INFO

1. Geo target ID 21176 (Texas) resolved from seed CSV.

2. RSA in "Emergency Plumbing" pins 1 of 6 headlines — within recommended limits.
```

Exit code 0 only when zero ERRORs. WARN-only is acceptable.

## Source attribution

- Google Ads Editor Help: prepare a CSV file (answer 56368), CSV file columns (answer 57747), import a CSV file (answer 30564).
- Bright Builders, "How to Import Campaigns Into Google Ads Editor" — empirical error catalog.
- Marshall et al., *Ultimate Guide to Google Ads 6e* (2020), Ch 6, Ch 10.
- McDonald, *Google Ads Workbook 2023*, §2, §4.
