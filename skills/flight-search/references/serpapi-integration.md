# SerpAPI Google Flights Integration

Sources: SerpAPI official documentation (serpapi.com), Google Flights API reference,
SerpAPI blog posts (2025-2026)

Covers: complete integration guide for the SerpAPI Google Flights engine including
endpoints, parameters, response parsing, and round-trip workflow.

## Endpoint

```
GET https://serpapi.com/search?engine=google_flights
```

All parameters are query string parameters. Auth via `api_key` parameter.

## Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `engine` | string | Must be `google_flights` |
| `api_key` | string | Your SerpAPI key |
| `departure_id` | string | Origin IATA code(s), comma-separated for multi-airport |
| `arrival_id` | string | Destination IATA code(s) |
| `outbound_date` | string | `YYYY-MM-DD` format |

## Key Optional Parameters

| Parameter | Values | Default | Notes |
|-----------|--------|---------|-------|
| `return_date` | `YYYY-MM-DD` | (one-way) | Omit for one-way |
| `type` | `1`/`2`/`3` | `1` | Round-trip / One-way / Multi-city |
| `travel_class` | `1`-`4` | `1` | Economy / Premium Eco / Business / First |
| `adults` | 1-9 | 1 | Adult passengers |
| `children` | 0-9 | 0 | Ages 2-11 |
| `infants_in_seat` | 0-9 | 0 | Under 2, own seat |
| `infants_on_lap` | 0-9 | 0 | Under 2, on lap |
| `stops` | `0`-`3` | `0` | Any / Nonstop / 1 stop max / 2 stops max |
| `currency` | ISO 4217 | `USD` | Price currency |
| `hl` | language code | `en` | UI language |
| `deep_search` | `true`/`false` | `false` | Browser-identical results (slower) |
| `show_hidden` | `true`/`false` | `false` | Include "View more flights" results |
| `max_price` | integer | - | Max total price filter |

### Multi-Airport Example

```
departure_id=JFK,EWR,LGA&arrival_id=LHR,LGW
```

Searches all NYC-area airports to all London airports.

### Airline Filtering

| Parameter | Description |
|-----------|-------------|
| `include_airlines` | Comma-separated IATA codes to include (e.g., `UA,DL`) |
| `exclude_airlines` | Comma-separated IATA codes to exclude |

## Response Structure

### Top-Level Fields

```json
{
  "search_metadata": { "id": "...", "status": "Success", "created_at": "..." },
  "search_parameters": { ... },
  "best_flights": [ ... ],
  "other_flights": [ ... ],
  "price_insights": { ... },
  "airports": [ ... ]
}
```

- `best_flights`: Google's recommended flights (top picks)
- `other_flights`: All remaining results
- `price_insights`: Price analysis for this route

### Flight Object

```json
{
  "flights": [
    {
      "departure_airport": { "name": "JFK", "id": "JFK", "time": "2026-06-01 08:00" },
      "arrival_airport": { "name": "Heathrow", "id": "LHR", "time": "2026-06-01 20:15" },
      "duration": 435,
      "airplane": "Boeing 777",
      "airline": "British Airways",
      "airline_logo": "https://www.gstatic.com/flights/airline_logos/70px/BA.png",
      "flight_number": "BA 178",
      "travel_class": "Economy",
      "legroom": "31 in",
      "overnight": false,
      "often_delayed_by_over_30_min": false,
      "extensions": ["Wi-Fi for a fee", "In-seat power & USB outlets"]
    }
  ],
  "layovers": [
    { "duration": 120, "name": "Dublin Airport", "id": "DUB", "overnight": false }
  ],
  "total_duration": 615,
  "carbon_emissions": { "this_flight": 612000, "typical_for_this_route": 665000, "difference_percent": -8 },
  "price": 892,
  "type": "Round trip",
  "airline_logo": "https://...",
  "departure_token": "WyJDal...",
  "booking_token": "..."
}
```

### Key Fields for Display

