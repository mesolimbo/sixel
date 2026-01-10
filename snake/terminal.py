"""
Terminal handling module.

Handles keyboard input, terminal configuration, and the game loop.
"""

import sys
import select
import termios
import tty
from typing import Optional, Callable
import time

from game import GameState, Direction
from sixel import (
    pixels_to_sixel,
    create_pixel_buffer,
    fill_rect,
    COLOR_INDICES,
)


# Key mappings
KEY_MAP = {
    # WASD keys
    'w': Direction.UP,
    'W': Direction.UP,
    's': Direction.DOWN,
    'S': Direction.DOWN,
    'a': Direction.LEFT,
    'A': Direction.LEFT,
    'd': Direction.RIGHT,
    'D': Direction.RIGHT,
}

# Arrow key escape sequences
ARROW_UP = '\x1b[A'
ARROW_DOWN = '\x1b[B'
ARROW_RIGHT = '\x1b[C'
ARROW_LEFT = '\x1b[D'


class Terminal:
    """Manages terminal state and input."""

    def __init__(self):
        self.old_settings = None
        self.is_raw = False

    def enter_raw_mode(self) -> None:
        """Put the terminal into raw mode for character-by-character input."""
        if self.is_raw:
            return
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        self.is_raw = True

    def exit_raw_mode(self) -> None:
        """Restore the terminal to its original mode."""
        if self.old_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            self.is_raw = False

    def read_key(self, timeout: float = 0.0) -> Optional[str]:
        """
        Read a key from stdin with optional timeout.

        Args:
            timeout: How long to wait for input (0 = non-blocking)

        Returns:
            The key pressed, or None if no input available
        """
        if not select.select([sys.stdin], [], [], timeout)[0]:
            return None

        char = sys.stdin.read(1)

        # Handle escape sequences (arrow keys)
        if char == '\x1b':
            if select.select([sys.stdin], [], [], 0.01)[0]:
                char += sys.stdin.read(1)
                if char == '\x1b[':
                    if select.select([sys.stdin], [], [], 0.01)[0]:
                        char += sys.stdin.read(1)

        return char

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        sys.stdout.write('\x1b[2J\x1b[H')
        sys.stdout.flush()

    def move_cursor_home(self) -> None:
        """Move cursor to the top-left corner."""
        sys.stdout.write('\x1b[H')
        sys.stdout.flush()

    def hide_cursor(self) -> None:
        """Hide the terminal cursor."""
        sys.stdout.write('\x1b[?25l')
        sys.stdout.flush()

    def show_cursor(self) -> None:
        """Show the terminal cursor."""
        sys.stdout.write('\x1b[?25h')
        sys.stdout.flush()


def render_game(game: GameState, pixel_width: int, pixel_height: int) -> str:
    """
    Render the game state to a sixel string.

    Args:
        game: The current game state
        pixel_width: Width in pixels
        pixel_height: Height in pixels

    Returns:
        Sixel string representing the current frame
    """
    pixels = create_pixel_buffer(pixel_width, pixel_height, COLOR_INDICES["background"])
    ps = game.pixel_size

    # Draw border
    border_color = COLOR_INDICES["border"]
    # Top and bottom
    fill_rect(pixels, 0, 0, pixel_width, ps, border_color)
    fill_rect(pixels, 0, pixel_height - ps, pixel_width, ps, border_color)
    # Left and right
    fill_rect(pixels, 0, 0, ps, pixel_height, border_color)
    fill_rect(pixels, pixel_width - ps, 0, ps, pixel_height, border_color)

    # Draw food
    fx, fy = game.food
    fill_rect(pixels, fx * ps, fy * ps, ps, ps, COLOR_INDICES["food"])

    # Draw snake body
    for segment in game.snake[1:]:
        sx, sy = segment
        fill_rect(pixels, sx * ps, sy * ps, ps, ps, COLOR_INDICES["snake_body"])

    # Draw snake head
    if game.snake:
        hx, hy = game.snake[0]
        fill_rect(pixels, hx * ps, hy * ps, ps, ps, COLOR_INDICES["snake_head"])

    return pixels_to_sixel(pixels, pixel_width, pixel_height)


def run_game_loop(
    game: GameState,
    pixel_width: int = 64,
    pixel_height: int = 64,
    fps: float = 8.0,
    on_quit: Optional[Callable[[], None]] = None
) -> None:
    """
    Run the main game loop.

    Args:
        game: The game state to run
        pixel_width: Width in pixels
        pixel_height: Height in pixels
        fps: Target frames per second
        on_quit: Optional callback when game is quit
    """
    terminal = Terminal()
    frame_time = 1.0 / fps

    try:
        terminal.enter_raw_mode()
        terminal.hide_cursor()
        terminal.clear_screen()

        last_update = time.time()

        while True:
            # Handle input
            key = terminal.read_key(timeout=0.01)

            if key:
                # Check for quit
                if key in ('q', 'Q', '\x03'):  # q or Ctrl-C
                    break

                # Check for direction keys
                if key in KEY_MAP:
                    game.change_direction(KEY_MAP[key])
                elif key == ARROW_UP:
                    game.change_direction(Direction.UP)
                elif key == ARROW_DOWN:
                    game.change_direction(Direction.DOWN)
                elif key == ARROW_LEFT:
                    game.change_direction(Direction.LEFT)
                elif key == ARROW_RIGHT:
                    game.change_direction(Direction.RIGHT)
                elif key == 'r' or key == 'R':
                    # Restart game
                    game.reset()

            # Update game at fixed rate
            current_time = time.time()
            if current_time - last_update >= frame_time:
                if not game.game_over:
                    game.update()
                last_update = current_time

                # Render
                terminal.move_cursor_home()
                frame = render_game(game, pixel_width, pixel_height)
                sys.stdout.write(frame)
                sys.stdout.write(f"\n\rScore: {game.score}")
                if game.game_over:
                    sys.stdout.write("  GAME OVER! Press 'r' to restart, 'q' to quit")
                sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        terminal.show_cursor()
        terminal.exit_raw_mode()
        sys.stdout.write('\n')
        if on_quit:
            on_quit()
