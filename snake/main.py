#!/usr/bin/env python3
"""
Snake game with Sixel graphics.

A tiny 64x64 snake game rendered using Sixel graphics.

Controls:
- WASD or Arrow keys: Move the snake
- Q or Ctrl-C: Quit
- R: Restart after game over

Requirements:
- A terminal that supports Sixel graphics (iTerm2, Windows Terminal, mlterm, etc.)
- Python 3.13+
"""

from game import create_game
from terminal import run_game_loop


PIXEL_WIDTH = 64
PIXEL_HEIGHT = 64
FPS = 8.0


def main() -> None:
    """Entry point for the snake game."""
    print("Snake Game - Sixel Graphics")
    print("Controls: WASD/Arrows to move, Q to quit, R to restart")
    print("Starting in 2 seconds...")

    import time
    time.sleep(2)

    game = create_game(PIXEL_WIDTH, PIXEL_HEIGHT)
    run_game_loop(game, PIXEL_WIDTH, PIXEL_HEIGHT, FPS)

    print(f"Final score: {game.score}")
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
