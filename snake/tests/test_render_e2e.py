"""
End-to-end tests for sixel rendering.

These tests verify that the game actually renders valid sixel output
that could be displayed on a sixel-capable terminal.
"""

import re
import sys
from io import StringIO

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from game import GameState, Direction, create_game
from renderer import GameRenderer
from sixel import (
    SIXEL_START,
    SIXEL_END,
    COLORS,
    COLOR_INDICES,
    generate_palette,
    create_pixel_buffer,
    fill_rect,
    draw_text,
    pixels_to_sixel,
    rgb_to_sixel_color,
    _encode_rle,
    get_text_width,
)


class TestSixelEscapeSequences:
    """Test that sixel output has correct escape sequences."""

    def test_sixel_start_sequence(self):
        """Verify SIXEL_START is the correct DCS sequence."""
        assert SIXEL_START == "\x1bPq"

    def test_sixel_end_sequence(self):
        """Verify SIXEL_END is the correct ST sequence."""
        assert SIXEL_END == "\x1b\\"

    def test_basic_sixel_output_format(self):
        """Verify a minimal sixel output has correct structure."""
        pixels = create_pixel_buffer(6, 6, 0)
        output = pixels_to_sixel(pixels, 6, 6)

        # Must start with DCS (Device Control String)
        assert output.startswith(SIXEL_START), "Sixel output must start with ESC P q"

        # Must end with ST (String Terminator)
        assert output.endswith(SIXEL_END), "Sixel output must end with ESC \\"

    def test_sixel_contains_raster_attributes(self):
        """Verify sixel output contains raster attributes (dimensions)."""
        pixels = create_pixel_buffer(10, 12, 0)
        output = pixels_to_sixel(pixels, 10, 12)

        # Raster attributes format: "Pan;Pad;Ph;Pv where Ph=width, Pv=height
        assert '"1;1;10;12' in output, "Sixel should contain raster attributes"


class TestColorPalette:
    """Test color palette generation and format."""

    def test_all_game_colors_defined(self):
        """Verify all required game colors are in the palette."""
        required_colors = [
            "background",
            "snake_head",
            "snake_body",
            "food",
            "border",
            "text",
            "text_green",
        ]
        for color in required_colors:
            assert color in COLORS, f"Missing color: {color}"
            assert color in COLOR_INDICES, f"Missing color index: {color}"

    def test_color_indices_are_unique(self):
        """Verify all color indices are unique."""
        indices = list(COLOR_INDICES.values())
        assert len(indices) == len(set(indices)), "Color indices must be unique"

    def test_rgb_to_sixel_conversion(self):
        """Verify RGB values are converted to 0-100 range correctly."""
        # Black
        assert rgb_to_sixel_color(0, 0, 0) == (0, 0, 0)
        # White
        assert rgb_to_sixel_color(255, 255, 255) == (100, 100, 100)
        # Mid gray
        r, g, b = rgb_to_sixel_color(128, 128, 128)
        assert 49 <= r <= 51  # ~50
        assert 49 <= g <= 51
        assert 49 <= b <= 51

    def test_palette_format(self):
        """Verify palette uses correct sixel color definition format."""
        palette = generate_palette()

        # Each color definition should be #index;2;r;g;b
        # 2 = RGB color space
        for name, idx in COLOR_INDICES.items():
            pattern = rf"#{idx};2;\d+;\d+;\d+"
            assert re.search(pattern, palette), f"Missing palette entry for {name}"

    def test_palette_in_sixel_output(self):
        """Verify palette is included in sixel output."""
        pixels = create_pixel_buffer(6, 6, COLOR_INDICES["snake_head"])
        output = pixels_to_sixel(pixels, 6, 6)

        # Check that the snake_head color is defined
        assert f"#{COLOR_INDICES['snake_head']};2;" in output


class TestRLEEncoding:
    """Test Run-Length Encoding optimization."""

    def test_rle_single_values(self):
        """Single values should not use RLE."""
        result = _encode_rle([1])
        assert result == "@"  # 63 + 1 = 64 = '@'
        assert "!" not in result

    def test_rle_two_values(self):
        """Two identical values should not use RLE."""
        result = _encode_rle([1, 1])
        assert result == "@@"
        assert "!" not in result

    def test_rle_three_or_more_values(self):
        """Three or more identical values should use RLE."""
        result = _encode_rle([1, 1, 1])
        assert result == "!3@"

    def test_rle_large_run(self):
        """Large runs should use RLE notation."""
        result = _encode_rle([0] * 100)
        assert result == "!100?"  # 63 + 0 = 63 = '?'

    def test_rle_mixed_runs(self):
        """Mixed values should encode correctly."""
        result = _encode_rle([1, 1, 1, 2, 2, 2, 2])
        assert "!3@" in result  # Three 1s
        assert "!4A" in result  # Four 2s (63 + 2 = 65 = 'A')


