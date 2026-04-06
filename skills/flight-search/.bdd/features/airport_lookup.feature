@airport_lookup
Feature: Airport IATA code resolution
  Resolve city names and airport codes using the builtin mapping.
  No API keys required for builtin lookups.

  Scenario Outline: Resolves common cities to IATA codes
    When I look up airport "<query>"
    Then stdout contains "<expected_code>"
    And the exit code is 0

    Examples:
      | query         | expected_code |
      | New York      | JFK           |
      | london        | LHR           |
      | tokyo         | NRT           |
      | paris         | CDG           |
      | tel aviv      | TLV           |
      | san francisco | SFO           |
      | chicago       | ORD           |

  Scenario: Multi-airport cities return all airports
    When I look up airport "new york"
    Then stdout contains "JFK"
    And stdout contains "EWR"
    And stdout contains "LGA"
    And the exit code is 0

  Scenario: Direct IATA code passes through
    When I look up airport "JFK"
    Then stdout contains "JFK"
    And the exit code is 0

  Scenario: Case-insensitive matching
    When I look up airport "LONDON"
    Then stdout contains "LHR"
    And the exit code is 0

  Scenario: Abbreviations are resolved
    When I look up airport "nyc"
    Then stdout contains "JFK"
    And stdout contains "EWR"
    And the exit code is 0

  Scenario: Unknown city shows helpful message
    When I look up airport "zzzznotacity"
    Then stdout contains "No airports found"
    And the exit code is 0

  Scenario: JSON output returns valid structure
    When I look up airport "london" with JSON output
    Then the exit code is 0
    And JSON output contains key "query"
    And JSON output contains key "results"
    And JSON results list is not empty

  Scenario: JSON output for unknown city returns empty results
    When I look up airport "zzzznotacity" with JSON output
    Then the exit code is 0
    And JSON output contains key "results"
    And JSON results list is empty

  Scenario: Partial city name matching
    When I look up airport "york"
    Then stdout contains "JFK"
    And the exit code is 0
