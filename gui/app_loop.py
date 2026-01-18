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

import sys
import time
import threading
from queue import Queue, Empty
from typing import Optional, Callable

from gui import GUIState, TextInput
from renderer import GUIRenderer
from terminals import Terminal, KeyEvent, InputEvent

# Platform detection for render timing
IS_MACOS = sys.platform == 'darwin'

# ANSI escape codes for cursor control
SAVE_CURSOR = "\x1b[s"
RESTORE_CURSOR = "\x1b[u"
MOVE_UP = "\x1b[{}A"    # Move cursor up N lines
CURSOR_HOME = "\x1b[H"  # Move cursor to top-left


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


class RenderThread(threading.Thread):  # pragma: no cover
    """
    Background thread for rendering frames asynchronously.

    Renders frames without blocking the main input loop, which is critical
    for responsiveness on macOS where rendering can take 100-200ms.
    """

    def __init__(self, renderer: GUIRenderer, gui_state: GUIState):
        super().__init__(daemon=True)
        self.renderer = renderer
        self.gui_state = gui_state
        self.running = True
        self.render_requested = threading.Event()
        self.frame_ready = threading.Event()
        self.current_frame: Optional[str] = None
        self.render_lock = threading.Lock()
        self._render_id = 0  # Track which render request we're on

    def request_render(self) -> int:
        """Request a new frame render. Returns render ID."""
        with self.render_lock:
            self._render_id += 1
            render_id = self._render_id
        self.frame_ready.clear()
        self.render_requested.set()
        return render_id

    def get_frame(self) -> Optional[str]:
        """Get the most recently rendered frame (non-blocking)."""
        with self.render_lock:
            return self.current_frame

    def wait_for_frame(self, timeout: float = 0.0) -> Optional[str]:
        """Wait for a frame to be ready, with timeout."""
        if self.frame_ready.wait(timeout):
            with self.render_lock:
                return self.current_frame
        return None

    def run(self) -> None:
        """Continuously render frames when requested."""
        while self.running:
            # Wait for a render request
            if self.render_requested.wait(timeout=0.1):
                self.render_requested.clear()

                if not self.running:
                    break

                # Render the frame
                try:
                    frame = self.renderer.render_frame(self.gui_state)
                    with self.render_lock:
                        self.current_frame = frame
                    self.frame_ready.set()
                except Exception:
                    pass

    def stop(self) -> None:
        """Signal the thread to stop."""
        self.running = False
        self.render_requested.set()  # Wake up the thread


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
    render_thread: Optional[RenderThread] = None

    # Calculate how many terminal rows the sixel output occupies
    # Sixel uses 6 pixels per character row
    sixel_rows = (renderer.height + 5) // 6

    # Will be set based on whether sixel fits in terminal
    use_home_position = False

    def render_frame():
        """Helper to render and display a frame."""
        frame = renderer.render_frame(gui_state)
        if use_home_position:
            # Large sixel mode: always go to top-left
            terminal.write(CURSOR_HOME)
        else:
            # Normal mode: restore to saved position
            terminal.write(RESTORE_CURSOR)
            terminal.write("\n")  # Top margin to avoid clipping command line
        terminal.write(frame)
        terminal.flush()

    try:
        with terminal:
            # Get terminal height to calculate how much space to reserve
            _, term_height = terminal.get_size()

            if sixel_rows >= term_height:
                # Sixel is larger than terminal - use home position mode
                # This ensures each frame starts at the same screen position
                use_home_position = True
                # Scroll to clear the screen first
                terminal.write("\n" * term_height)
                terminal.flush()
            else:
                # Sixel fits in terminal - use reserve-save-restore pattern
                rows_to_reserve = min(sixel_rows + 1, max(8, term_height // 3))
                terminal.write("\n" * rows_to_reserve)
                terminal.write(MOVE_UP.format(rows_to_reserve))
                terminal.write(SAVE_CURSOR)
                terminal.flush()

            # Focus the first focusable component
            gui_state.focus_next()

            # Start input thread
            input_thread = InputThread(terminal, event_queue)
            input_thread.start()

            # On macOS, use async rendering to keep input responsive
            # On other platforms, use synchronous rendering (faster overall)
            if IS_MACOS:
                render_thread = RenderThread(renderer, gui_state)
                render_thread.start()

            # Initial render (synchronous for first frame)
            render_frame()

            last_time = time.time()
            last_render_time = time.time()
            last_display_time = time.time()
            running = True

            # Platform-specific timing
            # macOS: async rendering, just throttle display updates
            # Others: sync rendering with frame rate limit
            min_render_interval = 0.05 if IS_MACOS else 0.04  # Request rate
            min_display_interval = 0.033 if IS_MACOS else 0.04  # Display rate (30 FPS max)
            cursor_blink_interval = 0.3 if IS_MACOS else 0.15
            input_check_interval = 0.008  # Fast input checking on all platforms

            # Track if we have a pending render
            render_pending = False
            last_frame_hash = 0

            while running:
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time

                # Process all queued input events immediately (responsive input)
                input_processed = False
                while True:
                    try:
                        event = event_queue.get_nowait()
                        should_continue, _ = process_input(event, gui_state)
                        input_processed = True
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

                # Check if a text input is focused (need periodic redraws for cursor blink)
                focused = gui_state.get_focused_component()
                needs_cursor_blink = isinstance(focused, TextInput) and focused.has_focus

                # Compute state hash to detect changes
                state_hash = hash((
                    gui_state._focused_window_index,
                    tuple(gui_state._component_index_per_window.items()),
                    tuple(w.active for w in gui_state.windows),
                    needs_cursor_blink,
                    int(current_time / 0.6) if needs_cursor_blink else 0,
                ))

                time_since_render = current_time - last_render_time
                time_since_display = current_time - last_display_time

                # Determine if we need to render
                state_changed = state_hash != last_frame_hash
                should_request_render = (
                    (state_changed and time_since_render >= min_render_interval) or
                    (needs_cursor_blink and time_since_render >= cursor_blink_interval) or
                    input_processed
                )

                if IS_MACOS and render_thread:
                    # Async rendering mode for macOS
                    if should_request_render and not render_pending:
                        render_thread.request_render()
                        render_pending = True
                        last_render_time = current_time
                        last_frame_hash = state_hash

                    # Check if a new frame is ready to display
                    if render_pending and time_since_display >= min_display_interval:
                        frame = render_thread.get_frame()
                        if frame:
                            if use_home_position:
                                terminal.write(CURSOR_HOME)
                            else:
                                terminal.write(RESTORE_CURSOR)
                                terminal.write("\n")
                            terminal.write(frame)
                            terminal.flush()
                            last_display_time = current_time
                            render_pending = False
                            gui_state.clear_dirty()
                else:
                    # Synchronous rendering for other platforms
                    if should_request_render and time_since_display >= min_display_interval:
                        frame = renderer.render_frame(gui_state)

                        if use_home_position:
                            terminal.write(CURSOR_HOME)
                        else:
                            terminal.write(RESTORE_CURSOR)
                            terminal.write("\n")
                        terminal.write(frame)
                        terminal.flush()

                        gui_state.clear_dirty()
                        last_render_time = current_time
                        last_display_time = current_time
                        last_frame_hash = state_hash

                # Small sleep to prevent CPU spinning
                time.sleep(input_check_interval)

    except KeyboardInterrupt:
        pass
    finally:
        if input_thread is not None:
            input_thread.stop()
            input_thread.join(timeout=0.5)

        if render_thread is not None:
            render_thread.stop()
            render_thread.join(timeout=0.5)

        if on_quit:
            on_quit()
