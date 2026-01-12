"""
Application loop module for sixtop.

Handles the main loop, input processing, and coordination
between the terminal, renderer, and metrics collection.
"""

import sys
import time
from typing import Optional, Callable

from metrics import MetricsCollector
from renderer import MetricsRenderer, MetricView, VIEW_TITLES
from terminals import Terminal, KeyEvent


# Update intervals
METRICS_UPDATE_INTERVAL = 1.0  # Update metrics every second
RENDER_INTERVAL = 0.5  # Render at 2 FPS (sufficient for monitoring)


def process_input(key: Optional[KeyEvent], renderer: MetricsRenderer) -> bool:
    """
    Process a key event and update application state.

    Args:
        key: The key event to process (or None if no input)
        renderer: The renderer to update view on

    Returns:
        False if the app should quit, True otherwise
    """
    if key is None:
        return True

    # Check for quit
    if key.is_quit:
        return False

    # Check for tab (t) to switch views
    if key.key_type.value == 'character' and key.value.lower() == 't':
        new_view = renderer.next_view()
        return True

    return True


def run_app_loop(
    metrics: MetricsCollector,
    renderer: MetricsRenderer,
    terminal: Terminal,
    on_quit: Optional[Callable[[], None]] = None
) -> None:
    """
    Run the main application loop.

    Uses separate timing for metrics updates and rendering to maintain
    responsive input even when rendering is slow.

    Args:
        metrics: The metrics collector
        renderer: The metrics renderer
        terminal: Terminal instance for I/O
        on_quit: Optional callback when app exits
    """
    # Pre-render initial frame
    term_cols, term_rows = terminal.get_size()
    row, col = renderer.calculate_terminal_position(term_cols, term_rows)

    # Do initial metrics collection
    metrics.update()
    cached_frame = renderer.render_frame(metrics)

    try:
        with terminal:
            last_metrics_update = time.time()
            last_render = 0.0
            needs_render = True

            while True:
                loop_start = time.time()

                # 1. Handle ALL pending input (non-blocking)
                while True:
                    key = terminal.read_key(timeout=0.001)
                    if key is None:
                        break
                    if not process_input(key, renderer):
                        return  # Quit requested
                    needs_render = True  # Input might change display

                # 2. Update metrics at fixed intervals
                current_time = time.time()
                if current_time - last_metrics_update >= METRICS_UPDATE_INTERVAL:
                    metrics.update()
                    needs_render = True
                    last_metrics_update = current_time

                # 3. Render only if needed and enough time has passed
                if needs_render and (current_time - last_render >= RENDER_INTERVAL):
                    terminal.move_cursor(row, col)
                    cached_frame = renderer.render_frame(metrics)
                    terminal.write(cached_frame)
                    terminal.flush()
                    last_render = current_time
                    needs_render = False

                # 4. Small sleep to prevent CPU spinning
                elapsed = time.time() - loop_start
                sleep_time = max(0.01, 0.05 - elapsed)  # Target ~20 loops/sec
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        if on_quit:
            on_quit()


def show_startup_message(terminal: Terminal, renderer: MetricsRenderer) -> bool:
    """
    Show startup message and wait for user to press space.

    Args:
        terminal: Terminal instance
        renderer: Renderer to show current view

    Returns:
        True if user pressed space to start, False if quit
    """
    # ANSI colors
    CYAN = "\x1b[36m"
    GREEN = "\x1b[32m"
    RESET = "\x1b[0m"

    print("Sixtop - System Monitor with Sixel Graphics")
    print(f"Current view: {CYAN}{VIEW_TITLES[renderer.current_view]}{RESET}")
    print()
    print(f"Controls:")
    print(f"  {GREEN}T{RESET}      - Tab between views (Energy/CPU/I-O/Memory/Network)")
    print(f"  {GREEN}Q{RESET}      - Quit")
    print()
    print(f"Press {GREEN}SPACE{RESET} to start...")

    try:
        terminal.enter_raw_mode()
        while True:
            key = terminal.read_key(timeout=0.1)
            if key is None:
                continue

            if key.is_quit:
                return False

            if key.key_type.value == 'character':
                if key.value == ' ':
                    return True
                if key.value.lower() == 'q':
                    return False

    finally:
        terminal.exit_raw_mode()
