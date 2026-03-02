@output
Feature: JSON output
  The CLI can output results as JSON for tooling.

  Background:
    Given a fresh cache

  Scenario: JSON output for matches has required fields
    When I run a JSON search for "button"
    Then JSON output is a list
    And every JSON item includes fields "name,type,description,registry,addCommandArgument"
    And the exit code is 0


  Scenario: JSON output for no matches is empty
    When I run a JSON search for "zzzznonexistent"
    Then JSON output is an empty list
    And the exit code is 0
