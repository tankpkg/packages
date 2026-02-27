Feature: Game Round Flow
  A complete round: prompt, submit answers, vote, see results.

  Scenario: Complete prompt-response round
    Given a game with 4 players in the "PROMPTING" phase
    Then all players should see the same prompt
    When Player "Alice" submits answer "A rubber duck"
    And Player "Bob" submits answer "Three raccoons"
    And Player "Charlie" submits answer "WiFi password"
    And Player "Dana" submits answer "Infinite breadsticks"
    Then the game should advance to "VOTING" phase
    And all players should see all 4 answers

  Scenario: Voting and scoring
    Given a game in the "VOTING" phase with 4 answers
    When Player "Alice" votes for answer 2
    And Player "Bob" votes for answer 1
    And Player "Charlie" votes for answer 4
    And Player "Dana" votes for answer 1
    Then the game should advance to "RESULTS" phase
    And all players should see updated scores
