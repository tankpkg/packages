---
name: "@tank/flight-search"
description: |
  Search for flights, compare prices, and find the cheapest dates to fly using
  real flight APIs. Covers SerpAPI Google Flights (primary, all airlines, 250
  free/month), Amadeus Self-Service (airport lookup, free tier), and
  Travelpayouts (price calendars, free). Includes ready-to-run Python scripts
  for searching flights, resolving airport codes, and viewing price calendars.
  Handles multi-API fallback, query interpretation (city names, flexible dates,
  passenger counts), and result formatting. No external dependencies beyond
  Python 3 standard library.

  Trigger phrases: "find flights", "search flights", "flight search",
  "cheap flights", "cheapest flights", "flight prices", "book a flight",
  "fly to", "flights from", "flights to", "when is cheapest to fly",
  "price calendar", "best time to fly", "nonstop flights", "direct flights",
  "round trip", "one way", "multi-city", "airline tickets", "airfare",
  "flight comparison", "compare flights", "SerpAPI flights", "Amadeus API",
  "IATA code", "airport code", "flight API"
---

# Flight Search

Search flights across real APIs, compare prices, find cheapest dates.

## Core Philosophy

1. **SerpAPI first, Amadeus second** — SerpAPI returns all airlines including
   AA, Delta, BA, and LCCs. Amadeus excludes them. Always prefer SerpAPI
   when SERPAPI_KEY is set.
2. **Scripts do the heavy lifting** — Run the Python scripts for deterministic
   API calls. Interpret and format results yourself.
3. **City names to IATA codes** — Users say "London" not "LHR". Resolve with
   the airport_lookup script before searching.
4. **Be honest about pricing** — SerpAPI free tier is 250 searches/month.
   Amadeus test data is cached/fake. Travelpayouts prices are historical.
   Always tell users the data source and freshness.

## Quick-Start: Common Tasks

### "Find flights from X to Y"

1. Resolve city names to IATA codes
   -> Run `scripts/airport_lookup.py "city name"`
2. Search flights with dates
   -> Run `scripts/search_flights.py --origin JFK --destination LHR --date 2026-06-01`
3. Format results as a comparison table
   -> See `references/search-strategies.md` for formatting patterns

### "When is the cheapest time to fly?"

1. Resolve IATA codes
2. Run `scripts/price_calendar.py --origin JFK --destination LHR --month 2026-09`
3. Show calendar with cheapest days highlighted
4. Note: Travelpayouts prices are cached, not live bookable fares

### "Which API should I use?"

-> See `references/api-comparison.md` for full decision matrix

## Environment Variables

| Variable | Required | Free Tier | Get At |
|----------|----------|-----------|--------|
| `SERPAPI_KEY` | Recommended | 250 searches/mo | serpapi.com |
| `AMADEUS_CLIENT_ID` | Optional | ~2000 calls/mo test | developers.amadeus.com |
| `AMADEUS_CLIENT_SECRET` | Optional | (same) | (same) |
| `TRAVELPAYOUTS_TOKEN` | Optional | Unlimited | travelpayouts.com |

The skill works with just SERPAPI_KEY. Additional APIs unlock airport lookup
(Amadeus) and price calendars (Travelpayouts).

## Scripts

| Script | Purpose | Required Env |
|--------|---------|-------------|
| `scripts/search_flights.py` | Search flights (SerpAPI -> Amadeus fallback) | SERPAPI_KEY or AMADEUS_* |
| `scripts/airport_lookup.py` | City name to IATA code resolution | None (builtin map), AMADEUS_* optional |
| `scripts/price_calendar.py` | Cheapest price per day in a month | TRAVELPAYOUTS_TOKEN |

All scripts use only Python 3 standard library (no pip install needed).
Run with `python scripts/<name>.py --help` for full usage.

## Decision Trees

### API Selection

| Signal | Use |
|--------|-----|
| SERPAPI_KEY set | SerpAPI Google Flights (all airlines) |
| Only AMADEUS_* set | Amadeus (missing AA, DL, BA, LCCs) |
| Neither set | Error with setup instructions |

### Query Type Routing

| User Request | Action |
|-------------|--------|
| Specific route + date | search_flights.py |
| "What's the code for Tokyo?" | airport_lookup.py |
| "Cheapest day in September" | price_calendar.py |
| "Where can I fly for under $300?" | search_flights.py with popular destinations |
| "Is this a good price?" | Check SerpAPI price_insights in response |

### Amadeus Limitation Awareness

| Route Type | Amadeus Coverage | Recommendation |
|-----------|-----------------|----------------|
| US domestic | Poor (no AA, DL, Spirit, Frontier) | Use SerpAPI |
| US-Europe | Fair (no BA, no LCCs) | Use SerpAPI |
| Europe-Europe | Fair (no Ryanair, EasyJet) | Use SerpAPI |
| Asia/Middle East | Good | Either works |

## Reference Index

| File | Contents |
|------|----------|
| `references/api-comparison.md` | All flight APIs compared: pricing, limits, coverage gaps, recommendations |
| `references/serpapi-integration.md` | SerpAPI Google Flights: endpoints, parameters, response parsing, round-trip workflow |
| `references/amadeus-integration.md` | Amadeus: auth, flight search, airport lookup, gotchas, critical airline gaps |
| `references/search-strategies.md` | Multi-API orchestration, query interpretation, price tips, output formatting |
