Feature: Game Lobby
  Players can create and join game rooms using room codes.

  Scenario: Host creates a room and players join
    Given Player "Host" creates a new room
    Then Player "Host" should see a 4-character room code
    When Player "Alice" joins the room
    And Player "Bob" joins the room
    Then all players should see 3 players in the lobby

  Scenario: Host starts the game
    Given a room with 3 players
    When Player "Host" starts the game
    Then all players should see the game has started

  Scenario: Player cannot join a full room
    Given a room with the maximum number of players
    When Player "Late" tries to join the room
    Then Player "Late" should see an error "Room is full"
