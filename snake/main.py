#!/usr/bin/env python3
"""
Snake game with Sixel graphics.

A snake game rendered using Sixel graphics with cross-platform support.

Controls:
- WASD or Arrow keys: Move the snake
- Q or Ctrl-C: Quit
- R: Restart after game over

Requirements:
- A terminal that supports Sixel graphics (iTerm2, Windows Terminal, mlterm, etc.)
- Python 3.13+
"""

import sys

from game import create_game
from game_loop import run_game_loop, wait_for_key
from terminals import create_terminal


# Double size on macOS for Retina displays
if sys.platform == 'darwin':
    PIXEL_WIDTH = 512
    PIXEL_HEIGHT = 512
else:
    PIXEL_WIDTH = 256
    PIXEL_HEIGHT = 256

FPS = 8.0


def main() -> None:
    """Entry point for the snake game."""
    # Create terminal instance for the current platform
    terminal = create_terminal()

    # ANSI colors for the welcome message
    GREEN = "\x1b[32m"
    RESET = "\x1b[0m"

    print("Snake Game - Sixel Graphics")
    print(f"Controls: {GREEN}WASD{RESET}/{GREEN}Arrows{RESET} to move, "
          f"{GREEN}Q{RESET} to quit, {GREEN}R{RESET} to restart")
    print(f"Press {GREEN}SPACE{RESET} to start...")

    # Wait for spacebar to start
    if not wait_for_key(terminal, {' '}, {'q'}):
        print("Goodbye!")
        return

    # Create and run the game
    game = create_game(PIXEL_WIDTH, PIXEL_HEIGHT)
    run_game_loop(game, terminal, FPS)

    print(f"Final score: {game.score}")
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
