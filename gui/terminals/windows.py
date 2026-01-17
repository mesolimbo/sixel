"""
Windows terminal implementation with mouse support.

Uses msvcrt for keyboard input and Windows Console API for terminal control.
Note: Sixel support on Windows requires Windows Terminal or similar.
Mouse support uses ANSI escape sequences (Windows Terminal) or Console API.
"""

import ctypes
import shutil
import signal
import sys
import time
from typing import Optional, Tuple

from .base import (
    Terminal, KeyEvent, MouseEvent, MouseButton,
    MouseEventType, InputEvent
)

# Windows Console API constants
STD_INPUT_HANDLE = -10
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_MOUSE_INPUT = 0x0010
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200


class WindowsTerminal(Terminal):
    """
    Terminal implementation for Windows with mouse support.

    Uses msvcrt for keyboard input. ANSI escape sequences are used for
    screen control and mouse tracking (supported in Windows 10+ and Windows Terminal).
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

    # Mouse tracking (SGR extended mode)
    MOUSE_ON = "\x1b[?1000h\x1b[?1006h"
    MOUSE_OFF = "\x1b[?1006l\x1b[?1000l"

    # Windows special key codes
    ARROW_KEYS = {
        'H': 'up',
        'P': 'down',
        'K': 'left',
        'M': 'right',
    }

    def __init__(self):
        self._is_raw: bool = False
        self._mouse_enabled: bool = False
        self._old_console_mode: Optional[int] = None
        self._kernel32 = None
        self._input_buffer = ""

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

    @property
    def mouse_enabled(self) -> bool:
        """Check if mouse tracking is enabled."""
        return self._mouse_enabled

    def enter_raw_mode(self) -> None:
        """Enter raw mode with virtual terminal input enabled."""
        if self._kernel32:
            stdin_handle = self._kernel32.GetStdHandle(STD_INPUT_HANDLE)
            mode = ctypes.c_ulong()
            if self._kernel32.GetConsoleMode(stdin_handle, ctypes.byref(mode)):
                self._old_console_mode = mode.value
                # Enable virtual terminal input for ANSI sequences
                new_mode = (mode.value & ~ENABLE_PROCESSED_INPUT) | ENABLE_VIRTUAL_TERMINAL_INPUT
                self._kernel32.SetConsoleMode(stdin_handle, new_mode)

        # Ignore SIGINT at Python level as a fallback
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

    def enable_mouse(self) -> None:
        """Enable mouse tracking."""
        if self._mouse_enabled:
            return
        self.write(self.MOUSE_ON)
        self.flush()
        self._mouse_enabled = True

    def disable_mouse(self) -> None:
        """Disable mouse tracking."""
        if not self._mouse_enabled:
            return
        self.write(self.MOUSE_OFF)
        self.flush()
        self._mouse_enabled = False

    def _parse_sgr_mouse(self, seq: str) -> Optional[MouseEvent]:
        """Parse SGR-format mouse event."""
        try:
            if seq.startswith('\x1b[<'):
                seq = seq[3:]

            is_release = seq.endswith('m')
            seq = seq[:-1]

            parts = seq.split(';')
            if len(parts) != 3:
                return None

            button_code = int(parts[0])
            x = int(parts[1]) - 1
            y = int(parts[2]) - 1

            if is_release:
                return MouseEvent.release(x, y)

            if button_code >= 64:
                if button_code == 64:
                    return MouseEvent(MouseEventType.PRESS, MouseButton.SCROLL_UP, x, y)
                elif button_code == 65:
                    return MouseEvent(MouseEventType.PRESS, MouseButton.SCROLL_DOWN, x, y)

            button_num = button_code & 0x03
            if button_num == 0:
                button = MouseButton.LEFT
            elif button_num == 1:
                button = MouseButton.MIDDLE
            elif button_num == 2:
                button = MouseButton.RIGHT
            else:
                button = MouseButton.RELEASE

            return MouseEvent.press(button, x, y)

        except (ValueError, IndexError):
            return None

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """Read a key from input with optional timeout (ignores mouse events)."""
        event = self.read_input(timeout)
        if isinstance(event, KeyEvent):
            return event
        return None

    def read_input(self, timeout: float = 0.0) -> Optional[InputEvent]:
        """Read any input (key or mouse) with optional timeout."""
        start = time.time()

        while True:
            if self._msvcrt.kbhit():
                ch = self._msvcrt.getch()

                # Handle escape sequences
                if ch == b'\x1b':
                    self._input_buffer = '\x1b'
                    # Read the rest of the sequence
                    while self._msvcrt.kbhit():
                        next_ch = self._msvcrt.getch().decode('latin-1')
                        self._input_buffer += next_ch
                        # Check for SGR mouse sequence terminator
                        if self._input_buffer.startswith('\x1b[<') and next_ch in 'Mm':
                            break
                        # Check for other sequence terminators
                        if next_ch.isalpha() or next_ch == '~':
                            break

                    # Parse SGR mouse event
                    if self._input_buffer.startswith('\x1b[<'):
                        mouse_event = self._parse_sgr_mouse(self._input_buffer)
                        self._input_buffer = ""
                        if mouse_event:
                            return mouse_event
                        return KeyEvent.special('unknown-mouse')

                    # Parse arrow keys
                    if len(self._input_buffer) >= 3 and self._input_buffer[1] == '[':
                        arrow_char = self._input_buffer[2]
                        arrow_map = {'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left'}
                        if arrow_char in arrow_map:
                            self._input_buffer = ""
                            return KeyEvent.arrow(arrow_map[arrow_char])

                    self._input_buffer = ""
                    return KeyEvent.special('escape')

                # Handle special keys (arrow keys via Windows API)
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

                # Handle Tab
                if char == '\x09':
                    return KeyEvent.special('tab')

                # Handle Backspace
                if char == '\x08':
                    return KeyEvent.special('backspace')

                # Handle Enter
                if char == '\r':
                    return KeyEvent.special('enter')

                return KeyEvent.character(char)

            # Check timeout
            if timeout > 0:
                if (time.time() - start) >= timeout:
                    return None
                time.sleep(0.01)
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
