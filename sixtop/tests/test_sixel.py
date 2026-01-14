"""
Tests for the sixel graphics module (sixel.py).

Tests cover:
- Color conversion
- Palette generation
- Pixel buffer operations
- Rectangle filling
- Line drawing
- Text rendering
- Graph rendering
- RLE compression
- Sixel output generation
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sixel import (
    rgb_to_sixel_color,
    generate_palette,
    create_pixel_buffer,
    set_pixel,
    fill_rect,
    draw_horizontal_line,
    draw_vertical_line,
    draw_rounded_corner,
    draw_rounded_rect_border,
    draw_line_graph,
    draw_dual_line_graph,
    draw_bar_graph,
    draw_text,
    get_text_width,
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

    def test_red_conversion(self):
        """Test converting pure red."""
        result = rgb_to_sixel_color(255, 0, 0)
        assert result == (100, 0, 0)

    def test_green_conversion(self):
        """Test converting pure green."""
        result = rgb_to_sixel_color(0, 255, 0)
        assert result == (0, 100, 0)

    def test_blue_conversion(self):
        """Test converting pure blue."""
        result = rgb_to_sixel_color(0, 0, 255)
        assert result == (0, 0, 100)

    def test_mid_gray_conversion(self):
        """Test converting mid-gray (128,128,128)."""
        result = rgb_to_sixel_color(128, 128, 128)
        # 128 * 100 // 255 = 50
        assert result == (50, 50, 50)

    def test_arbitrary_color_conversion(self):
        """Test converting an arbitrary color."""
        result = rgb_to_sixel_color(100, 150, 200)
        assert result == (39, 58, 78)


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
        # Should contain color definitions like #0;2;r;g;b
        assert ";2;" in palette  # RGB format indicator

    def test_palette_includes_all_colors(self):
        """Test that all colors in COLORS are in the palette."""
        palette = generate_palette()
        for name, (r, g, b) in COLORS.items():
            idx = COLOR_INDICES[name]
            assert f"#{idx};2;" in palette


class TestPixelBuffer:
    """Tests for pixel buffer creation and manipulation."""

    def test_create_buffer_dimensions(self):
        """Test that buffer has correct dimensions."""
        buffer = create_pixel_buffer(10, 5)
        assert len(buffer) == 5  # height
        assert len(buffer[0]) == 10  # width

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

    def test_create_empty_buffer(self):
        """Test creating a zero-size buffer."""
        buffer = create_pixel_buffer(0, 0)
        assert len(buffer) == 0


class TestSetPixel:
    """Tests for individual pixel setting."""

    def test_set_pixel_valid(self):
        """Test setting a valid pixel."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, 5, 5, 2)
        assert buffer[5][5] == 2

    def test_set_pixel_corner(self):
        """Test setting corner pixels."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, 0, 0, 1)
        set_pixel(buffer, 9, 9, 2)
        assert buffer[0][0] == 1
        assert buffer[9][9] == 2

    def test_set_pixel_out_of_bounds_x(self):
        """Test that out-of-bounds x is ignored."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, 15, 5, 1)  # Should not raise
        for row in buffer:
            for pixel in row:
                assert pixel == 0

    def test_set_pixel_out_of_bounds_y(self):
        """Test that out-of-bounds y is ignored."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, 5, 15, 1)  # Should not raise
        for row in buffer:
            for pixel in row:
                assert pixel == 0

    def test_set_pixel_negative_coords(self):
        """Test that negative coordinates are ignored."""
        buffer = create_pixel_buffer(10, 10)
        set_pixel(buffer, -1, 5, 1)
        set_pixel(buffer, 5, -1, 1)
        for row in buffer:
            for pixel in row:
                assert pixel == 0


class TestFillRect:
    """Tests for rectangle filling."""

    def test_fill_rect_basic(self):
        """Test basic rectangle fill."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 2, 2, 3, 3, 1)
        for y in range(2, 5):
            for x in range(2, 5):
                assert buffer[y][x] == 1
        assert buffer[0][0] == 0
        assert buffer[1][1] == 0

    def test_fill_rect_full_buffer(self):
        """Test filling entire buffer."""
        buffer = create_pixel_buffer(5, 5)
        fill_rect(buffer, 0, 0, 5, 5, 2)
        for row in buffer:
            for pixel in row:
                assert pixel == 2

    def test_fill_rect_single_pixel(self):
        """Test filling a single pixel."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 5, 5, 1, 1, 3)
        assert buffer[5][5] == 3
        assert buffer[5][4] == 0
        assert buffer[4][5] == 0

    def test_fill_rect_clips_to_bounds(self):
        """Test that rectangles are clipped to buffer bounds."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 8, 8, 5, 5, 1)
        assert buffer[8][8] == 1
        assert buffer[9][9] == 1

    def test_fill_rect_negative_start(self):
        """Test rectangle with negative start coordinates."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, -2, -2, 5, 5, 1)
        assert buffer[0][0] == 1
        assert buffer[1][1] == 1
        assert buffer[2][2] == 1
        assert buffer[3][3] == 0


class TestDrawLines:
    """Tests for line drawing functions."""

    def test_draw_horizontal_line(self):
        """Test drawing a horizontal line."""
        buffer = create_pixel_buffer(10, 10)
        draw_horizontal_line(buffer, 0, 5, 8, 1)
        for x in range(8):
            assert buffer[5][x] == 1
        assert buffer[5][8] == 0

    def test_draw_vertical_line(self):
        """Test drawing a vertical line."""
        buffer = create_pixel_buffer(10, 10)
        draw_vertical_line(buffer, 5, 0, 8, 1)
        for y in range(8):
            assert buffer[y][5] == 1
        assert buffer[8][5] == 0


class TestDrawRoundedCorner:
    """Tests for rounded corner drawing."""

    def test_draw_corner_tl(self):
        """Test drawing top-left corner."""
        buffer = create_pixel_buffer(20, 20)
        draw_rounded_corner(buffer, 0, 0, 5, 1, 'tl')
        # Some pixels should be set
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_corner_tr(self):
        """Test drawing top-right corner."""
        buffer = create_pixel_buffer(20, 20)
        draw_rounded_corner(buffer, 10, 0, 5, 1, 'tr')
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_corner_bl(self):
        """Test drawing bottom-left corner."""
        buffer = create_pixel_buffer(20, 20)
        draw_rounded_corner(buffer, 0, 10, 5, 1, 'bl')
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_corner_br(self):
        """Test drawing bottom-right corner."""
        buffer = create_pixel_buffer(20, 20)
        draw_rounded_corner(buffer, 10, 10, 5, 1, 'br')
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0


class TestDrawRoundedRectBorder:
    """Tests for rounded rectangle border drawing."""

    def test_draw_rounded_rect_all_corners(self):
        """Test drawing rounded rect with all corners."""
        buffer = create_pixel_buffer(40, 30)
        draw_rounded_rect_border(buffer, 5, 5, 30, 20, 5, 1, "tltrblbr")
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_rounded_rect_no_corners(self):
        """Test drawing rect with no rounded corners."""
        buffer = create_pixel_buffer(40, 30)
        draw_rounded_rect_border(buffer, 5, 5, 30, 20, 5, 1, "")
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0


class TestDrawLineGraph:
    """Tests for line graph drawing."""

    def test_draw_line_graph_basic(self):
        """Test drawing a basic line graph."""
        buffer = create_pixel_buffer(50, 30)
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        draw_line_graph(buffer, 0, 0, 50, 30, data, 1)
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_line_graph_empty_data(self):
        """Test drawing line graph with empty data."""
        buffer = create_pixel_buffer(50, 30)
        draw_line_graph(buffer, 0, 0, 50, 30, [], 1)
        # Should not crash, no pixels set
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set == 0

    def test_draw_line_graph_single_point(self):
        """Test drawing line graph with single point."""
        buffer = create_pixel_buffer(50, 30)
        draw_line_graph(buffer, 0, 0, 50, 30, [50], 1)
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_line_graph_with_fill(self):
        """Test drawing line graph with fill color."""
        buffer = create_pixel_buffer(50, 30)
        data = [10, 50, 30, 80, 20]
        draw_line_graph(buffer, 0, 0, 50, 30, data, 1, fill_color=2)
        line_pixels = sum(1 for row in buffer for p in row if p == 1)
        fill_pixels = sum(1 for row in buffer for p in row if p == 2)
        assert line_pixels > 0
        assert fill_pixels > 0


class TestDrawDualLineGraph:
    """Tests for dual line graph drawing."""

    def test_draw_dual_line_graph_basic(self):
        """Test drawing dual line graph."""
        buffer = create_pixel_buffer(50, 30)
        data1 = [10, 20, 30, 40, 50]
        data2 = [5, 15, 25, 35, 45]
        draw_dual_line_graph(buffer, 0, 0, 50, 30, data1, data2, 1, 2)
        pixels_1 = sum(1 for row in buffer for p in row if p == 1)
        pixels_2 = sum(1 for row in buffer for p in row if p == 2)
        assert pixels_1 > 0
        assert pixels_2 > 0

    def test_draw_dual_line_graph_empty_data(self):
        """Test dual line graph with empty data."""
        buffer = create_pixel_buffer(50, 30)
        draw_dual_line_graph(buffer, 0, 0, 50, 30, [], [], 1, 2)
        # Should not crash
        pixels_set = sum(1 for row in buffer for p in row if p != 0)
        assert pixels_set == 0


class TestDrawBarGraph:
    """Tests for bar graph drawing."""

    def test_draw_bar_graph_full(self):
        """Test drawing a full bar."""
        buffer = create_pixel_buffer(50, 10)
        draw_bar_graph(buffer, 0, 0, 50, 10, 100, 1)
        # Bar should fill most of the width
        filled = sum(1 for p in buffer[5] if p == 1)
        assert filled == 50

    def test_draw_bar_graph_half(self):
        """Test drawing a half bar."""
        buffer = create_pixel_buffer(50, 10)
        draw_bar_graph(buffer, 0, 0, 50, 10, 50, 1)
        filled = sum(1 for p in buffer[5] if p == 1)
        assert filled == 25

    def test_draw_bar_graph_empty(self):
        """Test drawing an empty bar."""
        buffer = create_pixel_buffer(50, 10)
        draw_bar_graph(buffer, 0, 0, 50, 10, 0, 1)
        filled = sum(1 for row in buffer for p in row if p == 1)
        assert filled == 0


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
        expected = 3 * (FONT_WIDTH + 1) * 1  # 3 chars, scale 1
        assert width == expected

    def test_draw_text_scaled(self):
        """Test drawing text with scale factor."""
        buffer = create_pixel_buffer(100, 50)
        draw_text(buffer, 0, 0, "A", 1, scale=2)
        pixels_scale2 = sum(1 for row in buffer for p in row if p == 1)

        buffer2 = create_pixel_buffer(100, 50)
        draw_text(buffer2, 0, 0, "A", 1, scale=1)
        pixels_scale1 = sum(1 for row in buffer2 for p in row if p == 1)

        assert pixels_scale2 > pixels_scale1

    def test_draw_text_uppercase_conversion(self):
        """Test that lowercase is converted to uppercase."""
        buffer1 = create_pixel_buffer(100, 20)
        buffer2 = create_pixel_buffer(100, 20)
        draw_text(buffer1, 0, 0, "abc", 1)
        draw_text(buffer2, 0, 0, "ABC", 1)
        assert buffer1 == buffer2

    def test_draw_text_bold(self):
        """Test drawing bold text."""
        buffer = create_pixel_buffer(100, 20)
        draw_text(buffer, 0, 0, "A", 1, bold=True)
        pixels_bold = sum(1 for row in buffer for p in row if p == 1)

        buffer2 = create_pixel_buffer(100, 20)
        draw_text(buffer2, 0, 0, "A", 1, bold=False)
        pixels_normal = sum(1 for row in buffer2 for p in row if p == 1)

        assert pixels_bold > pixels_normal

    def test_draw_text_unknown_char(self):
        """Test drawing unknown characters (skipped gracefully)."""
        buffer = create_pixel_buffer(100, 20)
        width = draw_text(buffer, 0, 0, "A@B", 1)
        assert width > 0

    def test_draw_text_with_numbers(self):
        """Test drawing numeric text."""
        buffer = create_pixel_buffer(100, 20)
        width = draw_text(buffer, 0, 0, "123", 1)
        assert width > 0
        pixels_set = sum(1 for row in buffer for p in row if p == 1)
        assert pixels_set > 0

    def test_draw_text_empty_string(self):
        """Test drawing empty string."""
        buffer = create_pixel_buffer(100, 20)
        width = draw_text(buffer, 0, 0, "", 1)
        assert width == 0


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

    def test_scaled_width(self):
        """Test width with scale factor."""
        width1 = get_text_width("A", scale=1)
        width2 = get_text_width("A", scale=2)
        assert width2 == width1 * 2

    def test_empty_string_width(self):
        """Test width of empty string."""
        width = get_text_width("", scale=1)
        assert width == -1  # 0 * (5+1) * 1 - 1 = -1

    def test_bold_text_width(self):
        """Test width of bold text with multiple characters."""
        # Use multiple characters as trailing adjustment cancels extra width for single chars
        width_normal = get_text_width("ABC", scale=1, bold=False)
        width_bold = get_text_width("ABC", scale=1, bold=True)
        assert width_bold > width_normal


class TestRLEEncoding:
    """Tests for Run-Length Encoding."""

    def test_rle_empty(self):
        """Test RLE with empty input."""
        result = _encode_rle([])
        assert result == ""

    def test_rle_single_value(self):
        """Test RLE with single value."""
        result = _encode_rle([0])
        assert result == "?"  # chr(63 + 0) = '?'

    def test_rle_no_repetition(self):
        """Test RLE with no repeated values."""
        result = _encode_rle([0, 1, 2])
        assert "?" in result  # 0
        assert "@" in result  # 1
        assert "A" in result  # 2

    def test_rle_short_repetition(self):
        """Test RLE with short repetition (< 3)."""
        result = _encode_rle([0, 0])
        assert result == "??"
        assert "!" not in result

    def test_rle_long_repetition(self):
        """Test RLE with long repetition (>= 3)."""
        result = _encode_rle([0, 0, 0, 0, 0])
        assert "!5?" in result

    def test_rle_mixed(self):
        """Test RLE with mixed values."""
        result = _encode_rle([0, 0, 0, 1, 1, 1])
        assert "!3?" in result  # 3 zeros
        assert "!3@" in result  # 3 ones


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

    def test_multiple_colors(self):
        """Test rendering with multiple colors."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 0, 0, 5, 5, 1)
        fill_rect(buffer, 5, 5, 5, 5, 2)
        result = pixels_to_sixel(buffer, 10, 10)
        assert "#1" in result
        assert "#2" in result

    def test_band_processing(self):
        """Test that tall images are processed in bands of 6."""
        buffer = create_pixel_buffer(10, 18)  # 3 bands of 6
        result = pixels_to_sixel(buffer, 10, 18)
        assert SIXEL_NEWLINE in result

    def test_carriage_return_for_colors(self):
        """Test that multiple colors in same band use carriage return."""
        buffer = create_pixel_buffer(10, 6)
        buffer[0][0] = 1
        buffer[0][5] = 2
        result = pixels_to_sixel(buffer, 10, 6)
        assert SIXEL_CARRIAGE_RETURN in result


class TestConstants:
    """Tests for module constants."""

    def test_colors_defined(self):
        """Test that all expected colors are defined."""
        expected = [
            "background", "panel_bg", "border", "border_highlight",
            "text", "text_dim", "text_cyan", "text_red", "text_green",
            "graph_cyan", "graph_red", "graph_green", "graph_blue",
            "graph_fill_cyan", "graph_fill_red", "graph_fill_green",
            "graph_fill_blue", "graph_yellow", "title_line", "bg_dark"
        ]
        for color in expected:
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

    def test_font_glyph_dimensions(self):
        """Test that font glyphs have correct dimensions."""
        for char, glyph in FONT.items():
            assert len(glyph) == FONT_HEIGHT, f"Glyph '{char}' has wrong height"

    def test_font_dimensions(self):
        """Test font dimension constants."""
        assert FONT_WIDTH == 5
        assert FONT_HEIGHT == 7

    def test_sixel_constants(self):
        """Test sixel escape sequence constants."""
        assert SIXEL_START == "\x1bPq"
        assert SIXEL_END == "\x1b\\"
        assert SIXEL_NEWLINE == "-"
        assert SIXEL_CARRIAGE_RETURN == "$"