class TestPixelBuffer:
    """Test pixel buffer operations."""

    def test_create_buffer_dimensions(self):
        """Buffer should have correct dimensions."""
        pixels = create_pixel_buffer(10, 20, 0)
        assert len(pixels) == 20  # height
        assert len(pixels[0]) == 10  # width

    def test_create_buffer_fill_value(self):
        """Buffer should be filled with specified value."""
        pixels = create_pixel_buffer(5, 5, 3)
        for row in pixels:
            assert all(p == 3 for p in row)

    def test_fill_rect_basic(self):
        """fill_rect should set pixels correctly."""
        pixels = create_pixel_buffer(10, 10, 0)
        fill_rect(pixels, 2, 2, 3, 3, 5)

        # Check filled area
        for y in range(2, 5):
            for x in range(2, 5):
                assert pixels[y][x] == 5

        # Check unfilled area
        assert pixels[0][0] == 0
        assert pixels[9][9] == 0

    def test_fill_rect_clipping(self):
        """fill_rect should clip to buffer bounds."""
        pixels = create_pixel_buffer(10, 10, 0)
        # This should not crash - it extends beyond bounds
        fill_rect(pixels, 8, 8, 5, 5, 1)

        # Only the in-bounds portion should be filled
        assert pixels[8][8] == 1
        assert pixels[9][9] == 1


class TestTextRendering:
    """Test bitmap font text rendering."""

    def test_get_text_width(self):
        """Text width calculation should be correct."""
        # Each char is 5 pixels + 1 space, minus trailing space
        width = get_text_width("AB", 1)
        assert width == 11  # 5 + 1 + 5 = 11 (no trailing space on last)

    def test_get_text_width_scaled(self):
        """Scaled text width should multiply correctly."""
        width_1x = get_text_width("A", 1)
        width_2x = get_text_width("A", 2)
        assert width_2x == width_1x * 2

    def test_draw_text_produces_pixels(self):
        """draw_text should produce non-zero pixels."""
        pixels = create_pixel_buffer(50, 20, 0)
        draw_text(pixels, 0, 0, "A", 1, 1)

        # Check that some pixels were drawn
        has_pixels = any(p == 1 for row in pixels for p in row)
        assert has_pixels, "Text should produce pixels"


class TestGameRenderer:
    """Test the game renderer produces valid sixel output."""

    @pytest.fixture
    def game(self):
        """Create a test game state."""
        return create_game(128, 128, 16)

    @pytest.fixture
    def renderer(self, game):
        """Create a renderer for the test game."""
        return GameRenderer(game)

    def test_renderer_frame_dimensions(self, renderer):
        """Renderer should calculate correct frame dimensions."""
        assert renderer.frame_width > 0
        assert renderer.frame_height > 0
        assert renderer.game_size == 128  # 8 * 16

    def test_render_frame_returns_sixel(self, renderer):
        """render_frame should return valid sixel string."""
        output = renderer.render_frame()

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        assert len(output) > 100  # Should have substantial content

    def test_render_frame_contains_colors(self, renderer):
        """Rendered frame should use multiple colors."""
        output = renderer.render_frame()

        # Should contain color definitions for at least snake, food, border
        assert f"#{COLOR_INDICES['snake_head']}" in output or \
               f"#{COLOR_INDICES['snake_body']}" in output
        assert f"#{COLOR_INDICES['food']}" in output

    def test_render_game_over(self, renderer, game):
        """Game over screen should render correctly."""
        game.game_over = True
        output = renderer.render_frame(show_game_over=True)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        # Game over text uses food color (red)
        assert f"#{COLOR_INDICES['food']}" in output

    def test_render_different_scores(self, renderer, game):
        """Renderer should handle different scores."""
        game.score = 0
        output1 = renderer.render_frame()

        game.score = 99
        output2 = renderer.render_frame()

        # Both should be valid sixel
        assert output1.startswith(SIXEL_START)
        assert output2.startswith(SIXEL_START)
        # Score change should produce different output
        assert output1 != output2

    def test_terminal_position_calculation(self, renderer):
        """Terminal position calculation should return valid coordinates."""
        row, col = renderer.calculate_terminal_position(80, 24)

        assert row >= 1
        assert col >= 1


