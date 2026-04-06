@price_calendar
Feature: Flight price calendar
  Show cheapest prices per day for a route and month.
  Uses Travelpayouts Data API (free, cached data).

  Scenario: No API token shows setup instructions
    When I run price_calendar without API keys using "--origin JFK --destination LHR --month 2026-09"
    Then the exit code is 1
    And stdout contains "No price calendar API configured"
    And stdout contains "TRAVELPAYOUTS_TOKEN"
    And stdout contains "travelpayouts.com"

  Scenario: Help flag shows usage
    When I run price_calendar with "--help"
    Then the exit code is 0
    And stdout contains "--origin"
    And stdout contains "--destination"
    And stdout contains "--month"
    And stdout contains "--currency"

  Scenario: Invalid month format shows error
    When I run price_calendar without API keys using "--origin JFK --destination LHR --month 2026-13"
    Then the exit code is 1
    And stderr contains "Invalid month format"

  Scenario: Another invalid month format
    When I run price_calendar without API keys using "--origin JFK --destination LHR --month September"
    Then the exit code is 1
    And stderr contains "Invalid month format"

  Scenario: Missing required arguments shows error
    When I run price_calendar with "--origin JFK"
    Then the exit code is not 0
    And stderr contains "required"

  @requires_travelpayouts
  Scenario: Real price calendar returns data
    When I run price_calendar with "--origin JFK --destination LHR --month 2026-09"
    Then the exit code is 0
    And JSON output contains key "calendar"
    And JSON output contains key "cheapest_date"
    And JSON output contains key "cheapest_price"
    And JSON output contains key "average_price"
    And JSON calendar list is not empty
