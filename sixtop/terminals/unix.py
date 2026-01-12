"""
Unix terminal implementation.

Uses termios for raw mode and select for non-blocking input.
Works on Linux, macOS, and other Unix-like systems.
"""

import os
import select
import shutil
import sys
import termios
import tty
from typing import Optional, Tuple, List

from .base import Terminal, KeyEvent


class UnixTerminal(Terminal):
    """
    Terminal implementation for Unix-like systems.

    Uses termios for terminal mode control and select for
    non-blocking input handling.
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
        self._is_raw: bool = False
        self._old_settings: Optional[List] = None
        self._fd = sys.stdin.fileno()

    @property
    def is_raw(self) -> bool:
        """Check if terminal is in raw mode."""
        return self._is_raw

    def enter_raw_mode(self) -> None:
        """Enter raw mode for character-by-character input."""
        if self._is_raw:
            return

        # Save current terminal settings
        self._old_settings = termios.tcgetattr(self._fd)

        # Set raw mode
        tty.setraw(self._fd)
        self._is_raw = True

    def exit_raw_mode(self) -> None:
        """Exit raw mode and restore original settings."""
        if not self._is_raw or self._old_settings is None:
            return

        # Restore original settings
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
        self._old_settings = None
        self._is_raw = False

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """
        Read a key from input with optional timeout.

        Uses select for non-blocking input check.
        """
        # Use select to check if input is available
        if timeout == 0:
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
        else:
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)

        if not rlist:
            return None

        # Read the first character
        char = sys.stdin.read(1)

        # Handle escape sequences (arrow keys, etc.)
        if char == '\x1b':
            # Check if more characters are available
            rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
            if rlist:
                char2 = sys.stdin.read(1)
                if char2 == '[':
                    # CSI sequence
                    rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if rlist:
                        char3 = sys.stdin.read(1)
                        arrow_map = {
                            'A': 'up',
                            'B': 'down',
                            'C': 'right',
                            'D': 'left',
                        }
                        if char3 in arrow_map:
                            return KeyEvent.arrow(arrow_map[char3])
                        return KeyEvent.special(f'csi-{char3}')
                return KeyEvent.special('escape')
            return KeyEvent.special('escape')

        # Handle Ctrl-C
        if char == '\x03':
            return KeyEvent.special('ctrl-c')

        return KeyEvent.character(char)

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
