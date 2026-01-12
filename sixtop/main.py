#!/usr/bin/env python3
"""
Sixtop - System Monitor with Sixel Graphics.

A terminal-based system monitor rendered using Sixel graphics.
Displays CPU, memory, disk I/O, network, and battery metrics
with real-time updating graphs.

Controls:
- T: Tab between metric views
- Q or Ctrl-C: Quit

Requirements:
- A terminal that supports Sixel graphics (Windows Terminal, iTerm2, etc.)
- Python 3.13+
- psutil
"""

import sys

from app_loop import run_app_loop, show_startup_message
from metrics import MetricsCollector
from renderer import MetricsRenderer, MetricView
from terminals import create_terminal


# Display settings
FRAME_WIDTH = 600
FRAME_HEIGHT = 180


def main() -> None:
    """Entry point for sixtop."""
    # Create terminal instance for the current platform
    terminal = create_terminal()

    # Initialize metrics collector
    try:
        metrics = MetricsCollector()
    except RuntimeError as e:
        print(f"Error: {e}")
        print("Please install psutil: pip install psutil")
        sys.exit(1)

    # Create renderer
    renderer = MetricsRenderer(FRAME_WIDTH, FRAME_HEIGHT)

    # Start with CPU view
    renderer.current_view = MetricView.CPU

    # Show startup message and wait for space
    if not show_startup_message(terminal, renderer):
        print("Goodbye!")
        return

    # Run the main loop
    run_app_loop(metrics, renderer, terminal)

    # Final message
    print("\nSixtop exited. Thanks for using!")


if __name__ == "__main__":
    main()
