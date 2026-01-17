"""
Tests for the terminals module.

Tests cover:
- Terminal base classes and protocols
- MockTerminal implementation
- Key events
- Mouse events
- Terminal context manager
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from terminals.base import (
    Terminal,
    KeyEvent,
    KeyType,
    MouseEvent,
    MouseButton,
    MouseEventType,
    InputHandler,
    OutputHandler,
    CursorController,
    ScreenController,
    ModeController,
    MouseController,
)


class TestKeyEvent:
    """Tests for KeyEvent class."""

    def test_character_event(self):
        """Test creating a character key event."""
        key = KeyEvent.character('a')
        assert key.key_type == KeyType.CHARACTER
        assert key.value == 'a'

    def test_arrow_event(self):
        """Test creating an arrow key event."""
        key = KeyEvent.arrow('up')
        assert key.key_type == KeyType.ARROW
        assert key.value == 'up'

    def test_special_event(self):
        """Test creating a special key event."""
        key = KeyEvent.special('ctrl-c')
        assert key.key_type == KeyType.SPECIAL
        assert key.value == 'ctrl-c'

    def test_is_quit_q_lowercase(self):
        """Test that 'q' is a quit key."""
        key = KeyEvent.character('q')
        assert key.is_quit is True

    def test_is_quit_q_uppercase(self):
        """Test that 'Q' is a quit key."""
        key = KeyEvent.character('Q')
        assert key.is_quit is True

    def test_is_quit_ctrl_c(self):
        """Test that Ctrl-C is a quit key."""
        key = KeyEvent.special('ctrl-c')
        assert key.is_quit is True

    def test_is_quit_other(self):
        """Test that other keys are not quit keys."""
        key = KeyEvent.character('x')
        assert key.is_quit is False


class TestMouseEvent:
    """Tests for MouseEvent class."""

    def test_press_event(self):
        """Test creating a mouse press event."""
        event = MouseEvent.press(MouseButton.LEFT, 10, 20)
        assert event.event_type == MouseEventType.PRESS
        assert event.button == MouseButton.LEFT
        assert event.x == 10
        assert event.y == 20

    def test_release_event(self):
        """Test creating a mouse release event."""
        event = MouseEvent.release(15, 25)
        assert event.event_type == MouseEventType.RELEASE
        assert event.button == MouseButton.RELEASE
        assert event.x == 15
        assert event.y == 25

    def test_move_event(self):
        """Test creating a mouse move event."""
        event = MouseEvent.move(5, 10)
        assert event.event_type == MouseEventType.MOVE
        assert event.x == 5
        assert event.y == 10


class TestMockTerminal:
    """Tests for MockTerminal from conftest."""

    def test_mock_terminal_raw_mode(self, mock_terminal):
        """Test mock terminal raw mode."""
        assert mock_terminal.is_raw is False
        mock_terminal.enter_raw_mode()
        assert mock_terminal.is_raw is True
        mock_terminal.exit_raw_mode()
        assert mock_terminal.is_raw is False

    def test_mock_terminal_mouse(self, mock_terminal):
        """Test mock terminal mouse tracking."""
        assert mock_terminal.mouse_enabled is False
        mock_terminal.enable_mouse()
        assert mock_terminal.mouse_enabled is True
        mock_terminal.disable_mouse()
        assert mock_terminal.mouse_enabled is False

    def test_mock_terminal_cursor(self, mock_terminal):
        """Test mock terminal cursor control."""
        assert mock_terminal.cursor_hidden is False
        mock_terminal.hide_cursor()
        assert mock_terminal.cursor_hidden is True
        mock_terminal.show_cursor()
        assert mock_terminal.cursor_hidden is False

    def test_mock_terminal_write(self, mock_terminal):
        """Test mock terminal write."""
        mock_terminal.write("Hello")
        mock_terminal.write("World")
        assert mock_terminal.written_data == ["Hello", "World"]

    def test_mock_terminal_read_key(self, mock_terminal):
        """Test mock terminal read key."""
        mock_terminal.add_key(KeyEvent.character('a'))
        key = mock_terminal.read_key()
        assert key.value == 'a'

    def test_mock_terminal_read_mouse(self, mock_terminal):
        """Test mock terminal read mouse event."""
        mock_terminal.add_click(10, 20)
        event = mock_terminal.read_input()
        assert isinstance(event, MouseEvent)
        assert event.x == 10
        assert event.y == 20

    def test_mock_terminal_context_manager(self, mock_terminal):
        """Test mock terminal context manager."""
        with mock_terminal:
            assert mock_terminal.is_raw is True
            assert mock_terminal.cursor_hidden is True
            # Mouse is no longer enabled by default (keyboard-only navigation)

        assert mock_terminal.is_raw is False
        assert mock_terminal.cursor_hidden is False


class TestProtocols:
    """Tests for protocol compliance."""

    def test_input_handler_protocol(self, mock_terminal):
        """Test InputHandler protocol."""
        assert isinstance(mock_terminal, InputHandler)

    def test_output_handler_protocol(self, mock_terminal):
        """Test OutputHandler protocol."""
        assert isinstance(mock_terminal, OutputHandler)

    def test_cursor_controller_protocol(self, mock_terminal):
        """Test CursorController protocol."""
        assert isinstance(mock_terminal, CursorController)

    def test_screen_controller_protocol(self, mock_terminal):
        """Test ScreenController protocol."""
        assert isinstance(mock_terminal, ScreenController)

    def test_mode_controller_protocol(self, mock_terminal):
        """Test ModeController protocol."""
        assert isinstance(mock_terminal, ModeController)

    def test_mouse_controller_protocol(self, mock_terminal):
        """Test MouseController protocol."""
        assert isinstance(mock_terminal, MouseController)
