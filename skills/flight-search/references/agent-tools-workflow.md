# Flight Search Without API Keys

Sources: Google Flights URL structure, Chrome DevTools MCP accessibility tree,
Exa search patterns, 2025-2026 browser scraping research

Covers: how to find real flight prices using the agent's built-in browser
and web search tools, without any external API keys.

## Approach Priority

1. **Browser scraping (best)** — Navigate Google Flights via Chrome DevTools.
   Returns exact prices, times, airlines, layovers, CO2. Same data users see.
2. **Web search (fallback)** — Exa/Google search for price ranges from
   aggregator sites. Less precise but works without a browser connection.

## Primary: Browser Scraping via Chrome DevTools

The agent has Chrome DevTools MCP which can navigate to Google Flights,
wait for JS to render, and read the full accessibility tree.

### Step 1: Resolve Airport Codes

```bash
python3 scripts/airport_lookup.py "london"
```

### Step 2: Construct Google Flights URL

```
https://www.google.com/travel/flights?q=flights+from+{ORIGIN}+to+{DEST}+on+{MONTH}+{DAY}+{YEAR}&curr=USD&hl=en
```

Use city names or IATA codes — Google resolves both.

### Step 3: Navigate and Scrape

```
1. navigate_page(url="...", type="url")
2. Handle Google consent if it appears:
   - take_snapshot() -> find "Accept all" button -> click()
3. wait_for(text=["Best departing", "Cheapest", "$", "hr"], timeout=15000)
   - If timeout: take_snapshot(), click "Reload" if present, wait again
4. take_snapshot() -> parse the accessibility tree
```

### Step 4: Parse the Snapshot

Each flight appears as a `link` element with a full description:

```
"From 1711 US dollars round trip total. 1 stop flight with Qatar Airways
and Virgin Australia. Leaves Queen Alia International Airport at 2:20 AM on
Wednesday, July 15 and arrives at Sydney Airport at 6:10 AM on Thursday,
July 16. Total duration 20 hr 50 min. Layover (1 of 1) is a 4 hr 5 min
layover at Hamad International Airport in Doha."
```

Individual StaticText nodes provide:
- Price: `"$1,711"` + `"round trip"`
- Airlines: `"Qatar Airways, Virgin Australia"`
- Duration: `"20 hr 50 min"`
- Stops: `"1 stop"`
- Layover: `"4 hr 5 min"` + airport code `"DOH"`
- CO2: `"Carbon emissions estimate: 1,047 kilograms. +16% emissions"`
- Price insights: `"Prices are currently typical"`

### Step 5: Present Results

```markdown
## Flights: {Origin} → {Dest} — {Date} round-trip
*Prices currently {typical/low/high}. Source: Google Flights*

| # | Price | Airlines | Depart | Arrive | Duration | Stops | Via |
|---|-------|----------|--------|--------|----------|-------|----|
| 1 | $1,711 | Qatar / Virgin Australia | 2:20 AM | 6:10 AM +1 | 20h 50m | 1 | DOH |

📎 [View on Google Flights]({url})
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Google consent page | Snapshot, click "Accept all" |
| "Oops, something went wrong" | Click "Reload", wait again |
| "Loading results" persists | wait_for with 15s timeout, retry once |
| "No results returned" | Date too far out or no flights on this route |

## Fallback: Web Search (No Browser)

When Chrome DevTools isn't connected, use web search.

### Exa Search (Best Fallback)

```
flights from {CITY} {IATA} to {CITY} {IATA} {MONTH} {YEAR} prices airlines
```

Returns Cheapflights/airline pages with "from $X" per-airline pricing.

### Google Search

```
cheapest flights {ORIGIN} to {DEST} {MONTH} {YEAR}
```

Returns general advice and price ranges. Always available.

### Present Fallback Results

```markdown
| Airline | Price From | Source |
|---------|-----------|--------|
| Qatar Airways | ~$1,149 AUD | cheapflights.com.au |

📎 [Search on Google Flights]({url})
```

## Booking Link Construction

Always provide both Google Flights and Skyscanner links so users can
cross-check prices on two engines.

### Google Flights

```
https://www.google.com/travel/flights?q=flights+from+{ORIGIN}+to+{DEST}+on+{MONTH}+{DAY}+{YEAR}&curr=USD&hl=en
```

| Variant | How |
|---------|-----|
| One-way | Append `+one+way` to the query |
| Explore (flexible dest) | `https://www.google.com/travel/explore?q=flights+from+{ORIGIN}&curr=USD` |

### Skyscanner

```
https://www.skyscanner.com/transport/flights/{ORIG}/{DEST}/{YYMMDD}/{YYMMDD}/?adultsv2={N}&cabinclass={CLASS}
```

Parameters:
- `{ORIG}` / `{DEST}` — Lowercase IATA codes (e.g. `amm`, `syd`)
- Date format: `YYMMDD` (e.g. July 15, 2026 = `260715`)
- `cabinclass` — `economy`, `premiumeconomy`, `business`, `first`
- For one-way: use only one date segment: `/flights/{ORIG}/{DEST}/{YYMMDD}/`

Example (AMM → SYD, Jul 15-19, 1 adult, economy):
```
https://www.skyscanner.com/transport/flights/amm/syd/260715/260719/?adultsv2=1&cabinclass=economy
```

Skyscanner has captcha anti-bot protection, so the agent cannot scrape it
directly. Always provide it as a clickable comparison link alongside the
Google Flights results the agent scraped.

### Kayak

```
https://www.kayak.com/flights/{ORIG}-{DEST}/{YYYY-MM-DD}/{YYYY-MM-DD}?sort=bestflight_a
```

Example:
```
https://www.kayak.com/flights/AMM-SYD/2026-07-15/2026-07-19?sort=bestflight_a
```

Kayak also has anti-bot protection and cannot be scraped directly.

### Output Template

Every flight search result should end with comparison links:

```markdown
📎 **Compare prices:**
- [Google Flights]({google_flights_url}) — *scraped results above*
- [Skyscanner]({skyscanner_url})
- [Kayak]({kayak_url})
```

## Why Only Google Flights Is Scrapable

Google Flights does not use captcha challenges on its search results page,
making it accessible via Chrome DevTools. Skyscanner and Kayak both use
anti-bot verification (press-and-hold challenges, captcha). If these sites
change their protection in the future, the approach may need updating.

## Comparison of Approaches

| Aspect | Browser Scraping | Web Search | SerpAPI (with key) |
|--------|-----------------|------------|-------------------|
| Price accuracy | Exact (live) | "From $X" ranges | Exact (live) |
| Itineraries | 8-20+ | 3-5 airlines | 10-20+ |
| Times/layovers | Yes | No | Yes |
| CO2/emissions | Yes | No | Yes |
| Price insights | Yes | No | Yes |
| Requires | Chrome DevTools | Web search tool | SERPAPI_KEY |
| Speed | 5-15 seconds | 2-3 seconds | 2-5 seconds |

## Price Insights Interpretation

| Level | Meaning | Advice |
|-------|---------|--------|
| "low" | Below typical range | Good time to book |
| "typical" | Normal range | Fair price |
| "high" | Above typical range | Try flexible dates |