| Field | Path | Type | Notes |
|-------|------|------|-------|
| Price | `.price` | integer | Total price in requested currency |
| Duration | `.total_duration` | integer | Minutes |
| Stops | `.flights` length - 1 | computed | 0 = nonstop |
| Airlines | `.flights[].airline` | string | Per segment |
| Departure | `.flights[0].departure_airport.time` | string | Local time |
| Arrival | `.flights[-1].arrival_airport.time` | string | Local time |
| Legroom | `.flights[].legroom` | string | e.g., "31 in" |
| Delay risk | `.flights[].often_delayed_by_over_30_min` | boolean | |
| CO2 | `.carbon_emissions.this_flight` | integer | Grams |
| Booking | `.booking_token` | string | For booking options call |

### Price Insights

```json
{
  "price_insights": {
    "lowest_price": 892,
    "price_level": "typical",
    "typical_price_range": [800, 1100],
    "price_history": [[1714521600, 945], [1714608000, 912], ...]
  }
}
```

`price_level` is one of: `"low"`, `"typical"`, `"high"`.

## Round-Trip Workflow (2-3 API calls)

Round-trip searches require multiple calls because Google Flights shows
outbound first, then return flights based on the selected outbound.

### Step 1: Search Outbound

```
GET /search?engine=google_flights
  &departure_id=JFK&arrival_id=LHR
  &outbound_date=2026-06-01&return_date=2026-06-10
  &type=1&api_key=KEY
```

Returns outbound flights. Each result has a `departure_token`.

### Step 2: Get Return Flights (Optional)

To see return flight options for a specific outbound, use the `departure_token`:

```
GET /search?engine=google_flights
  &departure_token=WyJDal...
  &api_key=KEY
```

This returns inbound flights paired with the selected outbound, including
the total round-trip price.

### Step 3: Get Booking Options (Optional)

Use the `booking_token` from the selected flight:

```
GET /search?engine=google_flights
  &booking_token=...
  &api_key=KEY
```

Returns OTA booking links (Expedia, airline sites, etc.) with prices.

### Practical Shortcut

For most use cases, Step 1 alone is sufficient. The initial round-trip
search returns combined outbound+return prices. Steps 2-3 are only needed
if you want to show return flight choices or booking links.

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Parse results |
| 400 | Invalid parameters | Check departure_id/arrival_id format |
| 401 | Invalid API key | Verify SERPAPI_KEY |
| 429 | Rate limit exceeded | Wait, check plan limits |
| Empty `best_flights` + `other_flights` | No results for this route/date | Try different dates or nearby airports |

## Caching Behavior

SerpAPI caches results for approximately 1 hour. Cached responses:
- Are returned instantly
- Do NOT count toward your monthly quota
- Are identical to fresh results for most routes (prices change slowly)

To force a fresh search, add `no_cache=true` (this always counts as a search).

## Code Pattern

```python
import os, requests

def search_flights_serpapi(origin, destination, date, return_date=None,
                           adults=1, travel_class=1, stops=0, currency="USD"):
    params = {
        "engine": "google_flights",
        "api_key": os.environ["SERPAPI_KEY"],
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date,
        "type": "1" if return_date else "2",
        "adults": str(adults),
        "travel_class": str(travel_class),
        "stops": str(stops),
        "currency": currency,
        "hl": "en",
    }
    if return_date:
        params["return_date"] = return_date

    resp = requests.get("https://serpapi.com/search", params=params)
    resp.raise_for_status()
    data = resp.json()

    flights = []
    for section in ["best_flights", "other_flights"]:
        for f in data.get(section, []):
            segments = f.get("flights", [])
            flights.append({
                "price": f.get("price"),
                "currency": currency,
                "total_duration_min": f.get("total_duration"),
                "stops": len(segments) - 1,
                "airlines": [s.get("airline") for s in segments],
                "departure": segments[0]["departure_airport"]["time"] if segments else None,
                "arrival": segments[-1]["arrival_airport"]["time"] if segments else None,
                "origin": segments[0]["departure_airport"]["id"] if segments else origin,
                "destination": segments[-1]["arrival_airport"]["id"] if segments else destination,
                "legroom": segments[0].get("legroom") if segments else None,
                "co2_grams": f.get("carbon_emissions", {}).get("this_flight"),
                "booking_token": f.get("booking_token"),
                "is_best": section == "best_flights",
            })

    price_insights = data.get("price_insights", {})
    return {"flights": flights, "price_insights": price_insights}
```
