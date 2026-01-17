"""
Base terminal interface with mouse support using Protocol for structural subtyping.

This module defines the contract that all terminal implementations must follow.
Extends the base terminal interface to support mouse events for GUI interaction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Tuple, Optional, Union, runtime_checkable


class KeyType(Enum):
    """Types of key inputs."""
    CHARACTER = "character"
    ARROW = "arrow"
    SPECIAL = "special"


class MouseButton(Enum):
    """Mouse button types."""
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2
    SCROLL_UP = 64
    SCROLL_DOWN = 65
    RELEASE = 3


class MouseEventType(Enum):
    """Types of mouse events."""
    PRESS = "press"
    RELEASE = "release"
    MOVE = "move"


@dataclass(frozen=True)
class KeyEvent:
    """
    Represents a keyboard input event.

    Attributes:
        key_type: The type of key (character, arrow, special)
        value: The key value (character, arrow direction, or special key name)
    """
    key_type: KeyType
    value: str

    @classmethod
    def character(cls, char: str) -> "KeyEvent":
        """Create a character key event."""
        return cls(KeyType.CHARACTER, char)

    @classmethod
    def arrow(cls, direction: str) -> "KeyEvent":
        """Create an arrow key event. Direction: 'up', 'down', 'left', 'right'."""
        return cls(KeyType.ARROW, direction)

    @classmethod
    def special(cls, name: str) -> "KeyEvent":
        """Create a special key event (e.g., 'ctrl-c', 'escape')."""
        return cls(KeyType.SPECIAL, name)

    @property
    def is_quit(self) -> bool:
        """Check if this is a quit key (q, Q, or Ctrl-C)."""
        if self.key_type == KeyType.CHARACTER and self.value.lower() == 'q':
            return True
        if self.key_type == KeyType.SPECIAL and self.value == 'ctrl-c':
            return True
        return False


@dataclass(frozen=True)
class MouseEvent:
    """
    Represents a mouse input event.

    Attributes:
        event_type: Type of mouse event (press, release, move)
        button: Which button was involved
        x: X coordinate in pixels (column)
        y: Y coordinate in pixels (row)
    """
    event_type: MouseEventType
    button: MouseButton
    x: int
    y: int

    @classmethod
    def press(cls, button: MouseButton, x: int, y: int) -> "MouseEvent":
        """Create a mouse press event."""
        return cls(MouseEventType.PRESS, button, x, y)

    @classmethod
    def release(cls, x: int, y: int) -> "MouseEvent":
        """Create a mouse release event."""
        return cls(MouseEventType.RELEASE, MouseButton.RELEASE, x, y)

    @classmethod
    def move(cls, x: int, y: int) -> "MouseEvent":
        """Create a mouse move event."""
        return cls(MouseEventType.MOVE, MouseButton.RELEASE, x, y)


# Union type for any input event
InputEvent = Union[KeyEvent, MouseEvent]


@runtime_checkable
class InputHandler(Protocol):
    """Protocol for handling keyboard and mouse input."""

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """Read a key from input with optional timeout."""
        ...

    def read_input(self, timeout: float = 0.0) -> Optional[InputEvent]:
        """Read any input (key or mouse) with optional timeout."""
        ...


@runtime_checkable
class OutputHandler(Protocol):
    """Protocol for handling terminal output."""

    def write(self, data: str) -> None:
        """Write data to the terminal."""
        ...

    def flush(self) -> None:
        """Flush the output buffer."""
        ...

    def get_size(self) -> Tuple[int, int]:
        """Get terminal size as (columns, rows)."""
        ...


@runtime_checkable
class CursorController(Protocol):
    """Protocol for cursor control operations."""

    def hide_cursor(self) -> None:
        """Hide the terminal cursor."""
        ...

    def show_cursor(self) -> None:
        """Show the terminal cursor."""
        ...

    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor to specific position (1-indexed)."""
        ...

    def move_cursor_home(self) -> None:
        """Move cursor to top-left corner (1, 1)."""
        ...


