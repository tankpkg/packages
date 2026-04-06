# Flight Search API Comparison

Sources: Amadeus developer docs, SerpAPI docs, Travelpayouts docs, Kiwi.com blog,
FlightAPI.io docs, Duffel pricing page, community reports (2024-2026)

Covers: every viable flight search API for individual developers, with honest
limitations, pricing, and selection guidance.

## Decision Matrix

| API | Real Prices | All Airlines | Free Tier | Auth Complexity | Best For |
|-----|-------------|-------------|-----------|-----------------|----------|
| SerpAPI Google Flights | Yes | Yes (all) | 250/mo | API key (trivial) | Primary search |
| Amadeus Self-Service | Yes | No (missing AA, DL, BA, LCCs) | ~2000/mo test | OAuth2 client creds | Airport lookup, supplements |
| Travelpayouts | Cached only | Most | Unlimited | Token param | Price trends, calendars |
| FlightAPI.io | Yes | Yes (Skyscanner-backed) | 20 credits trial | API key | High-volume budget |
| Duffel | Yes (bookable) | 300+ airlines | Search free, $3/booking | OAuth2 | Booking integration |

## SerpAPI Google Flights

Managed scraping proxy for Google Flights. Returns structured JSON matching
exactly what users see on google.com/travel/flights.

### Pricing (April 2026)

| Plan | Cost | Searches/Month | Per Search |
|------|------|----------------|------------|
| Free | $0 | 250 | $0 |
| Starter | $25 | 1,000 | $0.025 |
| Developer | $75 | 5,000 | $0.015 |
| Production | $150 | 15,000 | $0.010 |

Cached results (1h TTL) are free and don't count toward quota.

### Strengths
- All airlines globally (no coverage gaps)
- Exact Google Flights prices
- Rich metadata: legroom, delay flags, CO2, price insights, price history
- Booking tokens for OTA deep-links
- Multi-airport search (JFK,EWR)
- deep_search=true for browser-identical results

### Limitations
- 250 free/month is tight for heavy use
- Round-trip needs 2 API calls (outbound + return leg via departure_token)
- Scraping Google Flights is a ToS gray area (SerpAPI provides legal shield)
- No booking capability, only redirects to OTA/airline sites

### Auth
Single API key as URL parameter. No OAuth. Get key at serpapi.com.

## Amadeus Self-Service

Traditional GDS (Global Distribution System) API from one of the world's largest
travel technology companies.

### Pricing

| Environment | Cost | Rate Limit |
|-------------|------|------------|
| Test | Free (~2000 calls/mo) | 10 TPS |
| Production | Free quota + pay-per-call | 40 TPS |

Production requires signing a contract and adding billing info (no business
verification, just credit card). Approx $0.0001-$0.002 per call.

### Critical Limitation

**Amadeus Self-Service does NOT return data from:**
- American Airlines
- Delta Air Lines
- British Airways
- Low-cost carriers (Ryanair, EasyJet, Spirit, Frontier, etc.)

This is confirmed in their official FAQ. For US domestic routes, this gap is
massive since AA and DL are the #1 and #2 carriers.

### Strengths
- Excellent airport/city lookup API (best available)
- Flight Cheapest Date Search (cheapest date over a month)
- Flight Inspiration Search ("where can I fly for under $300?")
- Flight Price Analysis (is this price high/low/typical?)
- CO2 emissions data
- Python and Node.js SDKs with auto token refresh

### Best Used For
- Airport IATA code resolution (primary use case for this skill)
- Supplementary cheapest-date and inspiration searches
- NOT as primary fare search due to airline coverage gaps

### Auth
OAuth2 Client Credentials Grant. POST to /v1/security/oauth2/token with
client_id + client_secret. Token lasts 30 minutes. SDKs auto-refresh.

## Travelpayouts (Aviasales)

Affiliate-based data API from the Aviasales search engine. Returns cached/historical
pricing data, not live shopping results.

### Pricing
Free. No monthly cap documented. Rate limit ~200 req/hour per IP.
Monetization is via affiliate commissions when users book through your links.

### Data Quality
- Prices are cached/aggregated from past searches, not real-time shopping
- Updated periodically (delay varies by route)
- Good for "what does this route usually cost?" not "what can I book right now?"

### Key Endpoints
- `/v1/prices/cheap` — Cheapest flights for a route
- `/v1/prices/calendar` — Cheapest price per day in a month
- `/v1/prices/monthly` — Cheapest price per month for a year
- `/v2/prices/latest` — Latest cached prices

### Auth
Token as URL parameter (?token=YOUR_TOKEN). Get at travelpayouts.com.

## Dead Ends (Do Not Use)

### Kiwi.com Tequila API
**Status: B2B only since May 30, 2024.** New self-serve registrations are
closed. You must apply as a B2B affiliate partner. Community reports confirm
the free tier is gone. If you already have a key, it may still work.

### Skyscanner API
**Status: Partner-only.** Requires commercial partnership agreement. Individual
developers and small projects are routinely rejected. No self-serve access.

### Google Flights API
**Does not exist.** Google QPX Express was shut down in 2018. No replacement.
The only programmatic access is via SerpAPI (scraping).

### Google ITA Matrix
**No API.** Consumer-facing website only. Returns empty content to automated
requests.

### AviationStack
**100 free calls/month, no pricing data.** Tracks flight status/delays, not
fares. Wrong tool for price search. Only useful if you need "is flight BA123
on time?"

### Booking.com
**Hotels only.** No flight search capability in API or affiliate program.

## FlightAPI.io

Skyscanner-backed aggregator. Good for high-volume, budget-conscious use.

### Pricing

| Plan | Cost | Credits/Month | Effective Cost/Search |
|------|------|---------------|----------------------|
| Free trial | $0 | 20 | - |
| Lite | $49 | 30,000 | ~$0.003 |
| Standard | $99 | 100,000 | ~$0.002 |
| Plus | $199 | 500,000 | ~$0.0008 |

Each search costs 2 credits. 5-10x cheaper per search than SerpAPI.

### Trade-offs vs SerpAPI
- Cheaper per search
- Less metadata (no legroom, no delay history, no price insights)
- Skyscanner's internal response format (more complex to parse)
- Good as bulk price monitoring fallback, not primary user-facing search

## Duffel API

Modern GDS/NDC aggregator for actual booking (not just search).

### Pricing
- No upfront cost, no monthly fee
- $3.00 per confirmed booking + 1% order value
- Excess search fee: $0.005/search beyond 1500:1 search-to-book ratio

### When to Use
Only if you need to complete actual bookings programmatically. For a search-only
skill, the excess search fee model makes it uneconomical. Free to search if you
maintain a reasonable search-to-book ratio.

## Recommended Configuration for This Skill

```
Primary:     SerpAPI Google Flights (SERPAPI_KEY)
             Best coverage, all airlines, real-time prices

Supplement:  Amadeus Self-Service (AMADEUS_CLIENT_ID + SECRET)
             Airport lookup, cheapest date search, inspiration search

Trends:      Travelpayouts (TRAVELPAYOUTS_TOKEN)
             Price calendar, cheapest month, "when to fly" questions

Fallback:    FlightAPI.io (FLIGHTAPI_KEY) — optional
             If SerpAPI quota exhausted and need more searches
```

The scripts in this skill implement this tiered strategy automatically.
Set environment variables for the APIs you have keys for.
