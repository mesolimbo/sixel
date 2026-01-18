#!/usr/bin/env python3
"""
GUI Demo - Sixel-based interactive GUI components.

Demonstrates various GUI components rendered using sixel graphics
with mouse click interaction support.

Usage:
    python main.py [config.yaml]

    If a YAML config file is provided, the GUI will be built from that config.
    Otherwise, the built-in demo GUI will be used.

Requirements:
    - Terminal with sixel support (e.g., iTerm2, mlterm, xterm +sixel)
    - Terminal with mouse tracking support
"""

import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from terminals import create_terminal
from renderer import GUIRenderer
from app_loop import run_app_loop
from gui import (
    GUIState,
    Window,
    Button,
    Checkbox,
    RadioButton,
    RadioGroup,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    ImageDisplay,
)
from config import build_gui_from_config, apply_bindings, PLATFORM_SCALE
from sixel import IS_ITERM2


def create_demo_gui() -> GUIState:
    """Create the demo GUI with 8 windows showcasing different components."""
    gui = GUIState()

    # Layout constants with platform scaling (2x on macOS for better visibility)
    scale = PLATFORM_SCALE
    window_width = 240 * scale
    window_height = 210 * scale
    window_gap = 15 * scale
    start_x = 15 * scale
    start_y = 15 * scale
    title_bar_height = 36 * scale

    # Common scaled dimensions
    padding = 15 * scale
    btn_height = 42 * scale
    cb_height = 36 * scale
    slider_height = 30 * scale
    listbox_height = 150 * scale

    # ============================================================
    # Window 1: Buttons
    # ============================================================
    btn_window = Window(
        title="BUTTONS",
        x=start_x,
        y=start_y,
        width=window_width,
        height=window_height
    )

    # Primary button
    btn_window.add_component(Button(
        x=start_x + padding,
        y=start_y + title_bar_height + padding,
        width=window_width - 2 * padding,
        height=btn_height,
        label="PRIMARY"
    ))

    # Secondary button
    btn_window.add_component(Button(
        x=start_x + padding,
        y=start_y + title_bar_height + 68 * scale,
        width=window_width - 2 * padding,
        height=btn_height,
        label="SECONDARY"
    ))

    # Disabled button
    disabled_btn = Button(
        x=start_x + padding,
        y=start_y + title_bar_height + 121 * scale,
        width=window_width - 2 * padding,
        height=btn_height,
        label="DISABLED"
    )
    disabled_btn.enabled = False
    btn_window.add_component(disabled_btn)

    gui.add_window(btn_window)

    # ============================================================
    # Window 2: Checkboxes
    # ============================================================
    cb_window = Window(
        title="CHECKBOXES",
        x=start_x + window_width + window_gap,
        y=start_y,
        width=window_width,
        height=window_height
    )

    cb_x = cb_window.x + padding
    cb_y_start = cb_window.y + title_bar_height + padding

    cb_window.add_component(Checkbox(
        x=cb_x, y=cb_y_start,
        width=window_width - 2 * padding, height=cb_height,
        label="OPTION A",
        checked=True
    ))

    cb_window.add_component(Checkbox(
        x=cb_x, y=cb_y_start + 45 * scale,
        width=window_width - 2 * padding, height=cb_height,
        label="OPTION B",
        checked=False
    ))

    cb_window.add_component(Checkbox(
        x=cb_x, y=cb_y_start + 90 * scale,
        width=window_width - 2 * padding, height=cb_height,
        label="OPTION C",
        checked=True
    ))

    gui.add_window(cb_window)

    # ============================================================
    # Window 3: Radio Buttons
    # ============================================================
    radio_window = Window(
        title="RADIO",
        x=start_x + 2 * (window_width + window_gap),
        y=start_y,
        width=window_width,
        height=window_height
    )

    radio_group = RadioGroup()
    radio_x = radio_window.x + padding
    radio_y_start = radio_window.y + title_bar_height + padding

    rb1 = RadioButton(
        x=radio_x, y=radio_y_start,
        width=window_width - 2 * padding, height=cb_height,
        label="SMALL",
        selected=True
    )
    radio_group.add_button(rb1)
    radio_window.add_component(rb1)

    rb2 = RadioButton(
        x=radio_x, y=radio_y_start + 45 * scale,
        width=window_width - 2 * padding, height=cb_height,
        label="MEDIUM"
    )
    radio_group.add_button(rb2)
    radio_window.add_component(rb2)

    rb3 = RadioButton(
        x=radio_x, y=radio_y_start + 90 * scale,
        width=window_width - 2 * padding, height=cb_height,
        label="LARGE"
    )
    radio_group.add_button(rb3)
    radio_window.add_component(rb3)

    gui.add_window(radio_window)

    # ============================================================
    # Window 4: Text Input
    # ============================================================
    input_window = Window(
        title="TEXT INPUT",
        x=start_x + 3 * (window_width + window_gap),
        y=start_y,
        width=window_width,
        height=window_height
    )

    input_x = input_window.x + padding
    input_y_start = input_window.y + title_bar_height + padding

    input_window.add_component(TextInput(
        x=input_x, y=input_y_start,
        width=window_width - 2 * padding, height=btn_height,
        placeholder="NAME...",
        max_length=100
    ))

    input_window.add_component(TextInput(
        x=input_x, y=input_y_start + 57 * scale,
        width=window_width - 2 * padding, height=btn_height,
        placeholder="EMAIL...",
        max_length=100
    ))

    input_window.add_component(TextInput(
        x=input_x, y=input_y_start + 114 * scale,
        width=window_width - 2 * padding, height=btn_height,
        placeholder="PASSWORD...",
        max_length=100
    ))

    gui.add_window(input_window)

    # ============================================================
    # Window 5: Sliders (Row 2)
    # ============================================================
    row2_y = start_y + window_height + window_gap  # Second row y position

    slider_window = Window(
        title="SLIDERS",
        x=start_x,
        y=row2_y,
        width=window_width,
        height=window_height
    )

    slider_x = slider_window.x + padding
    slider_y_start = slider_window.y + title_bar_height + 22 * scale

    slider_window.add_component(Slider(
        x=slider_x, y=slider_y_start,
        width=window_width - 75 * scale, height=slider_height,
        min_value=0, max_value=100, value=25
    ))

    slider_window.add_component(Slider(
        x=slider_x, y=slider_y_start + 52 * scale,
        width=window_width - 75 * scale, height=slider_height,
        min_value=0, max_value=100, value=50
    ))

    slider_window.add_component(Slider(
        x=slider_x, y=slider_y_start + 104 * scale,
        width=window_width - 75 * scale, height=slider_height,
        min_value=0, max_value=100, value=75
    ))

    gui.add_window(slider_window)

    # ============================================================
    # Window 6: Progress Bars (Row 2)
    # ============================================================
    progress_window = Window(
        title="PROGRESS",
        x=start_x + 1 * (window_width + window_gap),
        y=row2_y,
        width=window_width,
        height=window_height
    )

    progress_x = progress_window.x + padding
    progress_y_start = progress_window.y + title_bar_height + 22 * scale

    progress_window.add_component(ProgressBar(
        x=progress_x, y=progress_y_start,
        width=window_width - 2 * padding, height=cb_height,
        value=100, max_value=100
    ))

    progress_window.add_component(ProgressBar(
        x=progress_x, y=progress_y_start + 52 * scale,
        width=window_width - 2 * padding, height=cb_height,
        value=65, max_value=100
    ))

    progress_window.add_component(ProgressBar(
        x=progress_x, y=progress_y_start + 104 * scale,
        width=window_width - 2 * padding, height=cb_height,
        value=25, max_value=100
    ))

    gui.add_window(progress_window)

    # ============================================================
    # Window 7: List Box (Row 2)
    # ============================================================
    list_window = Window(
        title="LIST",
        x=start_x + 2 * (window_width + window_gap),
        y=row2_y,
        width=window_width,
        height=window_height
    )

    list_x = list_window.x + padding
    list_y_start = list_window.y + title_bar_height + padding

    listbox = ListBox(
        x=list_x, y=list_y_start,
        width=window_width - 2 * padding, height=listbox_height,
        items=["ITEM 1", "ITEM 2", "ITEM 3", "ITEM 4", "ITEM 5"]
    )
    listbox.select_index(0)
    list_window.add_component(listbox)

    gui.add_window(list_window)

    # ============================================================
    # Window 8: Image Display (Row 2)
    # ============================================================
    image_window = Window(
        title="IMAGE",
        x=start_x + 3 * (window_width + window_gap),
        y=row2_y,
        width=window_width,
        height=window_height
    )

    image_x = image_window.x + padding
    image_y_start = image_window.y + title_bar_height + padding

    # Load the squirrel image
    image_path = str(Path(__file__).parent / "demo" / "squirel.png")
    image_display = ImageDisplay(
        x=image_x, y=image_y_start,
        width=window_width - 2 * padding, height=listbox_height,
        image_path=image_path
    )
    image_window.add_component(image_display)

    gui.add_window(image_window)

    return gui


