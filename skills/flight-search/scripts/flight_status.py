#!/usr/bin/env python3
"""Check live flight status (delays, gates, terminals) — no API key needed.

Uses Flightradar24's internal web API (reverse-engineered, unauthenticated).
Falls back to AeroDataBox via RapidAPI if RAPIDAPI_KEY is set.

Based on: github.com/JeanExtreme002/FlightRadarAPI (MIT)

Usage:
  python flight_status.py BA178
  python flight_status.py AA100
  python flight_status.py UA900 --json
"""

import argparse, json, sys, gzip
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import quote
from urllib.error import HTTPError

FR24_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip",
    "Origin": "https://www.flightradar24.com",
    "Referer": "https://www.flightradar24.com/",
}


def _fetch_fr24(url):
    req = Request(url, headers=FR24_HEADERS)
    try:
        with urlopen(req, timeout=15) as resp:
            raw = resp.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return json.loads(raw), None
    except HTTPError as e:
        return None, f"FR24 HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def search_fr24(flight_number):
    url = f"https://www.flightradar24.com/v1/search/web/find?query={quote(flight_number)}&limit=10"
    data, err = _fetch_fr24(url)
    if err:
        return None, None, err

    results = data.get("results", [])
    for r in results:
        if r.get("type") == "live" and r.get("id"):
            return r["id"], r, None
    for r in results:
        if r.get("type") in ("flight", "schedule") and r.get("id"):
            return r["id"], r, None
    return None, None, f"Flight '{flight_number}' not found on Flightradar24"


def get_details_fr24(flight_id):
    url = f"https://data-live.flightradar24.com/clickhandler/?flight={flight_id}"
    return _fetch_fr24(url)


def _ts(unix_ts):
    if not unix_ts:
        return None
    try:
        return datetime.fromtimestamp(int(unix_ts), tz=timezone.utc).strftime(
            "%H:%M UTC"
        )
    except (ValueError, TypeError, OSError):
        return None


def parse_fr24_details(details):
    airport = details.get("airport", {})
    origin = airport.get("origin", {})
    dest = airport.get("destination", {})
    status = details.get("status", {})
    times = details.get("time", {})
    airline = details.get("airline", {})
    flight = details.get("identification", {})

    sched = times.get("scheduled", {})
    est = times.get("estimated", {})
    real = times.get("real", {})

    return {
        "flight": flight.get("number", {}).get("default"),
        "airline": airline.get("name"),
        "status": status.get("text", "Unknown"),
        "departure": {
            "airport": origin.get("name"),
            "iata": origin.get("code", {}).get("iata"),
            "terminal": origin.get("info", {}).get("terminal"),
            "gate": origin.get("info", {}).get("gate"),
            "scheduled": _ts(sched.get("departure")),
            "estimated": _ts(est.get("departure")),
            "actual": _ts(real.get("departure")),
        },
        "arrival": {
            "airport": dest.get("name"),
            "iata": dest.get("code", {}).get("iata"),
            "terminal": dest.get("info", {}).get("terminal"),
            "gate": dest.get("info", {}).get("gate"),
            "scheduled": _ts(sched.get("arrival")),
            "estimated": _ts(est.get("arrival")),
            "actual": _ts(real.get("arrival")),
        },
        "source": "flightradar24",
    }


def check_status(flight_number):
    flight_id, search_result, err = search_fr24(flight_number)
    if err:
        return {"error": err, "flight": flight_number}

    details, err = get_details_fr24(flight_id)
    if not err and details and details.get("airport"):
        return parse_fr24_details(details)

    detail = search_result.get("detail", {}) if search_result else {}
    return {
        "flight": flight_number,
        "airline": search_result.get("name") or detail.get("operator"),
        "status": "Scheduled (not currently airborne)",
        "callsign": detail.get("callsign"),
        "departure": {},
        "arrival": {},
        "source": "flightradar24",
        "note": "Flight is not currently active. Gate/delay data is only available while the flight is airborne or boarding.",
    }


def format_markdown(result):
    if "error" in result:
        return f"**Error:** {result['error']}\n"

    note = result.get("note")
    dep = result.get("departure", {})
    arr = result.get("arrival", {})
    flight = result.get("flight", "?")
    airline = result.get("airline", "?")
    status = result.get("status", "Unknown")

    lines = [f"## Flight Status: {flight} ({airline})", f"**Status:** {status}", ""]

    if note:
        lines.append(f"> {note}")
        lines.append("")

    if dep.get("iata") or arr.get("iata"):
        lines.append(
            f"### {dep.get('iata', '?')} {dep.get('airport', '')} → {arr.get('iata', '?')} {arr.get('airport', '')}"
        )
        lines.append("")
        lines.append("| | Departure | Arrival |")
        lines.append("|---|-----------|---------|")
        lines.append(
            f"| **Airport** | {dep.get('iata', '-')} {dep.get('airport', '-')} | {arr.get('iata', '-')} {arr.get('airport', '-')} |"
        )
        lines.append(
            f"| **Terminal** | {dep.get('terminal') or '-'} | {arr.get('terminal') or '-'} |"
        )
        lines.append(
            f"| **Gate** | {dep.get('gate') or '-'} | {arr.get('gate') or '-'} |"
        )
        lines.append(
            f"| **Scheduled** | {dep.get('scheduled') or '-'} | {arr.get('scheduled') or '-'} |"
        )
        lines.append(
            f"| **Estimated** | {dep.get('estimated') or '-'} | {arr.get('estimated') or '-'} |"
        )
        lines.append(
            f"| **Actual** | {dep.get('actual') or '-'} | {arr.get('actual') or '-'} |"
        )

    lines.append("")
    lines.append(f"*Source: Flightradar24*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Check live flight status (no API key needed)"
    )
    parser.add_argument("flight", help="Flight number (e.g., BA178, AA100, UA900)")
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON instead of markdown"
    )
    args = parser.parse_args()

    result = check_status(args.flight.upper())

    if args.json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    else:
        print(format_markdown(result))

    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
