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
)


def create_demo_gui() -> GUIState:
    """Create the demo GUI with 7 windows showcasing different components."""
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
        label="PRIMARY",
        on_click=lambda: print("Primary clicked!")
    ))

    # Secondary button
    btn_window.add_component(Button(
        x=start_x + 10,
        y=start_y + title_bar_height + 45,
        width=window_width - 20,
        height=28,
        label="SECONDARY",
        on_click=lambda: print("Secondary clicked!")
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

    return gui


def create_animation_callback(gui: GUIState):
    """Create an animation callback for the progress bars."""
    last_update = [time.time()]
    progress_values = [100.0, 65.0, 25.0]
    progress_directions = [1, 1, 1]

    def animate(delta_time: float) -> None:
        current = time.time()
        # Update every 100ms
        if current - last_update[0] < 0.1:
            return

        last_update[0] = current

        # Find the progress window (6th window, index 5)
        if len(gui.windows) > 5:
            progress_window = gui.windows[5]
            for i, component in enumerate(progress_window.components):
                if isinstance(component, ProgressBar) and i < 3:
                    # Animate the progress bar
                    progress_values[i] += progress_directions[i] * 2
                    if progress_values[i] >= 100:
                        progress_values[i] = 100
                        progress_directions[i] = -1
                    elif progress_values[i] <= 0:
                        progress_values[i] = 0
                        progress_directions[i] = 1
                    component.value = progress_values[i]

    return animate


def main():
    """Main entry point."""
    # Create terminal
    terminal = create_terminal()

    # Create GUI state with demo components
    gui = create_demo_gui()

    # Calculate dimensions for 7 windows
    # Each window is 160px wide with 10px gap
    # Total: 7 * 160 + 6 * 10 + 20 (margins) = 1200
    width = 1200
    height = 180  # Enough for windows + instructions

    # Create renderer
    renderer = GUIRenderer(width=width, height=height)

    # Create animation callback
    animate = create_animation_callback(gui)

    print("GUI Demo - Sixel Interactive Components")
    print("=" * 40)
    print("Click on components to interact")
    print("Press 'q' to quit")
    print()

    # Run the app loop
    run_app_loop(
        gui_state=gui,
        renderer=renderer,
        terminal=terminal,
        animation_callback=animate
    )


if __name__ == "__main__":
    main()
