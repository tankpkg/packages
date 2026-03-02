@cache
Feature: Cache behavior
  The CLI refreshes catalogs when the cache is missing or stale.

  @smoke
  Scenario: First search downloads catalogs when cache missing
    Given no cache file exists
    When I run a search for "button"
    Then stdout contains "Downloading registry catalogs"
    And the cache file exists
    And the exit code is 0

  Scenario: Stale cache refreshes before search
    Given a stale cache older than 25 hours
    When I run a search for "button"
    Then stdout contains "Downloading registry catalogs"
    And the cache file exists
    And the exit code is 0

  Scenario: Fresh cache avoids download
    Given a fresh cache
    When I run a search for "button"
    Then stdout does not contain "Downloading component catalogs"
    And stdout contains "MATCHED COMPONENTS"
    And the exit code is 0

  Scenario: Refresh flag forces download even if cache fresh
    Given a fresh cache
    When I run the CLI with arguments "--refresh"
    Then stdout contains "Downloading registry catalogs"
    And the exit code is 0
