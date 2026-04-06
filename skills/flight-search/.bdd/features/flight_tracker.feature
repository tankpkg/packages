@flight_tracker
Feature: Flight price tracker
  Track flight prices over time with a JSON watch list.
  Add, list, check, and remove watched routes.

  Scenario: Add a route to watch list
    Given a clean tracker state
    When I run flight_tracker with "add --origin JFK --destination LHR --date 2026-09-15"
    Then the exit code is 0
    And JSON output contains key "action"
    And stdout contains "added"

  Scenario: List shows empty when no watches exist
    Given a clean tracker state
    When I run flight_tracker with "list"
    Then the exit code is 0
    And stdout contains "No flights being tracked"

  Scenario: List shows added watches
    Given a clean tracker state
    When I run flight_tracker with "add --origin JFK --destination LHR --date 2026-09-15"
    And I run flight_tracker with "list"
    Then the exit code is 0
    And stdout contains "JFK"
    And stdout contains "LHR"

  Scenario: Remove a watched route
    Given a clean tracker state
    When I run flight_tracker with "add --origin JFK --destination LHR --date 2026-09-15"
    And I run flight_tracker with "remove --id 0"
    Then the exit code is 0
    And stdout contains "removed"

  Scenario: Remove invalid ID shows error
    Given a clean tracker state
    When I run flight_tracker with "remove --id 99"
    Then the exit code is 1
    And stdout contains "Invalid watch ID"

  Scenario: Help flag shows usage
    When I run flight_tracker with "--help"
    Then the exit code is 0
    And stdout contains "add"
    And stdout contains "list"
    And stdout contains "check"
    And stdout contains "remove"

  @requires_fast_flights
  Scenario: Check fetches live prices for watched routes
    Given a clean tracker state
    When I run flight_tracker with "add --origin JFK --destination LHR --date 2026-09-15"
    And I run flight_tracker with "check --id 0"
    Then the exit code is 0
    And stdout contains "current_price"
    And stdout contains "First snapshot"
