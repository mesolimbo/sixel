"""
Tests for the terminals module.

Tests cover:
- KeyEvent creation and properties
- KeyType enum
- Terminal factory function
- Terminal registry
- Mock terminal behavior
"""

import pytest
import sys
from unittest.mock import patch, MagicMock

from terminals import (
    create_terminal,
    register_terminal,
    TERMINAL_REGISTRY,
    Terminal,
    KeyEvent,
    KeyType,
)
from terminals.base import (
    InputHandler,
    OutputHandler,
    CursorController,
    ScreenController,
    ModeController,
)


class TestKeyType:
    """Tests for the KeyType enum."""

    def test_key_type_values(self):
        """Test that KeyType has expected values."""
        assert KeyType.CHARACTER.value == "character"
        assert KeyType.ARROW.value == "arrow"
        assert KeyType.SPECIAL.value == "special"

    def test_key_type_count(self):
        """Test that KeyType has exactly 3 types."""
        assert len(KeyType) == 3


class TestKeyEvent:
    """Tests for the KeyEvent dataclass."""

    def test_character_factory(self):
        """Test KeyEvent.character factory method."""
        event = KeyEvent.character('a')
        assert event.key_type == KeyType.CHARACTER
        assert event.value == 'a'

    def test_arrow_factory(self):
        """Test KeyEvent.arrow factory method."""
        event = KeyEvent.arrow('up')
        assert event.key_type == KeyType.ARROW
        assert event.value == 'up'

    def test_special_factory(self):
        """Test KeyEvent.special factory method."""
        event = KeyEvent.special('ctrl-c')
        assert event.key_type == KeyType.SPECIAL
        assert event.value == 'ctrl-c'

    def test_is_quit_lowercase_q(self):
        """Test is_quit with lowercase 'q'."""
        event = KeyEvent.character('q')
        assert event.is_quit is True

    def test_is_quit_uppercase_Q(self):
        """Test is_quit with uppercase 'Q'."""
        event = KeyEvent.character('Q')
        assert event.is_quit is True

    def test_is_quit_ctrl_c(self):
        """Test is_quit with Ctrl-C."""
        event = KeyEvent.special('ctrl-c')
        assert event.is_quit is True

    def test_is_quit_other_character(self):
        """Test is_quit with non-quit characters."""
        event = KeyEvent.character('a')
        assert event.is_quit is False

    def test_is_quit_other_special(self):
        """Test is_quit with non-quit special keys."""
        event = KeyEvent.special('escape')
        assert event.is_quit is False

    def test_is_quit_arrow(self):
        """Test is_quit with arrow keys."""
        event = KeyEvent.arrow('up')
        assert event.is_quit is False

    def test_key_event_frozen(self):
        """Test that KeyEvent is immutable (frozen dataclass)."""
        event = KeyEvent.character('a')
        with pytest.raises(Exception):  # FrozenInstanceError
            event.value = 'b'

    def test_key_event_equality(self):
        """Test KeyEvent equality comparison."""
        event1 = KeyEvent.character('a')
        event2 = KeyEvent.character('a')
        event3 = KeyEvent.character('b')
        assert event1 == event2
        assert event1 != event3

    def test_key_event_hashable(self):
        """Test that KeyEvent is hashable (can be used in sets)."""
        event = KeyEvent.character('a')
        event_set = {event}
        assert event in event_set


class TestTerminalRegistry:
    """Tests for terminal registry functionality."""

    def test_registry_not_empty(self):
        """Test that registry is populated on import."""
        assert len(TERMINAL_REGISTRY) > 0

    def test_registry_has_platform_entries(self):
        """Test that registry has expected platform entries."""
        # Should have at least unix or windows
        if sys.platform == 'win32':
            assert 'windows' in TERMINAL_REGISTRY
        else:
            assert 'unix' in TERMINAL_REGISTRY


class TestCreateTerminal:
    """Tests for the create_terminal factory function."""

    def test_create_terminal_auto_detect(self):
        """Test creating terminal with auto-detection."""
        terminal = create_terminal()
        assert terminal is not None
        assert isinstance(terminal, Terminal)

    def test_create_terminal_explicit_platform(self):
        """Test creating terminal with explicit platform."""
        if sys.platform == 'win32':
            terminal = create_terminal('windows')
        else:
            terminal = create_terminal('unix')
        assert terminal is not None

    def test_create_terminal_invalid_platform(self):
        """Test creating terminal with invalid platform."""
        with pytest.raises(RuntimeError) as exc_info:
            create_terminal('nonexistent')
        assert 'No terminal implementation' in str(exc_info.value)


class TestRegisterTerminal:
    """Tests for custom terminal registration."""

    def test_register_custom_terminal(self, mock_terminal):
        """Test registering a custom terminal class."""
        # Get the MockTerminal class from the fixture's type
        MockTerminal = type(mock_terminal)

        # Register mock terminal
        register_terminal('mock_test', MockTerminal)
        assert 'mock_test' in TERMINAL_REGISTRY

        # Create instance
        terminal = create_terminal('mock_test')
        assert isinstance(terminal, MockTerminal)

        # Cleanup
        del TERMINAL_REGISTRY['mock_test']


