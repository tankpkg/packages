#!/usr/bin/env python3
"""Track flight prices over time. Agent-driven, no cron needed.

Stores watched routes in a JSON file. The agent calls 'add' to watch a route,
'check' to re-search all watched routes and report price changes, and
'remove' to stop watching.

Storage: /tmp/flight-tracker/watches.json (persists until system reboot)

Requires: pip install fast-flights playwright (for 'check' command only)

Usage:
  python flight_tracker.py add --origin JFK --destination LHR --date 2026-09-15
  python flight_tracker.py list
  python flight_tracker.py check
  python flight_tracker.py check --id 0
  python flight_tracker.py remove --id 0
"""

import argparse, json, os, sys, tempfile
from datetime import datetime
from pathlib import Path

TRACKER_DIR = Path("/tmp/flight-tracker")
WATCHES_FILE = TRACKER_DIR / "watches.json"
MAX_PRICE_HISTORY = 100


def load_watches():
    if not WATCHES_FILE.exists():
        return []
    try:
        with open(WATCHES_FILE) as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, OSError):
        return []


def save_watches(watches):
    TRACKER_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp_path = tempfile.mkstemp(dir=TRACKER_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(watches, f, indent=2)
        os.replace(tmp_path, WATCHES_FILE)
    except BaseException:
        os.unlink(tmp_path)
        raise


def cmd_add(args):
    watches = load_watches()
    watch = {
        "origin": args.origin.upper(),
        "destination": args.destination.upper(),
        "date": args.date,
        "return_date": getattr(args, "return_date", None),
        "added_at": datetime.now().isoformat(),
        "price_history": [],
    }
    watches.append(watch)
    save_watches(watches)
    return {
        "action": "added",
        "id": len(watches) - 1,
        "watch": watch,
        "note": "Run 'check' to fetch the initial price snapshot.",
    }


def cmd_list(args):
    watches = load_watches()
    if not watches:
        return {"watches": [], "note": "No flights being tracked. Use 'add' to start."}

    result = []
    for i, w in enumerate(watches):
        last_price = w["price_history"][-1] if w["price_history"] else None
        result.append(
            {
                "id": i,
                "route": f"{w['origin']} -> {w['destination']}",
                "date": w["date"],
                "return_date": w.get("return_date"),
                "last_price": last_price.get("price") if last_price else None,
                "last_checked": last_price.get("checked_at") if last_price else None,
                "snapshots": len(w["price_history"]),
            }
        )
    return {"watches": result}


def cmd_remove(args):
    watches = load_watches()
    if args.id < 0 or args.id >= len(watches):
        return {"error": f"Invalid watch ID {args.id}. Use 'list' to see valid IDs."}
    removed = watches.pop(args.id)
    save_watches(watches)
    return {
        "action": "removed",
        "removed": f"{removed['origin']} -> {removed['destination']} on {removed['date']}",
        "remaining": len(watches),
    }


def fetch_price(origin, destination, date, return_date=None):
    try:
        from fast_flights import FlightData, Passengers, get_flights
    except ImportError:
        return None, "fast-flights not installed (pip install fast-flights playwright)"

    flight_data = [FlightData(date=date, from_airport=origin, to_airport=destination)]
    trip = "one-way"
    if return_date:
        flight_data.append(
            FlightData(date=return_date, from_airport=destination, to_airport=origin)
        )
        trip = "round-trip"

    try:
        result = get_flights(
            flight_data=flight_data,
            trip=trip,
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="local",
        )
    except Exception as e:
        return None, f"Search failed: {e}"

    if not result.flights:
        return None, "No flights found"

    best = result.flights[0]
    return {
        "price": best.price,
        "airlines": best.name,
        "duration": best.duration,
        "stops": best.stops,
        "checked_at": datetime.now().isoformat(),
    }, None


def cmd_check(args):
    watches = load_watches()
    if not watches:
        return {"error": "No flights being tracked. Use 'add' first."}

    indices = [args.id] if args.id is not None else range(len(watches))
    results = []

    for i in indices:
        if i < 0 or i >= len(watches):
            results.append({"id": i, "error": f"Invalid watch ID {i}"})
            continue

        w = watches[i]
        snapshot, err = fetch_price(
            w["origin"], w["destination"], w["date"], w.get("return_date")
        )

        if err:
            results.append(
                {"id": i, "route": f"{w['origin']} -> {w['destination']}", "error": err}
            )
            continue

        prev = w["price_history"][-1] if w["price_history"] else None
        w["price_history"].append(snapshot)
        if len(w["price_history"]) > MAX_PRICE_HISTORY:
            w["price_history"] = w["price_history"][-MAX_PRICE_HISTORY:]

        entry = {
            "id": i,
            "route": f"{w['origin']} -> {w['destination']}",
            "date": w["date"],
            "current_price": snapshot["price"],
            "airlines": snapshot["airlines"],
            "snapshots_total": len(w["price_history"]),
        }

        if prev:
            entry["previous_price"] = prev["price"]
            entry["previous_checked"] = prev["checked_at"]
            entry["changed"] = snapshot["price"] != prev["price"]
        else:
            entry["note"] = "First snapshot recorded"

        results.append(entry)

    save_watches(watches)
    return {"results": results}


def format_markdown(result, command):
    if isinstance(result, dict) and "error" in result:
        return f"**Error:** {result['error']}\n"

    if command == "add":
        w = result.get("watch", {})
        return (
            f"## Tracking Added\n\n"
            f"**Route:** {w.get('origin', '?')} → {w.get('destination', '?')}\n"
            f"**Date:** {w.get('date', '?')}\n"
            f"**ID:** {result.get('id', '?')}\n\n"
            f"> Run `check` to fetch the initial price snapshot.\n"
        )

    if command == "list":
        watches = result.get("watches", [])
        if not watches:
            return "No flights being tracked. Use `add` to start.\n"
        lines = ["## Tracked Flights", ""]
        lines.append("| ID | Route | Date | Last Price | Last Checked | Snapshots |")
        lines.append("|----|-------|------|------------|-------------|-----------|")
        for w in watches:
            lines.append(
                f"| {w['id']} | {w['route']} | {w['date']} "
                f"| {w.get('last_price') or '-'} "
                f"| {w.get('last_checked', '-')[:16] if w.get('last_checked') else '-'} "
                f"| {w.get('snapshots', 0)} |"
            )
        return "\n".join(lines)

    if command == "remove":
        return f"Removed: {result.get('removed', '?')}. {result.get('remaining', 0)} watches remaining.\n"

    if command == "check":
        entries = result.get("results", [])
        if not entries:
            return "No results.\n"
        lines = ["## Price Check Results", ""]
        for e in entries:
            if "error" in e:
                lines.append(f"**{e['route']}:** Error — {e['error']}")
                continue
            lines.append(f"### {e['route']} ({e['date']})")
            lines.append(
                f"- **Current:** {e.get('current_price', '?')} ({e.get('airlines', '?')})"
            )
            if e.get("previous_price"):
                changed = "changed" if e.get("changed") else "unchanged"
                lines.append(
                    f"- **Previous:** {e['previous_price']} (checked {e.get('previous_checked', '?')[:16]}) — **{changed}**"
                )
            elif e.get("note"):
                lines.append(f"- *{e['note']}*")
            lines.append("")
        return "\n".join(lines)

    return json.dumps(result, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Track flight prices over time")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Watch a route")
    p_add.add_argument("--origin", required=True)
    p_add.add_argument("--destination", required=True)
    p_add.add_argument("--date", required=True, help="Departure date YYYY-MM-DD")
    p_add.add_argument("--return-date", help="Return date YYYY-MM-DD")

    sub.add_parser("list", help="List watched routes")

    p_check = sub.add_parser("check", help="Re-check prices for watched routes")
    p_check.add_argument(
        "--id", type=int, default=None, help="Check specific watch ID only"
    )

    p_remove = sub.add_parser("remove", help="Stop watching a route")
    p_remove.add_argument("--id", type=int, required=True, help="Watch ID to remove")

    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON instead of markdown"
    )
    args = parser.parse_args()

    handlers = {
        "add": cmd_add,
        "list": cmd_list,
        "check": cmd_check,
        "remove": cmd_remove,
    }
    result = handlers[args.command](args)

    if args.json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    else:
        print(format_markdown(result, args.command))

    if isinstance(result, dict) and "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
