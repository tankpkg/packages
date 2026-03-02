@search
Feature: Offline search matching
  Searches match component name, description, type, and registry.

  Background:
    Given a fresh cache

  Scenario Outline: Searches match by different fields
    When I run a search for "<query>"
    Then stdout contains "<expected>"
    And the exit code is 0

    Examples:
      | query         | expected                 |
      | button        | stateful-button          |
      | kinetic       | split-text               |
      | icons         | [icons]                  |
      | @motion-lab   | @motion-lab              |

  Scenario: Case-insensitive search yields the same count
    When I run a search for "button" and store total as "lower"
    And I run a search for "BUTTON" and store total as "upper"
    Then totals "lower" and "upper" are equal

  Scenario: No results still shows total line
    When I run a search for "zzzznonexistent"
    Then stdout contains "Total: 0 cached matches"
    And the exit code is 0

  Scenario: Results per registry are capped with a more message
    When I run a search for "admin"
    Then stdout contains "@dashboard-pro (30)"
    And stdout contains "... and 5 more. Narrow your search."
    And the exit code is 0
