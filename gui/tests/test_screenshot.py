"""
Screenshot tests for GUI demo.

These tests generate PNG images from the rendered GUI for visual inspection
and comparison. Requires PIL/Pillow to be installed.
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
    ComponentState,
)
from sixel import (
    create_pixel_buffer,
    fill_rect,
    draw_text,
    draw_rounded_rect_filled,
    pixels_to_png,
    COLOR_INDICES,
    PIL_AVAILABLE,
)


# Skip all tests if PIL is not available
pytestmark = pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")

# Fixed screenshots directory for CI artifacts
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"


@pytest.fixture
def screenshot_dir():
    """Create a fixed directory for screenshots (for CI artifacts)."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS_DIR


class TestScreenshotGeneration:
    """Tests that generate screenshot images."""

    def test_generate_button_screenshot(self, screenshot_dir):
        """Generate screenshot of button component."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Create a simple pixel buffer with a button
        width, height = 120, 40
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw a button
        draw_rounded_rect_filled(
            pixels, 10, 5, 100, 30, 4,
            COLOR_INDICES["button_bg"],
            COLOR_INDICES["button_border"]
        )
        draw_text(pixels, 30, 12, "BUTTON", COLOR_INDICES["text"], 1, True)

        # Save as PNG
        output_path = screenshot_dir / "button.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()
        assert img.size == (width, height)

    def test_generate_checkbox_screenshot(self, screenshot_dir):
        """Generate screenshot of checkbox component."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        width, height = 140, 30
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw checkbox box
        fill_rect(pixels, 5, 5, 20, 20, COLOR_INDICES["checkbox_checked"])
        draw_text(pixels, 30, 8, "CHECKED", COLOR_INDICES["text"], 1, True)

        output_path = screenshot_dir / "checkbox.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()

    def test_generate_slider_screenshot(self, screenshot_dir):
        """Generate screenshot of slider component."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        width, height = 150, 30
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw slider track
        fill_rect(pixels, 10, 12, 120, 6, COLOR_INDICES["slider_track"])
        # Draw filled portion
        fill_rect(pixels, 10, 12, 60, 6, COLOR_INDICES["slider_fill"])
        # Draw thumb
        fill_rect(pixels, 65, 5, 10, 20, COLOR_INDICES["slider_thumb"])

        output_path = screenshot_dir / "slider.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()

    def test_generate_progress_bar_screenshot(self, screenshot_dir):
        """Generate screenshot of progress bar component."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        width, height = 180, 30
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw progress bar
        fill_rect(pixels, 10, 5, 160, 20, COLOR_INDICES["progress_bg"])
        fill_rect(pixels, 10, 5, 112, 20, COLOR_INDICES["progress_fill"])  # 70%
        draw_text(pixels, 75, 8, "70%", COLOR_INDICES["text_highlight"], 1, False)

        output_path = screenshot_dir / "progress.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()


