"""
Application loop module for GUI demo.

Handles the main loop, input processing (keyboard and mouse),
and coordination between the terminal, renderer, and GUI state.
"""

import time
import threading
from queue import Queue, Empty
from typing import Optional, Callable, Union

from gui import GUIState, ProgressBar
from renderer import GUIRenderer
from terminals import Terminal, KeyEvent, MouseEvent, InputEvent
from terminals.base import MouseButton, MouseEventType


# ANSI escape codes
SAVE_CURSOR = "\x1b[s"
RESTORE_CURSOR = "\x1b[u"
MOVE_UP = "\x1b[{}A"


class InputThread(threading.Thread):
    """
    Background thread for reading keyboard and mouse input.

    Reads events continuously and puts them in a queue for the main thread.
    """

    def __init__(self, terminal: Terminal, event_queue: Queue):
        super().__init__(daemon=True)
        self.terminal = terminal
        self.event_queue = event_queue
        self.running = True

    def run(self) -> None:
        """Continuously read input events and queue them."""
        while self.running:
            try:
                event = self.terminal.read_input(timeout=0.05)
                if event is not None:
                    self.event_queue.put(event)
            except Exception:
                break

    def stop(self) -> None:
        """Signal the thread to stop."""
        self.running = False


def process_input(
    event: Optional[InputEvent],
    gui_state: GUIState,
    renderer: GUIRenderer
) -> tuple[bool, bool]:
    """
    Process an input event and update application state.

    Args:
        event: The input event to process (or None if no input)
        gui_state: The GUI state to update
        renderer: The renderer (for coordinate translation)

    Returns:
        Tuple of (should_continue, needs_render)
    """
    if event is None:
        return True, False

    # Handle keyboard events
    if isinstance(event, KeyEvent):
        return process_key_event(event, gui_state)

    # Handle mouse events
    if isinstance(event, MouseEvent):
        return process_mouse_event(event, gui_state, renderer)

    return True, False


def process_key_event(event: KeyEvent, gui_state: GUIState) -> tuple[bool, bool]:
    """Process a keyboard event."""
    # Check for quit
    if event.is_quit:
        return False, False

    # Handle regular character input
    if event.key_type.value == 'character':
        if gui_state.handle_key(event.value):
            return True, True

    # Handle special keys
    if event.key_type.value == 'special':
        if event.value == 'backspace':
            if gui_state.handle_special_key('backspace'):
                return True, True
        elif event.value == 'tab':
            # Could implement tab navigation between components
            pass
        elif event.value == 'enter':
            # Could trigger button clicks or form submission
            pass

    # Handle arrow keys
    if event.key_type.value == 'arrow':
        if gui_state.handle_special_key(event.value):
            return True, True

    return True, False


def process_mouse_event(
    event: MouseEvent,
    gui_state: GUIState,
    renderer: GUIRenderer
) -> tuple[bool, bool]:
    """
    Process a mouse event.

    Note: Mouse coordinates from the terminal are in character cells.
    We need to convert to pixel coordinates for the sixel graphics.
    Each character cell is approximately 6 pixels wide and 6 pixels tall
    (sixel uses 6 vertical pixels per row).
    """
    # Convert character cell coordinates to approximate pixel coordinates
    # These values may need adjustment based on terminal font
    cell_width = 10  # Approximate pixels per character cell width
    cell_height = 20  # Approximate pixels per character cell height

    # Account for the reserved space at the top (see run_app_loop)
    px = event.x * cell_width
    py = event.y * cell_height

    if event.event_type == MouseEventType.PRESS:
        if event.button == MouseButton.LEFT:
            component = gui_state.handle_click(px, py)
            return True, True  # Always re-render on click

    return True, False


def run_app_loop(
    gui_state: GUIState,
    renderer: GUIRenderer,
    terminal: Terminal,
    on_quit: Optional[Callable[[], None]] = None,
    animation_callback: Optional[Callable[[float], None]] = None
) -> None:
    """
    Run the main application loop.

    Uses a separate thread for input handling to ensure responsiveness.
    Supports both keyboard and mouse input.

    Args:
        gui_state: The GUI state to manage
        renderer: The GUI renderer
        terminal: Terminal instance for I/O
        on_quit: Optional callback when app exits
        animation_callback: Optional callback for animations (called with delta time)
    """
    event_queue: Queue[InputEvent] = Queue()
    input_thread = None

    # Calculate sixel rows
    sixel_rows = (renderer.height + 5) // 6

    def render_frame():
        """Helper to render and display a frame."""
        frame = renderer.render_frame(gui_state)
        terminal.write(RESTORE_CURSOR)
        terminal.write("\n")
        terminal.write(frame)
        terminal.flush()

    try:
        with terminal:
            # Reserve space for rendering
            _, term_height = terminal.get_size()
            rows_to_reserve = min(sixel_rows + 1, max(8, term_height // 3))
            terminal.write("\n" * rows_to_reserve)
            terminal.write(MOVE_UP.format(rows_to_reserve))
            terminal.write(SAVE_CURSOR)
            terminal.flush()

            # Start input thread
            input_thread = InputThread(terminal, event_queue)
            input_thread.start()

            # Initial render
            render_frame()

            last_time = time.time()
            running = True

            while running:
                current_time = time.time()
                delta_time = current_time - last_time
                needs_render = False

                # Process all queued input events
                while True:
                    try:
                        event = event_queue.get_nowait()
                        should_continue, event_needs_render = process_input(
                            event, gui_state, renderer
                        )
                        if not should_continue:
                            running = False
                            break
                        if event_needs_render:
                            needs_render = True
                    except Empty:
                        break

                if not running:
                    break

                # Call animation callback if provided
                if animation_callback:
                    animation_callback(delta_time)
                    needs_render = True

                # Render if needed
                if needs_render:
                    render_frame()
                    last_time = current_time

                # Small sleep to prevent CPU spinning
                time.sleep(0.016)  # ~60 FPS max

    except KeyboardInterrupt:
        pass
    finally:
        if input_thread is not None:
            input_thread.stop()
            input_thread.join(timeout=0.5)

        if on_quit:
            on_quit()
