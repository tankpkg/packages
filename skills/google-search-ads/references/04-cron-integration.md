# Cron Integration

Sources: OpenClaw cron docs (openclaws.io/docs/automation/cron-jobs), Hermes Agent docs, Agentic OS APScheduler patterns. Plus the user's stated requirement: ASK before scheduling.

Covers: how the skill detects whether the host harness has a built-in scheduler, what payload to send if yes, and graceful fallbacks for hosts that don't.

## Why a weekly cadence

The skill's value loop is plan → analyze → revise. Without a recurring trigger, the loop dies after the user's initial setup. McDonald and Marshall both emphasize that the Search Terms Report needs weekly attention — too short and there's no data, too long and the wasted spend compounds.

Default cadence: **weekly, Monday 9am local**. Override available in the brief.

## Capability detection (host-agnostic)

`scripts/cron_detect.py` probes the agent's tool registry for any of these tool name patterns:

| Pattern | Harness |
|---|---|
| `cron.add`, `cron.list`, `cron.remove`, `cron.update`, `cron.run` | OpenClaw, Claw Gateway |
| `cron_add`, `cron_list`, `cron_remove` | Hermes Agent (older naming) |
| `scheduler.add_job`, `scheduler.remove_job` | Agentic OS (APScheduler) |
| `schedule.create`, `schedule.delete` | Generic harness conventions |

Return values:
- `"openclaw"` / `"claw"` — OpenClaw-family tooling available
- `"hermes"` — Hermes Agent tooling
- `"agentic_os"` — APScheduler-style
- `"generic"` — generic schedule.* family
- `"none"` — no cron primitive; use fallback

If detection returns `"none"`, the skill emits an `.ics` calendar file + a copy-pastable crontab line. Never silently fail to set up the loop.

## The interaction protocol

After a successful plan step, the skill asks ONCE:

> "Your campaign is ready to import. I detected [harness] supports scheduled check-ins. Want me to schedule a weekly review every Monday at 9am? I'll prompt you to upload your last-7-days reports and propose updates. (yes/no/change-time)"

Only when the user answers `yes` does the skill register the cron. Never default to yes.

If detection returns `"none"`:

> "Your campaign is ready to import. This environment doesn't have a built-in scheduler, so I'm dropping a calendar reminder file at `<path>/weekly-checkin.ics` — add it to Google/Apple Calendar. When the time comes, just ask me to run the analysis again."

## Cron payload shapes by harness

### OpenClaw / Claw Gateway

```json
{
  "name": "Google Search Ads weekly check-in",
  "schedule": {
    "kind": "cron",
    "expr": "0 9 * * MON",
    "tz": "America/Los_Angeles"
  },
  "sessionTarget": "isolated",
  "wakeMode": "next-heartbeat",
  "payload": {
    "kind": "agentTurn",
    "message": "Run @tank/google-search-ads weekly analysis. Please paste or upload your last 7 days of Google Ads CSV exports: Campaign report, Ad group report, Search terms report, Keyword report, and Ad report. I'll diagnose and propose updates.",
    "deliver": false
  },
  "isolation": {
    "postToMainPrefix": "Cron",
    "postToMainMode": "summary"
  }
}
```

Tool call:
```
cron.add(<payload above>)
```

### Hermes Agent

Identical shape to OpenClaw. Hermes uses the same persistence directory pattern (`~/.hermes/cron/jobs.json` vs `~/.openclaw/cron/jobs.json`) and the same tool names.

### Agentic OS (APScheduler)

```python
{
  "id": "google-search-ads-weekly",
  "trigger": {
    "type": "cron",
    "day_of_week": "mon",
    "hour": 9,
    "minute": 0,
    "timezone": "America/Los_Angeles"
  },
  "func": "agent.run_skill",
  "args": ["@tank/google-search-ads", "weekly-checkin"],
  "kwargs": {
    "prompt_template": "prompts/weekly-checkin.md"
  },
  "replace_existing": True
}
```

Tool call:
```
scheduler.add_job(<payload>)
```

### Generic harness (when only `schedule.create` exists)

```json
{
  "name": "google-search-ads-weekly",
  "cron": "0 9 * * MON",
  "tz": "America/Los_Angeles",
  "command": "skill:invoke @tank/google-search-ads weekly-checkin"
}
```

