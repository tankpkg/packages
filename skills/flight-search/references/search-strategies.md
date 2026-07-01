# Flight Search Strategies

Sources: Google Flights help center, travel hacking community patterns,
airline pricing research, SerpAPI documentation, 2025-2026

Covers: multi-API orchestration, user query interpretation, price
optimization tips, and common search patterns.

## Multi-API Orchestration

The scripts in this skill implement a tiered API strategy based on which
environment variables are set.

### Priority Order

1. **SERPAPI_KEY** set -> Use SerpAPI Google Flights (best coverage)
2. **AMADEUS_CLIENT_ID** + **AMADEUS_CLIENT_SECRET** set -> Amadeus fallback
3. Neither set -> Error with setup instructions

### When to Use Which

| User Request | Primary API | Supplement |
|-------------|-------------|------------|
| "Find flights JFK to London" | SerpAPI | - |
| "What's the IATA code for Tokyo?" | Amadeus locations | - |
| "Cheapest day to fly NYC to Miami in Sept" | Travelpayouts calendar | SerpAPI price_insights |
| "Where can I fly for under $200?" | SerpAPI (flexible dest) | Amadeus inspiration |
| "Compare prices across dates" | Travelpayouts calendar | SerpAPI per-date |

## Interpreting User Queries

### City Names to IATA Codes

Users say "London" not "LHR". Resolution strategy:

1. Check common city-to-IATA mappings (built into scripts)
2. If ambiguous, use Amadeus locations API for fuzzy search
3. For cities with multiple airports, search all (e.g., NYC -> JFK,EWR,LGA)

### Common City Mappings

| City | IATA | Notes |
|------|------|-------|
| New York | JFK,EWR,LGA | Multi-airport, use all three |
| London | LHR,LGW,STN,LTN,LCY | Heathrow primary, include Gatwick |
| Los Angeles | LAX | Single primary |
| Chicago | ORD,MDW | O'Hare + Midway |
| San Francisco | SFO,OAK,SJC | Include Oakland and San Jose |
| Paris | CDG,ORY | De Gaulle primary |
| Tokyo | NRT,HND | Narita international, Haneda domestic+some intl |
| Washington DC | IAD,DCA,BWI | Include Baltimore |

### Flexible Date Interpretation

| User Says | Interpret As |
|-----------|-------------|
| "in September" | Search full month, show cheapest |
| "next weekend" | Calculate Fri-Sun dates |
| "around June 15" | Search June 13-17 |
| "flexible dates" | Show price calendar for the month |
| "long weekend" | Thu/Fri departure, Sun/Mon return |

### Passenger Interpretation

| User Says | adults | children | infants |
|-----------|--------|----------|---------|
| "two of us" | 2 | 0 | 0 |
| "family of 4" | 2 | 2 | 0 |
| "me and my kid" | 1 | 1 | 0 |
| "with a baby" | 1 | 0 | 1 (on lap) |
| Default | 1 | 0 | 0 |

## Price Optimization Tips

Knowledge the agent should share with users when relevant.

### Day-of-Week Patterns
- Tuesday and Wednesday departures are typically cheapest for domestic US
- Saturday departures for international are often cheaper
- Avoid Friday evening and Sunday evening for domestic (business travel premium)

### Booking Window
- Domestic US: 1-3 months ahead is usually the sweet spot
- International: 2-8 months ahead
- Last-minute (< 7 days) is almost always more expensive
- Too far ahead (> 11 months) may not have the best fares yet

### Nearby Airports
Always check nearby airports. JFK vs EWR can differ by $100+ on the same route.
SerpAPI supports multi-airport search with comma-separated codes.

### Nonstop vs Connections
Nonstop flights are often cheaper than connections on the same airline for
short-haul routes. For long-haul, a connection can save 30-50%. Always
search both and let the user decide.

### Price Insights
When SerpAPI returns `price_insights`, interpret for the user:
- `price_level: "low"` -> "This is a good price for this route"
- `price_level: "typical"` -> "This is about average"
- `price_level: "high"` -> "Prices are elevated. Consider flexible dates"

## Output Formatting

### Standard Flight Result

Present each flight with these fields in order:

```
$892 USD | JFK -> LHR | 7h 15m nonstop
  British Airways BA178 | Economy | Boeing 777
  Departs: Jun 1, 8:00 AM | Arrives: Jun 1, 8:15 PM (local)
  Legroom: 31 in | CO2: 612 kg
```

### Comparison Table (Multiple Results)

```
| # | Price | Route | Duration | Stops | Airlines | Depart |
|---|-------|-------|----------|-------|----------|--------|
| 1 | $892  | JFK-LHR | 7h 15m | 0 | BA | 8:00 AM |
| 2 | $756  | JFK-LHR | 10h 30m | 1 (DUB) | Aer Lingus | 6:15 PM |
| 3 | $1,204 | JFK-LHR | 7h 10m | 0 | United | 10:30 PM |
```

### Price Calendar (Date Flexibility)

```
| Date | Price | vs Avg |
|------|-------|--------|
| Sep 1 (Mon) | $189 | -22% |
| Sep 2 (Tue) | $175 | -28% * cheapest |
| Sep 3 (Wed) | $182 | -25% |
| Sep 5 (Fri) | $245 | +1% |
| Sep 7 (Sun) | $268 | +10% |
```

## Common Search Patterns

### Pattern 1: Specific Route Search
User: "Find flights from San Francisco to Tokyo on March 15"
1. Resolve: SFO -> NRT,HND
2. Call search_flights.py with SFO, NRT, 2026-03-15
3. Sort by price, show top 5-10 results
4. Include price_insights if available

### Pattern 2: Cheapest Day Search
User: "When is the cheapest time to fly to Barcelona?"
1. Resolve origin (ask if not provided)
2. Call price_calendar.py for the next 2-3 months
3. Show calendar view with cheapest days highlighted
4. Offer to search specific cheap dates for details

### Pattern 3: Flexible Destination
User: "Where can I fly for under $300 round trip from Chicago?"
1. Use SerpAPI with various popular destinations
2. Or use Amadeus inspiration search (limited airlines)
3. Show destinations sorted by price

### Pattern 4: Multi-City
User: "NYC to London, then London to Paris, then Paris to NYC"
1. Search each leg separately via SerpAPI
2. Sum prices for total trip cost
3. Present each leg with its options

## Environment Variables

| Variable | Required? | Source |
|----------|-----------|--------|
| `SERPAPI_KEY` | Recommended | serpapi.com (250 free/mo) |
| `AMADEUS_CLIENT_ID` | Optional | developers.amadeus.com (free) |
| `AMADEUS_CLIENT_SECRET` | Optional | Same as above |
| `TRAVELPAYOUTS_TOKEN` | Optional | travelpayouts.com (free) |

The skill works with just SERPAPI_KEY. Additional APIs unlock more features.
