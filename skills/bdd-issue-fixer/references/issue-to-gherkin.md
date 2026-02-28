# Issue to Gherkin Translation

Sources: Nicieja (Writing Great Specifications), Wynne/Hellesoy (The Cucumber Book), Smart/Molak (BDD in Action), SWE-bench issue-to-test patterns

Covers: translating bug reports and feature requests into precise Gherkin scenarios, handling vague issues, file placement, quality enforcement.

## The Translation Pipeline

Every fixable issue goes through this 4-step pipeline before any code is written.

| Step | Input | Output |
|------|-------|--------|
| 1. Extract structured data | Raw issue text | Mental extraction template (from `issue-triage.md`) |
| 2. Identify behavior under test | Structured data | One-sentence behavior statement |
| 3. Write Gherkin scenario(s) | Behavior statement | `.feature` file with scenarios |
| 4. Place the file | Feature file | `.bdd/features/{domain}/{slug}.feature` |

The behavior statement is the bridge between the messy human issue and the
precise Gherkin test. Write it as: "When {action}, the system should {expected
behavior}, but instead it {actual behavior}."

## Bug Report to Gherkin

The most common translation. A bug report has three signals: what was tried,
what was expected, and what actually happened.

### Example: Clear Bug Report

**Raw issue:**
```
Title: CSV export fails when report has special characters
Body: When I export a financial report containing names with accents
(like "Jose Garcia"), the CSV file is corrupted. The special characters
turn into garbled text.
Expected: CSV should properly encode UTF-8 characters
Actual: Characters like e-acute, a-acute become mojibake
```

**Behavior statement:** "When exporting a report with accented names, the CSV
should contain valid UTF-8, but instead it produces mojibake."

**Gherkin output:**
```gherkin
Feature: CSV export handles special characters
  Financial reports with international names must export correctly.

  @issue-42
  Scenario: Report with accented names exports valid UTF-8
    Given a financial report containing the name "Jose Garcia"
    When the report is exported as CSV
    Then the CSV file should contain "Jose Garcia" encoded as valid UTF-8
    And the CSV should be parseable without encoding errors
```

### Example: Bug Report with Stack Trace

Users often dump a full stack trace. Extract the behavior, ignore the trace details.

**Raw issue:**
```
Title: App crashes when uploading large files
Body: I try to upload a 50MB report and get this error:

Error: PayloadTooLargeError: request entity too large
    at readStream (/app/node_modules/raw-body/index.js:155:17)
    at getRawBody (/app/node_modules/raw-body/index.js:108:12)

Expected: Upload should work for files up to 100MB (as documented)
```

**Behavior statement:** "When uploading a 50MB file, the upload should succeed,
but instead it throws PayloadTooLargeError."

**Gherkin output:**
```gherkin
Feature: Large file upload support
  The system must accept file uploads up to the documented 100MB limit.

  @issue-87
  Scenario: Upload a 50MB file successfully
    Given a valid report file of 50 megabytes
    When the file is uploaded
    Then the upload should complete successfully
    And the file should be accessible in the system

  Scenario: Upload at the documented limit
    Given a valid report file of 100 megabytes
    When the file is uploaded
    Then the upload should complete successfully
```

Notice: two scenarios. The reported case (50MB) and the documented limit (100MB).
Always test the boundary the documentation promises.

### Example: Vague Bug Report

**Raw issue:**
```
Title: Search doesn't work
Body: I type something in the search box and nothing happens.
```

No expected behavior stated. No error message. No repro steps. But the
behavior is inferable: search should return results when a query is entered.

**Behavior statement:** "When entering a search query, results should appear,
but instead nothing happens."

**Gherkin output:**
```gherkin
Feature: Search returns relevant results
  Users searching for content should see matching results.

  @issue-103
  Scenario: Search with a matching query returns results
    Given published content containing the word "deployment"
    When a search is performed for "deployment"
    Then search results should include content matching "deployment"
    And the results should appear within 3 seconds
```

When the issue is vague, write the Gherkin for what SHOULD work based on
the feature's purpose. Add a note in the PR that the scenario was inferred.

## Feature Request to Gherkin

Feature requests need acceptance criteria. Extract the "Definition of Done"
from the request.

### Example: Feature Request

**Raw issue:**
```
Title: Add dark mode support
Body: It would be great to have a dark mode toggle in settings.
The current white background is harsh at night.
```

**Gherkin output:**
```gherkin
Feature: Dark mode support
  Users should be able to switch between light and dark themes.

  @issue-55
  Scenario: User enables dark mode
    Given a user with default light mode settings
    When dark mode is enabled in settings
    Then the interface should render with a dark color scheme
    And the preference should persist across sessions

  Scenario: User switches back to light mode
    Given a user with dark mode enabled
    When light mode is selected in settings
    Then the interface should render with the light color scheme

  Scenario: Dark mode preference persists after logout
    Given a user who has enabled dark mode
    When the user logs out and logs back in
    Then dark mode should still be active
```

Feature requests typically produce 2-4 scenarios: happy path, the reverse
action, and persistence/edge cases.

## Gherkin Quality Rules

Every scenario must pass these quality checks.

### Rule 1: Declarative Over Imperative