class TestMockTerminal:
    """Tests for the MockTerminal test helper."""

    def test_mock_terminal_read_key_empty(self, mock_terminal):
        """Test reading from empty key queue."""
        assert mock_terminal.read_key() is None

    def test_mock_terminal_add_and_read_key(self, mock_terminal):
        """Test adding and reading keys."""
        key = KeyEvent.character('a')
        mock_terminal.add_key(key)
        assert mock_terminal.read_key() == key
        assert mock_terminal.read_key() is None

    def test_mock_terminal_write(self, mock_terminal):
        """Test writing to mock terminal."""
        mock_terminal.write("test data")
        assert "test data" in mock_terminal.written_data

    def test_mock_terminal_cursor_operations(self, mock_terminal):
        """Test cursor operations."""
        mock_terminal.hide_cursor()
        assert mock_terminal.cursor_hidden is True

        mock_terminal.show_cursor()
        assert mock_terminal.cursor_hidden is False

        mock_terminal.move_cursor(5, 10)
        assert mock_terminal.cursor_pos == (5, 10)

        mock_terminal.move_cursor_home()
        assert mock_terminal.cursor_pos == (1, 1)

    def test_mock_terminal_screen_operations(self, mock_terminal):
        """Test screen operations."""
        mock_terminal.enter_alternate_screen()
        assert mock_terminal.in_alternate_screen is True

        mock_terminal.exit_alternate_screen()
        assert mock_terminal.in_alternate_screen is False

        mock_terminal.clear_screen()
        assert "<CLEAR>" in mock_terminal.written_data

    def test_mock_terminal_raw_mode(self, mock_terminal):
        """Test raw mode operations."""
        assert mock_terminal.is_raw is False

        mock_terminal.enter_raw_mode()
        assert mock_terminal.is_raw is True

        mock_terminal.exit_raw_mode()
        assert mock_terminal.is_raw is False

    def test_mock_terminal_get_size(self, mock_terminal):
        """Test getting terminal size."""
        cols, rows = mock_terminal.get_size()
        assert cols == 80
        assert rows == 24

        mock_terminal.set_size(120, 40)
        cols, rows = mock_terminal.get_size()
        assert cols == 120
        assert rows == 40

    def test_mock_terminal_context_manager(self, mock_terminal):
        """Test mock terminal as context manager."""
        with mock_terminal:
            assert mock_terminal.is_raw is True
            assert mock_terminal.in_alternate_screen is True
            assert mock_terminal.cursor_hidden is True

        assert mock_terminal.is_raw is False
        assert mock_terminal.in_alternate_screen is False
        assert mock_terminal.cursor_hidden is False


class TestTerminalContextManager:
    """Tests for Terminal context manager behavior."""

    def test_context_manager_setup(self, mock_terminal):
        """Test that context manager sets up terminal correctly."""
        with mock_terminal as t:
            assert t is mock_terminal
            assert mock_terminal.is_raw
            assert mock_terminal.cursor_hidden
            assert mock_terminal.in_alternate_screen

    def test_context_manager_cleanup(self, mock_terminal):
        """Test that context manager cleans up correctly."""
        with mock_terminal:
            pass

        assert not mock_terminal.is_raw
        assert not mock_terminal.cursor_hidden
        assert not mock_terminal.in_alternate_screen

    def test_context_manager_cleanup_on_exception(self, mock_terminal):
        """Test that context manager cleans up even on exception."""
        try:
            with mock_terminal:
                raise ValueError("test error")
        except ValueError:
            pass

        assert not mock_terminal.is_raw
        assert not mock_terminal.cursor_hidden
        assert not mock_terminal.in_alternate_screen


class TestTerminalWriteAt:
    """Tests for Terminal.write_at convenience method."""

    def test_write_at_moves_and_writes(self, mock_terminal):
        """Test that write_at moves cursor and writes data."""
        mock_terminal.write_at(5, 10, "test")

        assert mock_terminal.cursor_pos == (5, 10)
        assert "test" in mock_terminal.written_data


class TestProtocols:
    """Tests for protocol definitions."""

    def test_input_handler_protocol(self, mock_terminal):
        """Test that MockTerminal satisfies InputHandler protocol."""
        assert isinstance(mock_terminal, InputHandler)

    def test_output_handler_protocol(self, mock_terminal):
        """Test that MockTerminal satisfies OutputHandler protocol."""
        assert isinstance(mock_terminal, OutputHandler)

    def test_cursor_controller_protocol(self, mock_terminal):
        """Test that MockTerminal satisfies CursorController protocol."""
        assert isinstance(mock_terminal, CursorController)

    def test_screen_controller_protocol(self, mock_terminal):
        """Test that MockTerminal satisfies ScreenController protocol."""
        assert isinstance(mock_terminal, ScreenController)

    def test_mode_controller_protocol(self, mock_terminal):
        """Test that MockTerminal satisfies ModeController protocol."""
        assert isinstance(mock_terminal, ModeController)
