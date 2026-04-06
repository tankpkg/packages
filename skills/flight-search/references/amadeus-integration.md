# Amadeus Self-Service Integration

Sources: Amadeus developer documentation (developers.amadeus.com), Amadeus FAQ,
amadeus-python SDK (github.com/amadeus4dev/amadeus-python), 2025-2026

Covers: authentication, flight search, airport lookup, cheapest dates, inspiration
search, and critical limitations of the Amadeus Self-Service API.

## Critical Limitation

Amadeus Self-Service does NOT return data from:
- **American Airlines** (AA)
- **Delta Air Lines** (DL)
- **British Airways** (BA)
- **Low-cost carriers** (Ryanair, EasyJet, Spirit, Frontier, Wizz, etc.)

Only published rates from participating airlines. No negotiated/special rates.
This makes Amadeus unsuitable as a primary fare search for US/UK markets.
Use it for airport lookup and supplementary features instead.

## Authentication

OAuth2 Client Credentials Grant. No browser or user interaction needed.

### Token Request

```
POST https://test.api.amadeus.com/v1/security/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=KEY&client_secret=SECRET
```

### Token Response

```json
{
  "access_token": "CpjU0sEenniHCgPDrndzOSWFk5mN",
  "token_type": "Bearer",
  "expires_in": 1799
}
```

Token lasts ~30 minutes. Re-request on 401. The Python SDK handles this
automatically.

### Base URLs

| Environment | URL |
|-------------|-----|
| Test | `https://test.api.amadeus.com` |
| Production | `https://api.amadeus.com` |

Same endpoints, same parameters. Just change the hostname.

## Airport & City Search

The most useful Amadeus endpoint for this skill. Resolves fuzzy city/airport
names to IATA codes.

```
GET /v1/reference-data/locations?keyword=London&subType=AIRPORT,CITY
```

### Response

```json
{
  "data": [
    {
      "type": "location",
      "subType": "CITY",
      "name": "LONDON",
      "iataCode": "LON",
      "address": { "cityName": "LONDON", "countryCode": "GB" },
      "geoCode": { "latitude": 51.50853, "longitude": -0.12574 }
    },
    {
      "type": "location",
      "subType": "AIRPORT",
      "name": "HEATHROW",
      "iataCode": "LHR",
      "address": { "cityName": "LONDON", "countryCode": "GB" }
    }
  ]
}
```

### Python SDK

```python
from amadeus import Client, Location
amadeus = Client(client_id='KEY', client_secret='SECRET')
response = amadeus.reference_data.locations.get(
    keyword='London', subType=Location.ANY
)
for loc in response.data:
    print(loc['iataCode'], loc['name'], loc['address']['cityName'])
```

## Flight Offers Search

Returns flight prices from participating GDS airlines (excludes AA, DL, BA, LCCs).

### GET Request (Simple)

```
GET /v2/shopping/flight-offers?originLocationCode=MAD&destinationLocationCode=BCN
  &departureDate=2026-08-15&adults=1&travelClass=ECONOMY&nonStop=false&max=10
```

### Required Parameters

| Parameter | Type | Example |
|-----------|------|---------|
| `originLocationCode` | IATA code | `JFK` |
| `destinationLocationCode` | IATA code | `CDG` |
| `departureDate` | `YYYY-MM-DD` | `2026-09-01` |
| `adults` | integer 1-9 | `1` |

### Optional Parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `returnDate` | `YYYY-MM-DD` | Omit for one-way |
| `travelClass` | string | `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST` |
| `nonStop` | boolean | `true` = direct only |
| `currencyCode` | ISO 4217 | Default EUR |
| `maxPrice` | integer | Max per traveler |
| `max` | integer | Max results (default/max 250) |
| `includedAirlineCodes` | string | Comma-separated IATA codes |
| `excludedAirlineCodes` | string | Comma-separated IATA codes |

### Response Key Fields

