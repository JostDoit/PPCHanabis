# PPCHanabis

# Goal
Implement a multi-process and multi-thread multiplayer game in Python.

# Minimun specifications
Hannabis is a simplified version of the Hanabi cooperative card game. Its deck contains numbered cards in
as many colors as there are players (e.g. for 2 players there are 2 colors: red and blue, for 3 players there
are 3 colors: red, blue and green, etc.): three 1s, two each of 2s, 3s, and 4s, and one 5. The game begins with
number_of_players + 3 information tokens and 3 fuse tokens. Players are dealt a hand of five cards. They
can see each other's cards but not their own. Each turn, a player must take one of the following actions:
• give information: pointing out cards of either a given number or a given color in the hand of
another player (e.g. "This card is your only red card," "These two cards are your only 2s", etc).
Giving information consumes one information token.
• play a card: by choosing a card from the hand and attempting to add it to the cards already played.
This is successful if the card is a 1 in a color suit that has not yet been played, or if it is the next
number in a suit that has been played. Otherwise a fuse token is consumed and the misplayed card
is discarded. Successfully playing a 5 of any suit restores one information token. Whether the play
was successful or not, the player draws a replacement card from the deck.
The game ends when either all fuse tokens are used up, resulting in a game loss, or all 5s have been played
successfully, leading to a game win.

# Minimal design

Hannabis involves 2 types of processes at least:
• game: implements the game session, manages the deck and keeps track of suits in construction
• player: interacts with the user 1
, the game process and other player processes keeping track of
and displaying hands and associated information. Interactions with the game process are carried
out in a separate thread.

## Inter-process communication: 
Suites in construction and tokens are stored in a shared memory
accessible to all processes, player processes communicate with the game process via sockets and among
themselves using a message queue requiring a carefully designed exchange protocol, end of game events
are notified via signals emitted by the appropriate process in each situation. 