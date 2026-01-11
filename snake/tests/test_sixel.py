"""
Tests for the sixel graphics module (sixel.py).

Tests cover:
- Color conversion
- Palette generation
- Pixel buffer operations
- Rectangle filling
- Text rendering
- RLE compression
- Sixel output generation
"""

import pytest

from sixel import (
    rgb_to_sixel_color,
    generate_palette,
    create_pixel_buffer,
    set_pixel,
    fill_rect,
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
        # Should contain color definitions like #0;2;0;0;0
        assert "#0;2;0;0;0" in palette  # background (black)

    def test_palette_includes_sixel_color_format(self):
        """Test that palette uses sixel color format (;2; prefix for RGB)."""
        palette = generate_palette()
        # All colors should use format: #index;2;R;G;B
        assert ";2;" in palette


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
        # Buffer should remain unchanged
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
        # Check filled area
        for y in range(2, 5):
            for x in range(2, 5):
                assert buffer[y][x] == 1
        # Check area outside is not filled
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
        # Rectangle extends beyond buffer
        fill_rect(buffer, 8, 8, 5, 5, 1)
        # Should only fill within bounds
        assert buffer[8][8] == 1
        assert buffer[9][9] == 1

    def test_fill_rect_negative_start(self):
        """Test rectangle with negative start coordinates."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, -2, -2, 5, 5, 1)
        # Should fill from 0,0 to 2,2
        assert buffer[0][0] == 1
        assert buffer[1][1] == 1
        assert buffer[2][2] == 1
        assert buffer[3][3] == 0

    def test_fill_rect_empty_buffer(self):
        """Test fill_rect with edge case buffer."""
        buffer = create_pixel_buffer(0, 0)
        # Should not raise
        fill_rect(buffer, 0, 0, 5, 5, 1)


class TestDrawText:
    """Tests for text drawing functionality."""

    def test_draw_single_character(self):
        """Test drawing a single character."""
        buffer = create_pixel_buffer(20, 20)
        width = draw_text(buffer, 0, 0, "A", 1)
        assert width > 0
        # Check that some pixels are set
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
        width = draw_text(buffer, 0, 0, "A", 1, scale=2)
        # At scale 2, should use more pixels
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

    def test_draw_text_unknown_char(self):
        """Test drawing unknown characters (skipped gracefully)."""
        buffer = create_pixel_buffer(100, 20)
        # Should not raise, unknown char is skipped
        width = draw_text(buffer, 0, 0, "A@B", 1)
        # Width should still account for the unknown char
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
        # Single char: (FONT_WIDTH + 1) * scale - scale = FONT_WIDTH
        assert width == FONT_WIDTH

    def test_multiple_char_width(self):
        """Test width of multiple characters."""
        width = get_text_width("ABC", scale=1)
        # 3 chars at scale 1
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
        # Each becomes its character
        assert "?" in result  # 0
        assert "@" in result  # 1
        assert "A" in result  # 2

    def test_rle_short_repetition(self):
        """Test RLE with short repetition (< 3)."""
        result = _encode_rle([0, 0])
        # Short runs are not compressed
        assert result == "??"

    def test_rle_long_repetition(self):
        """Test RLE with long repetition (>= 3)."""
        result = _encode_rle([0, 0, 0, 0, 0])
        # Should use RLE format: !5?
        assert "!5?" in result

    def test_rle_mixed(self):
        """Test RLE with mixed values."""
        # 3 zeros, then 3 ones
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
        # Should contain palette definitions
        assert "#0;2;" in result

    def test_includes_raster_attributes(self):
        """Test that output includes raster attributes."""
        buffer = create_pixel_buffer(10, 12)
        result = pixels_to_sixel(buffer, 10, 12)
        # Should contain raster attributes with dimensions
        assert '"1;1;10;12' in result

    def test_multiple_colors(self):
        """Test rendering with multiple colors."""
        buffer = create_pixel_buffer(10, 10)
        fill_rect(buffer, 0, 0, 5, 5, 1)  # Color 1
        fill_rect(buffer, 5, 5, 5, 5, 2)  # Color 2
        result = pixels_to_sixel(buffer, 10, 10)
        # Should reference multiple colors
        assert "#1" in result
        assert "#2" in result

    def test_band_processing(self):
        """Test that tall images are processed in bands of 6."""
        buffer = create_pixel_buffer(10, 18)  # 3 bands of 6
        result = pixels_to_sixel(buffer, 10, 18)
        # Should contain newline characters between bands
        assert "-" in result  # SIXEL_NEWLINE

    def test_carriage_return_for_colors(self):
        """Test that multiple colors in same band use carriage return."""
        buffer = create_pixel_buffer(10, 6)
        buffer[0][0] = 1
        buffer[0][5] = 2
        result = pixels_to_sixel(buffer, 10, 6)
        # Should use $ (carriage return) between color passes
        assert "$" in result


class TestConstants:
    """Tests for module constants."""

    def test_colors_defined(self):
        """Test that all expected colors are defined."""
        expected = ["background", "snake_head", "snake_body", "food", "border", "text", "text_green"]
        for color in expected:
            assert color in COLORS
            assert color in COLOR_INDICES

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
