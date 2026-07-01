#!/usr/bin/env python3
"""Resolve city/airport names to IATA codes.

Uses a built-in mapping for common cities, falls back to Amadeus API for
fuzzy lookup when available.

Environment variables:
  AMADEUS_CLIENT_ID       - Amadeus API key (optional, enables fuzzy search)
  AMADEUS_CLIENT_SECRET   - Amadeus API secret

Usage:
  python airport_lookup.py "New York"
  python airport_lookup.py "tokyo"
  python airport_lookup.py "CDG"
"""

import argparse, json, os, sys
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

# Common city -> IATA mappings (covers ~80% of queries without API call)
CITY_MAP = {
    "new york": [
        {"code": "JFK", "name": "John F. Kennedy International"},
        {"code": "EWR", "name": "Newark Liberty International"},
        {"code": "LGA", "name": "LaGuardia"},
    ],
    "nyc": [
        {"code": "JFK", "name": "John F. Kennedy International"},
        {"code": "EWR", "name": "Newark Liberty International"},
        {"code": "LGA", "name": "LaGuardia"},
    ],
    "london": [
        {"code": "LHR", "name": "Heathrow"},
        {"code": "LGW", "name": "Gatwick"},
        {"code": "STN", "name": "Stansted"},
        {"code": "LTN", "name": "Luton"},
        {"code": "LCY", "name": "London City"},
    ],
    "paris": [
        {"code": "CDG", "name": "Charles de Gaulle"},
        {"code": "ORY", "name": "Orly"},
    ],
    "los angeles": [{"code": "LAX", "name": "Los Angeles International"}],
    "la": [{"code": "LAX", "name": "Los Angeles International"}],
    "chicago": [
        {"code": "ORD", "name": "O'Hare International"},
        {"code": "MDW", "name": "Midway International"},
    ],
    "san francisco": [
        {"code": "SFO", "name": "San Francisco International"},
        {"code": "OAK", "name": "Oakland International"},
        {"code": "SJC", "name": "San Jose International"},
    ],
    "sf": [{"code": "SFO", "name": "San Francisco International"}],
    "washington": [
        {"code": "IAD", "name": "Washington Dulles"},
        {"code": "DCA", "name": "Ronald Reagan National"},
        {"code": "BWI", "name": "Baltimore-Washington"},
    ],
    "dc": [
        {"code": "IAD", "name": "Washington Dulles"},
        {"code": "DCA", "name": "Ronald Reagan National"},
    ],
    "tokyo": [
        {"code": "NRT", "name": "Narita International"},
        {"code": "HND", "name": "Haneda"},
    ],
    "miami": [
        {"code": "MIA", "name": "Miami International"},
        {"code": "FLL", "name": "Fort Lauderdale-Hollywood"},
    ],
    "bangkok": [
        {"code": "BKK", "name": "Suvarnabhumi"},
        {"code": "DMK", "name": "Don Mueang"},
    ],
    "seoul": [
        {"code": "ICN", "name": "Incheon International"},
        {"code": "GMP", "name": "Gimpo International"},
    ],
    "toronto": [
        {"code": "YYZ", "name": "Toronto Pearson"},
        {"code": "YTZ", "name": "Billy Bishop Toronto City"},
    ],
    "dubai": [
        {"code": "DXB", "name": "Dubai International"},
        {"code": "DWC", "name": "Al Maktoum International"},
    ],
    "singapore": [{"code": "SIN", "name": "Singapore Changi"}],
    "hong kong": [{"code": "HKG", "name": "Hong Kong International"}],
    "tel aviv": [{"code": "TLV", "name": "Ben Gurion International"}],
    "sydney": [{"code": "SYD", "name": "Sydney Kingsford Smith"}],
    "melbourne": [{"code": "MEL", "name": "Melbourne Tullamarine"}],
    "rome": [
        {"code": "FCO", "name": "Leonardo da Vinci-Fiumicino"},
        {"code": "CIA", "name": "Ciampino"},
    ],
    "barcelona": [{"code": "BCN", "name": "Barcelona-El Prat"}],
    "madrid": [{"code": "MAD", "name": "Adolfo Suarez Madrid-Barajas"}],
    "amsterdam": [{"code": "AMS", "name": "Amsterdam Schiphol"}],
    "berlin": [{"code": "BER", "name": "Berlin Brandenburg"}],
    "frankfurt": [{"code": "FRA", "name": "Frankfurt am Main"}],
    "munich": [{"code": "MUC", "name": "Munich Airport"}],
    "istanbul": [
        {"code": "IST", "name": "Istanbul Airport"},
        {"code": "SAW", "name": "Sabiha Gokcen"},
    ],
    "boston": [{"code": "BOS", "name": "Logan International"}],
    "seattle": [{"code": "SEA", "name": "Seattle-Tacoma International"}],
    "denver": [{"code": "DEN", "name": "Denver International"}],
    "atlanta": [{"code": "ATL", "name": "Hartsfield-Jackson Atlanta International"}],
    "dallas": [
        {"code": "DFW", "name": "Dallas/Fort Worth International"},
        {"code": "DAL", "name": "Dallas Love Field"},
    ],
    "houston": [
        {"code": "IAH", "name": "George Bush Intercontinental"},
        {"code": "HOU", "name": "William P. Hobby"},
    ],
    "lisbon": [{"code": "LIS", "name": "Humberto Delgado"}],
    "dublin": [{"code": "DUB", "name": "Dublin Airport"}],
    "cancun": [{"code": "CUN", "name": "Cancun International"}],
    "mexico city": [{"code": "MEX", "name": "Benito Juarez International"}],
    "buenos aires": [
        {"code": "EZE", "name": "Ministro Pistarini"},
        {"code": "AEP", "name": "Jorge Newbery Aeropark"},
    ],
    "sao paulo": [
        {"code": "GRU", "name": "Guarulhos International"},
        {"code": "CGH", "name": "Congonhas"},
    ],
    "mumbai": [{"code": "BOM", "name": "Chhatrapati Shivaji Maharaj International"}],
    "delhi": [{"code": "DEL", "name": "Indira Gandhi International"}],
    "beijing": [
        {"code": "PEK", "name": "Beijing Capital"},
        {"code": "PKX", "name": "Beijing Daxing"},
    ],
    "shanghai": [
        {"code": "PVG", "name": "Pudong International"},
        {"code": "SHA", "name": "Hongqiao International"},
    ],
}


