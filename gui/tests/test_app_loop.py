"""
Tests for the app_loop module.

Tests cover:
- Input processing
- Key event handling
- Keyboard navigation
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app_loop import process_input, process_key_event
from terminals.base import KeyEvent
from gui import GUIState, Window, Button, TextInput, Checkbox, Slider


class TestProcessKeyEvent:
    """Tests for keyboard event processing."""

    def test_quit_key_q(self):
        """Test that 'q' key quits when not in text input."""
        gui = GUIState()
        key = KeyEvent.character('q')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is False

    def test_quit_key_ctrl_c(self):
        """Test that Ctrl-C quits."""
        gui = GUIState()
        key = KeyEvent.special('ctrl-c')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is False

    def test_q_key_in_text_input_does_not_quit(self):
        """Test that 'q' key does not quit when in text input."""
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        ti = TextInput(10, 30, 120, 28)
        window.add_component(ti)
        gui.add_window(window)

        # Focus the text input
        gui.focus_next()
        assert ti.has_focus is True

        # Type 'q' - should NOT quit
        key = KeyEvent.character('q')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is True
        assert ti.text == "q"

    def test_character_input_no_focus(self):
        """Test character input with no focused component."""
        gui = GUIState()
        key = KeyEvent.character('a')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is True
        assert needs_render is False

    def test_character_input_with_focus(self):
        """Test character input to focused text input."""
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        ti = TextInput(10, 30, 120, 28)
        window.add_component(ti)
        gui.add_window(window)

        # Focus the text input
        gui.focus_next()
        assert ti.has_focus is True

        # Type a character
        key = KeyEvent.character('A')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is True
        assert needs_render is True
        assert ti.text == "A"

    def test_backspace_key(self):
        """Test backspace key handling."""
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        ti = TextInput(10, 30, 120, 28)
        window.add_component(ti)
        gui.add_window(window)

        # Focus and type
        gui.focus_next()
        ti.insert_char('A')
        ti.insert_char('B')

        key = KeyEvent.special('backspace')
        should_continue, needs_render = process_key_event(key, gui)
        assert ti.text == "A"
        assert needs_render is True

    def test_tab_navigation(self):
        """Test tab key navigates between windows."""
        gui = GUIState()

        window1 = Window(title="WIN1", x=0, y=0, width=100, height=100)
        window1.add_component(Button(10, 30, 80, 25, "BTN1"))
        gui.add_window(window1)

        window2 = Window(title="WIN2", x=110, y=0, width=100, height=100)
        window2.add_component(Button(120, 30, 80, 25, "BTN2"))
        gui.add_window(window2)

        # Initial state - no focus
        assert gui.get_focused_window() is None

        # First tab - focus first window
        key = KeyEvent.special('tab')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is True
        assert needs_render is True
        assert gui.get_focused_window() is window1

        # Second tab - focus second window
        should_continue, needs_render = process_key_event(key, gui)
        assert gui.get_focused_window() is window2

        # Third tab - wrap to first window
        should_continue, needs_render = process_key_event(key, gui)
        assert gui.get_focused_window() is window1

    def test_space_activates_button(self):
        """Test space key toggles focused button."""
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        btn = Button(10, 30, 80, 25, "CLICK")
        window.add_component(btn)
        gui.add_window(window)

        # Focus the button
        gui.focus_next()

        # Press space
        key = KeyEvent.character(' ')
        should_continue, needs_render = process_key_event(key, gui)
        assert should_continue is True
        assert needs_render is True
        assert btn.toggled is True

    def test_space_toggles_checkbox(self):
        """Test space key toggles focused checkbox."""
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        cb = Checkbox(10, 30, 100, 24, "CHECK", checked=False)
        window.add_component(cb)
        gui.add_window(window)

        # Focus the checkbox
        gui.focus_next()

        # Press space to check
        key = KeyEvent.character(' ')
        should_continue, needs_render = process_key_event(key, gui)
        assert cb.checked is True

        # Press space to uncheck
        should_continue, needs_render = process_key_event(key, gui)
        assert cb.checked is False

    def test_arrow_keys_adjust_slider(self):
        """Test arrow keys adjust slider value."""
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        slider = Slider(10, 30, 100, 20, min_value=0, max_value=100, value=50)
        window.add_component(slider)
        gui.add_window(window)

        # Focus the slider
        gui.focus_next()

        # Press right arrow
        key = KeyEvent.arrow('right')
        should_continue, needs_render = process_key_event(key, gui)
        assert slider.value > 50

        # Press left arrow
        key = KeyEvent.arrow('left')
        should_continue, needs_render = process_key_event(key, gui)
        # Value should decrease


class TestProcessInput:
    """Tests for combined input processing."""

    def test_process_none_input(self):
        """Test processing None input."""
        gui = GUIState()
        should_continue, needs_render = process_input(None, gui)
        assert should_continue is True
        assert needs_render is False

    def test_process_key_input(self):
        """Test processing key input."""
        gui = GUIState()
        key = KeyEvent.character('x')
        should_continue, needs_render = process_input(key, gui)
        assert should_continue is True
