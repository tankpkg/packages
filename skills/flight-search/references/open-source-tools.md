# Open-Source Flight Search Tools

Sources: GitHub repos (AWeirdDev/flights, LetsFG, irrisolto/skyscanner),
PyPI package docs, 2025-2026 community research

Covers: open-source tools for searching flights without paid API keys.

## fast-flights — The Primary Tool

**Repo**: github.com/AWeirdDev/flights (920+ stars, MIT, active)
**Install**: `pip install fast-flights playwright && playwright install chromium`
**How**: Reverse-engineers Google Flights' URL protobuf encoding
**Speed**: ~3 seconds per search
**Browser spawning**: None (uses Playwright headless only for consent pages)

### How It Works

Google Flights encodes search parameters as Base64-encoded Protocol Buffers
in the URL. fast-flights constructs these protobuf payloads directly and
parses the HTML response. No browser automation, no API key, no scraping
overhead.

The `local` fetch mode uses Playwright headless to handle Google's EU consent
page automatically. This spawns a single headless browser instance briefly,
not 200 visible windows.

### Usage

```python
from fast_flights import FlightData, Passengers, get_flights

result = get_flights(
    flight_data=[
        FlightData(date="2026-07-15", from_airport="AMM", to_airport="SYD"),
        FlightData(date="2026-07-25", from_airport="SYD", to_airport="AMM"),
    ],
    trip="round-trip",
    seat="economy",
    passengers=Passengers(adults=1),
    fetch_mode="local",
)

for f in result.flights:
    print(f"{f.price} | {f.name} | {f.departure} -> {f.arrival} | {f.duration}")

print(f"Price level: {result.current_price}")
```

### CLI Script

```bash
python scripts/search_google_flights.py --origin AMM --destination SYD --date 2026-07-15 --return-date 2026-07-25
```

### API Reference

```python
get_flights(
    flight_data: list[FlightData],    # origin/dest/date per leg
    trip: "round-trip" | "one-way" | "multi-city",
    seat: "economy" | "premium-economy" | "business" | "first",
    passengers: Passengers(adults=N),
    max_stops: int | None = None,     # 0 for nonstop
    fetch_mode: "common" | "local" = "local",  # use "local" for consent bypass
) -> Result
```

Result fields:
- `result.flights` — list of Flight objects
- `result.current_price` — "low", "typical", or "high"

Flight fields:
- `f.price` — price string (e.g., "$1,557" or "€1,557")
- `f.name` — airline names (e.g., "Qatar Airways, Virgin Australia")
- `f.departure` — departure time string
- `f.arrival` — arrival time string
- `f.duration` — total duration string
- `f.stops` — number of stops (int)
- `f.delay` — delay info if available

### fetch_mode Options

| Mode | How | When |
|------|-----|------|
| `common` | HTTP request via primp (Rust HTTP client) | Works if no consent page |
| `local` | Playwright headless (1 instance, auto-handles consent) | Default — works everywhere |
| `fallback` | Try common first, fall back to local | If you want to minimize Playwright usage |

### Limitations

- Google Flights data only (not Skyscanner/Kayak)
- v2.2 is current stable; v3.0 is release candidate with different API
- Price currency follows Google's geo-detection (use comparison links for USD)
- Playwright + chromium needed for `local` mode (~200MB disk)

## LetsFG — Heavy Alternative (Not Recommended as Default)

**Repo**: github.com/LetsFG/LetsFG (212+ stars, MIT)
**Install**: `pip install letsfg`
**Coverage**: 400+ airlines including Skyscanner, Ryanair, Spirit, Southwest

### Why Not Primary

LetsFG launches 200+ Playwright browser instances simultaneously to search
every airline connector in parallel. In practice this:
- Spawns ~100 visible browser windows
- Takes 3+ minutes per search
- Uses massive CPU/RAM
- Many connectors fail with 403/timeout errors

The 400+ airline coverage is impressive on paper, but the execution is too
resource-heavy for a responsive agent tool. Use fast-flights for instant
results + Skyscanner/Kayak comparison links instead.

### When to Consider LetsFG

- You need airlines not on Google Flights (rare edge case)
- You're running on a high-resource server, not a laptop
- You're OK with 3+ minute search times
- You want booking capability (LetsFG can book, fast-flights cannot)

## irrisolto/skyscanner — Skyscanner Android API (Fragile)

**Repo**: github.com/irrisolto/skyscanner (33 stars, GPL-3)
**Status**: Partially broken as of Feb 2026

Reverse-engineers Skyscanner's Android app API by impersonating the
PerimeterX mobile SDK. Clever approach but fragile — breaks when Skyscanner
updates their anti-bot SDK. Open issue reports persistent 403 errors.

Not recommended for the skill's default workflow. Documented here as a
reference for users who specifically need Skyscanner API access.

## Tool Selection Summary

| Need | Use | Speed |
|------|-----|-------|
| Default flight search | fast-flights (`search_google_flights.py`) | ~3s |
| No pip install possible | Chrome DevTools scraping | ~10s |
| SerpAPI key available | `search_flights.py` | ~2s |
| Skyscanner prices | Comparison link (manual) | User clicks |
| 400+ airline deep search | LetsFG (heavy, slow) | 3+ min |
