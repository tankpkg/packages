@flight_status
Feature: Live flight status via Flightradar24
  Check if a flight is delayed, what gate, what terminal.
  Uses FR24's internal web API — no API key needed.

  Scenario: Help flag shows usage
    When I run flight_status with "--help"
    Then the exit code is 0
    And stdout contains "flight"
    And stdout contains "BA178"

  Scenario: Returns status for a known flight
    When I run flight_status with "BA178 --json"
    Then the exit code is 0
    And JSON output contains key "flight"
    And JSON output contains key "status"
    And JSON output contains key "departure"
    And JSON output contains key "arrival"
    And JSON output contains key "source"

  Scenario: Returns airline name
    When I run flight_status with "UA900 --json"
    Then the exit code is 0
    And JSON output contains key "airline"

  Scenario: Invalid flight returns error
    When I run flight_status with "ZZZZZ999 --json"
    Then the exit code is 1
    And stdout contains "error"
