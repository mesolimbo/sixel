"""
Tests for the app_loop module.

Tests cover:
- Input processing
- Key event handling
- Mouse event handling
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app_loop import process_input, process_key_event, process_mouse_event
from terminals.base import KeyEvent, MouseEvent, MouseButton
from gui import GUIState, Window, Button, TextInput, Checkbox
from renderer import GUIRenderer


class TestProcessKeyEvent:
    """Tests for keyboard event processing."""

    def test_quit_key_q(self):
        """Test that 'q' key quits."""
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

        # Focus the text input by clicking
        gui.handle_click(50, 40)
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
        ti.focus()
        ti.insert_char('A')
        ti.insert_char('B')
        window.add_component(ti)
        gui.add_window(window)
        gui._focused_component = ti

        key = KeyEvent.special('backspace')
        should_continue, needs_render = process_key_event(key, gui)
        assert ti.text == "A"
        assert needs_render is True


class TestProcessMouseEvent:
    """Tests for mouse event processing."""

    def test_click_on_button(self):
        """Test clicking on a button."""
        gui = GUIState()
        renderer = GUIRenderer(width=200, height=100)

        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        btn = Button(10, 30, 80, 25, "CLICK")
        window.add_component(btn)
        gui.add_window(window)

        # Simulate click (coordinates in character cells)
        event = MouseEvent.press(MouseButton.LEFT, 3, 2)  # Should hit button area
        should_continue, needs_render = process_mouse_event(event, gui, renderer)

        assert should_continue is True
        assert needs_render is True

    def test_click_on_checkbox(self):
        """Test clicking on a checkbox."""
        gui = GUIState()
        renderer = GUIRenderer(width=200, height=100)

        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        cb = Checkbox(10, 30, 100, 24, "CHECK", checked=False)
        window.add_component(cb)
        gui.add_window(window)

        # Click within the checkbox bounds
        event = MouseEvent.press(MouseButton.LEFT, 2, 2)
        should_continue, needs_render = process_mouse_event(event, gui, renderer)

        assert should_continue is True
        assert needs_render is True


class TestProcessInput:
    """Tests for combined input processing."""

    def test_process_none_input(self):
        """Test processing None input."""
        gui = GUIState()
        renderer = GUIRenderer()
        should_continue, needs_render = process_input(None, gui, renderer)
        assert should_continue is True
        assert needs_render is False

    def test_process_key_input(self):
        """Test processing key input."""
        gui = GUIState()
        renderer = GUIRenderer()
        key = KeyEvent.character('x')
        should_continue, needs_render = process_input(key, gui, renderer)
        assert should_continue is True

    def test_process_mouse_input(self):
        """Test processing mouse input."""
        gui = GUIState()
        renderer = GUIRenderer()

        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        gui.add_window(window)

        event = MouseEvent.press(MouseButton.LEFT, 5, 5)
        should_continue, needs_render = process_input(event, gui, renderer)
        assert should_continue is True
        assert needs_render is True
