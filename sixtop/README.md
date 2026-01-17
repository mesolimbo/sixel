# Sixtop - System Monitor with Sixel Graphics

A terminal-based system monitor rendered entirely using Sixel graphics. Displays real-time system metrics with updating graphs, similar to Activity Monitor or Task Manager.

![Sixtop Screenshot](demo/screenshot.png)

## Features

- **Five metric views** with real-time updating graphs:
  - **Energy Impact**: Battery status and energy usage
  - **CPU Load**: User/system CPU usage with thread and process counts
  - **I/O**: Disk read/write operations and data throughput
  - **Memory Pressure**: Memory usage breakdown
  - **Network**: Packet and data transfer statistics

- **Real-time graphs**: Historical data visualization that updates live
- **Cross-platform terminal support**: Works with any Sixel-capable terminal

## Requirements

- Python 3.13+
- A terminal that supports Sixel graphics:
  - **Windows**: Windows Terminal (with Sixel support enabled)
  - **macOS**: iTerm2
  - **Linux**: mlterm, xterm (with Sixel enabled), foot, kitty

## Quick Start

```bash
cd sixtop
make install
make run
```

## Installation

1. Make sure you have Python 3.13 and pipenv installed:

   ```bash
   pip install pipenv
   ```

2. Install dependencies:

   ```bash
   make install
   ```

   Or manually:

   ```bash
   pipenv install
   ```

## Usage

Run the monitor:

```bash
make run
```

Or manually:

```bash
pipenv run python main.py
```

See all available commands:

```bash
make help
```

## Controls

| Key | Action |
|-----|--------|
| `T` | Tab through views (Energy → CPU → I/O → Memory → Network) |
| `Q` / `Ctrl-C` | Quit |

## Project Structure

```
sixtop/
├── Makefile        # Build commands (install, run, clean, help)
├── Pipfile         # Python dependencies
├── main.py         # Entry point and configuration
├── app_loop.py     # Main application loop and input handling
├── renderer.py     # Sixel graphics rendering for each view
├── sixel.py        # Sixel graphics generation with graphs
├── metrics.py      # System metrics collection (CPU, memory, disk, network)
├── terminals/      # Cross-platform terminal abstraction
│   ├── __init__.py
│   ├── base.py     # Terminal interface definition
│   ├── windows.py  # Windows terminal implementation
│   └── unix.py     # Unix/Linux/macOS terminal implementation
├── tests/          # Unit tests
└── README.md       # This file
```

## Module Overview

- **sixel.py**: Sixel encoding with line graphs, bar graphs, text rendering, and color palette support. Extended for system monitoring visualizations.

- **metrics.py**: System metrics collection using psutil. Collects CPU, memory, disk I/O, network, and battery metrics with historical data for graphs.

- **renderer.py**: Renders the five metric views as Sixel graphics, including panels, labels, and real-time graphs.

- **app_loop.py**: Main application loop handling input, metrics updates, and rendering at appropriate intervals.

- **terminals/**: Platform-specific terminal handling for raw input and Sixel output.

## Metrics Collected

### CPU
- System/User/Idle CPU percentage
- Thread count
- Process count

### Memory
- Physical memory total/used
- Cached files
- Swap usage
- App memory / Wired memory / Compressed

### Disk I/O
- Total read/write operations
- Operations per second
- Data read/written totals
- Data throughput per second

### Network
- Total packets in/out
- Packets per second
- Data received/sent totals
- Data throughput per second

### Battery/Energy
- Charge percentage
- Time remaining
- Time on battery
- Power state (plugged/unplugged)

## Troubleshooting

### Display doesn't render correctly

Make sure your terminal supports Sixel graphics. Test with:

```bash
cat ../test.sixel
```

If you see colored bars, your terminal supports Sixel.

### Terminal is messed up after exiting

If the app crashes or exits unexpectedly, your terminal may be stuck in raw mode. Run:

```bash
reset
```

### "psutil not found" error

Install psutil:

```bash
pipenv install psutil
```

Or with pip:

```bash
pip install psutil
```
