"""
Pytest fixtures for snake game tests.
"""

import sys
import pytest
from pathlib import Path
from typing import Optional, Tuple
from unittest.mock import MagicMock

# Add the snake package to the path
snake_dir = Path(__file__).parent.parent
sys.path.insert(0, str(snake_dir))

from game import GameState, Direction, create_game
from terminals.base import Terminal, KeyEvent, KeyType


@pytest.fixture
def small_game() -> GameState:
    """Create a small 8x8 game for testing."""
    return GameState(width=8, height=8, pixel_size=16)


@pytest.fixture
def medium_game() -> GameState:
    """Create a medium 16x16 game for testing."""
    return GameState(width=16, height=16, pixel_size=16)


@pytest.fixture
def custom_game():
    """Factory fixture to create games with custom parameters."""
    def _create(width=8, height=8, pixel_size=16, snake=None, direction=Direction.RIGHT, food=(3, 3)):
        game = GameState(
            width=width,
            height=height,
            pixel_size=pixel_size,
            snake=snake or [],
            direction=direction,
        )
        if snake:
            game.snake = snake
            game.food = food
        return game
    return _create


class MockTerminal(Terminal):
    """Mock terminal for testing game loop and input processing."""

    def __init__(self):
        self.written_data = []
        self.key_queue = []
        self.cursor_pos = (1, 1)
        self.cursor_hidden = False
        self.in_alternate_screen = False
        self._is_raw = False
        self._size = (80, 24)

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        if self.key_queue:
            return self.key_queue.pop(0)
        return None

    def add_key(self, key: KeyEvent) -> None:
        """Add a key to the input queue for testing."""
        self.key_queue.append(key)

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

    @property
    def is_raw(self) -> bool:
        return self._is_raw


@pytest.fixture
def mock_terminal() -> MockTerminal:
    """Create a mock terminal for testing."""
    return MockTerminal()