Describe WHAT the system does, not HOW the user clicks.

| BAD (imperative) | GOOD (declarative) |
|---|---|
| Given I click the "Login" button | Given Emma is logged in |
| When I fill in "email" with "test@example.com" | When Emma signs up with a valid email |
| Then I should see a green checkmark icon | Then the registration should be confirmed |
| And I scroll down to the results section | And search results should be visible |

Push all mechanics into step definitions and the interaction layer.

### Rule 2: Use Persona Names

Use "Emma", "Alex", "Sam" — not "the user", "I", or "a customer".

| BAD | GOOD |
|-----|------|
| Given the user is logged in | Given Emma is logged in |
| When a customer adds an item | When Alex adds "Running Shoes" to his cart |
| Then I should see results | Then Emma should see 5 search results |

### Rule 3: One Behavior Per Scenario

Each scenario tests exactly ONE behavior. If you write "And" more than twice
in the Then section, you are testing multiple behaviors.

| BAD (multiple behaviors) | GOOD (split) |
|---|---|
| Scenario: User signs up and sets preferences and gets welcome email | Scenario: New user signs up successfully |
| | Scenario: New user receives welcome email |
| | Scenario: New user can set preferences |

### Rule 4: Use Background for Shared Setup

```gherkin
Feature: Shopping cart management

  Background:
    Given Emma is a returning customer
    And "Running Shoes" is available for $89.99
    And "Water Bottle" is available for $12.99

  Scenario: Add single item to cart
    When Emma adds "Running Shoes" to her cart
    Then her cart should contain 1 item
    And her cart total should be $89.99

  Scenario: Add multiple items to cart
    When Emma adds "Running Shoes" to her cart
    And Emma adds "Water Bottle" to her cart
    Then her cart should contain 2 items
```

### Rule 5: Use Scenario Outline for Data Variants

```gherkin
Scenario Outline: Validate password strength
  Given a new user registration form
  When a password of "<password>" is entered
  Then the strength indicator should show "<strength>"

  Examples:
    | password    | strength |
    | abc         | weak     |
    | Abc123      | medium   |
    | Abc123!@#XY | strong   |
```

### Rule 6: Never Reference UI Elements

No "click button", "fill field", "see text on screen". Scenarios describe
business behavior, not UI interaction.

| BAD | GOOD |
|-----|------|
| When I click the "Delete" button on the first row | When Emma removes the first item from her cart |
| Then the error toast should appear at the top | Then an error message should indicate invalid input |
| And the submit button should be disabled | And the form should prevent submission |

## Handling Vague Issues

| Issue clarity | Action |
|--------------|--------|
| Clear expected/actual behavior stated | Direct translation to Gherkin |
| Has repro steps but no expected behavior | Infer expected from the feature's documented purpose |
| Vague but the symptom is reproducible | Write test for the reported symptom, note the assumption |
| Completely vague, no repro possible | Ask for clarification (see `issue-triage.md`) |
| Contradicts documentation | Test against what documentation promises |
| Multiple behaviors described in one issue | Split into multiple scenarios |

When inferring expected behavior:
1. Check existing tests for the related feature — what do they assert?
2. Read the code to understand current behavior
3. Check documentation or README for stated behavior
4. Write the Gherkin for what SHOULD work based on reasonable expectations
5. Add a comment in the PR: "Expected behavior inferred from [source]"

## File Placement

### Directory Structure

Place feature files in `.bdd/features/` organized by functional domain:

```
.bdd/features/
  auth/
    login.feature
    signup.feature
  export/
    csv-encoding.feature      <-- issue-42
  search/
    basic-search.feature      <-- issue-103
  settings/
    dark-mode.feature         <-- issue-55
```

### Naming Convention

| Component | Format | Example |
|-----------|--------|---------|
| Directory | Domain name, lowercase | `export/`, `auth/`, `billing/` |
| File name | Kebab-case of core behavior | `csv-encoding.feature` |
| Feature tag | `@issue-{number}` | `@issue-42` |

### One Issue, One Feature File

Each issue gets its own `.feature` file. If an issue touches multiple domains
(rare), pick the PRIMARY domain and reference the others in a comment.

```gherkin
# This issue also affects the billing domain.
# See related test in billing/invoice-export.feature if applicable.
@issue-42
Feature: CSV export handles special characters
  ...
```

## The Golden Test Rule

Once a Gherkin scenario is written, it becomes the source of truth.

**NEVER** change a scenario to match what the code currently does. The scenario
captures what the USER EXPECTS. If the scenario fails, the code is wrong.

**NEVER** add `@skip` or `.skip()` to a scenario. If it fails, fix the code.

**NEVER** reduce assertion precision. If the scenario says "should contain
exactly 5 items", do not change it to "should contain items" because the code
returns 4.

**NEVER** mock a dependency to avoid a failure. The test runs against the real
system.

The ONLY time to modify a scenario is when the issue itself is updated or
clarified by the reporter. If the reporter says "actually I meant X not Y",
update the scenario to match the new understanding.

If the scenario seems wrong after reading the code, re-read the issue. The
issue defines the behavior. The code conforms to the issue. Not the other way
around.

For the fix cycle that comes next, see `references/red-green-fix-cycle.md`.
