"""
Tests for the game loop module (game_loop.py).

Tests cover:
- Input processing
- Direction key handling
- Quit/restart command handling
- Key event processing
"""

import pytest
from unittest.mock import MagicMock, patch

from game import GameState, Direction
from game_loop import (
    process_input,
    DIRECTION_KEYS,
    ARROW_DIRECTIONS,
    wait_for_key,
)
from terminals.base import KeyEvent, KeyType


class TestProcessInput:
    """Tests for input processing function."""

    def test_process_none_input(self, small_game):
        """Test processing None input."""
        result = process_input(None, small_game)
        assert result is True

    def test_process_quit_key_q(self, small_game):
        """Test processing 'q' quit key."""
        key = KeyEvent.character('q')
        result = process_input(key, small_game)
        assert result is False

    def test_process_quit_key_Q(self, small_game):
        """Test processing 'Q' quit key."""
        key = KeyEvent.character('Q')
        result = process_input(key, small_game)
        assert result is False

    def test_process_quit_ctrl_c(self, small_game):
        """Test processing Ctrl-C quit."""
        key = KeyEvent.special('ctrl-c')
        result = process_input(key, small_game)
        assert result is False

    def test_process_restart_key(self, small_game):
        """Test processing 'r' restart key."""
        small_game.score = 10
        small_game.game_over = True
        key = KeyEvent.character('r')
        result = process_input(key, small_game)
        assert result is True
        assert small_game.score == 0
        assert small_game.game_over is False

    def test_process_restart_key_uppercase(self, small_game):
        """Test processing 'R' restart key."""
        small_game.score = 10
        small_game.game_over = True
        key = KeyEvent.character('R')
        result = process_input(key, small_game)
        assert result is True
        assert small_game.score == 0


class TestDirectionKeyProcessing:
    """Tests for direction key processing."""

    def test_process_wasd_up(self, small_game):
        """Test processing 'w' for up direction."""
        small_game.direction = Direction.RIGHT
        key = KeyEvent.character('w')
        process_input(key, small_game)
        assert small_game.direction == Direction.UP

    def test_process_wasd_down(self, small_game):
        """Test processing 's' for down direction."""
        small_game.direction = Direction.RIGHT
        key = KeyEvent.character('s')
        process_input(key, small_game)
        assert small_game.direction == Direction.DOWN

    def test_process_wasd_left(self, small_game):
        """Test processing 'a' for left direction."""
        small_game.direction = Direction.UP
        key = KeyEvent.character('a')
        process_input(key, small_game)
        assert small_game.direction == Direction.LEFT

    def test_process_wasd_right(self, small_game):
        """Test processing 'd' for right direction."""
        small_game.direction = Direction.UP
        key = KeyEvent.character('d')
        process_input(key, small_game)
        assert small_game.direction == Direction.RIGHT

    def test_process_wasd_uppercase(self, small_game):
        """Test processing uppercase WASD keys."""
        small_game.direction = Direction.RIGHT
        key = KeyEvent.character('W')
        process_input(key, small_game)
        assert small_game.direction == Direction.UP


class TestArrowKeyProcessing:
    """Tests for arrow key processing."""

    def test_process_arrow_up(self, small_game):
        """Test processing up arrow."""
        small_game.direction = Direction.RIGHT
        key = KeyEvent.arrow('up')
        process_input(key, small_game)
        assert small_game.direction == Direction.UP

    def test_process_arrow_down(self, small_game):
        """Test processing down arrow."""
        small_game.direction = Direction.RIGHT
        key = KeyEvent.arrow('down')
        process_input(key, small_game)
        assert small_game.direction == Direction.DOWN

    def test_process_arrow_left(self, small_game):
        """Test processing left arrow."""
        small_game.direction = Direction.UP
        key = KeyEvent.arrow('left')
        process_input(key, small_game)
        assert small_game.direction == Direction.LEFT

    def test_process_arrow_right(self, small_game):
        """Test processing right arrow."""
        small_game.direction = Direction.UP
        key = KeyEvent.arrow('right')
        process_input(key, small_game)
        assert small_game.direction == Direction.RIGHT

    def test_process_arrow_uppercase(self, small_game):
        """Test processing uppercase arrow direction."""
        small_game.direction = Direction.RIGHT
        key = KeyEvent.arrow('UP')
        process_input(key, small_game)
        assert small_game.direction == Direction.UP


class TestUnknownKeyProcessing:
    """Tests for unknown/unhandled key processing."""

    def test_process_unknown_character(self, small_game):
        """Test processing unknown character key."""
        original_direction = small_game.direction
        key = KeyEvent.character('x')
        result = process_input(key, small_game)
        assert result is True
        assert small_game.direction == original_direction

    def test_process_unknown_arrow(self, small_game):
        """Test processing unknown arrow direction."""
        original_direction = small_game.direction
        key = KeyEvent.arrow('diagonal')
        result = process_input(key, small_game)
        assert result is True
        assert small_game.direction == original_direction

    def test_process_unknown_special(self, small_game):
        """Test processing unknown special key."""
        original_direction = small_game.direction
        key = KeyEvent.special('f1')
        result = process_input(key, small_game)
        assert result is True
        assert small_game.direction == original_direction


