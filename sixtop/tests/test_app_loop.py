"""
Tests for the application loop module (app_loop.py).

Tests cover:
- Input processing
- View switching
- Quit handling
- InputThread behavior
- App loop coordination
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from queue import Queue

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_loop import (
    process_input,
    InputThread,
    UPDATE_INTERVAL,
    SAVE_CURSOR,
    RESTORE_CURSOR,
    MOVE_UP,
)
from renderer import MetricsRenderer, MetricView
from terminals.base import KeyEvent, KeyType


class TestProcessInput:
    """Tests for the process_input function."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer for testing."""
        return MetricsRenderer()

    def test_none_input_continues(self, renderer):
        """Test that None input returns continue=True, needs_render=False."""
        should_continue, needs_render = process_input(None, renderer)
        assert should_continue is True
        assert needs_render is False

    def test_quit_key_q_lowercase(self, renderer):
        """Test that 'q' key signals quit."""
        key = KeyEvent.character('q')
        should_continue, needs_render = process_input(key, renderer)
        assert should_continue is False
        assert needs_render is False

    def test_quit_key_Q_uppercase(self, renderer):
        """Test that 'Q' key signals quit."""
        key = KeyEvent.character('Q')
        should_continue, needs_render = process_input(key, renderer)
        assert should_continue is False
        assert needs_render is False

    def test_quit_key_ctrl_c(self, renderer):
        """Test that Ctrl-C signals quit."""
        key = KeyEvent.special('ctrl-c')
        should_continue, needs_render = process_input(key, renderer)
        assert should_continue is False
        assert needs_render is False

    def test_tab_key_t_lowercase(self, renderer):
        """Test that 't' key switches view and triggers render."""
        initial_view = renderer.current_view
        key = KeyEvent.character('t')
        should_continue, needs_render = process_input(key, renderer)

        assert should_continue is True
        assert needs_render is True
        assert renderer.current_view != initial_view

    def test_tab_key_T_uppercase(self, renderer):
        """Test that 'T' key switches view."""
        initial_view = renderer.current_view
        key = KeyEvent.character('T')
        should_continue, needs_render = process_input(key, renderer)

        assert should_continue is True
        assert needs_render is True
        assert renderer.current_view != initial_view

    def test_tab_cycles_through_views(self, renderer):
        """Test that pressing 't' multiple times cycles through all views."""
        views_seen = set()
        views_seen.add(renderer.current_view)

        for _ in range(5):  # There are 5 views
            key = KeyEvent.character('t')
            process_input(key, renderer)
            views_seen.add(renderer.current_view)

        # Should have seen all 5 views
        assert len(views_seen) == 5

    def test_other_keys_ignored(self, renderer):
        """Test that unrecognized keys are ignored."""
        initial_view = renderer.current_view
        key = KeyEvent.character('x')
        should_continue, needs_render = process_input(key, renderer)

        assert should_continue is True
        assert needs_render is False
        assert renderer.current_view == initial_view

    def test_arrow_keys_ignored(self, renderer):
        """Test that arrow keys are ignored."""
        for direction in ['up', 'down', 'left', 'right']:
            key = KeyEvent.arrow(direction)
            should_continue, needs_render = process_input(key, renderer)
            assert should_continue is True
            assert needs_render is False


class TestInputThread:
    """Tests for the InputThread class."""

    def test_initialization(self, mock_terminal):
        """Test InputThread initializes correctly."""
        key_queue = Queue()
        thread = InputThread(mock_terminal, key_queue)

        assert thread.terminal is mock_terminal
        assert thread.key_queue is key_queue
        assert thread.running is True
        assert thread.daemon is True

    def test_stop_sets_running_false(self, mock_terminal):
        """Test that stop() sets running to False."""
        key_queue = Queue()
        thread = InputThread(mock_terminal, key_queue)

        assert thread.running is True
        thread.stop()
        assert thread.running is False

    def test_thread_queues_keys(self, mock_terminal):
        """Test that thread queues keys from terminal."""
        key_queue = Queue()
        thread = InputThread(mock_terminal, key_queue)

        # Add a key to the mock terminal
        test_key = KeyEvent.character('a')
        mock_terminal.add_key(test_key)

        # Manually call run logic once (without actually starting thread)
        key = mock_terminal.read_key(timeout=0.05)
        if key is not None:
            key_queue.put(key)

        assert not key_queue.empty()
        queued_key = key_queue.get()
        assert queued_key == test_key


