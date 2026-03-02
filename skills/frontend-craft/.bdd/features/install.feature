@install
Feature: Install commands
  The CLI prints install commands for cached and uncached components.

  Background:
    Given a fresh cache

  Scenario: Install with cache match prints command
    When I run the CLI with arguments "--install @motion-lab:split-text"
    Then stdout contains "Installing split-text from @motion-lab"
    And stdout contains "npx shadcn@latest add @motion-lab/split-text"
    And the exit code is 0

  @error
  Scenario: Install format requires colon
    When I run the CLI with arguments "--install badformat"
    Then stderr contains "format must be 'registry:component-name'"
    And the exit code is 1

  @error
  Scenario: Install unknown registry or component
    When I run the CLI with arguments "--install unknownsource:foo"
    Then stderr contains "Unknown registry or component"
    And stderr contains "Registries:"
    And the exit code is 1
