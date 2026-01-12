"""
Application loop module for sixtop.

Handles the main loop, input processing, and coordination
between the terminal, renderer, and metrics collection.

Uses threading to ensure responsive input even during rendering.
"""

import sys
import time
import threading
from queue import Queue, Empty
from typing import Optional, Callable

from metrics import MetricsCollector
from renderer import MetricsRenderer, MetricView, VIEW_TITLES
from terminals import Terminal, KeyEvent


# Update interval
UPDATE_INTERVAL = 1.0  # Update and render once per second


class InputThread(threading.Thread):
    """
    Background thread for reading keyboard input.

    Reads keys continuously and puts them in a queue for the main thread.
    """

    def __init__(self, terminal: Terminal, key_queue: Queue):
        super().__init__(daemon=True)
        self.terminal = terminal
        self.key_queue = key_queue
        self.running = True

    def run(self) -> None:
        """Continuously read keys and queue them."""
        while self.running:
            try:
                # Short timeout to allow checking self.running
                key = self.terminal.read_key(timeout=0.05)
                if key is not None:
                    self.key_queue.put(key)
            except Exception:
                # Terminal might be closed, stop gracefully
                break

    def stop(self) -> None:
        """Signal the thread to stop."""
        self.running = False


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
        renderer.next_view()
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

    Uses a separate thread for input handling to ensure responsiveness
    even during rendering. Renders once per second.

    Args:
        metrics: The metrics collector
        renderer: The metrics renderer
        terminal: Terminal instance for I/O
        on_quit: Optional callback when app exits
    """
    # Queue for input events from the input thread
    key_queue: Queue[KeyEvent] = Queue()

    # Do initial metrics collection
    metrics.update()

    # Start the input thread
    input_thread = None

    try:
        with terminal:
            # Start input thread after entering raw mode
            input_thread = InputThread(terminal, key_queue)
            input_thread.start()

            last_update = 0.0
            running = True

            while running:
                current_time = time.time()

                # Process ALL queued input (non-blocking)
                while True:
                    try:
                        key = key_queue.get_nowait()
                        if not process_input(key, renderer):
                            running = False
                            break
                    except Empty:
                        break

                if not running:
                    break

                # Update metrics and render once per second
                if current_time - last_update >= UPDATE_INTERVAL:
                    metrics.update()

                    # Render frame
                    frame = renderer.render_frame(metrics)

                    # Move cursor to start of output area and draw
                    terminal.move_cursor_home()
                    terminal.write(frame)
                    terminal.flush()

                    last_update = current_time

                # Small sleep to prevent CPU spinning while remaining responsive
                time.sleep(0.02)  # 50 loops/sec for responsive input

    except KeyboardInterrupt:
        pass
    finally:
        # Stop input thread
        if input_thread is not None:
            input_thread.stop()
            input_thread.join(timeout=0.5)

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
    print(f"  {GREEN}T{RESET}      - Tab between views (Energy/CPU/IO/Memory/Network)")
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
