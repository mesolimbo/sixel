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
    ImageDisplay,
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

        # Create a simple pixel buffer with a button (taller for proper display)
        width, height = 140, 55
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw a button with rounded corners
        draw_rounded_rect_filled(
            pixels, 10, 10, 120, 35, 6,
            COLOR_INDICES["button_bg"],
            COLOR_INDICES["button_border"]
        )
        draw_text(pixels, 35, 20, "BUTTON", COLOR_INDICES["text"], 1, True)

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

        width, height = 160, 36
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw slider track with rounded corners
        draw_rounded_rect_filled(pixels, 10, 14, 130, 8, 4, COLOR_INDICES["slider_track"])
        # Draw filled portion with rounded corners
        draw_rounded_rect_filled(pixels, 10, 14, 65, 8, 4, COLOR_INDICES["slider_fill"])
        # Draw thumb with rounded corners
        draw_rounded_rect_filled(pixels, 70, 6, 15, 24, 4, COLOR_INDICES["slider_thumb"])

        output_path = screenshot_dir / "slider.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()

    def test_generate_progress_bar_screenshot(self, screenshot_dir):
        """Generate screenshot of progress bar component."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        width, height = 190, 40
        pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])

        # Draw progress bar with rounded corners
        draw_rounded_rect_filled(pixels, 10, 8, 170, 24, 6, COLOR_INDICES["progress_bg"])
        draw_rounded_rect_filled(pixels, 10, 8, 119, 24, 6, COLOR_INDICES["progress_fill"])  # 70%
        draw_text(pixels, 80, 13, "70%", COLOR_INDICES["text_highlight"], 1, False)

        output_path = screenshot_dir / "progress.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()

    def test_generate_image_display_screenshot(self, screenshot_dir):
        """Generate screenshot of image display component."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Create GUI with image display (1.5x scale)
        gui = GUIState()
        window = Window(title="IMAGE", x=15, y=15, width=240, height=210)

        # Load the squirrel demo image
        demo_dir = Path(__file__).parent.parent / "demo"
        image_path = str(demo_dir / "squirel.png")
        img_display = ImageDisplay(
            x=30, y=66, width=210, height=150,
            image_path=image_path
        )
        window.add_component(img_display)
        gui.add_window(window)

        # Render
        renderer = GUIRenderer(width=270, height=240)
        pixels = create_pixel_buffer(270, 240, COLOR_INDICES["background"])
        for w in gui.windows:
            renderer._render_window(pixels, w)

        output_path = screenshot_dir / "image_display.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()


