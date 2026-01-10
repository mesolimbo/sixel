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
from terminal import run_game_loop, Terminal


PIXEL_WIDTH = 256
PIXEL_HEIGHT = 256
FPS = 8.0


def wait_for_spacebar() -> bool:
    """Wait for spacebar press. Returns False if user wants to quit."""
    terminal = Terminal()
    try:
        terminal.enter_raw_mode()
        while True:
            key = terminal.read_key(timeout=0.1)
            if key == ' ':
                return True
            if key in ('q', 'Q', '\x03'):
                return False
    finally:
        terminal.exit_raw_mode()


def main() -> None:
    """Entry point for the snake game."""
    # ANSI colors
    GREEN = "\x1b[32m"
    RESET = "\x1b[0m"

    print("Snake Game - Sixel Graphics")
    print(f"Controls: {GREEN}WASD{RESET}/{GREEN}Arrows{RESET} to move, {GREEN}Q{RESET} to quit, {GREEN}R{RESET} to restart")
    print(f"Press {GREEN}SPACE{RESET} to start...")

    if not wait_for_spacebar():
        print("Goodbye!")
        return

    game = create_game(PIXEL_WIDTH, PIXEL_HEIGHT)
    run_game_loop(game, PIXEL_WIDTH, PIXEL_HEIGHT, FPS)

    print(f"Final score: {game.score}")
    print("Thanks for playing!")


if __name__ == "__main__":
    main()
