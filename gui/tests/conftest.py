"""
Pytest fixtures for GUI demo tests.
"""

import sys
import pytest
from pathlib import Path
from typing import Optional, Tuple, Union

# Add the gui package to the path
gui_dir = Path(__file__).parent.parent
sys.path.insert(0, str(gui_dir))

from terminals.base import (
    Terminal, KeyEvent, KeyType, MouseEvent, MouseButton,
    MouseEventType, InputEvent
)
from renderer import GUIRenderer
from gui import (
    GUIState,
    Window,
    Component,
    ComponentState,
    Button,
    Checkbox,
    RadioButton,
    RadioGroup,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    Bounds,
)


class MockTerminal(Terminal):
    """Mock terminal for testing app loop and input processing."""

    def __init__(self):
        self.written_data = []
        self.event_queue = []
        self.cursor_pos = (1, 1)
        self.cursor_hidden = False
        self.in_alternate_screen = False
        self._is_raw = False
        self._mouse_enabled = False
        self._size = (120, 40)

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        event = self.read_input(timeout)
        if isinstance(event, KeyEvent):
            return event
        return None

    def read_input(self, timeout: float = 0.0) -> Optional[InputEvent]:
        if self.event_queue:
            return self.event_queue.pop(0)
        return None

    def add_event(self, event: InputEvent) -> None:
        """Add an event to the input queue for testing."""
        self.event_queue.append(event)

    def add_key(self, key: KeyEvent) -> None:
        """Add a key event to the input queue."""
        self.add_event(key)

    def add_click(self, x: int, y: int, button: MouseButton = MouseButton.LEFT) -> None:
        """Add a mouse click event."""
        self.add_event(MouseEvent.press(button, x, y))

    def write(self, data: str) -> None:
        self.written_data.append(data)

    def flush(self) -> None:
        pass

    def get_size(self) -> Tuple[int, int]:
        return self._size

    def set_size(self, cols: int, rows: int) -> None:
        """Set terminal size for testing."""
        self._size = (cols, rows)

    def hide_cursor(self) -> None:
        self.cursor_hidden = True

    def show_cursor(self) -> None:
        self.cursor_hidden = False

    def move_cursor(self, row: int, col: int) -> None:
        self.cursor_pos = (row, col)

    def move_cursor_home(self) -> None:
        self.cursor_pos = (1, 1)

    def clear_screen(self) -> None:
        self.written_data.append("<CLEAR>")

    def enter_alternate_screen(self) -> None:
        self.in_alternate_screen = True

    def exit_alternate_screen(self) -> None:
        self.in_alternate_screen = False

    def enter_raw_mode(self) -> None:
        self._is_raw = True

    def exit_raw_mode(self) -> None:
        self._is_raw = False

    def enable_mouse(self) -> None:
        self._mouse_enabled = True

    def disable_mouse(self) -> None:
        self._mouse_enabled = False

    @property
    def is_raw(self) -> bool:
        return self._is_raw

    @property
    def mouse_enabled(self) -> bool:
        return self._mouse_enabled


@pytest.fixture
def mock_terminal() -> MockTerminal:
    """Create a mock terminal for testing."""
    return MockTerminal()


@pytest.fixture
def renderer() -> GUIRenderer:
    """Create a default GUI renderer."""
    return GUIRenderer()


@pytest.fixture
def small_renderer() -> GUIRenderer:
    """Create a smaller renderer for testing."""
    return GUIRenderer(width=400, height=200)


@pytest.fixture
def gui_state() -> GUIState:
    """Create an empty GUI state."""
    return GUIState()


@pytest.fixture
def sample_window() -> Window:
    """Create a sample window with basic dimensions."""
    return Window(
        title="TEST WINDOW",
        x=10, y=10,
        width=200, height=150
    )


@pytest.fixture
def sample_button() -> Button:
    """Create a sample button."""
    return Button(
        x=20, y=40,
        width=100, height=30,
        label="TEST"
    )


@pytest.fixture
def sample_checkbox() -> Checkbox:
    """Create a sample checkbox."""
    return Checkbox(
        x=20, y=40,
        width=120, height=24,
        label="CHECK ME"
    )


@pytest.fixture
def sample_slider() -> Slider:
    """Create a sample slider."""
    return Slider(
        x=20, y=40,
        width=100, height=20,
        min_value=0, max_value=100,
        value=50
    )


@pytest.fixture
def sample_text_input() -> TextInput:
    """Create a sample text input."""
    return TextInput(
        x=20, y=40,
        width=150, height=28,
        placeholder="Enter text..."
    )


@pytest.fixture
def sample_progress_bar() -> ProgressBar:
    """Create a sample progress bar."""
    return ProgressBar(
        x=20, y=40,
        width=150, height=24,
        value=50
    )


@pytest.fixture
def sample_listbox() -> ListBox:
    """Create a sample list box."""
    return ListBox(
        x=20, y=40,
        width=120, height=100,
        items=["Item 1", "Item 2", "Item 3"]
    )


@pytest.fixture
def populated_gui() -> GUIState:
    """Create a GUI state with a window and components."""
    gui = GUIState()

    window = Window(
        title="TEST",
        x=0, y=0,
        width=200, height=200
    )

    window.add_component(Button(
        x=10, y=30,
        width=80, height=25,
        label="BTN"
    ))

    window.add_component(Checkbox(
        x=10, y=60,
        width=100, height=24,
        label="CHECK"
    ))

    gui.add_window(window)
    return gui
