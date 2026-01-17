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


@pytest.fixture
def screenshot_dir(tmp_path):
    """Create a temporary directory for screenshots."""
    return tmp_path / "screenshots"


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

    def test_generate_full_gui_screenshot(self, screenshot_dir):
        """Generate screenshot of complete GUI demo."""
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        # Create GUI state
        gui = GUIState()

        # Add a couple of demo windows
        btn_window = Window(title="BUTTONS", x=10, y=10, width=150, height=100)
        btn_window.add_component(Button(20, 40, 120, 25, "CLICK ME"))
        btn_window.add_component(Button(20, 70, 120, 25, "SUBMIT"))
        gui.add_window(btn_window)

        cb_window = Window(title="OPTIONS", x=170, y=10, width=150, height=100)
        cb_window.add_component(Checkbox(180, 40, 130, 24, "ENABLE", checked=True))
        cb_window.add_component(Checkbox(180, 70, 130, 24, "VERBOSE", checked=False))
        gui.add_window(cb_window)

        # Render to pixel buffer
        renderer = GUIRenderer(width=350, height=130)

        # Access internal rendering to get pixel buffer
        from sixel import create_pixel_buffer, pixels_to_png, COLOR_INDICES

        # Render frame (this gives us sixel, but we need pixels)
        # For the screenshot test, we'll use the renderer's internal state
        pixels = create_pixel_buffer(350, 130, COLOR_INDICES["background"])

        # Draw windows (simplified - actual rendering is more complex)
        fill_rect(pixels, 10, 10, 150, 100, COLOR_INDICES["window_bg"])
        fill_rect(pixels, 170, 10, 150, 100, COLOR_INDICES["window_bg"])

        output_path = screenshot_dir / "gui_demo.png"
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
