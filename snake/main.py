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


# Platform-specific settings
if sys.platform == 'darwin':
    # macOS: 1.5x size for Retina (balance between size and performance)
    PIXEL_WIDTH = 384
    PIXEL_HEIGHT = 384
    PIXEL_SIZE = 24
    FPS = 12.0
else:
    PIXEL_WIDTH = 256
    PIXEL_HEIGHT = 256
    PIXEL_SIZE = 16
    FPS = 8.0


def main() -> None:
    """Entry point for the snake game."""
    # Create terminal instance for the current platform
    terminal = create_terminal()

    # ANSI colors
    GREEN = "\x1b[32m"
    RED = "\x1b[91m"  # Bright red like the pellet
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
    game = create_game(PIXEL_WIDTH, PIXEL_HEIGHT, PIXEL_SIZE)
    run_game_loop(game, terminal, FPS)

    print(f"Final score: {RED}{game.score}{RESET}")
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
