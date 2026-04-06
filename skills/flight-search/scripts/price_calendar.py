#!/usr/bin/env python3
"""Show cheapest flight prices per day for a route and month.

Uses Travelpayouts Data API (free, affiliate model) for cached price data.
Falls back to SerpAPI price_insights if available.

Environment variables:
  TRAVELPAYOUTS_TOKEN     - Travelpayouts API token (free at travelpayouts.com)
  SERPAPI_KEY             - SerpAPI key (optional, for price insights)

Usage:
  python price_calendar.py --origin JFK --destination LHR --month 2026-09
  python price_calendar.py --origin JFK --destination CDG --month 2026-06 --currency EUR
"""

import argparse, json, os, sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError
from datetime import datetime


def travelpayouts_calendar(origin, destination, month, currency="USD"):
    """Get cheapest price per day from Travelpayouts."""
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        return None

    params = {
        "origin": origin,
        "destination": destination,
        "month": month,  # YYYY-MM
        "currency": currency.lower(),
        "token": token,
    }

    url = f"https://api.travelpayouts.com/v1/prices/calendar?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "FlightSearchSkill/1.0"})

    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as e:
        return {"error": f"Travelpayouts HTTP {e.code}"}

    if not data.get("success"):
        return {"error": "Travelpayouts returned unsuccessful response", "data": data}

    prices = data.get("data", {})
    calendar = []

    for date_str, info in sorted(prices.items()):
        calendar.append(
            {
                "date": date_str,
                "price": info.get("price"),
                "airline": info.get("airline"),
                "flight_number": info.get("flight_number"),
                "departure_at": info.get("departure_at"),
                "return_at": info.get("return_at"),
                "transfers": info.get("transfers", 0),
            }
        )

    if not calendar:
        return {"error": f"No price data for {origin}->{destination} in {month}"}

    priced_entries = [d for d in calendar if d.get("price") is not None]
    if not priced_entries:
        return {"error": f"No price data for {origin}->{destination} in {month}"}
    cheapest = min(priced_entries, key=lambda x: x["price"])
    avg_price = sum(d["price"] for d in priced_entries) / len(priced_entries)

    return {
        "origin": origin,
        "destination": destination,
        "month": month,
        "currency": currency.upper(),
        "calendar": calendar,
        "cheapest_date": cheapest["date"],
        "cheapest_price": cheapest["price"],
        "average_price": round(avg_price, 2),
        "source": "travelpayouts",
        "note": "Prices are cached/historical, not real-time. Use search_flights.py for bookable prices.",
    }


def travelpayouts_cheap(origin, destination, depart_month, currency="USD"):
    """Get cheapest flights for a route (alternative endpoint)."""
    token = os.environ.get("TRAVELPAYOUTS_TOKEN")
    if not token:
        return None

    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_month,  # YYYY-MM
        "currency": currency.lower(),
        "token": token,
    }

    url = f"https://api.travelpayouts.com/v1/prices/cheap?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "FlightSearchSkill/1.0"})

    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as e:
        return {"error": f"Travelpayouts HTTP {e.code}"}

    return data


def main():
    parser = argparse.ArgumentParser(description="Show cheapest flight prices per day")
    parser.add_argument("--origin", required=True, help="Origin IATA code")
    parser.add_argument("--destination", required=True, help="Destination IATA code")
    parser.add_argument(
        "--month", required=True, help="Month as YYYY-MM (e.g., 2026-09)"
    )
    parser.add_argument("--currency", default="USD", help="Currency (default USD)")
    args = parser.parse_args()

    # Validate month format
    try:
        datetime.strptime(args.month, "%Y-%m")
    except ValueError:
        print(
            json.dumps({"error": f"Invalid month format '{args.month}'. Use YYYY-MM."}),
            file=sys.stderr,
        )
        sys.exit(1)

    result = travelpayouts_calendar(
        args.origin.upper(), args.destination.upper(), args.month, args.currency.upper()
    )

    if result is None:
        result = {
            "error": "No price calendar API configured",
            "setup": "Set TRAVELPAYOUTS_TOKEN env var (get free token at travelpayouts.com)",
        }
        json.dump(result, sys.stdout, indent=2)
        sys.exit(1)

    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