class TestConstants:
    """Tests for module constants."""

    def test_update_interval(self):
        """Test UPDATE_INTERVAL is set correctly."""
        assert UPDATE_INTERVAL == 1.0

    def test_save_cursor_sequence(self):
        """Test SAVE_CURSOR escape sequence."""
        assert SAVE_CURSOR == "\x1b[s"

    def test_restore_cursor_sequence(self):
        """Test RESTORE_CURSOR escape sequence."""
        assert RESTORE_CURSOR == "\x1b[u"

    def test_move_up_format(self):
        """Test MOVE_UP format string."""
        assert MOVE_UP == "\x1b[{}A"
        assert MOVE_UP.format(5) == "\x1b[5A"


class TestKeyEventHelpers:
    """Tests for KeyEvent helper methods and properties."""

    def test_character_factory(self):
        """Test KeyEvent.character factory method."""
        key = KeyEvent.character('a')
        assert key.key_type == KeyType.CHARACTER
        assert key.value == 'a'

    def test_arrow_factory(self):
        """Test KeyEvent.arrow factory method."""
        key = KeyEvent.arrow('up')
        assert key.key_type == KeyType.ARROW
        assert key.value == 'up'

    def test_special_factory(self):
        """Test KeyEvent.special factory method."""
        key = KeyEvent.special('ctrl-c')
        assert key.key_type == KeyType.SPECIAL
        assert key.value == 'ctrl-c'

    def test_is_quit_q(self):
        """Test is_quit property for 'q' key."""
        key = KeyEvent.character('q')
        assert key.is_quit is True

    def test_is_quit_Q(self):
        """Test is_quit property for 'Q' key."""
        key = KeyEvent.character('Q')
        assert key.is_quit is True

    def test_is_quit_ctrl_c(self):
        """Test is_quit property for Ctrl-C."""
        key = KeyEvent.special('ctrl-c')
        assert key.is_quit is True

    def test_is_quit_other_char(self):
        """Test is_quit property for non-quit key."""
        key = KeyEvent.character('x')
        assert key.is_quit is False

    def test_is_quit_other_special(self):
        """Test is_quit property for non-quit special key."""
        key = KeyEvent.special('escape')
        assert key.is_quit is False


class TestProcessInputSequences:
    """Tests for processing sequences of inputs."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer for testing."""
        return MetricsRenderer()

    def test_multiple_tab_presses(self, renderer):
        """Test multiple tab presses cycle views correctly."""
        views = []
        views.append(renderer.current_view)

        for _ in range(10):
            key = KeyEvent.character('t')
            process_input(key, renderer)
            views.append(renderer.current_view)

        # Should cycle back to start after 5 tabs
        assert views[0] == views[5]
        assert views[1] == views[6]

    def test_tab_then_quit(self, renderer):
        """Test tab followed by quit."""
        # Tab first
        key_t = KeyEvent.character('t')
        should_continue, needs_render = process_input(key_t, renderer)
        assert should_continue is True
        assert needs_render is True

        # Then quit
        key_q = KeyEvent.character('q')
        should_continue, needs_render = process_input(key_q, renderer)
        assert should_continue is False

    def test_mixed_keys_sequence(self, renderer):
        """Test sequence of mixed keys."""
        keys = [
            KeyEvent.character('x'),  # Ignored
            KeyEvent.character('t'),  # Tab view
            KeyEvent.arrow('up'),     # Ignored
            KeyEvent.character('t'),  # Tab view
            KeyEvent.character('q'),  # Quit
        ]

        for i, key in enumerate(keys):
            should_continue, _ = process_input(key, renderer)
            if key.value.lower() == 'q':
                assert should_continue is False
            else:
                assert should_continue is True
