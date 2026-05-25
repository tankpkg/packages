#!/usr/bin/env python3
"""
cron_detect.py — Probe the host harness for a built-in scheduler.

Returns one of: openclaw | hermes | agentic_os | generic | none

The skill calls this BEFORE asking the user whether to schedule a weekly
check-in. If `none`, the skill falls back to emitting a .ics calendar file
plus a crontab line.

Detection strategies, in order:
  1. Environment variable `OMO_HOST` or `AGENT_HARNESS` if set
  2. Filesystem signature (~/.openclaw, ~/.hermes, etc.)
  3. Process tree inspection (`openclaw`, `hermes-gateway`, `agentic_os`)
  4. CLI binary in PATH
  5. Tool-registry probe (only useful when called from inside the agent —
     CLI users won't have this; the skill prompt passes available tool
     names via --tools)

Usage:
    python3 cron_detect.py
    python3 cron_detect.py --tools cron.add,cron.list,read,write
    python3 cron_detect.py --json
"""

from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


# Tool-name patterns per harness (substring match)
TOOL_PATTERNS = {
    "openclaw":     ["cron.add", "cron.list", "cron.remove", "cron.run"],
    "hermes":       ["cron_add", "cron_list", "cron_remove"],
    "agentic_os":   ["scheduler.add_job", "scheduler.remove_job"],
    "generic":      ["schedule.create", "schedule.delete"],
}

# Filesystem signatures
FS_SIGNATURES = [
    (Path.home() / ".openclaw" / "cron",   "openclaw"),
    (Path.home() / ".hermes" / "cron",     "hermes"),
    (Path.home() / ".agentic_os",          "agentic_os"),
    (Path.home() / ".claw",                "openclaw"),
]

# CLI binary names
BINARIES = {
    "openclaw":   ["openclaw"],
    "hermes":     ["hermes", "hermes-agent"],
    "agentic_os": ["agentic-os"],
}

# Environment variable values
ENV_MAPPINGS = {
    "openclaw":   ["openclaw", "claw", "claw-gateway"],
    "hermes":     ["hermes", "hermes-agent"],
    "agentic_os": ["agentic_os", "agentic-os", "agenticos"],
}


def detect_from_env() -> str | None:
    for var in ("OMO_HOST", "AGENT_HARNESS", "HARNESS"):
        v = os.environ.get(var, "").strip().lower()
        if not v:
            continue
        for harness, patterns in ENV_MAPPINGS.items():
            if v in patterns:
                return harness
    return None


def detect_from_fs() -> str | None:
    for path, harness in FS_SIGNATURES:
        if path.exists():
            return harness
    return None


def detect_from_proc() -> str | None:
    """Check parent process ancestry (Linux/macOS). Best-effort, no failure."""
    if not sys.platform.startswith(("linux", "darwin")):
        return None
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("PPid:"):
                    ppid = int(line.split()[1])
                    break
            else:
                return None
        with open(f"/proc/{ppid}/comm") as f:
            comm = f.read().strip().lower()
        for harness, names in {**BINARIES, "openclaw": ["openclaw", "claw"]}.items():
            for name in names:
                if name in comm:
                    return harness
    except Exception:
        return None
    return None


def detect_from_path() -> str | None:
    for harness, bins in BINARIES.items():
        for b in bins:
            if shutil.which(b):
                return harness
    return None


def detect_from_tools(tools: list[str]) -> str | None:
    if not tools:
        return None
    available = {t.strip() for t in tools}
    for harness, patterns in TOOL_PATTERNS.items():
        for pat in patterns:
            if pat in available:
                return harness
    return None


def detect(tools: list[str]) -> dict:
    """Return {harness, source, evidence} or {harness: 'none'}."""
    detectors = [
        ("env",   detect_from_env),
        ("tools", lambda: detect_from_tools(tools)),
        ("fs",    detect_from_fs),
        ("proc",  detect_from_proc),
        ("path",  detect_from_path),
    ]
    for source, fn in detectors:
        try:
            h = fn()
        except Exception:
            h = None
        if h:
            return {"harness": h, "source": source}
    return {"harness": "none", "source": None}


def cron_payload(harness: str, prompt_text: str, schedule_cron: str, tz: str) -> dict:
    """Generate the right shape of cron payload for the detected harness."""
    if harness in {"openclaw", "hermes"}:
        return {
            "_tool_call": "cron.add" if harness == "openclaw" else "cron_add",
            "payload": {
                "name": "Google Search Ads weekly check-in",
                "schedule": {
                    "kind": "cron",
                    "expr": schedule_cron,
                    "tz": tz,
                },
                "sessionTarget": "isolated",
                "wakeMode": "next-heartbeat",
                "payload": {
                    "kind": "agentTurn",
                    "message": prompt_text,
                    "deliver": False,
                },
                "isolation": {
                    "postToMainPrefix": "Cron",
                    "postToMainMode": "summary",
                },
            },
        }
    if harness == "agentic_os":
        # Parse cron expr (best-effort)
        parts = schedule_cron.split()
        return {
            "_tool_call": "scheduler.add_job",
            "payload": {
                "id": "google-search-ads-weekly",
                "trigger": {
                    "type": "cron",
                    "minute": parts[0],
                    "hour": parts[1],
                    "day": parts[2],
                    "month": parts[3],
                    "day_of_week": parts[4],
                    "timezone": tz,
                },
                "args": ["@tank/google-search-ads", "weekly-checkin"],
                "kwargs": {"prompt_template": "prompts/weekly-checkin.md"},
                "replace_existing": True,
            },
        }
    if harness == "generic":
        return {
            "_tool_call": "schedule.create",
            "payload": {
                "name": "google-search-ads-weekly",
                "cron": schedule_cron,
                "tz": tz,
                "command": "skill:invoke @tank/google-search-ads weekly-checkin",
            },
        }
    # none → fallback
    return {
        "_tool_call": None,
        "fallback": "ics_and_crontab",
        "ics_path": "assets/weekly-checkin.ics",
        "crontab_line": (
            f"# Add via `crontab -e`:\n"
            f"{schedule_cron} echo 'Time for @tank/google-search-ads weekly check-in.' | "
            "wall 2>/dev/null || true"
        ),
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--tools", default="",
                   help="Comma-separated list of tool names available to the agent")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("--emit-payload", action="store_true",
                   help="Also emit the cron payload for the detected harness")
    p.add_argument("--cron-expr", default="0 9 * * MON")
    p.add_argument("--tz", default="UTC")
    p.add_argument("--prompt", default=(
        "Run @tank/google-search-ads weekly analysis. "
        "Please paste or upload your last 7 days of Google Ads CSV exports: "
        "Campaign report, Ad group report, Search terms report, Keyword report, "
        "and Ad report. I'll diagnose and propose updates."
    ))
    args = p.parse_args(argv)

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    result = detect(tools)
    if args.emit_payload:
        result["cron_payload"] = cron_payload(
            result["harness"], args.prompt, args.cron_expr, args.tz)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"harness: {result['harness']}")
        if result.get("source"):
            print(f"source:  {result['source']}")
        if args.emit_payload and result.get("cron_payload"):
            print("---")
            print(json.dumps(result["cron_payload"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