def link_sliders_to_progress_bars(gui: GUIState):
    """Link sliders to corresponding progress bars."""
    # Window 5 (index 4) has sliders
    # Window 6 (index 5) has progress bars
    if len(gui.windows) <= 5:
        return

    slider_window = gui.windows[4]
    progress_window = gui.windows[5]

    sliders = [c for c in slider_window.components if isinstance(c, Slider)]
    progress_bars = [c for c in progress_window.components if isinstance(c, ProgressBar)]

    # Link each slider to corresponding progress bar
    for i, (slider, progress) in enumerate(zip(sliders, progress_bars)):
        # Set initial value
        progress.value = slider.value

        # Create callback to update progress bar when slider changes
        def make_callback(pb):
            def on_change(value):
                pb.value = value
            return on_change

        slider._on_change = make_callback(progress)


def create_sync_callback(gui: GUIState):
    """Create a callback that syncs sliders to progress bars each frame."""
    # Cache previous values to detect changes
    prev_values = {}

    def sync(delta_time: float) -> None:
        # Sync slider values to progress bars
        if len(gui.windows) > 5:
            slider_window = gui.windows[4]
            progress_window = gui.windows[5]

            sliders = [c for c in slider_window.components if isinstance(c, Slider)]
            progress_bars = [c for c in progress_window.components if isinstance(c, ProgressBar)]

            changed = False
            for i, (slider, progress) in enumerate(zip(sliders, progress_bars)):
                if prev_values.get(i) != slider.value:
                    progress.value = slider.value
                    prev_values[i] = slider.value
                    changed = True

            # Only mark progress window dirty if values changed
            if changed:
                gui.mark_dirty(5)  # Progress window is at index 5

    return sync


