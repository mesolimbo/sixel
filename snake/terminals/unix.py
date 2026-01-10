"""
Unix terminal implementation for Linux and macOS.

Uses POSIX terminal APIs (termios, tty) for raw mode and input handling.
Compatible with any Unix-like system including Linux, macOS, and BSD.
"""

import select
import shutil
import sys
import termios
import tty
from typing import Optional, Tuple

from .base import Terminal, KeyEvent


class UnixTerminal(Terminal):
    """
    Terminal implementation for Unix-like systems (Linux, macOS, BSD).

    Uses POSIX termios for raw mode and select for non-blocking input.
    """

    # ANSI escape sequences
    ESC = "\x1b"
    CSI = "\x1b["

    # Cursor control
    CURSOR_HIDE = "\x1b[?25l"
    CURSOR_SHOW = "\x1b[?25h"
    CURSOR_HOME = "\x1b[H"

    # Screen control
    CLEAR_SCREEN = "\x1b[2J\x1b[H"
    ALT_SCREEN_ON = "\x1b[?1049h"
    ALT_SCREEN_OFF = "\x1b[?1049l"

    def __init__(self):
        self._old_settings: Optional[list] = None
        self._is_raw: bool = False

    @property
    def is_raw(self) -> bool:
        """Check if terminal is in raw mode."""
        return self._is_raw

    def enter_raw_mode(self) -> None:
        """Enter raw mode for character-by-character input."""
        if self._is_raw:
            return
        self._old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        self._is_raw = True

    def exit_raw_mode(self) -> None:
        """Exit raw mode and restore original settings."""
        if self._old_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            self._old_settings = None
        self._is_raw = False

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """
        Read a key from input with optional timeout.

        Handles escape sequences for arrow keys and other special keys.
        """
        if not select.select([sys.stdin], [], [], timeout)[0]:
            return None

        char = sys.stdin.read(1)

        # Handle Ctrl-C
        if char == '\x03':
            return KeyEvent.special('ctrl-c')

        # Handle escape sequences
        if char == '\x1b':
            return self._read_escape_sequence()

        return KeyEvent.character(char)

    def _read_escape_sequence(self) -> KeyEvent:
        """Parse escape sequence for arrow keys and other special keys."""
        # Check if more characters are available
        if not select.select([sys.stdin], [], [], 0.05)[0]:
            return KeyEvent.special('escape')

        second = sys.stdin.read(1)

        # CSI sequences (ESC [)
        if second == '[':
            if not select.select([sys.stdin], [], [], 0.05)[0]:
                return KeyEvent.special('escape')

            third = sys.stdin.read(1)

            # Arrow keys
            arrow_map = {
                'A': 'up',
                'B': 'down',
                'C': 'right',
                'D': 'left',
            }
            if third in arrow_map:
                return KeyEvent.arrow(arrow_map[third])

            # Other special keys could be handled here
            return KeyEvent.special(f'csi-{third}')

        # SS3 sequences (ESC O) - some terminals use this for arrows
        if second == 'O':
            if not select.select([sys.stdin], [], [], 0.05)[0]:
                return KeyEvent.special('escape')

            third = sys.stdin.read(1)
            arrow_map = {
                'A': 'up',
                'B': 'down',
                'C': 'right',
                'D': 'left',
            }
            if third in arrow_map:
                return KeyEvent.arrow(arrow_map[third])

            return KeyEvent.special(f'ss3-{third}')

        return KeyEvent.special(f'esc-{second}')

    def write(self, data: str) -> None:
        """Write data to the terminal."""
        sys.stdout.write(data)

    def flush(self) -> None:
        """Flush the output buffer."""
        sys.stdout.flush()

    def get_size(self) -> Tuple[int, int]:
        """Get terminal size as (columns, rows)."""
        size = shutil.get_terminal_size()
        return size.columns, size.lines

    def hide_cursor(self) -> None:
        """Hide the terminal cursor."""
        self.write(self.CURSOR_HIDE)
        self.flush()

    def show_cursor(self) -> None:
        """Show the terminal cursor."""
        self.write(self.CURSOR_SHOW)
        self.flush()

    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor to specific position (1-indexed)."""
        self.write(f'{self.CSI}{row};{col}H')
        self.flush()

    def move_cursor_home(self) -> None:
        """Move cursor to top-left corner."""
        self.write(self.CURSOR_HOME)
        self.flush()

    def clear_screen(self) -> None:
        """Clear the entire screen."""
        self.write(self.CLEAR_SCREEN)
        self.flush()

    def enter_alternate_screen(self) -> None:
        """Enter alternate screen buffer."""
        self.write(self.ALT_SCREEN_ON)
        self.flush()

    def exit_alternate_screen(self) -> None:
        """Exit alternate screen buffer."""
        self.write(self.ALT_SCREEN_OFF)
        self.flush()
