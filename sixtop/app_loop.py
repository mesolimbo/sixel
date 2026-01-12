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

# ANSI escape codes
SAVE_CURSOR = "\x1b[s"
RESTORE_CURSOR = "\x1b[u"


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
    even during rendering. Renders once per second at the current
    cursor position.

    Args:
        metrics: The metrics collector
        renderer: The metrics renderer
        terminal: Terminal instance for I/O
        on_quit: Optional callback when app exits
    """
    # Queue for input events from the input thread
    key_queue: Queue[KeyEvent] = Queue()

    # Start the input thread
    input_thread = None

    # Track if we've collected stats yet
    stats_ready = False

    try:
        with terminal:
            # Save cursor position for redrawing in place
            terminal.write(SAVE_CURSOR)
            terminal.flush()

            # Start input thread after entering raw mode
            input_thread = InputThread(terminal, key_queue)
            input_thread.start()

            # Render initial frame immediately with stats_ready=False
            frame = renderer.render_frame(metrics, stats_ready=False)
            terminal.write(RESTORE_CURSOR)
            terminal.write(SAVE_CURSOR)
            terminal.write(frame)
            terminal.flush()

            last_update = time.time()
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
                    stats_ready = True

                    # Render frame
                    frame = renderer.render_frame(metrics, stats_ready=stats_ready)

                    # Restore to saved position and redraw
                    terminal.write(RESTORE_CURSOR)
                    terminal.write(SAVE_CURSOR)
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
