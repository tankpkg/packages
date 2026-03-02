@output
Feature: Sources and help output
  The CLI lists sources and shows help for missing arguments.

  Background:
    Given a fresh cache

  Scenario: Sources list includes retained registries and skips filtered
    When I run the CLI with arguments "--sources"
    Then stdout contains "Registries (offline search + install)"
    And stdout contains "@acme/ui"
    And stdout contains "@motion-lab"
    And stdout contains "@dashboard-pro"
    And stdout contains "Skipped registries"
    And stdout contains "@ai-chat/ui"
    And stdout contains "@broken-registry"
    And the exit code is 0

  @error
  Scenario: No arguments shows help and exits 1
    When I run the CLI with no arguments
    Then stdout contains "Offline-first shadcn registry search"
    And the exit code is 1

  @smoke
  Scenario: Help flag shows usage
    When I run the CLI with arguments "--help"
    Then stdout contains "usage:"
    And stdout contains "--refresh"
    And stdout contains "--json"
    And the exit code is 0
