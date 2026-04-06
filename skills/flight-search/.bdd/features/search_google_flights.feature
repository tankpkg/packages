@search_google_flights
Feature: Google Flights search via fast-flights
  The primary flight search tool. Uses the fast-flights package to
  reverse-engineer Google Flights' protobuf API. No API key needed.

  Scenario: Help flag shows usage
    When I run search_google_flights with "--help"
    Then the exit code is 0
    And stdout contains "--origin"
    And stdout contains "--destination"
    And stdout contains "--date"
    And stdout contains "--return-date"
    And stdout contains "--nonstop"

  Scenario: Missing required argument shows error
    When I run search_google_flights with "--origin JFK"
    Then the exit code is not 0
    And stderr contains "required"

  Scenario: All seat classes are accepted via help
    When I run search_google_flights with "--origin JFK --destination LHR --date 2026-09-01 --class first --help"
    Then the exit code is 0

  @requires_fast_flights
  Scenario: Returns flight results for a real route
    When I search google flights with "--origin JFK --destination LHR --date 2026-09-15 --max 3"
    Then the exit code is 0
    And JSON output contains key "flights"
    And JSON output contains key "source"
    And JSON flights list is not empty
    And each flight has "price"
    And each flight has "airlines"
    And each flight has "departure"

  @requires_fast_flights
  Scenario: Round-trip search returns results
    When I search google flights with "--origin JFK --destination LHR --date 2026-09-15 --return-date 2026-09-22 --max 3"
    Then the exit code is 0
    And JSON flights list is not empty

  @requires_fast_flights
  Scenario: Nonstop filter works
    When I search google flights with "--origin JFK --destination LAX --date 2026-09-15 --nonstop --max 5"
    Then the exit code is 0
    And JSON output contains key "flights"
    And every flight has 0 stops

  @requires_fast_flights
  Scenario: Response includes price level
    When I search google flights with "--origin JFK --destination LHR --date 2026-09-15 --max 3"
    Then the exit code is 0
    And JSON output contains key "price_level"
