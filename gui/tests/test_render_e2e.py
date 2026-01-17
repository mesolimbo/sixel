"""
End-to-end rendering tests for GUI demo.

These tests verify that the complete rendering pipeline works correctly.
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer import GUIRenderer
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
from sixel import SIXEL_START, SIXEL_END


class TestFullGUIRendering:
    """End-to-end tests for full GUI rendering."""

    def test_render_complete_demo(self):
        """Test rendering a complete GUI demo setup."""
        gui = GUIState()

        # Create multiple windows with various components
        # Window 1: Buttons
        btn_window = Window(title="BUTTONS", x=10, y=10, width=150, height=120)
        btn_window.add_component(Button(20, 40, 120, 25, "PRIMARY"))
        btn_window.add_component(Button(20, 70, 120, 25, "SECONDARY"))
        gui.add_window(btn_window)

        # Window 2: Checkboxes
        cb_window = Window(title="CHECKBOXES", x=170, y=10, width=150, height=120)
        cb_window.add_component(Checkbox(180, 40, 130, 24, "OPTION A", checked=True))
        cb_window.add_component(Checkbox(180, 70, 130, 24, "OPTION B", checked=False))
        gui.add_window(cb_window)

        # Window 3: Radio buttons
        radio_window = Window(title="RADIO", x=330, y=10, width=150, height=120)
        group = RadioGroup()
        rb1 = RadioButton(340, 40, 130, 24, "SMALL", selected=True)
        rb2 = RadioButton(340, 70, 130, 24, "LARGE")
        group.add_button(rb1)
        group.add_button(rb2)
        radio_window.add_component(rb1)
        radio_window.add_component(rb2)
        gui.add_window(radio_window)

        # Window 4: Text input
        input_window = Window(title="INPUT", x=490, y=10, width=150, height=120)
        input_window.add_component(TextInput(500, 40, 130, 28, placeholder="NAME..."))
        input_window.add_component(TextInput(500, 75, 130, 28, placeholder="EMAIL..."))
        gui.add_window(input_window)

        # Window 5: Sliders
        slider_window = Window(title="SLIDERS", x=650, y=10, width=150, height=120)
        slider_window.add_component(Slider(660, 40, 100, 20, value=25))
        slider_window.add_component(Slider(660, 70, 100, 20, value=75))
        gui.add_window(slider_window)

        # Window 6: Progress bars
        progress_window = Window(title="PROGRESS", x=810, y=10, width=150, height=120)
        progress_window.add_component(ProgressBar(820, 40, 130, 24, value=80))
        progress_window.add_component(ProgressBar(820, 75, 130, 24, value=30))
        gui.add_window(progress_window)

        # Render
        renderer = GUIRenderer(width=1000, height=160)
        frame = renderer.render_frame(gui)

        # Verify output structure
        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)

        # Verify reasonable output size
        assert len(frame) > 1000  # Should have substantial content

    def test_render_with_interactions(self):
        """Test rendering after user interactions."""
        gui = GUIState()

        window = Window(title="TEST", x=0, y=0, width=200, height=150)

        btn = Button(10, 30, 80, 25, "CLICK")
        cb = Checkbox(10, 60, 100, 24, "CHECK", checked=False)
        slider = Slider(10, 90, 100, 20, value=50)

        window.add_component(btn)
        window.add_component(cb)
        window.add_component(slider)
        gui.add_window(window)

        # Simulate interactions
        gui.handle_click(50, 42)  # Click button
        gui.handle_click(20, 72)  # Click checkbox
        gui.handle_click(60, 100)  # Click slider

        # Render
        renderer = GUIRenderer(width=250, height=180)
        frame = renderer.render_frame(gui)

        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)

        # Verify state changes
        assert btn.toggled is True
        assert cb.checked is True

    def test_render_focused_text_input(self):
        """Test rendering with focused text input showing cursor."""
        gui = GUIState()

        window = Window(title="TEXT", x=0, y=0, width=200, height=80)
        ti = TextInput(10, 30, 150, 28, placeholder="Type here...")
        window.add_component(ti)
        gui.add_window(window)

        # Focus and type
        ti.focus()
        ti.insert_char('H')
        ti.insert_char('e')
        ti.insert_char('l')
        ti.insert_char('l')
        ti.insert_char('o')

        renderer = GUIRenderer(width=220, height=100)
        frame = renderer.render_frame(gui)

        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)

    def test_render_listbox_with_selection(self):
        """Test rendering list box with selected item."""
        gui = GUIState()

        window = Window(title="LIST", x=0, y=0, width=150, height=150)
        lb = ListBox(10, 30, 130, 100, items=["Item 1", "Item 2", "Item 3", "Item 4"])
        lb.select_index(2)
        window.add_component(lb)
        gui.add_window(window)

        renderer = GUIRenderer(width=170, height=180)
        frame = renderer.render_frame(gui)

        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)


class TestRenderingPerformance:
    """Basic performance tests for rendering."""

    def test_render_time_reasonable(self):
        """Test that rendering completes in reasonable time."""
        import time

        gui = GUIState()

        # Create a moderately complex GUI
        for i in range(5):
            window = Window(
                title=f"WINDOW {i}",
                x=i * 160, y=10,
                width=150, height=120
            )
            window.add_component(Button(i * 160 + 10, 40, 100, 25, "BTN"))
            window.add_component(Checkbox(i * 160 + 10, 70, 100, 24, "CHK"))
            gui.add_window(window)

        renderer = GUIRenderer(width=850, height=160)

        start = time.time()
        for _ in range(10):
            frame = renderer.render_frame(gui)
        elapsed = time.time() - start

        # Should complete 10 frames in under 2 seconds
        assert elapsed < 2.0, f"Rendering too slow: {elapsed:.2f}s for 10 frames"