@runtime_checkable
class ScreenController(Protocol):
    """Protocol for screen control operations."""

    def clear_screen(self) -> None:
        """Clear the entire screen."""
        ...

    def enter_alternate_screen(self) -> None:
        """Enter alternate screen buffer."""
        ...

    def exit_alternate_screen(self) -> None:
        """Exit alternate screen buffer."""
        ...


@runtime_checkable
class ModeController(Protocol):
    """Protocol for terminal mode control."""

    def enter_raw_mode(self) -> None:
        """Enter raw mode for character-by-character input."""
        ...

    def exit_raw_mode(self) -> None:
        """Exit raw mode and restore original terminal settings."""
        ...

    @property
    def is_raw(self) -> bool:
        """Check if terminal is currently in raw mode."""
        ...


@runtime_checkable
class MouseController(Protocol):
    """Protocol for mouse control operations."""

    def enable_mouse(self) -> None:
        """Enable mouse tracking."""
        ...

    def disable_mouse(self) -> None:
        """Disable mouse tracking."""
        ...

    @property
    def mouse_enabled(self) -> bool:
        """Check if mouse tracking is enabled."""
        ...


class Terminal(ABC):
    """
    Abstract base class combining all terminal protocols with mouse support.

    Concrete implementations should inherit from this class and implement
    all abstract methods for a complete terminal interface with mouse support.
    """

    @abstractmethod
    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """Read a key from input with optional timeout."""
        ...

    @abstractmethod
    def read_input(self, timeout: float = 0.0) -> Optional[InputEvent]:
        """Read any input (key or mouse) with optional timeout."""
        ...

    @abstractmethod
    def write(self, data: str) -> None:
        """Write data to the terminal."""
        ...

    @abstractmethod
    def flush(self) -> None:
        """Flush the output buffer."""
        ...

    @abstractmethod
    def get_size(self) -> Tuple[int, int]:
        """Get terminal size as (columns, rows)."""
        ...

    @abstractmethod
    def hide_cursor(self) -> None:
        """Hide the terminal cursor."""
        ...

    @abstractmethod
    def show_cursor(self) -> None:
        """Show the terminal cursor."""
        ...

    @abstractmethod
    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor to specific position (1-indexed)."""
        ...

    @abstractmethod
    def move_cursor_home(self) -> None:
        """Move cursor to top-left corner."""
        ...

    @abstractmethod
    def clear_screen(self) -> None:
        """Clear the entire screen."""
        ...

    @abstractmethod
    def enter_alternate_screen(self) -> None:
        """Enter alternate screen buffer."""
        ...

    @abstractmethod
    def exit_alternate_screen(self) -> None:
        """Exit alternate screen buffer."""
        ...

    @abstractmethod
    def enter_raw_mode(self) -> None:
        """Enter raw mode for character-by-character input."""
        ...

    @abstractmethod
    def exit_raw_mode(self) -> None:
        """Exit raw mode and restore original settings."""
        ...

    @property
    @abstractmethod
    def is_raw(self) -> bool:
        """Check if terminal is in raw mode."""
        ...

    @abstractmethod
    def enable_mouse(self) -> None:
        """Enable mouse tracking."""
        ...

    @abstractmethod
    def disable_mouse(self) -> None:
        """Disable mouse tracking."""
        ...

    @property
    @abstractmethod
    def mouse_enabled(self) -> bool:
        """Check if mouse tracking is enabled."""
        ...

    def write_at(self, row: int, col: int, data: str) -> None:
        """Convenience method to move cursor and write data."""
        self.move_cursor(row, col)
        self.write(data)
        self.flush()

    def __enter__(self) -> "Terminal":
        """Context manager entry - enters raw mode and hides cursor."""
        self.enter_raw_mode()
        self.hide_cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - restores terminal state."""
        self.show_cursor()
        self.exit_raw_mode()
        self.write("\n")
        self.flush()
