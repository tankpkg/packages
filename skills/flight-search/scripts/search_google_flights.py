#!/usr/bin/env python3
"""Search Google Flights via fast-flights (protobuf reverse-engineering).

No API key needed. No browser spawning. Uses Google's internal protobuf
format to query flights.google.com directly.

Requires: pip install fast-flights playwright && playwright install chromium
  (playwright is needed because EU/some IPs hit Google's consent page;
   the 'local' fetch mode uses Playwright to handle that automatically)

Usage:
  python search_google_flights.py --origin AMM --destination SYD --date 2026-07-15
  python search_google_flights.py --origin JFK --destination LHR --date 2026-06-01 --return-date 2026-06-10
  python search_google_flights.py --origin JFK --destination LAX --date 2026-09-01 --class business --max 5
"""

import argparse, json, sys


def search(
    origin,
    destination,
    date,
    return_date=None,
    adults=1,
    seat="economy",
    max_stops=None,
    max_results=10,
):
    try:
        from fast_flights import FlightData, Passengers, get_flights
    except ImportError:
        return {
            "error": "fast-flights not installed",
            "setup": "pip install fast-flights playwright && playwright install chromium",
        }

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
            seat=seat,
            passengers=Passengers(adults=adults),
            max_stops=max_stops,
            fetch_mode="local",
        )
    except RuntimeError as e:
        return {"error": f"No flights found: {e}"}
    except Exception as e:
        return {"error": f"Search failed: {type(e).__name__}: {e}"}

    flights = []
    for f in result.flights[:max_results]:
        flights.append(
            {
                "price": f.price,
                "airlines": f.name,
                "departure": f.departure,
                "arrival": f.arrival,
                "duration": f.duration,
                "stops": f.stops,
                "delay": getattr(f, "delay", None),
            }
        )

    return {
        "flights": flights,
        "total_found": len(result.flights),
        "price_level": getattr(result, "current_price", None),
        "source": "google_flights_via_fast_flights",
    }


SEAT_MAP = {
    "economy": "economy",
    "premium": "premium-economy",
    "business": "business",
    "first": "first",
}


def format_markdown(result, origin, destination, date, return_date=None):
    if "error" in result:
        return f"**Error:** {result['error']}\n"

    flights = result.get("flights", [])
    if not flights:
        return f"No flights found for {origin} → {destination} on {date}.\n"

    trip = f"{origin} → {destination}"
    header = f"## Flights: {trip} — {date}"
    if return_date:
        header += f" to {return_date}"
    header += " (round-trip)" if return_date else " (one-way)"

    level = result.get("price_level")
    if level:
        header += (
            f"\n*Prices currently **{level}** for this route. Source: Google Flights*\n"
        )

    lines = [header, ""]
    lines.append("| # | Price | Airlines | Departure | Arrival | Duration | Stops |")
    lines.append("|---|-------|----------|-----------|---------|----------|-------|")
    for i, f in enumerate(flights, 1):
        lines.append(
            f"| {i} | {f.get('price', '?')} "
            f"| {f.get('airlines', '?')} "
            f"| {f.get('departure', '?')} "
            f"| {f.get('arrival', '?')} "
            f"| {f.get('duration', '?')} "
            f"| {f.get('stops', '?')} |"
        )

    lines.append("")
    lines.append(f"*{result.get('total_found', len(flights))} total flights found.*")
    lines.append("")

    gf = f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}+on+{date}&curr=USD&hl=en"
    d1 = date.replace("-", "")[2:]
    d2 = (return_date or date).replace("-", "")[2:]
    sk = f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{destination.lower()}/{d1}/{d2}/?adultsv2=1&cabinclass=economy"
    ky = f"https://www.kayak.com/flights/{origin}-{destination}/{date}/{return_date or date}?sort=bestflight_a"

    lines.append("**Compare prices:**")
    lines.append(f"- [Google Flights]({gf})")
    lines.append(f"- [Skyscanner]({sk})")
    lines.append(f"- [Kayak]({ky})")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Search Google Flights (no API key needed)"
    )
    parser.add_argument("--origin", required=True, help="Origin IATA code")
    parser.add_argument("--destination", required=True, help="Destination IATA code")
    parser.add_argument("--date", required=True, help="Departure date YYYY-MM-DD")
    parser.add_argument("--return-date", help="Return date YYYY-MM-DD")
    parser.add_argument("--adults", type=int, default=1, help="Adults (default 1)")
    parser.add_argument(
        "--class",
        dest="seat",
        default="economy",
        choices=["economy", "premium", "business", "first"],
    )
    parser.add_argument("--nonstop", action="store_true", help="Nonstop only")
    parser.add_argument("--max", type=int, default=10, help="Max results")
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON instead of markdown"
    )
    args = parser.parse_args()

    result = search(
        args.origin.upper(),
        args.destination.upper(),
        args.date,
        return_date=args.return_date,
        adults=args.adults,
        seat=SEAT_MAP[args.seat],
        max_stops=0 if args.nonstop else None,
        max_results=args.max,
    )

    if args.json:
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    else:
        print(
            format_markdown(
                result,
                args.origin.upper(),
                args.destination.upper(),
                args.date,
                args.return_date,
            )
        )

    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