class TestDirectionKeyMappings:
    """Tests for direction key mapping constants."""

    def test_direction_keys_mapping(self):
        """Test that DIRECTION_KEYS contains correct mappings."""
        assert DIRECTION_KEYS['w'] == Direction.UP
        assert DIRECTION_KEYS['a'] == Direction.LEFT
        assert DIRECTION_KEYS['s'] == Direction.DOWN
        assert DIRECTION_KEYS['d'] == Direction.RIGHT

    def test_arrow_directions_mapping(self):
        """Test that ARROW_DIRECTIONS contains correct mappings."""
        assert ARROW_DIRECTIONS['up'] == Direction.UP
        assert ARROW_DIRECTIONS['down'] == Direction.DOWN
        assert ARROW_DIRECTIONS['left'] == Direction.LEFT
        assert ARROW_DIRECTIONS['right'] == Direction.RIGHT


class TestWaitForKey:
    """Tests for wait_for_key function."""

    def test_wait_for_key_returns_true_on_target(self, mock_terminal):
        """Test that wait_for_key returns True when target key is pressed."""
        mock_terminal.add_key(KeyEvent.character(' '))
        result = wait_for_key(mock_terminal, {' '})
        assert result is True

    def test_wait_for_key_returns_false_on_quit(self, mock_terminal):
        """Test that wait_for_key returns False when quit key is pressed."""
        mock_terminal.add_key(KeyEvent.character('q'))
        result = wait_for_key(mock_terminal, {' '})
        assert result is False

    def test_wait_for_key_returns_false_on_ctrl_c(self, mock_terminal):
        """Test that wait_for_key returns False on Ctrl-C."""
        mock_terminal.add_key(KeyEvent.special('ctrl-c'))
        result = wait_for_key(mock_terminal, {' '})
        assert result is False

    def test_wait_for_key_custom_quit_keys(self, mock_terminal):
        """Test wait_for_key with custom quit keys."""
        mock_terminal.add_key(KeyEvent.character('x'))
        result = wait_for_key(mock_terminal, {' '}, quit_keys={'x'})
        assert result is False

    def test_wait_for_key_enters_raw_mode(self, mock_terminal):
        """Test that wait_for_key enters raw mode."""
        mock_terminal.add_key(KeyEvent.character(' '))
        wait_for_key(mock_terminal, {' '})
        # After completion, raw mode should be exited
        assert mock_terminal.is_raw is False

    def test_wait_for_key_ignores_non_target_keys(self, mock_terminal):
        """Test that wait_for_key ignores non-target keys."""
        mock_terminal.add_key(KeyEvent.character('x'))
        mock_terminal.add_key(KeyEvent.character('y'))
        mock_terminal.add_key(KeyEvent.character(' '))  # Target
        result = wait_for_key(mock_terminal, {' '})
        assert result is True

    def test_wait_for_key_handles_arrow_keys(self, mock_terminal):
        """Test that wait_for_key ignores arrow keys (non-character)."""
        mock_terminal.add_key(KeyEvent.arrow('up'))
        mock_terminal.add_key(KeyEvent.character(' '))  # Target
        result = wait_for_key(mock_terminal, {' '})
        assert result is True


class TestInputSequences:
    """Tests for sequences of input processing."""

    def test_multiple_direction_changes(self, small_game):
        """Test processing multiple direction changes."""
        small_game.direction = Direction.RIGHT

        # Change to up
        process_input(KeyEvent.character('w'), small_game)
        assert small_game.direction == Direction.UP

        # Change to left
        process_input(KeyEvent.character('a'), small_game)
        assert small_game.direction == Direction.LEFT

        # Change to down
        process_input(KeyEvent.character('s'), small_game)
        assert small_game.direction == Direction.DOWN

    def test_direction_change_respects_game_rules(self, small_game):
        """Test that direction changes respect 180-degree rule."""
        small_game.direction = Direction.RIGHT

        # Try to go left (opposite) - should be blocked
        process_input(KeyEvent.character('a'), small_game)
        assert small_game.direction == Direction.RIGHT

        # Go up first
        process_input(KeyEvent.character('w'), small_game)
        assert small_game.direction == Direction.UP

        # Now can go left
        process_input(KeyEvent.character('a'), small_game)
        assert small_game.direction == Direction.LEFT

    def test_restart_during_game(self, small_game):
        """Test restart key during active game."""
        small_game.score = 5
        small_game.game_over = False

        # Restart should work even during active game
        process_input(KeyEvent.character('r'), small_game)
        assert small_game.score == 0

    def test_mixed_input_types(self, small_game):
        """Test mixing different input types."""
        small_game.direction = Direction.RIGHT

        # Arrow key
        process_input(KeyEvent.arrow('up'), small_game)
        assert small_game.direction == Direction.UP

        # WASD key
        process_input(KeyEvent.character('a'), small_game)
        assert small_game.direction == Direction.LEFT

        # Unknown key (should not change direction)
        process_input(KeyEvent.character('x'), small_game)
        assert small_game.direction == Direction.LEFT
