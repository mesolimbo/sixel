#!/usr/bin/env python3
"""
GUI Demo - Sixel-based interactive GUI components.

Demonstrates various GUI components rendered using sixel graphics
with mouse click interaction support.

Usage:
    python main.py

Requirements:
    - Terminal with sixel support (e.g., iTerm2, mlterm, xterm +sixel)
    - Terminal with mouse tracking support
"""

import sys
import time
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


def create_demo_gui() -> GUIState:
    """Create the demo GUI with 8 windows showcasing different components."""
    gui = GUIState()

    # Layout constants
    window_width = 160
    window_height = 140
    window_gap = 10
    start_x = 10
    start_y = 10
    title_bar_height = 24

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
        x=start_x + 10,
        y=start_y + title_bar_height + 10,
        width=window_width - 20,
        height=28,
        label="PRIMARY"
    ))

    # Secondary button
    btn_window.add_component(Button(
        x=start_x + 10,
        y=start_y + title_bar_height + 45,
        width=window_width - 20,
        height=28,
        label="SECONDARY"
    ))

    # Disabled button
    disabled_btn = Button(
        x=start_x + 10,
        y=start_y + title_bar_height + 80,
        width=window_width - 20,
        height=28,
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

    cb_x = cb_window.x + 10
    cb_y_start = cb_window.y + title_bar_height + 10

    cb_window.add_component(Checkbox(
        x=cb_x, y=cb_y_start,
        width=window_width - 20, height=24,
        label="OPTION A",
        checked=True
    ))

    cb_window.add_component(Checkbox(
        x=cb_x, y=cb_y_start + 30,
        width=window_width - 20, height=24,
        label="OPTION B",
        checked=False
    ))

    cb_window.add_component(Checkbox(
        x=cb_x, y=cb_y_start + 60,
        width=window_width - 20, height=24,
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
    radio_x = radio_window.x + 10
    radio_y_start = radio_window.y + title_bar_height + 10

    rb1 = RadioButton(
        x=radio_x, y=radio_y_start,
        width=window_width - 20, height=24,
        label="SMALL",
        selected=True
    )
    radio_group.add_button(rb1)
    radio_window.add_component(rb1)

    rb2 = RadioButton(
        x=radio_x, y=radio_y_start + 30,
        width=window_width - 20, height=24,
        label="MEDIUM"
    )
    radio_group.add_button(rb2)
    radio_window.add_component(rb2)

    rb3 = RadioButton(
        x=radio_x, y=radio_y_start + 60,
        width=window_width - 20, height=24,
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

    input_x = input_window.x + 10
    input_y_start = input_window.y + title_bar_height + 10

    input_window.add_component(TextInput(
        x=input_x, y=input_y_start,
        width=window_width - 20, height=28,
        placeholder="NAME...",
        max_length=15
    ))

    input_window.add_component(TextInput(
        x=input_x, y=input_y_start + 38,
        width=window_width - 20, height=28,
        placeholder="EMAIL...",
        max_length=20
    ))

    input_window.add_component(TextInput(
        x=input_x, y=input_y_start + 76,
        width=window_width - 20, height=28,
        placeholder="PASSWORD...",
        max_length=15
    ))

    gui.add_window(input_window)

    # ============================================================
    # Window 5: Sliders
    # ============================================================
    slider_window = Window(
        title="SLIDERS",
        x=start_x + 4 * (window_width + window_gap),
        y=start_y,
        width=window_width,
        height=window_height
    )

    slider_x = slider_window.x + 10
    slider_y_start = slider_window.y + title_bar_height + 15

    slider_window.add_component(Slider(
        x=slider_x, y=slider_y_start,
        width=window_width - 50, height=20,
        min_value=0, max_value=100, value=25
    ))

    slider_window.add_component(Slider(
        x=slider_x, y=slider_y_start + 35,
        width=window_width - 50, height=20,
        min_value=0, max_value=100, value=50
    ))

    slider_window.add_component(Slider(
        x=slider_x, y=slider_y_start + 70,
        width=window_width - 50, height=20,
        min_value=0, max_value=100, value=75
    ))

    gui.add_window(slider_window)

    # ============================================================
    # Window 6: Progress Bars
    # ============================================================
    progress_window = Window(
        title="PROGRESS",
        x=start_x + 5 * (window_width + window_gap),
        y=start_y,
        width=window_width,
        height=window_height
    )

    progress_x = progress_window.x + 10
    progress_y_start = progress_window.y + title_bar_height + 15

    progress_window.add_component(ProgressBar(
        x=progress_x, y=progress_y_start,
        width=window_width - 20, height=24,
        value=100, max_value=100
    ))

    progress_window.add_component(ProgressBar(
        x=progress_x, y=progress_y_start + 35,
        width=window_width - 20, height=24,
        value=65, max_value=100
    ))

    progress_window.add_component(ProgressBar(
        x=progress_x, y=progress_y_start + 70,
        width=window_width - 20, height=24,
        value=25, max_value=100
    ))

    gui.add_window(progress_window)

    # ============================================================
    # Window 7: List Box
    # ============================================================
    list_window = Window(
        title="LIST",
        x=start_x + 6 * (window_width + window_gap),
        y=start_y,
        width=window_width,
        height=window_height
    )

    list_x = list_window.x + 10
    list_y_start = list_window.y + title_bar_height + 10

    listbox = ListBox(
        x=list_x, y=list_y_start,
        width=window_width - 20, height=100,
        items=["ITEM 1", "ITEM 2", "ITEM 3", "ITEM 4", "ITEM 5"]
    )
    listbox.select_index(0)
    list_window.add_component(listbox)

    gui.add_window(list_window)

    # ============================================================
    # Window 8: Image Display
    # ============================================================
    image_window = Window(
        title="IMAGE",
        x=start_x + 7 * (window_width + window_gap),
        y=start_y,
        width=window_width,
        height=window_height
    )

    image_x = image_window.x + 10
    image_y_start = image_window.y + title_bar_height + 5

    # Load the squirrel image
    image_path = str(Path(__file__).parent / "demo" / "squirel.png")
    image_display = ImageDisplay(
        x=image_x, y=image_y_start,
        width=window_width - 20, height=100,
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
    def sync(delta_time: float) -> None:
        # Sync slider values to progress bars
        if len(gui.windows) > 5:
            slider_window = gui.windows[4]
            progress_window = gui.windows[5]

            sliders = [c for c in slider_window.components if isinstance(c, Slider)]
            progress_bars = [c for c in progress_window.components if isinstance(c, ProgressBar)]

            for slider, progress in zip(sliders, progress_bars):
                progress.value = slider.value

    return sync


def main():
    """Main entry point."""
    # Create terminal
    terminal = create_terminal()

    # Create GUI state with demo components
    gui = create_demo_gui()

    # Link sliders to progress bars
    link_sliders_to_progress_bars(gui)

    # Calculate dimensions for 8 windows
    # Each window is 160px wide with 10px gap
    # Total: 8 * 160 + 7 * 10 + 20 (margins) = 1370
    width = 1370
    height = 180  # Enough for windows + instructions

    # Create renderer
    renderer = GUIRenderer(width=width, height=height)

    # Create sync callback to update progress bars from sliders
    sync_callback = create_sync_callback(gui)

    # Print instructions
    print("GUI Demo - Sixel Interactive Components")
    print("=" * 50)
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
