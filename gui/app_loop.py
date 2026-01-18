"""
Application loop module for GUI demo.

Handles the main loop, keyboard input processing,
and coordination between the terminal, renderer, and GUI state.

Navigation:
- Tab: Move focus to next component
- Shift+Tab (or Backtab): Move focus to previous component
- Arrow keys: Interact with focused component (sliders, radio buttons, lists)
- Space/Enter: Activate focused component (buttons, checkboxes)
- Text input: Type in focused text fields
- q: Quit (when not in a text field)
"""

import time
import threading
from queue import Queue, Empty
from typing import Optional, Callable

from gui import GUIState, TextInput
from renderer import GUIRenderer
from terminals import Terminal, KeyEvent, InputEvent


# ANSI escape codes
SAVE_CURSOR = "\x1b[s"
RESTORE_CURSOR = "\x1b[u"
MOVE_UP = "\x1b[{}A"


class InputThread(threading.Thread):  # pragma: no cover
    """
    Background thread for reading keyboard input.

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
    gui_state: GUIState
) -> tuple[bool, bool]:
    """
    Process an input event and update application state.

    Args:
        event: The input event to process (or None if no input)
        gui_state: The GUI state to update

    Returns:
        Tuple of (should_continue, needs_render)
    """
    if event is None:
        return True, False

    # Handle keyboard events
    if isinstance(event, KeyEvent):
        return process_key_event(event, gui_state)

    return True, False


def process_key_event(event: KeyEvent, gui_state: GUIState) -> tuple[bool, bool]:
    """
    Process a keyboard event for navigation and interaction.

    Returns:
        Tuple of (should_continue, needs_render)
    """
    focused = gui_state.get_focused_component()

    # Check if focused component is a text input
    is_text_input = isinstance(focused, TextInput) if focused else False

    # Handle special keys
    if event.key_type.value == 'special':
        key = event.value

        # Quit on 'q' or Ctrl-C (but not when in text input)
        if key == 'ctrl-c':
            return False, False

        # Tab navigation
        if key == 'tab':
            gui_state.focus_next()
            return True, True

        # Enter/Space to activate
        if key in ('enter', 'space') and not is_text_input:
            if focused:
                gui_state.activate_focused()
            return True, True

        # Backspace for text input
        if key == 'backspace' and is_text_input:
            if gui_state.handle_special_key('backspace'):
                return True, True

        # Enter in text field moves to next
        if key == 'enter' and is_text_input:
            gui_state.focus_next()
            return True, True

        # Escape to unfocus text input
        if key == 'escape' and is_text_input:
            gui_state.clear_focus()
            return True, True

    # Handle arrow keys
    if event.key_type.value == 'arrow':
        direction = event.value
        if gui_state.handle_special_key(direction):
            return True, True
        return True, False

    # Handle character input
    if event.key_type.value == 'character':
        char = event.value

        # 'q' to quit (but not when in text input)
        if char == 'q' and not is_text_input:
            return False, False

        # Space to activate (but not when in text input)
        if char == ' ' and not is_text_input:
            if focused:
                gui_state.activate_focused()
            return True, True

        # Type in text input
        if is_text_input:
            if gui_state.handle_key(char):
                return True, True

        return True, False

    return True, False


def run_app_loop(  # pragma: no cover
    gui_state: GUIState,
    renderer: GUIRenderer,
    terminal: Terminal,
    on_quit: Optional[Callable[[], None]] = None,
    animation_callback: Optional[Callable[[float], None]] = None
) -> None:
    """
    Run the main application loop.

    Uses a separate thread for input handling to ensure responsiveness.
    Keyboard-only navigation (no mouse).

    Args:
        gui_state: The GUI state to manage
        renderer: The GUI renderer
        terminal: Terminal instance for I/O
        on_quit: Optional callback when app exits
        animation_callback: Optional callback for animations (called with delta time)
    """
    event_queue: Queue[InputEvent] = Queue()
    input_thread = None

    # Calculate sixel rows for spacing
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
            # Ensure we reserve enough rows for the full sixel content
            rows_to_reserve = min(sixel_rows + 2, term_height - 2)
            terminal.write("\n" * rows_to_reserve)
            terminal.write(MOVE_UP.format(rows_to_reserve))
            terminal.write(SAVE_CURSOR)
            terminal.flush()

            # Focus the first focusable component
            gui_state.focus_next()

            # Start input thread
            input_thread = InputThread(terminal, event_queue)
            input_thread.start()

            # Initial render
            render_frame()

            last_time = time.time()
            last_render_time = time.time()
            running = True
            min_render_interval = 0.033  # ~30 FPS max for rendering

            while running:
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time

                # Process all queued input events immediately (responsive input)
                while True:
                    try:
                        event = event_queue.get_nowait()
                        should_continue, _ = process_input(event, gui_state)
                        if not should_continue:
                            running = False
                            break
                    except Empty:
                        break

                if not running:
                    break

                # Call animation callback if provided
                if animation_callback:
                    animation_callback(delta_time)

                # Only render if dirty and enough time has passed
                time_since_render = current_time - last_render_time
                if gui_state.is_dirty() and time_since_render >= min_render_interval:
                    render_frame()
                    gui_state.clear_dirty()
                    last_render_time = current_time

                # Small sleep to prevent CPU spinning
                time.sleep(0.008)  # Check input more frequently

    except KeyboardInterrupt:
        pass
    finally:
        if input_thread is not None:
            input_thread.stop()
            input_thread.join(timeout=0.5)

        if on_quit:
            on_quit()
