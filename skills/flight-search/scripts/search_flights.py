#!/usr/bin/env python3
"""Flight search using SerpAPI Google Flights (primary) or Amadeus (fallback).

Environment variables:
  SERPAPI_KEY              - SerpAPI key (250 free searches/month)
  AMADEUS_CLIENT_ID       - Amadeus API key (optional fallback)
  AMADEUS_CLIENT_SECRET   - Amadeus API secret (optional fallback)

Usage:
  python search_flights.py --origin JFK --destination LHR --date 2026-06-01
  python search_flights.py --origin JFK --destination LHR --date 2026-06-01 --return-date 2026-06-10
  python search_flights.py --origin JFK --destination LHR --date 2026-06-01 --adults 2 --class business --nonstop
"""

import argparse, json, os, sys, re
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError


def serpapi_search(
    origin,
    destination,
    date,
    return_date=None,
    adults=1,
    travel_class=1,
    nonstop=False,
    currency="USD",
    max_results=10,
):
    """Search via SerpAPI Google Flights engine."""
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        return None

    params = {
        "engine": "google_flights",
        "api_key": key,
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date,
        "type": "1" if return_date else "2",
        "adults": str(adults),
        "travel_class": str(travel_class),
        "currency": currency,
        "hl": "en",
    }
    if return_date:
        params["return_date"] = return_date
    if nonstop:
        params["stops"] = "1"  # 1 = nonstop only in SerpAPI

    url = f"https://serpapi.com/search?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "FlightSearchSkill/1.0"})

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"SerpAPI HTTP {e.code}", "detail": body}

    flights = []
    for section in ["best_flights", "other_flights"]:
        for f in data.get(section, []):
            segments = f.get("flights", [])
            if not segments:
                continue

            layover_info = []
            for lay in f.get("layovers", []):
                layover_info.append(
                    {
                        "airport": lay.get("name", ""),
                        "code": lay.get("id", ""),
                        "duration_min": lay.get("duration", 0),
                    }
                )

            flights.append(
                {
                    "price": f.get("price"),
                    "currency": currency,
                    "total_duration_min": f.get("total_duration"),
                    "stops": len(segments) - 1,
                    "airlines": list(
                        dict.fromkeys(s.get("airline", "") for s in segments)
                    ),
                    "flight_numbers": [s.get("flight_number", "") for s in segments],
                    "departure_time": segments[0]
                    .get("departure_airport", {})
                    .get("time"),
                    "arrival_time": segments[-1].get("arrival_airport", {}).get("time"),
                    "origin": segments[0]
                    .get("departure_airport", {})
                    .get("id", origin),
                    "destination": segments[-1]
                    .get("arrival_airport", {})
                    .get("id", destination),
                    "aircraft": [s.get("airplane", "") for s in segments],
                    "legroom": segments[0].get("legroom"),
                    "co2_grams": f.get("carbon_emissions", {}).get("this_flight"),
                    "delay_risk": any(
                        s.get("often_delayed_by_over_30_min", False) for s in segments
                    ),
                    "layovers": layover_info,
                    "booking_token": f.get("booking_token"),
                    "is_best": section == "best_flights",
                    "source": "google_flights",
                }
            )

    price_insights = data.get("price_insights", {})
    return {
        "flights": flights[:max_results],
        "total_found": len(flights),
        "price_insights": price_insights,
        "source": "serpapi_google_flights",
    }


_amadeus_token_cache = {"token": None, "expiry": 0}