### Fallback — `.ics` + crontab one-liner

When detection returns `"none"`, the skill emits two files:

`assets/weekly-checkin.ics`:
```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//tank//google-search-ads//EN
BEGIN:VEVENT
UID:google-search-ads-weekly@tank
DTSTAMP:20260524T190000Z
DTSTART:20260601T090000
RRULE:FREQ=WEEKLY;BYDAY=MO
SUMMARY:Google Search Ads weekly review
DESCRIPTION:Export last 7 days of campaign + ad-group + search-terms + keyword + ad reports from Google Ads UI, then run @tank/google-search-ads analyze.
END:VEVENT
END:VCALENDAR
```

`assets/crontab-line.txt`:
```
# Add to crontab via `crontab -e`:
0 9 * * 1 echo "Time to run @tank/google-search-ads weekly check-in. Open your OpenCode session and paste your last-7d Google Ads CSV exports." | wall
```

(The `wall` fallback notifies all logged-in terminals; users on macOS or in containers can swap for `osascript -e 'display notification ...'` or a Slack webhook curl. Don't assume any particular notification surface — just provide the trigger.)

## What the cron-fired session does

The weekly check-in session is **isolated** — it starts with a fresh context (no carry-over from prior sessions) and runs through this script:

```
[cron:] Run @tank/google-search-ads weekly analysis.

1. Greet user: "Hi! Time for your weekly Google Search Ads review."
2. Request CSVs: list the 5 files needed, with exact UI paths.
3. Wait for upload / paste.
4. Run scripts/normalize_report.py on each file.
5. Run scripts/diagnose.py against the latest campaign.json.
6. Present ranked findings list (top 5 critical + top 5 high + top 5 medium).
7. Ask: "Apply auto-fixable items? (yes/select/no)"
8. If yes/select → run scripts/revise.py, emit campaign_v2.json + new CSVs + DIFF.md.
9. Remind user to re-import via Google Ads Editor.
10. Done. Schedule next run automatically (cron handles this; nothing extra needed).
```

## Versioning and history

Every revise step creates a new campaign.json named `campaign_v{N}.json` where N increments. The skill keeps:

- `campaign.json` → symlink or copy of the latest version
- `campaign_v1.json`, `campaign_v2.json`, ... → historical versions
- `diff_v1_to_v2.md`, `diff_v2_to_v3.md`, ... → per-step DIFFs
- `weekly-report-2026-05-25.md`, ... → per-run diagnostic snapshots

This way the user can roll back if a revise step turns out badly. The skill emits a `git init` recommendation in IMPORT_GUIDE.md so users tracking their ads via git get free version history.

## Decision tree

```
PLAN STEP COMPLETES
  |
  v
Detect host cron capability via cron_detect.py
  |
  v
  none?         openclaw/hermes?      agentic_os?       generic?
    |              |                       |                |
    v              v                       v                v
emit .ics +    ASK user                ASK user         ASK user
crontab line   "want weekly?"          "want weekly?"   "want weekly?"
    |              |                       |                |
    |              v                       v                v
    |          if yes → call           if yes → call    if yes → call
    |          cron.add(...)           scheduler.add_   schedule.create
    |                                  job(...)         (...)
    v
   done
```

## What NOT to do

- Never call `cron.add` without explicit user `yes`. Hosts often charge per scheduled run or per agent-turn.
- Never schedule isolated sessions to `deliver: true` with a default channel. Output goes to the main session via the standard summary post.
- Never schedule the brief itself (Step 1 in `01-plan-workflow.md`). The brief is one-time; the recurring job is the analyze + revise loop only.
- Never use a `wakeMode: "now"` for the weekly job. Use `next-heartbeat` — there's no rush.

## Source attribution

- OpenClaw cron docs: openclaws.io/docs/automation/cron-jobs
- Claw Gateway docs: docs.claw.so/engine/automation/cron-jobs
- Hermes Agent setup notes: github.com/affaan-m/everything-claude-code (HERMES-SETUP.md)
- Agentic OS: github.com/modimihir07/agentic-os (APScheduler-backed)
- iCalendar RFC 5545 for `.ics` syntax
