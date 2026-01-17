"""
Terminals package - Cross-platform terminal abstraction for GUI demo.

This package provides a unified interface for terminal operations across
different platforms (Unix/Linux/macOS, Windows) with mouse support.

Usage:
    from terminals import create_terminal, Terminal

    # Auto-detect and create the appropriate terminal
    terminal = create_terminal()

    # Use with context manager for automatic cleanup
    with terminal:
        terminal.write("Hello, World!")
        event = terminal.read_input(timeout=1.0)
"""

import sys
from typing import Dict, Type, Optional

from .base import Terminal, KeyEvent, KeyType, MouseEvent, InputEvent

# Registry of available terminal implementations
TERMINAL_REGISTRY: Dict[str, Type[Terminal]] = {}


def _register_terminals() -> None:
    """Register platform-specific terminal implementations."""
    global TERMINAL_REGISTRY

    if sys.platform == 'win32':
        from .windows import WindowsTerminal
        TERMINAL_REGISTRY['windows'] = WindowsTerminal
    else:
        # Unix-like systems (Linux, macOS, BSD, etc.)
        from .unix import UnixTerminal
        TERMINAL_REGISTRY['unix'] = UnixTerminal
        TERMINAL_REGISTRY['linux'] = UnixTerminal
        TERMINAL_REGISTRY['darwin'] = UnixTerminal  # macOS


def create_terminal(platform: Optional[str] = None) -> Terminal:
    """
    Create a terminal instance appropriate for the current platform.

    Args:
        platform: Optional platform override. If None, auto-detects.
                 Valid values: 'windows', 'unix', 'linux', 'darwin'

    Returns:
        A Terminal instance for the specified or detected platform.

    Raises:
        RuntimeError: If no suitable terminal implementation is found.
    """
    # Ensure terminals are registered
    if not TERMINAL_REGISTRY:
        _register_terminals()

    # Determine which implementation to use
    if platform is not None:
        key = platform.lower()
    elif sys.platform == 'win32':
        key = 'windows'
    elif sys.platform == 'darwin':
        key = 'darwin'
    else:
        key = 'unix'

    if key not in TERMINAL_REGISTRY:
        available = ', '.join(TERMINAL_REGISTRY.keys())
        raise RuntimeError(
            f"No terminal implementation for '{key}'. "
            f"Available: {available}"
        )

    return TERMINAL_REGISTRY[key]()


def register_terminal(name: str, terminal_class: Type[Terminal]) -> None:
    """
    Register a custom terminal implementation.

    Args:
        name: Identifier for the terminal type
        terminal_class: Class implementing the Terminal interface
    """
    if not TERMINAL_REGISTRY:
        _register_terminals()
    TERMINAL_REGISTRY[name] = terminal_class


# Initialize registry on import
_register_terminals()

# Public API
__all__ = [
    'Terminal',
    'KeyEvent',
    'KeyType',
    'MouseEvent',
    'InputEvent',
    'create_terminal',
    'register_terminal',
    'TERMINAL_REGISTRY',
]