def main():
    """Main entry point."""
    # Create terminal
    terminal = create_terminal()

    # Check for config file argument
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        # Resolve relative paths
        if not Path(config_path).is_absolute():
            config_path = str(Path.cwd() / config_path)

    if config_path and Path(config_path).exists():
        # Load GUI from YAML configuration
        gui, gui_config, width, height = build_gui_from_config(config_path)
        sync_callback = apply_bindings(gui_config)
        print(f"Loaded GUI from: {config_path}")
    else:
        # Use built-in demo GUI
        gui = create_demo_gui()
        link_sliders_to_progress_bars(gui)
        sync_callback = create_sync_callback(gui)

        # Calculate dimensions for 2 rows of 4 windows (with platform scaling)
        # Each window is 240px wide with 15px gap (scaled on macOS)
        # Width: 4 * 240 + 3 * 15 + 30 (margins) = 1035
        # Height: 2 * 210 + 1 * 15 + 30 (margins) + 30 (instructions) = 495
        scale = PLATFORM_SCALE
        width = 1035 * scale
        height = 495 * scale

        if config_path:
            print(f"Config file not found: {config_path}")
            print("Using built-in demo GUI")

    # Create renderer
    renderer = GUIRenderer(width=width, height=height)

    # Print instructions
    print("GUI Demo - Interactive Terminal Graphics")
    print("=" * 50)
    if IS_ITERM2:
        print("Rendering: iTerm2 inline image protocol (optimized)")
    else:
        print("Rendering: Sixel graphics protocol")
    print("Tab: Next window | Up/Down: Select item | Left/Right: Adjust")
    print("Space: Activate | q: Quit (when not in text field)")
    print()

    # Run the app loop
    run_app_loop(
        gui_state=gui,
        renderer=renderer,
        terminal=terminal,
        animation_callback=sync_callback
    )


if __name__ == "__main__":
    main()
