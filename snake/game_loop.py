"""
Game loop module.

Handles the main game loop, input processing, and coordination
between the terminal, renderer, and game state.
"""

import sys
import time
from typing import Optional, Callable

from game import GameState, Direction
from renderer import GameRenderer
from terminals import Terminal, KeyEvent

# Platform-specific render settings
# macOS with Retina needs lower render rate due to larger sixel data
IS_MACOS = sys.platform == 'darwin'
MIN_RENDER_INTERVAL = 0.1 if IS_MACOS else 0.05  # 10 FPS on macOS, 20 FPS elsewhere


# Key mappings for direction control
DIRECTION_KEYS = {
    'w': Direction.UP,
    'a': Direction.LEFT,
    's': Direction.DOWN,
    'd': Direction.RIGHT,
}

ARROW_DIRECTIONS = {
    'up': Direction.UP,
    'down': Direction.DOWN,
    'left': Direction.LEFT,
    'right': Direction.RIGHT,
}


def process_input(key: Optional[KeyEvent], game: GameState) -> bool:
    """
    Process a key event and update game state.

    Args:
        key: The key event to process (or None if no input)
        game: The game state to update

    Returns:
        False if the game should quit, True otherwise
    """
    if key is None:
        return True

    # Check for quit
    if key.is_quit:
        return False

    # Check for restart
    if key.key_type.value == 'character' and key.value.lower() == 'r':
        game.reset()
        return True

    # Check for direction keys
    if key.key_type.value == 'character':
        char = key.value.lower()
        if char in DIRECTION_KEYS:
            game.change_direction(DIRECTION_KEYS[char])

    elif key.key_type.value == 'arrow':
        direction = key.value.lower()
        if direction in ARROW_DIRECTIONS:
            game.change_direction(ARROW_DIRECTIONS[direction])

    return True


def run_game_loop(
    game: GameState,
    terminal: Terminal,
    fps: float = 8.0,
    on_quit: Optional[Callable[[], None]] = None
) -> None:
    """
    Run the main game loop.

    Uses separate timing for game updates and rendering to maintain
    responsive input even when rendering is slow.

    Args:
        game: The game state
        terminal: Terminal instance for I/O
        fps: Target frames per second (game tick rate)
        on_quit: Optional callback when game exits
    """
    renderer = GameRenderer(game)
    game_tick_time = 1.0 / fps  # Time between game state updates

    # Pre-render initial frame
    term_cols, term_rows = terminal.get_size()
    row, col = renderer.calculate_terminal_position(term_cols, term_rows)
    cached_frame = renderer.render_frame(game.game_over)

    try:
        with terminal:
            last_game_tick = time.time()
            last_render = 0.0
            needs_render = True

            while True:
                loop_start = time.time()

                # 1. Handle ALL pending input (non-blocking)
                # Process multiple keys if they've queued up
                while True:
                    key = terminal.read_key(timeout=0.001)  # 1ms timeout
                    if key is None:
                        break
                    if not process_input(key, game):
                        return  # Quit requested
                    needs_render = True  # Input might change display

                # 2. Update game state at fixed intervals
                current_time = time.time()
                if current_time - last_game_tick >= game_tick_time:
                    if not game.game_over:
                        game.update()
                        needs_render = True
                    last_game_tick = current_time

                # 3. Render only if needed and enough time has passed
                # Limit render rate to avoid overwhelming slow terminals
                if needs_render and (current_time - last_render >= MIN_RENDER_INTERVAL):
                    terminal.move_cursor(row, col)
                    cached_frame = renderer.render_frame(game.game_over)
                    terminal.write(cached_frame)
                    terminal.flush()
                    last_render = current_time
                    needs_render = False

                # 4. Small sleep to prevent CPU spinning
                # But keep it short for responsive input
                elapsed = time.time() - loop_start
                sleep_time = max(0.001, 0.005 - elapsed)  # Target ~200 loops/sec
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        if on_quit:
            on_quit()


def wait_for_key(
    terminal: Terminal,
    target_keys: set[str],
    quit_keys: Optional[set[str]] = None
) -> bool:
    """
    Wait for a specific key press.

    Args:
        terminal: Terminal instance
        target_keys: Set of characters to wait for
        quit_keys: Optional set of characters that mean quit

    Returns:
        True if target key was pressed, False if quit key was pressed
    """
    if quit_keys is None:
        quit_keys = {'q'}

    try:
        terminal.enter_raw_mode()
        while True:
            key = terminal.read_key(timeout=0.1)
            if key is None:
                continue

            if key.is_quit:
                return False

            if key.key_type.value == 'character':
                if key.value in target_keys:
                    return True
                if key.value.lower() in quit_keys:
                    return False

    finally:
        terminal.exit_raw_mode()
