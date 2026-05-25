# Import Guide — Loading the CSVs into Google Ads Editor

This guide is bundled with every campaign you generate. Follow it once; subsequent weekly revisions follow the same pattern.

## 1. Account-level precheck (one-time)

Before importing anything, confirm these account-level settings. Some of them are McDonald's "Gotchas" that silently destroy budgets.

| Setting | Where | Required value |
|---|---|---|
| Account mode | Tools → Switch to Expert Mode | **Expert Mode** (Smart Mode blocks CSV imports) |
| Ad Suggestions | Settings → Account Settings → Ad Suggestions | **Don't automatically apply ad suggestions** |
| Automated Assets | Ads & Assets → Assets → Associations (legacy) → 3-dot menu → Account-level automated assets → Advanced Settings | **All OFF** |
| Two-step verification | Google Account → Security | **ON** (ad accounts are stolen for budget abuse) |
| Conversion tracking | Tools → Conversions | At least one **Sales** or **Leads** conversion verified against your CRM/Stripe |

## 2. Install Google Ads Editor

Download from https://ads.google.com/home/tools/ads-editor/. Free, macOS + Windows. Log in with the same Google account that owns the ad account.

## 3. Sync your current account

In Editor: **Account → Get recent changes → All recent changes**. This pulls your live account state. Always sync before importing — otherwise Editor will think any existing items conflict.

## 4. Import the CSVs in this order

Google Ads Editor is strict about order. Parents before children, every time. Import each file separately — never combine them.

1. **Campaigns.csv** → Account menu → Import → From file → select Campaigns.csv → review proposed changes → Keep proposed changes.
2. **Locations.csv** → same flow.
3. **AdGroups.csv** → same flow. (Warnings about missing bids are expected if you're using Smart Bidding.)
4. **Keywords.csv** → same flow.
5. **NegativeKeywords.csv** → same flow.
6. **RSAs.csv** → same flow. (You'll see "Created" entries appear under each ad group.)
7. **Callouts.csv** / **Sitelinks.csv** / **StructuredSnippets.csv** → import any that exist in your bundle.

After each import, Editor shows you a preview pane. Click **Keep proposed changes** if everything looks right. If you see "Ambiguous row type" or "Unknown location" errors, run `python3 scripts/validate.py --in campaign.json --csv-dir out/` — the validator catches every known failure mode before you'd see it in Editor.

## 5. Review before posting

Don't skip this. In Editor's left tree, click each campaign and verify:

- **Networks** = `Google search` only (no Display Network checkmark)
- **Locations** = your intended geo IDs (not "Unknown")
- **Status** = `Paused` for every entity (the generator emits everything paused so you don't accidentally spend before reviewing)
- **Bid strategy** = `Manual CPC` (or whatever you chose)

In **Tools → Check changes**, run a validation pass. Editor will warn about anything it doesn't like.

## 6. Post the changes

Account → **Post**. The changes go live in your account. Items remain Paused. Don't enable them yet.

## 7. Enable the campaigns

Switch over to ads.google.com (the web UI) and enable each campaign manually:

1. Open the campaign.
2. Confirm bid strategy + budget look right.
3. Toggle the campaign from Paused → Enabled.

Manual enable is intentional — it forces you to look at the campaign once before money starts flowing.

## 8. After 7 days

The weekly check-in fires (if you scheduled it). Otherwise, ping the skill: "Time for the weekly Google Search Ads review." Export the 5 CSVs listed in `prompts/weekly-checkin.md` and run the analyze + revise loop.

## Common errors and fixes

| Editor error | Cause | Fix |
|---|---|---|
| "Ambiguous row type" | Multiple entity types in one CSV | Use the bundle we emit; never combine files |
| "Unknown location" | Location names instead of numeric IDs | Verify Locations.csv uses numeric IDs (validator catches this) |
| Import button greyed out | Residual bad rows from prior failed import | In Editor, delete the orphaned rows under Keywords & Targeting → Locations, then retry |
| Smart Bidding warning on Max CPC | Bid strategy is automated but Max CPC is set | Remove Max CPC from AdGroups.csv (regenerate after editing campaign.json's bid_strategy) |
| RSA "Headline N position" empty rows ignored | Empty pin columns are fine — Editor treats them as unpinned | No action needed |

## Reverting

If a revision looks bad after import, you can always roll back:

```
# Re-emit from the previous campaign.json version
python3 scripts/csv_emit.py --in campaign_v{N-1}.json --out-dir rollback-out/
# Import rollback-out/ in Editor (it will replace the current values)
```

The skill keeps `campaign_v1.json`, `campaign_v2.json`, ... so you can always go back.
