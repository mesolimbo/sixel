"""
Renderer module for the snake game.

Handles converting game state to sixel graphics.
Separated from terminal handling for single responsibility.
"""

from game import GameState
from typing import Optional
from sixel import (
    pixels_to_sixel,
    sixel_to_png,
    verify_sixel_roundtrip,
    create_pixel_buffer,
    clear_pixel_buffer,
    fill_rect,
    draw_text,
    get_text_width,
    COLOR_INDICES,
    FONT_HEIGHT,
)

GAME_TITLE = "SIXEL SNAKE"


class GameRenderer:
    """
    Renders game state to sixel graphics.

    Encapsulates all rendering logic including layout calculations,
    text rendering, and sixel conversion.
    """

    def __init__(self, game: GameState):
        """
        Initialize renderer with game state.

        Args:
            game: The game state to render
        """
        self.game = game

        # Scale factor based on pixel size (1x at 16px, 1.5x at 24px, 2x at 32px)
        scale_ratio = game.pixel_size / 16

        # Layout constants (scaled)
        self.title_height = int(50 * scale_ratio)
        self.status_height = int(120 * scale_ratio)
        self.padding = int(40 * scale_ratio)

        # Text scales (scaled, must be integers >= 1)
        self.title_scale = max(1, int(4 * scale_ratio))
        self.score_scale = max(1, int(2 * scale_ratio))
        self.game_over_scale = max(1, int(4 * scale_ratio))
        self.hint_scale = max(1, int(2 * scale_ratio))

        # Spacing scale for consistent proportions
        self.spacing_scale = scale_ratio

        # Calculate dimensions
        self.game_size = game.width * game.pixel_size
        game_based_width = self.game_size + self.padding

        # Ensure frame is wide enough for the title
        title_width = get_text_width(GAME_TITLE, self.title_scale)
        min_title_width = title_width + self.padding

        self.frame_width = max(game_based_width, min_title_width)
        self.frame_height = self.title_height + self.game_size + self.status_height
        self.game_area_y = self.title_height
        self.game_area_x = (self.frame_width - self.game_size) // 2

        # Reusable pixel buffer (optimization: avoid allocation per frame)
        self._pixels = create_pixel_buffer(
            self.frame_width,
            self.frame_height,
            COLOR_INDICES["background"]
        )
        self._bg_color = COLOR_INDICES["background"]

    def render_frame(self, show_game_over: bool = False) -> str:
        """
        Render the complete frame as a sixel string.

        Args:
            show_game_over: Whether to display game over text

        Returns:
            Sixel escape sequence string
        """
        # Clear reusable pixel buffer (optimization: faster than creating new)
        clear_pixel_buffer(self._pixels, self._bg_color)
        pixels = self._pixels

        self._draw_frame_border(pixels)
        self._draw_title(pixels)
        self._draw_game_border(pixels)
        self._draw_food(pixels)
        self._draw_snake(pixels)
        self._draw_score(pixels)

        if show_game_over:
            self._draw_game_over(pixels)

        return pixels_to_sixel(pixels, self.frame_width, self.frame_height)

    def _draw_frame_border(self, pixels: list) -> None:
        """Draw the outer frame border."""
        frame_color = COLOR_INDICES["text_green"]
        border_width = int(2 * self.spacing_scale)

        # Top edge
        fill_rect(pixels, 0, 0, self.frame_width, border_width, frame_color)
        # Bottom edge
        fill_rect(
            pixels, 0, self.frame_height - border_width,
            self.frame_width, border_width, frame_color
        )
        # Left edge
        fill_rect(pixels, 0, 0, border_width, self.frame_height, frame_color)
        # Right edge
        fill_rect(
            pixels, self.frame_width - border_width, 0,
            border_width, self.frame_height, frame_color
        )

    def _draw_title(self, pixels: list) -> None:
        """Draw the game title."""
        title_width = get_text_width(GAME_TITLE, self.title_scale)
        title_x = (self.frame_width - title_width) // 2
        title_y = int(8 * self.spacing_scale)
        draw_text(pixels, title_x, title_y, GAME_TITLE, COLOR_INDICES["text_green"], self.title_scale)

    def _draw_game_border(self, pixels: list) -> None:
        """Draw the border around the game area."""
        ps = self.game.pixel_size
        border_color = COLOR_INDICES["border"]
        gx, gy = self.game_area_x, self.game_area_y

        # Top and bottom
        fill_rect(pixels, gx, gy, self.game_size, ps, border_color)
        fill_rect(pixels, gx, gy + self.game_size - ps, self.game_size, ps, border_color)
        # Left and right
        fill_rect(pixels, gx, gy, ps, self.game_size, border_color)
        fill_rect(pixels, gx + self.game_size - ps, gy, ps, self.game_size, border_color)

    def _draw_food(self, pixels: list) -> None:
        """Draw the food item."""
        ps = self.game.pixel_size
        fx, fy = self.game.food
        fill_rect(
            pixels,
            self.game_area_x + fx * ps,
            self.game_area_y + fy * ps,
            ps, ps,
            COLOR_INDICES["food"]
        )

    def _draw_snake(self, pixels: list) -> None:
        """Draw the snake body and head."""
        ps = self.game.pixel_size

        # Draw body segments
        for segment in self.game.snake[1:]:
            sx, sy = segment
            fill_rect(
                pixels,
                self.game_area_x + sx * ps,
                self.game_area_y + sy * ps,
                ps, ps,
                COLOR_INDICES["snake_body"]
            )

        # Draw head
        if self.game.snake:
            hx, hy = self.game.snake[0]
            fill_rect(
                pixels,
                self.game_area_x + hx * ps,
                self.game_area_y + hy * ps,
                ps, ps,
                COLOR_INDICES["snake_head"]
            )

    def _draw_score(self, pixels: list) -> None:
        """Draw the current score."""
        score_text = f"SCORE: {self.game.score}"
        score_width = get_text_width(score_text, self.score_scale)
        score_x = (self.frame_width - score_width) // 2
        score_y = int(self.game_area_y + self.game_size + 16 * self.spacing_scale)
        draw_text(pixels, score_x, score_y, score_text, COLOR_INDICES["text"], self.score_scale)

    def _draw_game_over(self, pixels: list) -> None:
        """Draw game over text and hints."""
        score_y = int(self.game_area_y + self.game_size + 16 * self.spacing_scale)

        # Game over text
        go_text = "GAME OVER!"
        go_width = get_text_width(go_text, self.game_over_scale)
        go_x = (self.frame_width - go_width) // 2
        go_y = int(score_y + FONT_HEIGHT * self.score_scale + 16 * self.spacing_scale)
        draw_text(pixels, go_x, go_y, go_text, COLOR_INDICES["food"], self.game_over_scale)

        # Hint text
        hint_text = "'R' RESTART  'Q' QUIT"
        hint_width = get_text_width(hint_text, self.hint_scale)
        hint_x = (self.frame_width - hint_width) // 2
        hint_y = int(go_y + FONT_HEIGHT * self.game_over_scale + 12 * self.spacing_scale)
        draw_text(pixels, hint_x, hint_y, hint_text, COLOR_INDICES["text"], self.hint_scale)

    def calculate_terminal_position(
        self, term_cols: int, term_rows: int
    ) -> tuple[int, int]:
        """
        Calculate the position to center the game in the terminal.

        Args:
            term_cols: Terminal width in columns
            term_rows: Terminal height in rows

        Returns:
            Tuple of (row, col) for cursor positioning (1-indexed)
        """
        # Approximate character cell dimensions
        pixels_per_col = 10
        pixels_per_row = 20

        sixel_char_width = self.frame_width // pixels_per_col
        sixel_char_height = self.frame_height // pixels_per_row

        center_col = max(1, (term_cols - sixel_char_width) // 2)
        center_row = max(1, (term_rows - sixel_char_height) // 2)

        return center_row, center_col

    def save_screenshot(
        self,
        output_path: str,
        show_game_over: bool = False,
        verify: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Save a screenshot of the current game state as a PNG.

        This uses the full round-trip: renders to sixel format, then
        decodes that sixel back to pixels to verify the encoding.
        The resulting PNG shows exactly what a sixel terminal would display.

        Args:
            output_path: Path to save the PNG file
            show_game_over: Whether to display game over text
            verify: If True, verify the sixel round-trip matches original pixels

        Returns:
            Tuple of (success, error_message). If success is True, error_message is None.
        """
        # Build the original pixel buffer
        pixels = create_pixel_buffer(
            self.frame_width,
            self.frame_height,
            COLOR_INDICES["background"]
        )

        self._draw_frame_border(pixels)
        self._draw_title(pixels)
        self._draw_game_border(pixels)
        self._draw_food(pixels)
        self._draw_snake(pixels)
        self._draw_score(pixels)

        if show_game_over:
            self._draw_game_over(pixels)

        # Encode to sixel (what would be sent to terminal)
        sixel_output = pixels_to_sixel(pixels, self.frame_width, self.frame_height)

        # Verify the round-trip if requested
        if verify:
            success, error = verify_sixel_roundtrip(pixels, sixel_output)
            if not success:
                return False, f"Sixel round-trip verification failed: {error}"

        # Decode sixel and save as PNG
        if not sixel_to_png(sixel_output, output_path):
            return False, "Failed to save PNG"

        return True, None