def amadeus_auth(client_id, client_secret, base_url):
    import time

    if (
        _amadeus_token_cache["token"]
        and time.time() < _amadeus_token_cache["expiry"] - 60
    ):
        return _amadeus_token_cache["token"]
    data = urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = Request(
        f"{base_url}/v1/security/oauth2/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlopen(req, timeout=15) as resp:
            resp_data = json.loads(resp.read().decode())
    except HTTPError as e:
        raise RuntimeError(
            f"Amadeus auth failed (HTTP {e.code}). Check AMADEUS_CLIENT_ID/SECRET."
        ) from e
    _amadeus_token_cache["token"] = resp_data["access_token"]
    _amadeus_token_cache["expiry"] = time.time() + resp_data.get("expires_in", 1799)
    return _amadeus_token_cache["token"]


def parse_iso_duration(dur):
    """PT14H30M -> 870 minutes."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", dur or "")
    if not m:
        return 0
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def amadeus_search(
    origin,
    destination,
    date,
    return_date=None,
    adults=1,
    travel_class="ECONOMY",
    nonstop=False,
    currency="USD",
    max_results=10,
):
    """Search via Amadeus Self-Service API (fallback, limited airline coverage)."""
    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    base_url = (
        "https://api.amadeus.com"
        if os.environ.get("AMADEUS_PRODUCTION")
        else "https://test.api.amadeus.com"
    )
    token = amadeus_auth(client_id, client_secret, base_url)

    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": date,
        "adults": str(adults),
        "travelClass": travel_class,
        "nonStop": "true" if nonstop else "false",
        "currencyCode": currency,
        "max": str(min(max_results, 250)),
    }
    if return_date:
        params["returnDate"] = return_date

    url = f"{base_url}/v2/shopping/flight-offers?{urlencode(params)}"
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "FlightSearchSkill/1.0",
        },
    )

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return {"error": f"Amadeus HTTP {e.code}", "detail": body}

    carriers = data.get("dictionaries", {}).get("carriers", {})
    flights = []

    for offer in data.get("data", []):
        itinerary = offer.get("itineraries", [{}])[0]
        segments = itinerary.get("segments", [])
        if not segments:
            continue
        price = offer.get("price", {})

        flights.append(
            {
                "price": float(price.get("grandTotal", "0")),
                "currency": price.get("currency", currency),
                "total_duration_min": parse_iso_duration(itinerary.get("duration")),
                "stops": len(segments) - 1,
                "airlines": list(
                    dict.fromkeys(
                        carriers.get(s.get("carrierCode", ""), s.get("carrierCode", ""))
                        for s in segments
                    )
                ),
                "flight_numbers": [
                    f"{s.get('carrierCode', '')}{s.get('number', '')}" for s in segments
                ],
                "departure_time": segments[0].get("departure", {}).get("at"),
                "arrival_time": segments[-1].get("arrival", {}).get("at"),
                "origin": segments[0].get("departure", {}).get("iataCode", origin),
                "destination": segments[-1]
                .get("arrival", {})
                .get("iataCode", destination),
                "aircraft": [],
                "legroom": None,
                "co2_grams": None,
                "delay_risk": False,
                "layovers": [],
                "booking_token": None,
                "is_best": False,
                "source": "amadeus_gds",
            }
        )

    return {
        "flights": flights[:max_results],
        "total_found": len(flights),
        "price_insights": {},
        "source": "amadeus_self_service",
        "note": "Amadeus excludes American Airlines, Delta, British Airways, and low-cost carriers",
    }


CLASS_MAP = {
    "economy": ("1", "ECONOMY"),
    "premium": ("2", "PREMIUM_ECONOMY"),
    "business": ("3", "BUSINESS"),
    "first": ("4", "FIRST"),
}


def main():
    parser = argparse.ArgumentParser(description="Search flights across multiple APIs")
    parser.add_argument("--origin", required=True, help="Origin IATA code (e.g., JFK)")
    parser.add_argument(
        "--destination", required=True, help="Destination IATA code (e.g., LHR)"
    )
    parser.add_argument("--date", required=True, help="Departure date YYYY-MM-DD")
    parser.add_argument(
        "--return-date", help="Return date YYYY-MM-DD (omit for one-way)"
    )
    parser.add_argument(
        "--adults", type=int, default=1, help="Number of adults (default 1)"
    )
    parser.add_argument(
        "--class",
        dest="travel_class",
        default="economy",
        choices=["economy", "premium", "business", "first"],
    )
    parser.add_argument("--nonstop", action="store_true", help="Nonstop flights only")
    parser.add_argument(
        "--currency", default="USD", help="Price currency (default USD)"
    )
    parser.add_argument("--max", type=int, default=10, help="Max results (default 10)")
    args = parser.parse_args()

    serpapi_class, amadeus_class = CLASS_MAP[args.travel_class]

    # Try SerpAPI first (comprehensive coverage)
    result = serpapi_search(
        args.origin.upper(),
        args.destination.upper(),
        args.date,
        return_date=args.return_date,
        adults=args.adults,
        travel_class=int(serpapi_class),
        nonstop=args.nonstop,
        currency=args.currency,
        max_results=args.max,
    )

    if result and "error" not in result and result.get("flights"):
        json.dump(result, sys.stdout, indent=2)
        return

    # Fallback to Amadeus (limited airline coverage)
    result = amadeus_search(
        args.origin.upper(),
        args.destination.upper(),
        args.date,
        return_date=args.return_date,
        adults=args.adults,
        travel_class=amadeus_class,
        nonstop=args.nonstop,
        currency=args.currency,
        max_results=args.max,
    )

    if result and "error" not in result:
        json.dump(result, sys.stdout, indent=2)
        return

    # No API configured
    json.dump(
        {
            "error": "No flight API configured",
            "setup": {
                "option_1": "Set SERPAPI_KEY env var (get free key at serpapi.com, 250 searches/month)",
                "option_2": "Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET (get free at developers.amadeus.com)",
            },
        },
        sys.stdout,
        indent=2,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
