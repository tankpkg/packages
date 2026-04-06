---
name: "@tank/flight-search"
description: |
  Search for flights, compare prices, and find cheapest dates to fly.
  Primary tool: fast-flights (pip install fast-flights) — reverse-engineers
  Google Flights' protobuf API for instant results with no API key, no browser
  spawning. Also supports Chrome DevTools scraping of Google Flights as a
  fallback, and optional SerpAPI/Amadeus/Travelpayouts for structured data.
  Includes scripts for airport code lookup (40+ cities builtin, zero deps),
  Google Flights search, SerpAPI/Amadeus search, and price calendars.
  Always provides comparison links for Google Flights, Skyscanner, and Kayak.

  Trigger phrases: "find flights", "search flights", "flight search",
  "cheap flights", "cheapest flights", "flight prices", "book a flight",
  "fly to", "flights from", "flights to", "when is cheapest to fly",
  "price calendar", "best time to fly", "nonstop flights", "direct flights",
  "round trip", "one way", "multi-city", "airline tickets", "airfare",
  "Skyscanner", "compare flights", "IATA code", "airport code"
---

# Flight Search

Search flights, compare prices, find cheapest dates — no API keys needed.

## Core Philosophy

1. **fast-flights first** — `pip install fast-flights playwright` gives you
   Google Flights data in ~3 seconds via protobuf reverse-engineering. No API
   key, no browser windows, no scraping overhead.
2. **Chrome DevTools as fallback** — If fast-flights isn't installed, scrape
   Google Flights directly via the browser. Returns the same data, takes ~10s.
3. **Paid APIs are optional** — SerpAPI, Amadeus, Travelpayouts add structured
   JSON. Nice extras, never required.
4. **City names to IATA codes** — `scripts/airport_lookup.py` resolves 40+
   cities offline, zero deps.
5. **Always give comparison links** — End every search with Google Flights +
   Skyscanner + Kayak URLs.

## Quick-Start: Common Tasks

### "Find flights from X to Y" (primary — fast-flights)

1. Resolve city names -> `scripts/airport_lookup.py "city name"`
2. Search:
   ```
   scripts/search_google_flights.py --origin AMM --destination SYD --date 2026-07-15
   ```
3. Present results as comparison table + booking links
   -> See `references/open-source-tools.md` for fast-flights details

### "Find flights from X to Y" (fallback — Chrome DevTools)

1. Build Google Flights URL and navigate via Chrome DevTools
2. Handle consent, wait for results, parse accessibility tree
   -> See `references/agent-tools-workflow.md` for step-by-step

### "When is the cheapest time to fly?"

1. Run fast-flights with different dates and compare prices
2. Or web search: `"cheapest month to fly {origin} to {dest}"`
3. With TRAVELPAYOUTS_TOKEN: `scripts/price_calendar.py`

## Workflow Priority

| Tier | Approach | Speed | Requires |
|------|----------|-------|----------|
| **1** | `search_google_flights.py` (fast-flights) | ~3s | `pip install fast-flights playwright` |
| **2** | Chrome DevTools → Google Flights | ~10s | Chrome DevTools MCP connected |
| **3** | Exa/Google web search | ~3s | Web search tool (always available) |
| **4** | `search_flights.py` (SerpAPI/Amadeus) | ~2s | SERPAPI_KEY or AMADEUS_* |

## Scripts

| Script | Purpose | Requires |
|--------|---------|----------|
| `scripts/search_google_flights.py` | Google Flights via fast-flights | `pip install fast-flights playwright` |
| `scripts/flight_tracker.py` | Track prices over time (add/check/list/remove) | fast-flights for check; add/list/remove need nothing |
| `scripts/flight_status.py` | Live flight status (delays, gates) | RAPIDAPI_KEY optional (free 600/mo) |
| `scripts/airport_lookup.py` | City name to IATA code | Nothing (40+ cities builtin) |
| `scripts/search_flights.py` | SerpAPI/Amadeus search | SERPAPI_KEY or AMADEUS_* |
| `scripts/price_calendar.py` | Cheapest price per day | TRAVELPAYOUTS_TOKEN |

## Tracking Workflows

### "Track this flight's price"

1. `flight_tracker.py add --origin JFK --destination LHR --date 2026-09-15`
2. Stores in `/tmp/flight-tracker/watches.json` with price history
3. When user asks "check my flights":
   `flight_tracker.py check` → re-searches all routes, compares to last price
4. `flight_tracker.py list` → show all watched routes + last prices
5. `flight_tracker.py remove --id 0` → stop tracking

### "Is flight BA178 on time?"

1. With RAPIDAPI_KEY: `flight_status.py BA178` → delay, gate, terminal
2. Without key: use web search for `"BA178 flight status today"`

## Decision Trees

### Query Type Routing

| User Request | Best Tool |
|-------------|-----------|
| Specific route + date | `search_google_flights.py` |
| "What's the code for Tokyo?" | `airport_lookup.py` |
| "Track JFK to LHR" | `flight_tracker.py add` then `check` |
| "Check my tracked flights" | `flight_tracker.py check` |
| "Is BA178 delayed?" | `flight_status.py BA178` or web search |
| "Cheapest day in September" | fast-flights with multiple dates |
| Need structured JSON | `search_flights.py` with SERPAPI_KEY |

### Booking Link Construction

| Engine | URL Pattern |
|--------|------------|
| Google Flights | `https://www.google.com/travel/flights?q=flights+from+{ORIGIN}+to+{DEST}+on+{DATE}&curr=USD&hl=en` |
| Skyscanner | `https://www.skyscanner.com/transport/flights/{orig}/{dest}/{YYMMDD}/{YYMMDD}/?adultsv2=1&cabinclass=economy` |
| Kayak | `https://www.kayak.com/flights/{ORIG}-{DEST}/{YYYY-MM-DD}/{YYYY-MM-DD}?sort=bestflight_a` |

## Reference Index

| File | Contents |
|------|----------|
| `references/open-source-tools.md` | fast-flights usage, LetsFG, irrisolto/skyscanner (alternatives) |
| `references/agent-tools-workflow.md` | Chrome DevTools scraping, web search fallback, URL construction |
| `references/api-comparison.md` | All flight APIs compared: pricing, limits, coverage gaps |
| `references/serpapi-integration.md` | SerpAPI Google Flights: endpoints, parameters, response parsing |
| `references/amadeus-integration.md` | Amadeus: auth, airport lookup, flight search, airline gaps |
| `references/search-strategies.md` | Query interpretation, price tips, output formatting |
