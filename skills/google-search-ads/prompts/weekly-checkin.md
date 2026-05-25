# Weekly Check-in (cron-triggered)

Time for your weekly Google Search Ads review. Please export these 5 CSV reports from Google Ads UI (last 7 days), then paste or upload them in this conversation.

**Where to find each report:**

| Report | UI path |
|---|---|
| Campaign report | Insights & reports → Predefined reports → Campaign → Set date range to "Last 7 days" → Download CSV |
| Ad group report | Insights & reports → Predefined reports → Ad group → Last 7 days → Download CSV |
| Search terms report | Insights & reports → Predefined reports → Search terms → Last 7 days → Download CSV |
| Search keyword report | Insights & reports → Predefined reports → Search keyword → Add columns: Quality Score, Expected CTR, Ad Relevance, Landing page experience → Last 7 days → Download CSV |
| Ad report | Insights & reports → Predefined reports → Ad → Last 7 days → Download CSV |

Once you upload them:

1. I'll run `normalize_report.py` to parse each file.
2. Run `diagnose.py` against your latest `campaign.json`.
3. Show you a ranked findings list (critical → high → medium → low).
4. Ask you to confirm before applying auto-fixable items.
5. If you approve, run `revise.py` → produce `campaign_v{N+1}.json` + `DIFF.md` + new CSVs.
6. You re-import the new CSVs via Google Ads Editor.

If there's nothing concerning this week, the report will say so — no busy work.

Reply with the 5 CSV files (or `skip` if you don't have time today).