def lookup_local(query):
    q = query.lower().strip()

    if q in CITY_MAP:
        return [dict(a, source="builtin") for a in CITY_MAP[q]]

    if len(q) == 3 and q.isalpha():
        return [{"code": q.upper(), "name": q.upper(), "source": "iata_code"}]

    matches = []
    for city, airports in CITY_MAP.items():
        if q in city or city in q:
            matches.extend(dict(a, source="builtin", city=city) for a in airports)
    return matches


def lookup_amadeus(query):
    """Fuzzy search via Amadeus locations API."""
    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    base = "https://test.api.amadeus.com"

    # Auth
    auth_data = urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = Request(
        f"{base}/v1/security/oauth2/token",
        data=auth_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlopen(req, timeout=15) as resp:
            token = json.loads(resp.read().decode())["access_token"]
    except (HTTPError, KeyError):
        return None

    # Lookup
    params = urlencode({"keyword": query, "subType": "AIRPORT,CITY"})
    url = f"{base}/v1/reference-data/locations?{params}"
    req = Request(url, headers={"Authorization": f"Bearer {token}"})

    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError:
        return None

    results = []
    for loc in data.get("data", []):
        results.append(
            {
                "code": loc.get("iataCode", ""),
                "name": loc.get("name", ""),
                "type": loc.get("subType", ""),
                "city": loc.get("address", {}).get("cityName", ""),
                "country": loc.get("address", {}).get("countryCode", ""),
                "source": "amadeus",
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Resolve city/airport names to IATA codes"
    )
    parser.add_argument("query", help="City name, airport name, or IATA code")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    # Try local first
    results = lookup_local(args.query)

    # If no local match, try Amadeus
    if not results:
        amadeus_results = lookup_amadeus(args.query)
        if amadeus_results:
            results = amadeus_results

    if not results:
        output = {
            "query": args.query,
            "results": [],
            "note": "No matches found. Try a different spelling or set AMADEUS_CLIENT_ID + AMADEUS_CLIENT_SECRET for fuzzy search.",
        }
    else:
        output = {"query": args.query, "results": results}

    if args.json:
        json.dump(output, sys.stdout, indent=2)
    else:
        if not output["results"]:
            print(f"No airports found for '{args.query}'")
            if "note" in output:
                print(f"Tip: {output['note']}")
        else:
            for r in output["results"]:
                extra = (
                    f" ({r.get('city', '')}, {r.get('country', '')})"
                    if r.get("country")
                    else ""
                )
                print(f"  {r['code']}  {r['name']}{extra}")


if __name__ == "__main__":
    main()
