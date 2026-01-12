"""
Screenshot capture tests for the snake game.

These tests render the game and save screenshots as PNG files,
which are uploaded as CI artifacts for visual inspection.

Screenshots are generated using a full round-trip through sixel encoding:
1. Render game state to pixel buffer
2. Encode pixel buffer to sixel escape sequences
3. Verify decoded sixel matches original pixels (lossless check)
4. Decode sixel and save as PNG
"""

import os
import sys
import platform
import pytest
from pathlib import Path

# Add the snake package to the path
snake_dir = Path(__file__).parent.parent
sys.path.insert(0, str(snake_dir))

from game import GameState, Direction
from renderer import GameRenderer


# Output directory for screenshots
SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"


def get_os_name() -> str:
    """Get a clean OS name for the screenshot filename."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


@pytest.fixture(scope="module", autouse=True)
def setup_screenshot_dir():
    """Create the screenshots directory before tests run."""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    yield


class TestGameScreenshots:
    """Capture representative screenshots of the snake game."""

    def test_initial_game_state(self):
        """Capture a screenshot of the initial game state."""
        # Create a game with default settings
        game = GameState(width=16, height=16, pixel_size=16)
        renderer = GameRenderer(game)

        os_name = get_os_name()
        output_path = SCREENSHOT_DIR / f"game_initial_{os_name}.png"

        success, error = renderer.save_screenshot(str(output_path))
        assert success, f"Failed to save screenshot: {error}"
        assert output_path.exists(), f"Screenshot not found at {output_path}"

        # Verify the file has content
        file_size = output_path.stat().st_size
        assert file_size > 0, "Screenshot file is empty"

        print(f"\nScreenshot saved: {output_path} ({file_size} bytes)")
        print("Sixel round-trip verification: PASSED")

    def test_game_with_longer_snake(self):
        """Capture a screenshot with a longer snake (simulating gameplay)."""
        # Create a game with a snake that has grown
        game = GameState(width=16, height=16, pixel_size=16)

        # Manually set a longer snake to simulate gameplay
        game.snake = [
            (8, 8),   # head
            (7, 8),   # body
            (6, 8),
            (5, 8),
            (4, 8),
            (3, 8),
        ]
        game.score = 5
        game.food = (12, 5)

        renderer = GameRenderer(game)

        os_name = get_os_name()
        output_path = SCREENSHOT_DIR / f"game_playing_{os_name}.png"

        success, error = renderer.save_screenshot(str(output_path))
        assert success, f"Failed to save screenshot: {error}"
        assert output_path.exists(), f"Screenshot not found at {output_path}"

        file_size = output_path.stat().st_size
        print(f"\nScreenshot saved: {output_path} ({file_size} bytes)")
        print("Sixel round-trip verification: PASSED")

    def test_game_over_state(self):
        """Capture a screenshot of the game over state."""
        # Create a game in game over state
        game = GameState(width=16, height=16, pixel_size=16)
        game.snake = [(8, 8), (7, 8), (6, 8), (5, 8)]
        game.score = 10
        game.game_over = True

        renderer = GameRenderer(game)

        os_name = get_os_name()
        output_path = SCREENSHOT_DIR / f"game_over_{os_name}.png"

        success, error = renderer.save_screenshot(str(output_path), show_game_over=True)
        assert success, f"Failed to save screenshot: {error}"
        assert output_path.exists(), f"Screenshot not found at {output_path}"

        file_size = output_path.stat().st_size
        print(f"\nScreenshot saved: {output_path} ({file_size} bytes)")
        print("Sixel round-trip verification: PASSED")


class TestScreenshotVariations:
    """Test different game configurations for screenshot variety."""

    @pytest.mark.parametrize("pixel_size", [16, 24, 32])
    def test_different_pixel_sizes(self, pixel_size):
        """Capture screenshots at different pixel sizes."""
        game = GameState(width=12, height=12, pixel_size=pixel_size)
        game.snake = [(6, 6), (5, 6), (4, 6)]
        game.score = 2

        renderer = GameRenderer(game)

        os_name = get_os_name()
        output_path = SCREENSHOT_DIR / f"game_px{pixel_size}_{os_name}.png"

        success, error = renderer.save_screenshot(str(output_path))
        assert success, f"Failed to save screenshot for pixel_size={pixel_size}: {error}"

        file_size = output_path.stat().st_size
        print(f"\nScreenshot saved: {output_path} ({file_size} bytes)")
        print(f"Sixel round-trip verification (px{pixel_size}): PASSED")
