@search_flights
Feature: Flight search via SerpAPI/Amadeus (optional paid tier)
  Search for flights using SerpAPI or Amadeus when API keys are available.
  These are optional — the primary search is search_google_flights.
  Tests without API keys verify error handling and CLI interface.

  Scenario: No API keys shows setup instructions
    When I search flights without API keys using "--origin JFK --destination LHR --date 2026-09-01"
    Then the exit code is 1
    And stdout contains "No flight API configured"
    And stdout contains "SERPAPI_KEY"
    And stdout contains "serpapi.com"

  Scenario: Help flag shows usage
    When I run search_flights with "--help"
    Then the exit code is 0
    And stdout contains "--origin"
    And stdout contains "--destination"
    And stdout contains "--date"
    And stdout contains "--return-date"
    And stdout contains "--nonstop"
    And stdout contains "--currency"

  Scenario: Missing required argument shows error
    When I run search_flights with "--origin JFK"
    Then the exit code is not 0
    And stderr contains "required"

  Scenario: All travel classes are accepted
    When I run search_flights with "--origin JFK --destination LHR --date 2026-09-01 --class business --help"
    Then the exit code is 0

  @requires_serpapi
  Scenario: SerpAPI returns flight results
    When I search flights with "--origin JFK --destination LHR --date 2026-09-15 --max 3"
    Then the exit code is 0
    And JSON output contains key "flights"
    And JSON output contains key "source"
    And JSON flights list is not empty
    And each flight has "price"
    And each flight has "airlines"
    And each flight has "departure_time"
    And each flight has "destination"

  @requires_serpapi
  Scenario: SerpAPI nonstop filter works
    When I search flights with "--origin JFK --destination LAX --date 2026-09-15 --nonstop --max 5"
    Then the exit code is 0
    And JSON output contains key "flights"
    And every flight has 0 stops

  @requires_serpapi
  Scenario: Round-trip search returns results
    When I search flights with "--origin JFK --destination LHR --date 2026-09-15 --return-date 2026-09-22 --max 3"
    Then the exit code is 0
    And JSON flights list is not empty

  @requires_amadeus
  Scenario: Amadeus fallback works when SerpAPI is unavailable
    When I search flights without serpapi using "--origin MAD --destination BCN --date 2026-09-15 --max 3"
    Then the exit code is 0
    And JSON output contains key "source"
    And stdout contains "amadeus"