class TestFullGUIScreenshot:
    """Tests for full GUI screenshots."""

    def _create_demo_gui(self) -> GUIState:
        """Create a demo GUI matching the main.py demo."""
        gui = GUIState()

        # Layout constants
        window_width = 160
        window_height = 140
        window_gap = 10
        start_x = 10
        start_y = 10
        title_bar_height = 24

        # Window 1: Buttons
        btn_window = Window(
            title="BUTTONS", x=start_x, y=start_y,
            width=window_width, height=window_height
        )
        btn_window.add_component(Button(
            start_x + 10, start_y + title_bar_height + 10,
            window_width - 20, 28, "PRIMARY"
        ))
        btn_window.add_component(Button(
            start_x + 10, start_y + title_bar_height + 45,
            window_width - 20, 28, "SECONDARY"
        ))
        disabled_btn = Button(
            start_x + 10, start_y + title_bar_height + 80,
            window_width - 20, 28, "DISABLED"
        )
        disabled_btn.enabled = False
        btn_window.add_component(disabled_btn)
        gui.add_window(btn_window)

        # Window 2: Checkboxes
        cb_window = Window(
            title="CHECKBOXES",
            x=start_x + window_width + window_gap, y=start_y,
            width=window_width, height=window_height
        )
        cb_x = cb_window.x + 10
        cb_y_start = cb_window.y + title_bar_height + 10
        cb_window.add_component(Checkbox(cb_x, cb_y_start, window_width - 20, 24, "OPTION A", checked=True))
        cb_window.add_component(Checkbox(cb_x, cb_y_start + 30, window_width - 20, 24, "OPTION B", checked=False))
        cb_window.add_component(Checkbox(cb_x, cb_y_start + 60, window_width - 20, 24, "OPTION C", checked=True))
        gui.add_window(cb_window)

        # Window 3: Radio Buttons
        radio_window = Window(
            title="RADIO",
            x=start_x + 2 * (window_width + window_gap), y=start_y,
            width=window_width, height=window_height
        )
        radio_group = RadioGroup()
        radio_x = radio_window.x + 10
        radio_y_start = radio_window.y + title_bar_height + 10
        rb1 = RadioButton(radio_x, radio_y_start, window_width - 20, 24, "SMALL", selected=True)
        rb2 = RadioButton(radio_x, radio_y_start + 30, window_width - 20, 24, "MEDIUM")
        rb3 = RadioButton(radio_x, radio_y_start + 60, window_width - 20, 24, "LARGE")
        radio_group.add_button(rb1)
        radio_group.add_button(rb2)
        radio_group.add_button(rb3)
        radio_window.add_component(rb1)
        radio_window.add_component(rb2)
        radio_window.add_component(rb3)
        gui.add_window(radio_window)

        # Window 4: Text Input
        input_window = Window(
            title="TEXT INPUT",
            x=start_x + 3 * (window_width + window_gap), y=start_y,
            width=window_width, height=window_height
        )
        input_x = input_window.x + 10
        input_y_start = input_window.y + title_bar_height + 10
        input_window.add_component(TextInput(input_x, input_y_start, window_width - 20, 28, "NAME...", 15))
        input_window.add_component(TextInput(input_x, input_y_start + 38, window_width - 20, 28, "EMAIL...", 20))
        input_window.add_component(TextInput(input_x, input_y_start + 76, window_width - 20, 28, "PASSWORD...", 15))
        gui.add_window(input_window)

        # Window 5: Sliders
        slider_window = Window(
            title="SLIDERS",
            x=start_x + 4 * (window_width + window_gap), y=start_y,
            width=window_width, height=window_height
        )
        slider_x = slider_window.x + 10
        slider_y_start = slider_window.y + title_bar_height + 15
        slider_window.add_component(Slider(slider_x, slider_y_start, window_width - 50, 20, 0, 100, 25))
        slider_window.add_component(Slider(slider_x, slider_y_start + 35, window_width - 50, 20, 0, 100, 50))
        slider_window.add_component(Slider(slider_x, slider_y_start + 70, window_width - 50, 20, 0, 100, 75))
        gui.add_window(slider_window)

        # Window 6: Progress Bars
        progress_window = Window(
            title="PROGRESS",
            x=start_x + 5 * (window_width + window_gap), y=start_y,
            width=window_width, height=window_height
        )
        progress_x = progress_window.x + 10
        progress_y_start = progress_window.y + title_bar_height + 15
        progress_window.add_component(ProgressBar(progress_x, progress_y_start, window_width - 20, 24, 100, 100))
        progress_window.add_component(ProgressBar(progress_x, progress_y_start + 35, window_width - 20, 24, 65, 100))
        progress_window.add_component(ProgressBar(progress_x, progress_y_start + 70, window_width - 20, 24, 25, 100))
        gui.add_window(progress_window)

        # Window 7: List Box
        list_window = Window(
            title="LIST",
            x=start_x + 6 * (window_width + window_gap), y=start_y,
            width=window_width, height=window_height
        )
        list_x = list_window.x + 10
        list_y_start = list_window.y + title_bar_height + 10
        listbox = ListBox(list_x, list_y_start, window_width - 20, 100, ["ITEM 1", "ITEM 2", "ITEM 3", "ITEM 4", "ITEM 5"])
        listbox.select_index(0)
        list_window.add_component(listbox)
        gui.add_window(list_window)

        return gui

    def test_generate_full_gui_screenshot(self, screenshot_dir):
        """Generate screenshot of complete GUI demo."""
        # Create full demo GUI
        gui = self._create_demo_gui()

        # Create renderer with same dimensions as main.py
        renderer = GUIRenderer(width=1200, height=180)

        # Render to pixel buffer (we need to access internal rendering)
        pixels = create_pixel_buffer(1200, 180, COLOR_INDICES["background"])

        # Render each window
        for window in gui.windows:
            renderer._render_window(pixels, window)

        # Draw instructions
        renderer._draw_instructions(pixels)

        output_path = screenshot_dir / "gui_demo.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()
        assert img.size == (1200, 180)

    def test_generate_focused_button_screenshot(self, screenshot_dir):
        """Generate screenshot showing focused button state."""
        gui = GUIState()

        # Create buttons window with one focused
        btn_window = Window(title="BUTTONS", x=10, y=10, width=160, height=140)
        btn_window.active = True

        btn1 = Button(20, 44, 140, 28, "FOCUSED")
        btn1.state = ComponentState.FOCUSED
        btn_window.add_component(btn1)

        btn2 = Button(20, 79, 140, 28, "NORMAL")
        btn_window.add_component(btn2)

        btn3 = Button(20, 114, 140, 28, "PRESSED")
        btn3.state = ComponentState.PRESSED
        btn_window.add_component(btn3)

        gui.add_window(btn_window)

        renderer = GUIRenderer(width=180, height=170)
        pixels = create_pixel_buffer(180, 170, COLOR_INDICES["background"])

        for window in gui.windows:
            renderer._render_window(pixels, window)

        output_path = screenshot_dir / "gui_buttons_states.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()


class TestPNGExport:
    """Tests for PNG export functionality."""

    def test_png_export_dimensions(self, screenshot_dir):
        """Test that exported PNG has correct dimensions."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        width, height = 200, 150
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        output_path = screenshot_dir / "dimensions.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert img.size == (width, height)

    def test_png_export_without_path(self):
        """Test PNG export returning image without saving."""
        pixels = create_pixel_buffer(50, 50, COLOR_INDICES["background"])
        img = pixels_to_png(pixels)

        assert img is not None
        assert img.size == (50, 50)

    def test_png_export_empty_buffer(self):
        """Test PNG export with empty buffer."""
        pixels = create_pixel_buffer(0, 0)
        img = pixels_to_png(pixels)

        assert img is None
