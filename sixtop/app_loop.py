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
from typing import Optional, Callable, Tuple

from metrics import MetricsCollector
from renderer import MetricsRenderer, MetricView, VIEW_TITLES
from terminals import Terminal, KeyEvent


# Update interval
UPDATE_INTERVAL = 1.0  # Update metrics once per second

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


def process_input(key: Optional[KeyEvent], renderer: MetricsRenderer) -> Tuple[bool, bool]:
    """
    Process a key event and update application state.

    Args:
        key: The key event to process (or None if no input)
        renderer: The renderer to update view on

    Returns:
        Tuple of (should_continue, needs_render)
    """
    if key is None:
        return True, False

    # Check for quit
    if key.is_quit:
        return False, False

    # Check for tab (t) to switch views
    if key.key_type.value == 'character' and key.value.lower() == 't':
        renderer.next_view()
        return True, True  # Need to re-render immediately

    return True, False


def run_app_loop(
    metrics: MetricsCollector,
    renderer: MetricsRenderer,
    terminal: Terminal,
    on_quit: Optional[Callable[[], None]] = None
) -> None:
    """
    Run the main application loop.

    Uses a separate thread for input handling to ensure responsiveness
    even during rendering. Renders immediately on view changes and
    updates metrics once per second.

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

    def render_frame():
        """Helper to render and display a frame."""
        frame = renderer.render_frame(metrics, stats_ready=stats_ready)
        terminal.write(RESTORE_CURSOR)
        terminal.write(SAVE_CURSOR)
        terminal.write(frame)
        terminal.flush()

    try:
        with terminal:
            # Save cursor position for redrawing in place
            terminal.write(SAVE_CURSOR)
            terminal.flush()

            # Start input thread after entering raw mode
            input_thread = InputThread(terminal, key_queue)
            input_thread.start()

            # Render initial frame immediately with stats_ready=False
            render_frame()

            last_update = time.time()
            running = True

            while running:
                current_time = time.time()
                needs_render = False

                # Process ALL queued input (non-blocking)
                while True:
                    try:
                        key = key_queue.get_nowait()
                        should_continue, key_needs_render = process_input(key, renderer)
                        if not should_continue:
                            running = False
                            break
                        if key_needs_render:
                            needs_render = True
                    except Empty:
                        break

                if not running:
                    break

                # Render immediately if input changed the view
                if needs_render:
                    render_frame()

                # Update metrics once per second
                if current_time - last_update >= UPDATE_INTERVAL:
                    metrics.update()
                    stats_ready = True
                    render_frame()
                    last_update = current_time

                # Small sleep to prevent CPU spinning while remaining responsive
                time.sleep(0.01)  # 100 loops/sec for very responsive input

    except KeyboardInterrupt:
        pass
    finally:
        # Stop input thread
        if input_thread is not None:
            input_thread.stop()
            input_thread.join(timeout=0.5)

        if on_quit:
            on_quit()
