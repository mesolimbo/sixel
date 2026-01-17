# GUI Demo - Sixel Interactive Components

A demonstration of interactive GUI components rendered using sixel graphics in the terminal. Features mouse click interaction for buttons, checkboxes, radio buttons, text inputs, sliders, progress bars, and list boxes.

## Features

- **7 Demo Windows** showcasing different GUI components:
  - **Buttons**: Click to increment counter
  - **Checkboxes**: Toggle between checked/unchecked states
  - **Radio Buttons**: Mutually exclusive selection
  - **Text Input**: Click to focus, type to enter text
  - **Sliders**: Click to adjust value
  - **Progress Bars**: Animated progress indicators
  - **List Box**: Click to select items

- **Mouse Interaction**: Full mouse click support via ANSI mouse tracking (SGR extended mode)
- **Keyboard Support**: Text input, quit with 'q'
- **SOLID Architecture**: Clean, extensible component design
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Requirements

- Python 3.13+
- Terminal with sixel support:
  - iTerm2 (macOS)
  - mlterm
  - xterm (compiled with +sixel)
  - Windows Terminal (with appropriate settings)
- Terminal with mouse tracking support

## Installation

```bash
# Install dependencies
make install

# Or for development
make install-dev
```

## Usage

```bash
# Run the GUI demo
make run

# Or directly
python main.py
```

## Controls

- **Mouse Click**: Interact with components
- **Keyboard**: Type in focused text inputs
- **Backspace**: Delete characters in text inputs
- **Arrow Keys**: Move cursor in text inputs
- **Q**: Quit the application

## Architecture

The project follows SOLID principles:

- **Single Responsibility**: Each component manages only its own state
- **Open/Closed**: New components can be added without modifying existing code
- **Liskov Substitution**: All components are interchangeable via the Component base class
- **Interface Segregation**: Separate protocols for Clickable, Focusable, ValueHolder
- **Dependency Inversion**: High-level modules depend on abstractions

### File Structure

```
gui/
├── main.py           # Entry point and demo setup
├── app_loop.py       # Main event loop with mouse support
├── renderer.py       # Sixel rendering for all components
├── gui.py            # Component classes and state management
├── sixel.py          # Sixel encoding and drawing primitives
├── terminals/        # Cross-platform terminal abstraction
│   ├── __init__.py   # Factory and registry
│   ├── base.py       # Abstract interfaces with mouse support
│   ├── unix.py       # Unix/Linux/macOS implementation
│   └── windows.py    # Windows implementation
├── tests/            # Test suite
├── Makefile          # Build and test commands
└── Pipfile           # Dependencies
```

## Testing

```bash
# Run all tests
make test

# Run unit tests only
make unit

# Run with coverage
make coverage
```

## License

Part of the sixel project.
