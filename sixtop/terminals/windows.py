"""
Windows terminal implementation.

Uses msvcrt for keyboard input and Windows Console API for terminal control.
Note: Sixel support on Windows requires Windows Terminal or similar.
"""

import ctypes
import shutil
import signal
import sys
import time
from typing import Optional, Tuple

from .base import Terminal, KeyEvent

# Windows Console API constants
STD_INPUT_HANDLE = -10
ENABLE_PROCESSED_INPUT = 0x0001


class WindowsTerminal(Terminal):
    """
    Terminal implementation for Windows.

    Uses msvcrt for keyboard input. ANSI escape sequences are used for
    screen control (supported in Windows 10+ and Windows Terminal).
    """

    # ANSI escape sequences (supported in Windows 10+)
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

    # Windows special key codes
    ARROW_KEYS = {
        'H': 'up',
        'P': 'down',
        'K': 'left',
        'M': 'right',
    }

    def __init__(self):
        self._is_raw: bool = False
        self._old_console_mode: Optional[int] = None
        self._kernel32 = None
        # Import msvcrt here to avoid import errors on Unix
        try:
            import msvcrt
            self._msvcrt = msvcrt
        except ImportError:
            raise RuntimeError("WindowsTerminal requires Windows with msvcrt")

        # Get kernel32 handle for console mode manipulation
        try:
            self._kernel32 = ctypes.windll.kernel32
        except AttributeError:
            pass  # Not on Windows, kernel32 not available

    @property
    def is_raw(self) -> bool:
        """Check if terminal is in raw mode."""
        return self._is_raw

    def enter_raw_mode(self) -> None:
        """
        Enter raw mode.

        On Windows, msvcrt already provides unbuffered input.
        We also disable ENABLE_PROCESSED_INPUT to prevent Ctrl+C
        from generating SIGINT, allowing us to read it as a character.
        """
        if self._kernel32:
            # Get stdin handle
            stdin_handle = self._kernel32.GetStdHandle(STD_INPUT_HANDLE)
            # Save current console mode
            mode = ctypes.c_ulong()
            if self._kernel32.GetConsoleMode(stdin_handle, ctypes.byref(mode)):
                self._old_console_mode = mode.value
                # Disable ENABLE_PROCESSED_INPUT to prevent Ctrl+C from
                # generating SIGINT - instead it will be read as '\x03'
                new_mode = mode.value & ~ENABLE_PROCESSED_INPUT
                self._kernel32.SetConsoleMode(stdin_handle, new_mode)

        # Also ignore SIGINT at Python level as a fallback
        self._old_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
        self._is_raw = True

    def exit_raw_mode(self) -> None:
        """Exit raw mode and restore console settings."""
        # Restore original SIGINT handler
        if hasattr(self, '_old_sigint') and self._old_sigint is not None:
            signal.signal(signal.SIGINT, self._old_sigint)
            self._old_sigint = None

        # Restore original console mode
        if self._kernel32 and self._old_console_mode is not None:
            stdin_handle = self._kernel32.GetStdHandle(STD_INPUT_HANDLE)
            self._kernel32.SetConsoleMode(stdin_handle, self._old_console_mode)
            self._old_console_mode = None

        self._is_raw = False

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """
        Read a key from input with optional timeout.

        Uses msvcrt.kbhit() for non-blocking input check.
        """
        start = time.time()

        while True:
            if self._msvcrt.kbhit():
                ch = self._msvcrt.getch()

                # Handle special keys (arrow keys, function keys)
                if ch in (b'\x00', b'\xe0'):
                    if self._msvcrt.kbhit():
                        special = self._msvcrt.getch().decode('latin-1')
                        if special in self.ARROW_KEYS:
                            return KeyEvent.arrow(self.ARROW_KEYS[special])
                        return KeyEvent.special(f'special-{special}')
                    return KeyEvent.special('special')

                char = ch.decode('latin-1')

                # Handle Ctrl-C
                if char == '\x03':
                    return KeyEvent.special('ctrl-c')

                return KeyEvent.character(char)

            # Check timeout
            if timeout > 0:
                if (time.time() - start) >= timeout:
                    return None
                time.sleep(0.01)  # Small sleep to avoid busy waiting
            else:
                return None

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