```python
offer = response["data"][0]

# Price
total = offer["price"]["grandTotal"]  # String, use Decimal
currency = offer["price"]["currency"]

# Itinerary
outbound = offer["itineraries"][0]
duration = outbound["duration"]  # ISO 8601: "PT14H30M"
stops = len(outbound["segments"]) - 1

# Per segment
for seg in outbound["segments"]:
    origin = seg["departure"]["iataCode"]
    depart_time = seg["departure"]["at"]  # Local time, no TZ
    dest = seg["arrival"]["iataCode"]
    arrive_time = seg["arrival"]["at"]
    airline = seg["carrierCode"]
    flight_num = seg["number"]

# Cabin class (check actual, not requested)
cabin = offer["travelerPricings"][0]["fareDetailsBySegment"][0]["cabin"]

# Airline name lookup
carriers = response["dictionaries"]["carriers"]  # {"IB": "IBERIA"}
```

### Duration Parsing

Amadeus returns ISO 8601 durations. Parse with:

```python
import re
def parse_duration(iso_dur):
    """PT14H30M -> 870 minutes"""
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso_dur)
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    return hours * 60 + minutes
```

## Flight Cheapest Date Search

Find cheapest travel dates over a date range. Uses cached data.

```
GET /v1/shopping/flight-dates?origin=JFK&destination=CDG&departureDate=2026-09-01,2026-09-30
```

Returns array of dates with prices, sorted by price.

## Flight Inspiration Search

"Where can I fly from JFK for under $300?"

```
GET /v1/shopping/flight-destinations?origin=JFK&maxPrice=300
```

Returns destinations sorted by price. Uses cached data.

## Common Gotchas

### Test Data Is Fake
Test environment returns cached snapshots, not live prices. Some routes
return no results. Only production has real GDS data.

### Price Strings
`price.total` and `price.grandTotal` are **strings**, not numbers. Always
parse with `Decimal`, never `float`.

### travelClass Is a Preference
The `travelClass` parameter is a preference filter, not a hard constraint.
The API may return other cabin classes. Always check
`travelerPricings[0].fareDetailsBySegment[0].cabin` in the response.

### Times Are Local
Departure/arrival times have no timezone offset. They're local to the
airport. If you need UTC, look up the airport's timezone separately.

### Rate Limits
- Test: 10 requests/second (100ms between calls)
- Production: 40 requests/second
- Monthly quota varies by API; check workspace dashboard
- 429 response includes `Retry-After` header

## Python SDK Setup

```bash
pip install amadeus
```

```python
from amadeus import Client, ResponseError
import os

amadeus = Client(
    client_id=os.environ.get('AMADEUS_CLIENT_ID'),
    client_secret=os.environ.get('AMADEUS_CLIENT_SECRET'),
    # hostname='production'  # uncomment for real data
)
```

The SDK auto-handles token fetch, renewal, and retry on 401.

## Raw HTTP Client

```python
import requests, time, os

class AmadeusClient:
    def __init__(self, client_id=None, client_secret=None, production=False):
        self.client_id = client_id or os.environ.get('AMADEUS_CLIENT_ID')
        self.client_secret = client_secret or os.environ.get('AMADEUS_CLIENT_SECRET')
        host = "api.amadeus.com" if production else "test.api.amadeus.com"
        self.base = f"https://{host}"
        self._token = None
        self._expiry = 0

    def _auth(self):
        if time.time() < self._expiry - 60:
            return self._token
        r = requests.post(f"{self.base}/v1/security/oauth2/token", data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        r.raise_for_status()
        d = r.json()
        self._token = d["access_token"]
        self._expiry = time.time() + d["expires_in"]
        return self._token

    def get(self, path, params=None):
        r = requests.get(f"{self.base}{path}",
            headers={"Authorization": f"Bearer {self._auth()}"},
            params=params)
        r.raise_for_status()
        return r.json()
```
