"""
Tests for the sixel graphics module (sixel.py).

Tests cover:
- Color conversion
- Palette generation
- Pixel buffer operations
- Rectangle filling
- Line drawing
- Text rendering
- GUI-specific drawing primitives
- RLE compression
- Sixel output generation
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sixel import (
    rgb_to_sixel_color,
    generate_palette,
    create_pixel_buffer,
    set_pixel,
    fill_rect,
    draw_horizontal_line,
    draw_vertical_line,
    draw_rect_border,
    draw_rounded_corner,
    draw_rounded_rect_border,
    draw_rounded_rect_filled,
    draw_checkmark,
    draw_circle,
    draw_text,
    get_text_width,
    draw_progress_bar,
    draw_slider,
    _encode_rle,
    pixels_to_sixel,
    COLORS,
    COLOR_INDICES,
    FONT,
    FONT_WIDTH,
    FONT_HEIGHT,
    SIXEL_START,
    SIXEL_END,
    SIXEL_NEWLINE,
    SIXEL_CARRIAGE_RETURN,
)


class TestColorConversion:
    """Tests for RGB to sixel color conversion."""

    def test_black_conversion(self):
        """Test converting black (0,0,0)."""
        result = rgb_to_sixel_color(0, 0, 0)
        assert result == (0, 0, 0)

    def test_white_conversion(self):
        """Test converting white (255,255,255)."""
        result = rgb_to_sixel_color(255, 255, 255)
        assert result == (100, 100, 100)

    def test_mid_gray_conversion(self):
        """Test converting mid-gray (128,128,128)."""
        result = rgb_to_sixel_color(128, 128, 128)
        assert result == (50, 50, 50)


class TestPaletteGeneration:
    """Tests for sixel palette generation."""

    def test_palette_not_empty(self):
        """Test that palette is generated."""
        palette = generate_palette()
        assert len(palette) > 0

    def test_palette_contains_all_colors(self):
        """Test that palette contains all defined colors."""
        palette = generate_palette()
        for name in COLORS:
            idx = COLOR_INDICES[name]
            assert f"#{idx};" in palette

    def test_palette_format(self):
        """Test that palette entries have correct format."""
        palette = generate_palette()
        assert ";2;" in palette


class TestPixelBuffer:
    """Tests for pixel buffer creation and manipulation."""

    def test_create_buffer_dimensions(self):
        """Test that buffer has correct dimensions."""
        buffer = create_pixel_buffer(10, 5)
        assert len(buffer) == 5
        assert len(buffer[0]) == 10

    def test_create_buffer_default_fill(self):
        """Test that buffer is filled with default value (0)."""
        buffer = create_pixel_buffer(5, 5)
        for row in buffer:
            for pixel in row:
                assert pixel == 0

    def test_create_buffer_custom_fill(self):
        """Test that buffer can be filled with custom value."""
        buffer = create_pixel_buffer(5, 5, fill=3)
        for row in buffer:
            for pixel in row:
                assert pixel == 3


class TestSetPixel:
    """Tests for individual pixel setting."""

    def test_set_pixel_valid(self):
        """Test setting a valid pixel."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, 5, 5, 2)
        assert buffer[5][5] == 2

    def test_set_pixel_out_of_bounds(self):
        """Test that out-of-bounds is ignored."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, 15, 5, 1)
        set_pixel(buffer, 5, 15, 1)
        set_pixel(buffer, -1, 5, 1)
        # Should not raise and buffer should be unchanged


class TestFillRect:
    """Tests for rectangle filling."""

    def test_fill_rect_basic(self):
        """Test basic rectangle fill."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 2, 2, 3, 3, 1)
        for y in range(2, 5):
            for x in range(2, 5):
                assert buffer[y][x] == 1

    def test_fill_rect_clips_to_bounds(self):
        """Test that rectangles are clipped to buffer bounds."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 8, 8, 5, 5, 1)
        assert buffer[8][8] == 1
        assert buffer[9][9] == 1


class TestDrawLines:
    """Tests for line drawing functions."""

    def test_draw_horizontal_line(self):
        """Test drawing a horizontal line."""
        buffer = create_pixel_buffer(10, 10)
        draw_horizontal_line(buffer, 0, 5, 8, 1)
        for x in range(8):
            assert buffer[5][x] == 1

    def test_draw_vertical_line(self):
        """Test drawing a vertical line."""
        buffer = create_pixel_buffer(10, 10)
        draw_vertical_line(buffer, 5, 0, 8, 1)
        for y in range(8):
            assert buffer[y][5] == 1


class TestDrawRectBorder:
    """Tests for rectangle border drawing."""

    def test_draw_rect_border(self):
        """Test drawing a rectangle border."""
        buffer = create_pixel_buffer(20, 20)
        draw_rect_border(buffer, 5, 5, 10, 10, 1)
        # Check top and bottom lines
        for x in range(5, 15):
            assert buffer[5][x] == 1
            assert buffer[14][x] == 1
        # Check left and right lines
        for y in range(5, 15):
            assert buffer[y][5] == 1
            assert buffer[y][14] == 1


class TestDrawRoundedRect:
    """Tests for rounded rectangle drawing."""

    def test_draw_rounded_rect_border(self):
        """Test drawing rounded rect border."""
        buffer = create_pixel_buffer(40, 30)
        draw_rounded_rect_border(buffer, 5, 5, 30, 20, 5, 1, "tltrblbr")
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_rounded_rect_filled(self):
        """Test drawing filled rounded rect."""
        buffer = create_pixel_buffer(40, 30)
        draw_rounded_rect_filled(buffer, 5, 5, 30, 20, 5, 1, 2)
        # Check that both fill and border colors are present
        fill_pixels = sum(1 for row in buffer for p in row if p == 1)
        border_pixels = sum(1 for row in buffer for p in row if p == 2)
        assert fill_pixels > 0
        assert border_pixels > 0


class TestDrawCheckmark:
    """Tests for checkmark drawing."""

    def test_draw_checkmark(self):
        """Test drawing a checkmark."""
        buffer = create_pixel_buffer(20, 20)
        draw_checkmark(buffer, 2, 2, 12, 1)
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0


class TestDrawCircle:
    """Tests for circle drawing."""

    def test_draw_circle_outline(self):
        """Test drawing a circle outline."""
        buffer = create_pixel_buffer(30, 30)
        draw_circle(buffer, 15, 15, 10, 1, filled=False)
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_circle_filled(self):
        """Test drawing a filled circle."""
        buffer = create_pixel_buffer(30, 30)
        draw_circle(buffer, 15, 15, 10, 1, filled=True)
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        # Filled circle should have more pixels than outline
        assert pixels_set > 50


class TestDrawText:
    """Tests for text drawing functionality."""

    def test_draw_single_character(self):
        """Test drawing a single character."""
        buffer = create_pixel_buffer(20, 20)
        width = draw_text(buffer, 0, 0, "A", 1)
        assert width > 0
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_text_returns_width(self):
        """Test that draw_text returns correct width."""
        buffer = create_pixel_buffer(100, 20)
        width = draw_text(buffer, 0, 0, "ABC", 1)
        expected = 3 * (FONT_WIDTH + 1) * 1
        assert width == expected

    def test_draw_text_uppercase_conversion(self):
        """Test that lowercase is converted to uppercase."""
        buffer1 = create_pixel_buffer(100, 20)
        buffer2 = create_pixel_buffer(100, 20)
        draw_text(buffer1, 0, 0, "abc", 1)
        draw_text(buffer2, 0, 0, "ABC", 1)
        assert buffer1 == buffer2


class TestGetTextWidth:
    """Tests for text width calculation."""

    def test_single_char_width(self):
        """Test width of single character."""
        width = get_text_width("A", scale=1)
        assert width == FONT_WIDTH

    def test_multiple_char_width(self):
        """Test width of multiple characters."""
        width = get_text_width("ABC", scale=1)
        expected = 3 * (FONT_WIDTH + 1) * 1 - 1
        assert width == expected


class TestDrawProgressBar:
    """Tests for progress bar drawing."""

    def test_draw_progress_bar_full(self):
        """Test drawing a full progress bar."""
        buffer = create_pixel_buffer(100, 20)
        draw_progress_bar(buffer, 0, 0, 100, 20, 100, 1, 2)
        fill_pixels = sum(1 for row in buffer for p in row if p == 2)
        assert fill_pixels == 100 * 20

    def test_draw_progress_bar_half(self):
        """Test drawing a half progress bar."""
        buffer = create_pixel_buffer(100, 20)
        draw_progress_bar(buffer, 0, 0, 100, 20, 50, 1, 2)
        fill_pixels = sum(1 for row in buffer for p in row if p == 2)
        assert fill_pixels == 50 * 20


class TestDrawSlider:
    """Tests for slider drawing."""

    def test_draw_slider(self):
        """Test drawing a slider."""
        buffer = create_pixel_buffer(120, 30)
        thumb_x = draw_slider(buffer, 10, 5, 100, 20, 50, 1, 2, 3)
        # Check that thumb position is correct (50% of the way)
        assert 50 <= thumb_x <= 70


class TestRLEEncoding:
    """Tests for Run-Length Encoding."""

    def test_rle_empty(self):
        """Test RLE with empty input."""
        result = _encode_rle([])
        assert result == ""

    def test_rle_single_value(self):
        """Test RLE with single value."""
        result = _encode_rle([0])
        assert result == "?"

    def test_rle_long_repetition(self):
        """Test RLE with long repetition (>= 3)."""
        result = _encode_rle([0, 0, 0, 0, 0])
        assert "!5?" in result


class TestPixelsToSixel:
    """Tests for the main sixel conversion function."""

    def test_basic_output_structure(self):
        """Test that output has correct sixel structure."""
        buffer = create_pixel_buffer(10, 10)
        result = pixels_to_sixel(buffer, 10, 10)
        assert result.startswith(SIXEL_START)
        assert result.endswith(SIXEL_END)

    def test_includes_palette(self):
        """Test that output includes color palette."""
        buffer = create_pixel_buffer(10, 10)
        result = pixels_to_sixel(buffer, 10, 10)
        assert "#0;2;" in result

    def test_includes_raster_attributes(self):
        """Test that output includes raster attributes."""
        buffer = create_pixel_buffer(10, 12)
        result = pixels_to_sixel(buffer, 10, 12)
        assert '"1;1;10;12' in result


class TestConstants:
    """Tests for module constants."""

    def test_gui_colors_defined(self):
        """Test that GUI-specific colors are defined."""
        gui_colors = [
            "background", "window_bg", "window_border",
            "button_bg", "button_hover", "button_pressed",
            "checkbox_bg", "checkbox_checked",
            "slider_track", "slider_fill", "slider_thumb",
            "progress_bg", "progress_fill",
            "list_bg", "list_item_selected",
        ]
        for color in gui_colors:
            assert color in COLORS, f"Missing color: {color}"
            assert color in COLOR_INDICES, f"Missing color index: {color}"

    def test_color_indices_unique(self):
        """Test that color indices are unique."""
        indices = list(COLOR_INDICES.values())
        assert len(indices) == len(set(indices))

    def test_font_contains_basic_chars(self):
        """Test that font contains basic characters."""
        assert " " in FONT
        assert "A" in FONT
        assert "Z" in FONT
        assert "0" in FONT
        assert "9" in FONT

    def test_sixel_constants(self):
        """Test sixel escape sequence constants."""
        assert SIXEL_START == "\x1bPq"
        assert SIXEL_END == "\x1b\\"
        assert SIXEL_NEWLINE == "-"
        assert SIXEL_CARRIAGE_RETURN == "$"
