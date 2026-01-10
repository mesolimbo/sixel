"""
Terminal handling module.

Handles keyboard input, terminal configuration, and the game loop.
Cross-platform support for Windows and Unix.
Pure sixel rendering - no ANSI text mixing.
"""

import shutil
import sys
import time
from typing import Optional, Callable, Tuple

from game import GameState, Direction
from sixel import (
    pixels_to_sixel,
    create_pixel_buffer,
    fill_rect,
    draw_text,
    get_text_width,
    COLOR_INDICES,
    FONT_HEIGHT,
)

# Detect platform
IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    import msvcrt
else:
    import select
    import termios
    import tty


# Key mappings
KEY_MAP = {
    'w': Direction.UP,
    'W': Direction.UP,
    's': Direction.DOWN,
    'S': Direction.DOWN,
    'a': Direction.LEFT,
    'A': Direction.LEFT,
    'd': Direction.RIGHT,
    'D': Direction.RIGHT,
}

# Arrow key codes
if IS_WINDOWS:
    ARROW_UP = 'H'
    ARROW_DOWN = 'P'
    ARROW_LEFT = 'K'
    ARROW_RIGHT = 'M'
else:
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
        if self.is_raw:
            return
        if not IS_WINDOWS:
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setraw(sys.stdin.fileno())
        self.is_raw = True

    def exit_raw_mode(self) -> None:
        if not IS_WINDOWS and self.old_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        self.is_raw = False

    def read_key(self, timeout: float = 0.0) -> Optional[str]:
        if IS_WINDOWS:
            return self._read_key_windows(timeout)
        else:
            return self._read_key_unix(timeout)

    def _read_key_windows(self, timeout: float) -> Optional[str]:
        start = time.time()
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b'\x00', b'\xe0'):
                    if msvcrt.kbhit():
                        special = msvcrt.getch().decode('latin-1')
                        return ('ARROW', special)
                return ch.decode('latin-1')
            if timeout > 0 and (time.time() - start) >= timeout:
                return None
            if timeout == 0:
                return None
            time.sleep(0.01)

    def _read_key_unix(self, timeout: float) -> Optional[str]:
        if not select.select([sys.stdin], [], [], timeout)[0]:
            return None
        char = sys.stdin.read(1)
        if char == '\x1b':
            if select.select([sys.stdin], [], [], 0.01)[0]:
                char += sys.stdin.read(1)
                if char == '\x1b[':
                    if select.select([sys.stdin], [], [], 0.01)[0]:
                        char += sys.stdin.read(1)
        return char

    def enter_alternate_screen(self) -> None:
        sys.stdout.write('\x1b[?1049h')
        sys.stdout.flush()

    def exit_alternate_screen(self) -> None:
        sys.stdout.write('\x1b[?1049l')
        sys.stdout.flush()

    def clear_screen(self) -> None:
        sys.stdout.write('\x1b[2J\x1b[H')
        sys.stdout.flush()

    def hide_cursor(self) -> None:
        sys.stdout.write('\x1b[?25l')
        sys.stdout.flush()

    def show_cursor(self) -> None:
        sys.stdout.write('\x1b[?25h')
        sys.stdout.flush()

    def move_cursor_home(self) -> None:
        sys.stdout.write('\x1b[H')
        sys.stdout.flush()

    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor to specific row and column (1-indexed)."""
        sys.stdout.write(f'\x1b[{row};{col}H')
        sys.stdout.flush()

    def get_size(self) -> Tuple[int, int]:
        """Get terminal size as (columns, rows)."""
        size = shutil.get_terminal_size()
        return size.columns, size.lines


def render_frame(
    game: GameState,
    frame_width: int,
    frame_height: int,
    game_area_y: int,
    show_game_over: bool
) -> str:
    """
    Render the complete frame (title, game, status) as a single sixel image.
    """
    pixels = create_pixel_buffer(frame_width, frame_height, COLOR_INDICES["background"])
    ps = game.pixel_size
    game_size = game.width * ps  # Game area is square

    # Draw 2-pixel green frame around the entire image
    frame_color = COLOR_INDICES["text_green"]
    # Top edge
    fill_rect(pixels, 0, 0, frame_width, 2, frame_color)
    # Bottom edge
    fill_rect(pixels, 0, frame_height - 2, frame_width, 2, frame_color)
    # Left edge
    fill_rect(pixels, 0, 0, 2, frame_height, frame_color)
    # Right edge
    fill_rect(pixels, frame_width - 2, 0, 2, frame_height, frame_color)

    # Calculate centering for game area
    game_x = (frame_width - game_size) // 2

    # Draw title "SIXEL SNAKE" centered at top
    title = "SIXEL SNAKE"
    title_scale = 4
    title_width = get_text_width(title, title_scale)
    title_x = (frame_width - title_width) // 2
    title_y = 8
    draw_text(pixels, title_x, title_y, title, COLOR_INDICES["text_green"], title_scale)

    # Draw game border
    border_color = COLOR_INDICES["border"]
    game_y = game_area_y
    # Top and bottom
    fill_rect(pixels, game_x, game_y, game_size, ps, border_color)
    fill_rect(pixels, game_x, game_y + game_size - ps, game_size, ps, border_color)
    # Left and right
    fill_rect(pixels, game_x, game_y, ps, game_size, border_color)
    fill_rect(pixels, game_x + game_size - ps, game_y, ps, game_size, border_color)

    # Draw food
    fx, fy = game.food
    fill_rect(pixels, game_x + fx * ps, game_y + fy * ps, ps, ps, COLOR_INDICES["food"])

    # Draw snake body
    for segment in game.snake[1:]:
        sx, sy = segment
        fill_rect(pixels, game_x + sx * ps, game_y + sy * ps, ps, ps, COLOR_INDICES["snake_body"])

    # Draw snake head
    if game.snake:
        hx, hy = game.snake[0]
        fill_rect(pixels, game_x + hx * ps, game_y + hy * ps, ps, ps, COLOR_INDICES["snake_head"])

    # Draw score below game
    score_text = f"SCORE: {game.score}"
    score_scale = 2
    score_width = get_text_width(score_text, score_scale)
    score_x = (frame_width - score_width) // 2
    score_y = game_y + game_size + 16
    draw_text(pixels, score_x, score_y, score_text, COLOR_INDICES["text"], score_scale)

    # Draw game over text if needed
    if show_game_over:
        go_text = "GAME OVER!"
        go_scale = 4
        go_width = get_text_width(go_text, go_scale)
        go_x = (frame_width - go_width) // 2
        go_y = score_y + FONT_HEIGHT * score_scale + 16
        draw_text(pixels, go_x, go_y, go_text, COLOR_INDICES["food"], go_scale)

        hint_text = "'R' RESTART  'Q' QUIT"
        hint_scale = 2
        hint_width = get_text_width(hint_text, hint_scale)
        hint_x = (frame_width - hint_width) // 2
        hint_y = go_y + FONT_HEIGHT * go_scale + 12
        draw_text(pixels, hint_x, hint_y, hint_text, COLOR_INDICES["text"], hint_scale)

    return pixels_to_sixel(pixels, frame_width, frame_height)


def run_game_loop(
    game: GameState,
    pixel_width: int = 128,
    pixel_height: int = 128,
    fps: float = 8.0,
    on_quit: Optional[Callable[[], None]] = None
) -> None:
    """
    Run the main game loop with pure sixel rendering.
    """
    terminal = Terminal()
    frame_time = 1.0 / fps

    # Calculate frame dimensions
    # Title area + game + status
    title_height = 50  # Space for title (scale 4 = 28px + padding)
    game_size = game.width * game.pixel_size
    status_height = 120  # Space for score and game over text
    frame_width = game_size + 40  # Add some padding
    frame_height = title_height + game_size + status_height
    game_area_y = title_height

    try:
        terminal.enter_raw_mode()
        terminal.enter_alternate_screen()
        terminal.hide_cursor()
        terminal.clear_screen()

        last_update = time.time()

        while True:
            # Handle input
            key = terminal.read_key(timeout=0.01)

            if key:
                if isinstance(key, tuple) and key[0] == 'ARROW':
                    arrow = key[1]
                    if arrow == ARROW_UP:
                        game.change_direction(Direction.UP)
                    elif arrow == ARROW_DOWN:
                        game.change_direction(Direction.DOWN)
                    elif arrow == ARROW_LEFT:
                        game.change_direction(Direction.LEFT)
                    elif arrow == ARROW_RIGHT:
                        game.change_direction(Direction.RIGHT)
                elif key in ('q', 'Q', '\x03'):
                    break
                elif key in KEY_MAP:
                    game.change_direction(KEY_MAP[key])
                elif key == ARROW_UP:
                    game.change_direction(Direction.UP)
                elif key == ARROW_DOWN:
                    game.change_direction(Direction.DOWN)
                elif key == ARROW_LEFT:
                    game.change_direction(Direction.LEFT)
                elif key == ARROW_RIGHT:
                    game.change_direction(Direction.RIGHT)
                elif key in ('r', 'R'):
                    game.reset()

            # Update game at fixed rate
            current_time = time.time()
            if current_time - last_update >= frame_time:
                if not game.game_over:
                    game.update()
                last_update = current_time

                # Render complete frame as single sixel
                # Center in terminal (assuming ~10 pixels per character cell width)
                term_cols, term_rows = terminal.get_size()
                sixel_char_width = frame_width // 10
                center_col = max(1, (term_cols - sixel_char_width) // 2)
                sixel_char_height = frame_height // 20  # ~20 pixels per row
                center_row = max(1, (term_rows - sixel_char_height) // 2)

                terminal.move_cursor(center_row, center_col)
                frame = render_frame(
                    game,
                    frame_width,
                    frame_height,
                    game_area_y,
                    game.game_over
                )
                sys.stdout.write(frame)
                sys.stdout.flush()

    except KeyboardInterrupt:
        pass
    finally:
        terminal.show_cursor()
        terminal.exit_alternate_screen()
        terminal.exit_raw_mode()
        if on_quit:
            on_quit()
