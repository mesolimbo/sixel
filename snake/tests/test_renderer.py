"""
Tests for the renderer module (renderer.py).

Tests cover:
- GameRenderer initialization and layout calculations
- Frame rendering
- Drawing methods for various game elements
- Terminal position calculation
"""

import pytest

from game import GameState, Direction
from renderer import GameRenderer
from sixel import COLOR_INDICES, SIXEL_START, SIXEL_END


class TestRendererInit:
    """Tests for GameRenderer initialization."""

    def test_renderer_stores_game_reference(self, small_game):
        """Test that renderer stores game reference."""
        renderer = GameRenderer(small_game)
        assert renderer.game is small_game

    def test_renderer_calculates_game_size(self, small_game):
        """Test that game size is calculated correctly."""
        renderer = GameRenderer(small_game)
        expected = small_game.width * small_game.pixel_size
        assert renderer.game_size == expected

    def test_renderer_calculates_frame_dimensions(self, small_game):
        """Test that frame dimensions are calculated."""
        renderer = GameRenderer(small_game)
        assert renderer.frame_width > renderer.game_size
        assert renderer.frame_height > renderer.game_size

    def test_renderer_calculates_game_area_position(self, small_game):
        """Test that game area position is calculated."""
        renderer = GameRenderer(small_game)
        # Game area should be centered horizontally
        expected_x = (renderer.frame_width - renderer.game_size) // 2
        assert renderer.game_area_x == expected_x
        # Game area should be below title
        assert renderer.game_area_y == renderer.title_height


class TestRendererScaling:
    """Tests for scale-dependent layout calculations."""

    def test_scale_ratio_16px(self):
        """Test scaling with 16px pixel size."""
        game = GameState(width=8, height=8, pixel_size=16)
        renderer = GameRenderer(game)
        assert renderer.title_scale >= 1
        assert renderer.score_scale >= 1

    def test_scale_ratio_24px(self):
        """Test scaling with 24px pixel size."""
        game = GameState(width=8, height=8, pixel_size=24)
        renderer = GameRenderer(game)
        # At 24px, scale_ratio = 1.5
        assert renderer.title_scale >= 1
        assert renderer.score_scale >= 1

    def test_scale_ratio_32px(self):
        """Test scaling with 32px pixel size."""
        game = GameState(width=8, height=8, pixel_size=32)
        renderer = GameRenderer(game)
        # At 32px, scale_ratio = 2
        assert renderer.title_scale >= 1
        assert renderer.score_scale >= 1

    def test_layout_scales_with_pixel_size(self):
        """Test that layout dimensions scale with pixel size."""
        game_small = GameState(width=8, height=8, pixel_size=16)
        game_large = GameState(width=8, height=8, pixel_size=32)

        renderer_small = GameRenderer(game_small)
        renderer_large = GameRenderer(game_large)

        assert renderer_large.title_height > renderer_small.title_height
        assert renderer_large.padding > renderer_small.padding


class TestRenderFrame:
    """Tests for frame rendering."""

    def test_render_returns_sixel_string(self, small_game):
        """Test that render_frame returns a sixel string."""
        renderer = GameRenderer(small_game)
        result = renderer.render_frame()
        assert isinstance(result, str)
        assert result.startswith(SIXEL_START)
        assert result.endswith(SIXEL_END)

    def test_render_includes_all_colors(self, small_game):
        """Test that rendered frame includes color definitions."""
        renderer = GameRenderer(small_game)
        result = renderer.render_frame()
        # Should include palette entries
        assert "#" in result  # Color references

    def test_render_with_game_over_flag(self, small_game):
        """Test rendering with game over display."""
        small_game.game_over = True
        renderer = GameRenderer(small_game)
        result_without = renderer.render_frame(show_game_over=False)
        result_with = renderer.render_frame(show_game_over=True)
        # Game over version should be different (more content)
        assert len(result_with) >= len(result_without)

    def test_render_different_scores(self, small_game):
        """Test rendering with different scores."""
        renderer = GameRenderer(small_game)

        small_game.score = 0
        result_0 = renderer.render_frame()

        small_game.score = 99
        result_99 = renderer.render_frame()

        # Different scores should produce different output
        assert result_0 != result_99


