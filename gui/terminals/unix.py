"""
Unix terminal implementation with mouse support.

Uses termios for raw mode and select for non-blocking input.
Supports mouse tracking via ANSI escape sequences.
Works on Linux, macOS, and other Unix-like systems.
"""

import os
import select
import shutil
import sys
import termios
import tty
from typing import Optional, Tuple, List, Union

from .base import (
    Terminal, KeyEvent, MouseEvent, MouseButton,
    MouseEventType, InputEvent
)


class UnixTerminal(Terminal):
    """
    Terminal implementation for Unix-like systems with mouse support.

    Uses termios for terminal mode control, select for non-blocking
    input handling, and ANSI escape sequences for mouse tracking.
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

    # Mouse tracking (SGR extended mode for better compatibility)
    MOUSE_ON = "\x1b[?1000h\x1b[?1006h"  # Enable basic + SGR extended
    MOUSE_OFF = "\x1b[?1006l\x1b[?1000l"  # Disable SGR extended + basic

    def __init__(self):
        self._is_raw: bool = False
        self._mouse_enabled: bool = False
        self._old_settings: Optional[List] = None
        self._fd = sys.stdin.fileno()
        self._is_macos: bool = sys.platform == 'darwin'

    @property
    def is_raw(self) -> bool:
        """Check if terminal is in raw mode."""
        return self._is_raw

    @property
    def mouse_enabled(self) -> bool:
        """Check if mouse tracking is enabled."""
        return self._mouse_enabled

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
        """
        Parse SGR-format mouse event.
        Format: CSI < Cb ; Cx ; Cy M (press) or m (release)
        """
        try:
            # Remove CSI and '<' prefix
            if seq.startswith('\x1b[<'):
                seq = seq[3:]

            # Find terminator (M for press, m for release)
            is_release = seq.endswith('m')
            seq = seq[:-1]  # Remove terminator

            parts = seq.split(';')
            if len(parts) != 3:
                return None

            button_code = int(parts[0])
            x = int(parts[1]) - 1  # Convert to 0-indexed
            y = int(parts[2]) - 1

            # Decode button
            if is_release:
                return MouseEvent.release(x, y)

            # Check for scroll
            if button_code >= 64:
                if button_code == 64:
                    return MouseEvent(
                        MouseEventType.PRESS,
                        MouseButton.SCROLL_UP, x, y
                    )
                elif button_code == 65:
                    return MouseEvent(
                        MouseEventType.PRESS,
                        MouseButton.SCROLL_DOWN, x, y
                    )

            # Regular button
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

    def _read_escape_sequence(self) -> str:
        """Read a complete escape sequence from input."""
        seq = '\x1b'

        # Use longer timeout on macOS for reliable escape sequence reading
        esc_timeout = 0.1 if self._is_macos else 0.05

        # Read next character using os.read for more reliable raw byte reading
        rlist, _, _ = select.select([self._fd], [], [], esc_timeout)
        if not rlist:
            return seq

        data = os.read(self._fd, 1)
        if not data:
            return seq
        char = data.decode('utf-8', errors='replace')
        seq += char

        # Handle both CSI sequences (ESC [) and SS3 sequences (ESC O)
        if char == '[':
            # CSI sequence - read until we hit a letter
            while True:
                rlist, _, _ = select.select([self._fd], [], [], esc_timeout)
                if not rlist:
                    break
                data = os.read(self._fd, 1)
                if not data:
                    break
                char = data.decode('utf-8', errors='replace')
                seq += char
                # Letters (except for '<' which starts SGR mouse) terminate CSI
                if char.isalpha() or char == '~':
                    break
                # SGR mouse sequence continues until M or m
                if seq.startswith('\x1b[<') and char in 'Mm':
                    break
        elif char == 'O':
            # SS3 sequence - some terminals (especially macOS) use this for arrows
            rlist, _, _ = select.select([self._fd], [], [], esc_timeout)
            if rlist:
                data = os.read(self._fd, 1)
                if data:
                    char = data.decode('utf-8', errors='replace')
                    seq += char

        return seq

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        """Read a key from input with optional timeout (ignores mouse events)."""
        event = self.read_input(timeout)
        if isinstance(event, KeyEvent):
            return event
        return None

    def read_input(self, timeout: float = 0.0) -> Optional[InputEvent]:
        """
        Read any input (key or mouse) with optional timeout.

        Uses select for non-blocking input check and os.read for
        consistent raw byte reading (important for escape sequences on macOS).
        """
        # Use select to check if input is available
        if timeout == 0:
            rlist, _, _ = select.select([self._fd], [], [], 0)
        else:
            rlist, _, _ = select.select([self._fd], [], [], timeout)

        if not rlist:
            return None

        # Read the first character using os.read for consistent raw byte handling
        data = os.read(self._fd, 1)
        if not data:
            return None
        char = data.decode('utf-8', errors='replace')

        # Handle escape sequences
        if char == '\x1b':
            seq = self._read_escape_sequence()

            # Check for SGR mouse event
            if seq.startswith('\x1b[<'):
                mouse_event = self._parse_sgr_mouse(seq)
                if mouse_event:
                    return mouse_event
                return KeyEvent.special('unknown-mouse')

            # Check for arrow keys - both CSI (ESC [) and SS3 (ESC O) formats
            if len(seq) >= 3:
                arrow_map = {
                    'A': 'up',
                    'B': 'down',
                    'C': 'right',
                    'D': 'left',
                }
                # CSI format: ESC [ A/B/C/D
                if seq[1] == '[':
                    if seq[2] in arrow_map:
                        return KeyEvent.arrow(arrow_map[seq[2]])
                    # Shift+Tab sends ESC [ Z
                    if seq[2] == 'Z':
                        return KeyEvent.special('shift-tab')
                    return KeyEvent.special(f'csi-{seq[2]}')
                # SS3 format: ESC O A/B/C/D (used by some macOS terminals)
                elif seq[1] == 'O':
                    if seq[2] in arrow_map:
                        return KeyEvent.arrow(arrow_map[seq[2]])
                    return KeyEvent.special(f'ss3-{seq[2]}')

            return KeyEvent.special('escape')

        # Handle Ctrl-C
        if char == '\x03':
            return KeyEvent.special('ctrl-c')

        # Handle Tab
        if char == '\x09':
            return KeyEvent.special('tab')

        # Handle Backspace
        if char == '\x7f':
            return KeyEvent.special('backspace')

        # Handle Enter/Return
        if char == '\r' or char == '\n':
            return KeyEvent.special('enter')

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
        fd = sys.stdin.fileno()

        # Wait for response with timeout
        ready, _, _ = select.select([fd], [], [], 0.1)
        if not ready:
            return None

        while True:
            ready, _, _ = select.select([fd], [], [], 0.01)
            if ready:
                char = os.read(fd, 1).decode('latin-1', errors='ignore')
                response += char
                if char == 'R':
                    break
            else:
                break

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
