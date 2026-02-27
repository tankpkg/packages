Feature: Edge Cases
  Handling disconnections, reconnections, and unusual situations.

  Scenario: Player disconnects during game
    Given a game with 4 players in progress
    When Player "Bob" disconnects
    Then the remaining 3 players should see "Bob" as disconnected
    And the game should continue with 3 players

  Scenario: Host disconnects and migrates
    Given a game with 4 players where "Host" is the host
    When Player "Host" disconnects
    Then another player should become the new host
    And the game should continue

  Scenario: Player reconnects
    Given Player "Bob" disconnected from an active game
    When Player "Bob" reconnects to the same room
    Then Player "Bob" should see the current game state
    And Player "Bob" should be able to continue playing

  Scenario: Timer expires with missing submissions
    Given a game in "SUBMITTING" phase with 30 second timer
    And Player "Alice" has submitted an answer
    And Player "Bob" has not submitted
    When the timer expires
    Then the game should advance to "VOTING" phase
    And Player "Bob" should have a default empty answer
