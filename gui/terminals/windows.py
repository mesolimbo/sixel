"""
Windows terminal implementation with mouse support.

Uses msvcrt for input and VT escape sequences for mouse tracking.
Note: Sixel support on Windows requires Windows Terminal or similar.
Mouse support uses ANSI escape sequences (SGR mode) which work in
Windows Terminal even when running through Git Bash.
"""

import ctypes
import ctypes.wintypes
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
STD_OUTPUT_HANDLE = -11
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040


class WindowsTerminal(Terminal):
    """
    Terminal implementation for Windows with mouse support.

    Uses msvcrt for input reading and VT escape sequences for mouse tracking.
    This approach works with Windows Terminal even when running through Git Bash,
    unlike the Console API mouse events which are blocked by the MSYS2/PTY layer.
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

    # Mouse tracking (SGR extended mode - works in Windows Terminal)
    # 1000h = basic mouse tracking (clicks)
    # 1006h = SGR extended mode (better coordinate support)
    MOUSE_ON = "\x1b[?1000h\x1b[?1006h"
    MOUSE_OFF = "\x1b[?1006l\x1b[?1000l"

    def __init__(self):
        self._is_raw: bool = False
        self._mouse_enabled: bool = False
        self._old_input_mode: Optional[int] = None
        self._old_output_mode: Optional[int] = None
        self._kernel32 = None
        self._stdin_handle = None
        self._stdout_handle = None
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
            self._stdin_handle = self._kernel32.GetStdHandle(STD_INPUT_HANDLE)
            self._stdout_handle = self._kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        except AttributeError:
            raise RuntimeError("WindowsTerminal requires Windows")

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
        if self._kernel32 and self._stdin_handle:
            # Save and set input mode - enable VT input for ANSI sequences
            mode = ctypes.c_ulong()
            if self._kernel32.GetConsoleMode(self._stdin_handle, ctypes.byref(mode)):
                self._old_input_mode = mode.value
                # Enable VT input, disable processed input and quick edit
                new_mode = (
                    (mode.value & ~ENABLE_PROCESSED_INPUT & ~ENABLE_QUICK_EDIT_MODE)
                    | ENABLE_VIRTUAL_TERMINAL_INPUT
                    | ENABLE_EXTENDED_FLAGS
                )
                self._kernel32.SetConsoleMode(self._stdin_handle, new_mode)

            # Save and set output mode for ANSI support
            if self._kernel32.GetConsoleMode(self._stdout_handle, ctypes.byref(mode)):
                self._old_output_mode = mode.value
                new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                self._kernel32.SetConsoleMode(self._stdout_handle, new_mode)

        # Ignore SIGINT at Python level as a fallback
        self._old_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
        self._is_raw = True

    def exit_raw_mode(self) -> None:
        """Exit raw mode and restore console settings."""
        # Restore original SIGINT handler
        if hasattr(self, '_old_sigint') and self._old_sigint is not None:
            signal.signal(signal.SIGINT, self._old_sigint)
            self._old_sigint = None

        # Restore original console modes
        if self._kernel32:
            if self._old_input_mode is not None:
                self._kernel32.SetConsoleMode(self._stdin_handle, self._old_input_mode)
                self._old_input_mode = None
            if self._old_output_mode is not None:
                self._kernel32.SetConsoleMode(self._stdout_handle, self._old_output_mode)
                self._old_output_mode = None

        self._is_raw = False

    def enable_mouse(self) -> None:
        """Enable mouse tracking using VT escape sequences."""
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
        """
        Parse SGR-format mouse event.

        SGR format: ESC [ < Cb ; Cx ; Cy M/m
        Where M = press, m = release
        Cb = button code, Cx = column (1-based), Cy = row (1-based)
        """
        try:
            # Remove the ESC [ < prefix if present
            if seq.startswith('\x1b[<'):
                seq = seq[3:]

            # Check if it's a release (ends with 'm') or press (ends with 'M')
            is_release = seq.endswith('m')
            seq = seq[:-1]  # Remove the M/m suffix

            parts = seq.split(';')
            if len(parts) != 3:
                return None

            button_code = int(parts[0])
            x = int(parts[1]) - 1  # Convert to 0-based
            y = int(parts[2]) - 1  # Convert to 0-based

            # Handle release
            if is_release:
                return MouseEvent.release(x, y)

            # Handle scroll wheel (button codes 64, 65)
            if button_code >= 64:
                if button_code == 64:
                    return MouseEvent(MouseEventType.PRESS, MouseButton.SCROLL_UP, x, y)
                elif button_code == 65:
                    return MouseEvent(MouseEventType.PRESS, MouseButton.SCROLL_DOWN, x, y)

            # Handle regular buttons
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
        """
        Read any input (key or mouse) with optional timeout.

        Uses msvcrt for reading and parses VT escape sequences for
        mouse events and special keys.
        """
        start = time.time()

        while True:
            if self._msvcrt.kbhit():
                ch = self._msvcrt.getch()

                # Handle escape sequences (mouse events, arrow keys, etc.)
                if ch == b'\x1b':
                    self._input_buffer = '\x1b'

                    # Read more characters with a short timeout to get the full sequence
                    seq_start = time.time()
                    while (time.time() - seq_start) < 0.02:  # 20ms timeout for sequence
                        if self._msvcrt.kbhit():
                            next_ch = self._msvcrt.getch()
                            try:
                                next_char = next_ch.decode('latin-1')
                            except:
                                continue
                            self._input_buffer += next_char

                            # Check for SGR mouse sequence terminator (M or m)
                            if self._input_buffer.startswith('\x1b[<') and next_char in 'Mm':
                                break
                            # Check for other escape sequence terminators
                            if len(self._input_buffer) >= 3 and next_char.isalpha():
                                break
                            if next_char == '~':
                                break
                        else:
                            # Small sleep to avoid busy waiting
                            time.sleep(0.001)

                    # Parse SGR mouse event
                    if self._input_buffer.startswith('\x1b[<'):
                        mouse_event = self._parse_sgr_mouse(self._input_buffer)
                        self._input_buffer = ""
                        if mouse_event:
                            return mouse_event
                        # If parsing failed, treat as unknown
                        return None

                    # Parse arrow keys (ESC [ A/B/C/D)
                    if len(self._input_buffer) >= 3 and self._input_buffer[1] == '[':
                        arrow_char = self._input_buffer[2]
                        arrow_map = {'A': 'up', 'B': 'down', 'C': 'right', 'D': 'left'}
                        if arrow_char in arrow_map:
                            self._input_buffer = ""
                            return KeyEvent.arrow(arrow_map[arrow_char])

                    # Just escape key
                    self._input_buffer = ""
                    return KeyEvent.special('escape')

                # Handle special keys (Windows-specific extended keys)
                if ch in (b'\x00', b'\xe0'):
                    if self._msvcrt.kbhit():
                        special = self._msvcrt.getch()
                        try:
                            special_char = special.decode('latin-1')
                        except:
                            return KeyEvent.special('special')

                        # Windows arrow key codes
                        arrow_codes = {'H': 'up', 'P': 'down', 'K': 'left', 'M': 'right'}
                        if special_char in arrow_codes:
                            return KeyEvent.arrow(arrow_codes[special_char])
                        return KeyEvent.special(f'special-{ord(special_char)}')
                    return KeyEvent.special('special')

                # Decode regular character
                try:
                    char = ch.decode('latin-1')
                except:
                    continue

                # Handle Ctrl-C
                if char == '\x03':
                    return KeyEvent.special('ctrl-c')

                # Handle Tab
                if char == '\x09':
                    return KeyEvent.special('tab')

                # Handle Backspace (both ASCII BS and DEL)
                if char == '\x08' or char == '\x7f':
                    return KeyEvent.special('backspace')

                # Handle Enter
                if char == '\r':
                    return KeyEvent.special('enter')

                # Regular character
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

    def get_cursor_position(self) -> Optional[Tuple[int, int]]:
        """
        Get current cursor position by querying the terminal.

        Sends the DSR (Device Status Report) escape sequence and parses
        the CPR (Cursor Position Report) response.

        Returns:
            Tuple of (row, col) 1-indexed, or None if query fails.
        """
        # Send cursor position query
        self.write('\x1b[6n')
        self.flush()

        # Read response: ESC [ row ; col R
        response = ""
        start_time = time.time()
        timeout = 0.1  # 100ms timeout

        while (time.time() - start_time) < timeout:
            if self._msvcrt.kbhit():
                ch = self._msvcrt.getch()
                try:
                    char = ch.decode('latin-1')
                    response += char
                    # Response ends with 'R'
                    if char == 'R':
                        break
                except:
                    continue
            else:
                time.sleep(0.001)

        # Parse response: ESC [ row ; col R
        if response.startswith('\x1b[') and response.endswith('R'):
            try:
                coords = response[2:-1]  # Remove ESC [ and R
                parts = coords.split(';')
                if len(parts) == 2:
                    row = int(parts[0])
                    col = int(parts[1])
                    return (row, col)
            except (ValueError, IndexError):
                pass

        return None

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