class TestFullGameRendering:
    """Integration tests for complete game rendering scenarios."""

    def test_render_initial_game_state(self):
        """A fresh game should render without errors."""
        game = create_game(128, 128, 16)
        renderer = GameRenderer(game)
        output = renderer.render_frame()

        # Validate structure
        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

        # Should have reasonable size (not empty or trivially small)
        assert len(output) > 1000

    def test_render_after_movement(self):
        """Game should render correctly after snake moves."""
        game = create_game(128, 128, 16)
        renderer = GameRenderer(game)

        # Render initial state
        output1 = renderer.render_frame()

        # Move snake
        game.update()
        output2 = renderer.render_frame()

        # Both should be valid
        assert output1.startswith(SIXEL_START) and output1.endswith(SIXEL_END)
        assert output2.startswith(SIXEL_START) and output2.endswith(SIXEL_END)

        # Output should differ (snake moved)
        assert output1 != output2

    def test_render_snake_with_different_directions(self):
        """Snake should render in all directions."""
        for direction in Direction:
            game = create_game(128, 128, 16)
            game.direction = direction
            renderer = GameRenderer(game)
            output = renderer.render_frame()

            assert output.startswith(SIXEL_START), f"Failed for direction {direction}"
            assert output.endswith(SIXEL_END), f"Failed for direction {direction}"

    def test_render_multiple_frames(self):
        """Game should render multiple frames consistently."""
        game = create_game(128, 128, 16)
        renderer = GameRenderer(game)

        frames = []
        for _ in range(10):
            frames.append(renderer.render_frame())
            game.update()

        # All frames should be valid sixel
        for i, frame in enumerate(frames):
            assert frame.startswith(SIXEL_START), f"Frame {i} invalid start"
            assert frame.endswith(SIXEL_END), f"Frame {i} invalid end"

    def test_render_game_over_sequence(self):
        """Game over should render correctly after collision."""
        game = create_game(128, 128, 16)
        renderer = GameRenderer(game)

        # Run until game over (wall collision)
        while not game.game_over:
            game.update()
            if game.score > 100:  # Safety limit
                break

        assert game.game_over

        output = renderer.render_frame(show_game_over=True)
        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestSixelOutputParsing:
    """Test that sixel output can be parsed and validated."""

    def test_sixel_band_structure(self):
        """Sixel output should have proper band structure."""
        pixels = create_pixel_buffer(10, 18, 0)  # 3 bands of 6 rows
        output = pixels_to_sixel(pixels, 10, 18)

        # Remove start/end sequences for analysis
        content = output[len(SIXEL_START):-len(SIXEL_END)]

        # Should have band separators (-)
        # For 18 rows, we need 2 newlines (after band 0 and band 1)
        assert content.count("-") >= 2

    def test_sixel_color_switching(self):
        """Multi-color output should switch colors with $ or -."""
        pixels = create_pixel_buffer(10, 6, 0)
        # Add different colors
        fill_rect(pixels, 0, 0, 5, 6, COLOR_INDICES["snake_head"])
        fill_rect(pixels, 5, 0, 5, 6, COLOR_INDICES["food"])
        output = pixels_to_sixel(pixels, 10, 6)

        # Should contain multiple color references
        assert output.count("#") >= 2


class TestCrossPlatformRendering:
    """Test rendering works across platform configurations."""

    @pytest.mark.parametrize("pixel_size", [16, 24, 32])
    def test_different_pixel_sizes(self, pixel_size):
        """Game should render at different pixel sizes."""
        game = create_game(128, 128, pixel_size)
        renderer = GameRenderer(game)
        output = renderer.render_frame()

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    @pytest.mark.parametrize("dimensions", [(128, 128), (256, 256), (384, 384)])
    def test_different_game_sizes(self, dimensions):
        """Game should render at different sizes."""
        width, height = dimensions
        game = create_game(width, height, 16)
        renderer = GameRenderer(game)
        output = renderer.render_frame()

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        assert len(output) > 100  # Should have content