class TestFullGUIScreenshot:
    """Tests for full GUI screenshots."""

    def _create_demo_gui(self) -> GUIState:
        """Create a demo GUI matching the main.py demo (2 rows of 4 windows)."""
        gui = GUIState()

        # Layout constants (1.5x scale for better display)
        window_width = 240
        window_height = 210
        window_gap = 15
        start_x = 15
        start_y = 15
        title_bar_height = 36

        def get_window_pos(index: int):
            """Get window position for 2-row, 4-column layout."""
            row = index // 4
            col = index % 4
            x = start_x + col * (window_width + window_gap)
            y = start_y + row * (window_height + window_gap)
            return x, y

        # Window 1: Buttons (row 0, col 0)
        wx, wy = get_window_pos(0)
        btn_window = Window(title="BUTTONS", x=wx, y=wy, width=window_width, height=window_height)
        btn_window.add_component(Button(wx + 15, wy + title_bar_height + 15, window_width - 30, 42, "PRIMARY"))
        btn_window.add_component(Button(wx + 15, wy + title_bar_height + 68, window_width - 30, 42, "SECONDARY"))
        disabled_btn = Button(wx + 15, wy + title_bar_height + 121, window_width - 30, 42, "DISABLED")
        disabled_btn.enabled = False
        btn_window.add_component(disabled_btn)
        gui.add_window(btn_window)

        # Window 2: Checkboxes (row 0, col 1)
        wx, wy = get_window_pos(1)
        cb_window = Window(title="CHECKBOXES", x=wx, y=wy, width=window_width, height=window_height)
        cb_y = wy + title_bar_height + 15
        cb_window.add_component(Checkbox(wx + 15, cb_y, window_width - 30, 36, "OPTION A", checked=True))
        cb_window.add_component(Checkbox(wx + 15, cb_y + 45, window_width - 30, 36, "OPTION B", checked=False))
        cb_window.add_component(Checkbox(wx + 15, cb_y + 90, window_width - 30, 36, "OPTION C", checked=True))
        gui.add_window(cb_window)

        # Window 3: Radio Buttons (row 0, col 2)
        wx, wy = get_window_pos(2)
        radio_window = Window(title="RADIO", x=wx, y=wy, width=window_width, height=window_height)
        radio_group = RadioGroup()
        radio_y = wy + title_bar_height + 15
        rb1 = RadioButton(wx + 15, radio_y, window_width - 30, 36, "SMALL", selected=True)
        rb2 = RadioButton(wx + 15, radio_y + 45, window_width - 30, 36, "MEDIUM")
        rb3 = RadioButton(wx + 15, radio_y + 90, window_width - 30, 36, "LARGE")
        radio_group.add_button(rb1)
        radio_group.add_button(rb2)
        radio_group.add_button(rb3)
        radio_window.add_component(rb1)
        radio_window.add_component(rb2)
        radio_window.add_component(rb3)
        gui.add_window(radio_window)

        # Window 4: Text Input (row 0, col 3)
        wx, wy = get_window_pos(3)
        input_window = Window(title="TEXT INPUT", x=wx, y=wy, width=window_width, height=window_height)
        input_y = wy + title_bar_height + 15
        input_window.add_component(TextInput(wx + 15, input_y, window_width - 30, 42, "NAME...", 100))
        input_window.add_component(TextInput(wx + 15, input_y + 57, window_width - 30, 42, "EMAIL...", 100))
        input_window.add_component(TextInput(wx + 15, input_y + 114, window_width - 30, 42, "PASSWORD...", 100))
        gui.add_window(input_window)

        # Window 5: Sliders (row 1, col 0)
        wx, wy = get_window_pos(4)
        slider_window = Window(title="SLIDERS", x=wx, y=wy, width=window_width, height=window_height)
        slider_y = wy + title_bar_height + 22
        slider_window.add_component(Slider(wx + 15, slider_y, window_width - 75, 30, 0, 100, 25))
        slider_window.add_component(Slider(wx + 15, slider_y + 52, window_width - 75, 30, 0, 100, 50))
        slider_window.add_component(Slider(wx + 15, slider_y + 104, window_width - 75, 30, 0, 100, 75))
        gui.add_window(slider_window)

        # Window 6: Progress Bars (row 1, col 1)
        wx, wy = get_window_pos(5)
        progress_window = Window(title="PROGRESS", x=wx, y=wy, width=window_width, height=window_height)
        progress_y = wy + title_bar_height + 22
        progress_window.add_component(ProgressBar(wx + 15, progress_y, window_width - 30, 36, 100, 100))
        progress_window.add_component(ProgressBar(wx + 15, progress_y + 52, window_width - 30, 36, 65, 100))
        progress_window.add_component(ProgressBar(wx + 15, progress_y + 104, window_width - 30, 36, 25, 100))
        gui.add_window(progress_window)

        # Window 7: List Box (row 1, col 2)
        wx, wy = get_window_pos(6)
        list_window = Window(title="LIST", x=wx, y=wy, width=window_width, height=window_height)
        listbox = ListBox(wx + 15, wy + title_bar_height + 15, window_width - 30, 150,
                         ["ITEM 1", "ITEM 2", "ITEM 3", "ITEM 4", "ITEM 5"])
        listbox.select_index(0)
        list_window.add_component(listbox)
        gui.add_window(list_window)

        # Window 8: Image Display (row 1, col 3)
        wx, wy = get_window_pos(7)
        image_window = Window(title="IMAGE", x=wx, y=wy, width=window_width, height=window_height)
        demo_dir = Path(__file__).parent.parent / "demo"
        image_path = str(demo_dir / "squirel.png")
        img_display = ImageDisplay(
            x=wx + 15, y=wy + title_bar_height + 15,
            width=window_width - 30, height=150,
            image_path=image_path
        )
        image_window.add_component(img_display)
        gui.add_window(image_window)

        return gui

    def test_generate_full_gui_screenshot(self, screenshot_dir):
        """Generate screenshot of complete GUI demo (2 rows of 4 windows)."""
        # Create full demo GUI
        gui = self._create_demo_gui()

        # Create renderer with dimensions for 2 rows x 4 columns
        # Width: 15 + 4*(240+15) = 1035px
        # Height: 15 + 2*(210+15) + 30 (instructions) = 495px
        canvas_width = 1035
        canvas_height = 495
        renderer = GUIRenderer(width=canvas_width, height=canvas_height)

        # Render to pixel buffer
        pixels = create_pixel_buffer(canvas_width, canvas_height, COLOR_INDICES["background"])

        # Render each window
        for window in gui.windows:
            renderer._render_window(pixels, window)

        # Draw instructions
        renderer._draw_instructions(pixels)

        output_path = screenshot_dir / "gui_demo.png"
        img = pixels_to_png(pixels, str(output_path))

        assert img is not None
        assert output_path.exists()
        assert img.size == (canvas_width, canvas_height)

    def test_generate_focused_button_screenshot(self, screenshot_dir):
        """Generate screenshot showing focused button state."""
        gui = GUIState()

        # Create buttons window with one focused (1.5x scale)
        btn_window = Window(title="BUTTONS", x=15, y=15, width=240, height=210)
        btn_window.active = True

        btn1 = Button(30, 66, 210, 42, "FOCUSED")
        btn1.state = ComponentState.FOCUSED
        btn_window.add_component(btn1)

        btn2 = Button(30, 119, 210, 42, "NORMAL")
        btn_window.add_component(btn2)

        btn3 = Button(30, 172, 210, 42, "PRESSED")
        btn3.state = ComponentState.PRESSED
        btn_window.add_component(btn3)

        gui.add_window(btn_window)

        renderer = GUIRenderer(width=270, height=240)
        pixels = create_pixel_buffer(270, 240, COLOR_INDICES["background"])

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