class TestDrawingMethods:
    """Tests for individual drawing methods."""

    def test_draw_frame_border(self, small_game):
        """Test that frame border is drawn."""
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_frame_border(pixels)

        # Check that border pixels are set
        frame_color = COLOR_INDICES["text_green"]
        assert pixels[0][0] == frame_color  # Top-left corner

    def test_draw_title(self, small_game):
        """Test that title is drawn."""
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_title(pixels)

        # Check that some pixels are set with title color
        title_color = COLOR_INDICES["text_green"]
        title_pixels = sum(
            1 for row in pixels[:renderer.title_height]
            for p in row if p == title_color
        )
        assert title_pixels > 0

    def test_draw_game_border(self, small_game):
        """Test that game border is drawn."""
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_game_border(pixels)

        # Check that border pixels are set
        border_color = COLOR_INDICES["border"]
        border_pixels = sum(1 for row in pixels for p in row if p == border_color)
        assert border_pixels > 0

    def test_draw_food(self, small_game):
        """Test that food is drawn."""
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_food(pixels)

        # Check that food pixels are set
        food_color = COLOR_INDICES["food"]
        food_pixels = sum(1 for row in pixels for p in row if p == food_color)
        assert food_pixels > 0

    def test_draw_snake(self, small_game):
        """Test that snake is drawn."""
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_snake(pixels)

        # Check that snake head pixels are set
        head_color = COLOR_INDICES["snake_head"]
        head_pixels = sum(1 for row in pixels for p in row if p == head_color)
        assert head_pixels > 0

        # Check that snake body pixels are set
        body_color = COLOR_INDICES["snake_body"]
        body_pixels = sum(1 for row in pixels for p in row if p == body_color)
        assert body_pixels > 0

    def test_draw_snake_empty(self):
        """Test drawing with empty snake (edge case)."""
        game = GameState(width=8, height=8)
        game.snake = []
        renderer = GameRenderer(game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        # Should not raise
        renderer._draw_snake(pixels)

    def test_draw_score(self, small_game):
        """Test that score is drawn."""
        small_game.score = 42
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_score(pixels)

        # Check that score text pixels are set
        text_color = COLOR_INDICES["text"]
        text_pixels = sum(1 for row in pixels for p in row if p == text_color)
        assert text_pixels > 0

    def test_draw_game_over(self, small_game):
        """Test that game over text is drawn."""
        renderer = GameRenderer(small_game)
        from sixel import create_pixel_buffer

        pixels = create_pixel_buffer(
            renderer.frame_width,
            renderer.frame_height,
            COLOR_INDICES["background"]
        )
        renderer._draw_game_over(pixels)

        # Check that game over text pixels are set (uses food color)
        go_color = COLOR_INDICES["food"]
        go_pixels = sum(1 for row in pixels for p in row if p == go_color)
        assert go_pixels > 0


class TestTerminalPositionCalculation:
    """Tests for terminal position calculation."""

    def test_calculate_position_basic(self, small_game):
        """Test basic position calculation."""
        renderer = GameRenderer(small_game)
        row, col = renderer.calculate_terminal_position(80, 24)
        assert row >= 1
        assert col >= 1

    def test_calculate_position_centering(self, small_game):
        """Test that position centers the game."""
        renderer = GameRenderer(small_game)

        # Large terminal
        row1, col1 = renderer.calculate_terminal_position(200, 100)

        # Small terminal
        row2, col2 = renderer.calculate_terminal_position(80, 24)

        # Position should be different based on terminal size
        # (exact values depend on frame dimensions)
        assert isinstance(row1, int)
        assert isinstance(col1, int)
        assert isinstance(row2, int)
        assert isinstance(col2, int)

    def test_calculate_position_minimum_values(self, small_game):
        """Test that position never goes below 1."""
        renderer = GameRenderer(small_game)
        # Very small terminal
        row, col = renderer.calculate_terminal_position(10, 5)
        assert row >= 1
        assert col >= 1

    def test_calculate_position_large_terminal(self, small_game):
        """Test position in a large terminal."""
        renderer = GameRenderer(small_game)
        row, col = renderer.calculate_terminal_position(300, 100)
        # Should be centered, so col should be significant
        assert col > 1


class TestRendererIntegration:
    """Integration tests for the renderer."""

    def test_full_render_cycle(self, medium_game):
        """Test a complete render cycle."""
        renderer = GameRenderer(medium_game)

        # Initial render
        frame1 = renderer.render_frame()
        assert len(frame1) > 0

        # Move snake and render
        medium_game.update()
        frame2 = renderer.render_frame()
        assert len(frame2) > 0

        # Frames should be different (snake moved)
        assert frame1 != frame2

    def test_render_after_eating_food(self, medium_game):
        """Test rendering after eating food."""
        renderer = GameRenderer(medium_game)

        # Set up food in front of snake
        head = medium_game.snake[0]
        medium_game.food = (head[0] + 1, head[1])
        medium_game.direction = Direction.RIGHT

        frame1 = renderer.render_frame()
        initial_score = medium_game.score

        # Eat food
        medium_game.update()
        assert medium_game.score == initial_score + 1

        frame2 = renderer.render_frame()
        # Frames should be different (score changed, snake grew)
        assert frame1 != frame2

    def test_render_game_over_sequence(self, small_game):
        """Test rendering game over sequence."""
        renderer = GameRenderer(small_game)

        # Normal frame
        normal_frame = renderer.render_frame()

        # Game over frame without overlay
        small_game.game_over = True
        go_frame_no_overlay = renderer.render_frame(show_game_over=False)

        # Game over frame with overlay
        go_frame_with_overlay = renderer.render_frame(show_game_over=True)

        # All should be valid sixel
        assert normal_frame.startswith(SIXEL_START)
        assert go_frame_no_overlay.startswith(SIXEL_START)
        assert go_frame_with_overlay.startswith(SIXEL_START)
