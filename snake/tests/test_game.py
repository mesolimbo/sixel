"""
Tests for the game logic module (game.py).

Tests cover:
- GameState initialization
- Direction changes
- Movement and collisions
- Food spawning
- Score calculation
- Game reset
"""

import pytest
from unittest.mock import patch
import random

from game import GameState, Direction, create_game


class TestDirection:
    """Tests for the Direction enum."""

    def test_direction_values(self):
        """Test that directions have correct dx, dy values."""
        assert Direction.UP.value == (0, -1)
        assert Direction.DOWN.value == (0, 1)
        assert Direction.LEFT.value == (-1, 0)
        assert Direction.RIGHT.value == (1, 0)

    def test_direction_count(self):
        """Test that we have exactly 4 directions."""
        assert len(Direction) == 4


class TestGameStateInit:
    """Tests for GameState initialization."""

    def test_default_initialization(self, small_game):
        """Test that a game initializes with correct defaults."""
        assert small_game.width == 8
        assert small_game.height == 8
        assert small_game.pixel_size == 16
        assert small_game.score == 0
        assert small_game.game_over is False
        assert small_game.direction == Direction.RIGHT

    def test_snake_starts_in_center(self, small_game):
        """Test that snake starts in the center of the game area."""
        center_x = small_game.width // 2
        center_y = small_game.height // 2
        assert small_game.snake[0] == (center_x, center_y)
        assert len(small_game.snake) == 3

    def test_snake_initial_shape(self, small_game):
        """Test that snake starts as a horizontal line."""
        head = small_game.snake[0]
        for i, segment in enumerate(small_game.snake):
            assert segment == (head[0] - i, head[1])

    def test_food_spawned_on_init(self, small_game):
        """Test that food is spawned during initialization."""
        assert small_game.food is not None
        assert small_game.food != (0, 0) or small_game.food not in small_game.snake

    def test_food_not_on_snake(self, small_game):
        """Test that food is never spawned on the snake."""
        assert small_game.food not in small_game.snake

    def test_food_within_bounds(self, small_game):
        """Test that food is spawned within game boundaries."""
        fx, fy = small_game.food
        assert 1 <= fx < small_game.width - 1
        assert 1 <= fy < small_game.height - 1

    def test_custom_snake_initialization(self, custom_game):
        """Test that custom snake position is preserved."""
        custom_snake = [(3, 3), (2, 3), (1, 3)]
        game = custom_game(snake=custom_snake)
        assert game.snake == custom_snake


class TestDirectionChange:
    """Tests for direction change logic."""

    def test_change_direction_valid(self, small_game):
        """Test valid direction changes."""
        small_game.direction = Direction.RIGHT
        small_game.change_direction(Direction.UP)
        assert small_game.direction == Direction.UP

    def test_change_direction_opposite_blocked(self, small_game):
        """Test that 180-degree turns are blocked."""
        small_game.direction = Direction.RIGHT
        small_game.change_direction(Direction.LEFT)
        assert small_game.direction == Direction.RIGHT

    def test_all_opposite_directions_blocked(self):
        """Test all opposite direction pairs are blocked."""
        opposites = [
            (Direction.UP, Direction.DOWN),
            (Direction.DOWN, Direction.UP),
            (Direction.LEFT, Direction.RIGHT),
            (Direction.RIGHT, Direction.LEFT),
        ]
        for current, opposite in opposites:
            game = GameState(width=8, height=8)
            game.direction = current
            game.change_direction(opposite)
            assert game.direction == current

    def test_perpendicular_directions_allowed(self):
        """Test that perpendicular direction changes are allowed."""
        perpendiculars = [
            (Direction.UP, Direction.LEFT),
            (Direction.UP, Direction.RIGHT),
            (Direction.DOWN, Direction.LEFT),
            (Direction.DOWN, Direction.RIGHT),
            (Direction.LEFT, Direction.UP),
            (Direction.LEFT, Direction.DOWN),
            (Direction.RIGHT, Direction.UP),
            (Direction.RIGHT, Direction.DOWN),
        ]
        for current, new in perpendiculars:
            game = GameState(width=8, height=8)
            game.direction = current
            game.change_direction(new)
            assert game.direction == new


class TestGameUpdate:
    """Tests for game update logic."""

    def test_update_moves_snake_right(self, custom_game):
        """Test that snake moves in the right direction."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(1, 1))
        game.direction = Direction.RIGHT
        game.update()
        assert game.snake[0] == (5, 4)
        assert len(game.snake) == 3

    def test_update_moves_snake_up(self, custom_game):
        """Test that snake moves up correctly."""
        game = custom_game(snake=[(4, 4), (4, 5), (4, 6)], food=(1, 1))
        game.direction = Direction.UP
        game.update()
        assert game.snake[0] == (4, 3)

    def test_update_moves_snake_down(self, custom_game):
        """Test that snake moves down correctly."""
        game = custom_game(snake=[(4, 4), (4, 3), (4, 2)], food=(1, 1))
        game.direction = Direction.DOWN
        game.update()
        assert game.snake[0] == (4, 5)

    def test_update_moves_snake_left(self, custom_game):
        """Test that snake moves left correctly."""
        game = custom_game(snake=[(4, 4), (5, 4), (6, 4)], food=(1, 1))
        game.direction = Direction.LEFT
        game.update()
        assert game.snake[0] == (3, 4)

    def test_tail_follows_head(self, custom_game):
        """Test that tail follows head during movement."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(1, 1))
        game.direction = Direction.UP
        game.update()
        assert game.snake == [(4, 3), (4, 4), (3, 4)]

    def test_update_returns_true_when_alive(self, custom_game):
        """Test that update returns True when game is running."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(1, 1))
        assert game.update() is True

    def test_update_returns_false_when_game_over(self, custom_game):
        """Test that update returns False when game is over."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)])
        game.game_over = True
        assert game.update() is False


class TestWallCollision:
    """Tests for wall collision detection."""

    def test_collision_with_left_wall(self, custom_game):
        """Test collision with left wall."""
        game = custom_game(snake=[(1, 4), (2, 4), (3, 4)], food=(5, 5))
        game.direction = Direction.LEFT
        result = game.update()
        assert result is False
        assert game.game_over is True

    def test_collision_with_right_wall(self, custom_game):
        """Test collision with right wall."""
        game = custom_game(width=8, snake=[(6, 4), (5, 4), (4, 4)], food=(2, 2))
        game.direction = Direction.RIGHT
        result = game.update()
        assert result is False
        assert game.game_over is True

    def test_collision_with_top_wall(self, custom_game):
        """Test collision with top wall."""
        game = custom_game(snake=[(4, 1), (4, 2), (4, 3)], food=(2, 5))
        game.direction = Direction.UP
        result = game.update()
        assert result is False
        assert game.game_over is True

    def test_collision_with_bottom_wall(self, custom_game):
        """Test collision with bottom wall."""
        game = custom_game(height=8, snake=[(4, 6), (4, 5), (4, 4)], food=(2, 2))
        game.direction = Direction.DOWN
        result = game.update()
        assert result is False
        assert game.game_over is True


class TestSelfCollision:
    """Tests for self-collision detection."""

    def test_collision_with_own_body(self, custom_game):
        """Test collision when snake runs into itself."""
        # Snake arranged in a shape where it can hit itself
        game = custom_game(
            snake=[(4, 4), (4, 5), (5, 5), (5, 4), (5, 3)],
            food=(1, 1)
        )
        game.direction = Direction.RIGHT
        result = game.update()
        assert result is False
        assert game.game_over is True

    def test_no_collision_when_moving_safely(self, custom_game):
        """Test no collision when snake moves safely."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(1, 1))
        game.direction = Direction.UP
        result = game.update()
        assert result is True
        assert game.game_over is False


class TestFoodCollection:
    """Tests for food collection and scoring."""

    def test_eating_food_increases_score(self, custom_game):
        """Test that eating food increases score."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(5, 4))
        game.direction = Direction.RIGHT
        game.update()
        assert game.score == 1

    def test_eating_food_grows_snake(self, custom_game):
        """Test that eating food grows the snake."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(5, 4))
        initial_length = len(game.snake)
        game.direction = Direction.RIGHT
        game.update()
        assert len(game.snake) == initial_length + 1

    def test_new_food_spawned_after_eating(self, custom_game):
        """Test that new food is spawned after eating."""
        game = custom_game(snake=[(4, 4), (3, 4), (2, 4)], food=(5, 4))
        old_food = game.food
        game.direction = Direction.RIGHT
        game.update()
        # Food should be different or at least not on the snake
        assert game.food not in game.snake

    def test_multiple_food_collections(self, custom_game):
        """Test collecting multiple food items."""
        game = custom_game(snake=[(3, 4), (2, 4), (1, 4)], food=(4, 4))
        game.direction = Direction.RIGHT

        # Eat first food
        game.update()
        assert game.score == 1
        assert len(game.snake) == 4

        # Position new food and eat it
        game.food = (5, 4)
        game.update()
        assert game.score == 2
        assert len(game.snake) == 5


class TestFoodSpawning:
    """Tests for food spawning logic."""

    def test_food_not_on_border(self, small_game):
        """Test that food is never placed on the border."""
        for _ in range(100):  # Run multiple times due to randomness
            small_game._spawn_food()
            fx, fy = small_game.food
            assert fx > 0 and fx < small_game.width - 1
            assert fy > 0 and fy < small_game.height - 1

    def test_food_spawn_with_full_board(self, custom_game):
        """Test food spawning when board is nearly full."""
        # Create a snake that fills most of the board
        game = custom_game(width=4, height=4)
        # Fill most positions with snake
        game.snake = [(1, 1), (2, 1), (1, 2)]
        game._spawn_food()
        # Food should still be placed in available spot
        assert game.food not in game.snake


class TestGameReset:
    """Tests for game reset functionality."""

    def test_reset_clears_score(self, small_game):
        """Test that reset clears the score."""
        small_game.score = 10
        small_game.reset()
        assert small_game.score == 0

    def test_reset_clears_game_over(self, small_game):
        """Test that reset clears game over state."""
        small_game.game_over = True
        small_game.reset()
        assert small_game.game_over is False

    def test_reset_restores_direction(self, small_game):
        """Test that reset restores initial direction."""
        small_game.direction = Direction.UP
        small_game.reset()
        assert small_game.direction == Direction.RIGHT

    def test_reset_restores_snake_position(self, small_game):
        """Test that reset restores snake to center."""
        small_game.snake = [(1, 1), (1, 2)]
        small_game.reset()
        center_x = small_game.width // 2
        center_y = small_game.height // 2
        assert small_game.snake[0] == (center_x, center_y)
        assert len(small_game.snake) == 3

    def test_reset_spawns_new_food(self, small_game):
        """Test that reset spawns new food."""
        small_game.reset()
        assert small_game.food not in small_game.snake
        fx, fy = small_game.food
        assert 1 <= fx < small_game.width - 1
        assert 1 <= fy < small_game.height - 1


class TestCreateGame:
    """Tests for the create_game factory function."""

    def test_create_game_default(self):
        """Test create_game with default parameters."""
        game = create_game()
        assert game.width == 8  # 128 / 16
        assert game.height == 8  # 128 / 16
        assert game.pixel_size == 16

    def test_create_game_custom_size(self):
        """Test create_game with custom pixel dimensions."""
        game = create_game(pixel_width=256, pixel_height=256, pixel_size=16)
        assert game.width == 16
        assert game.height == 16

    def test_create_game_custom_pixel_size(self):
        """Test create_game with different pixel sizes."""
        game = create_game(pixel_width=128, pixel_height=128, pixel_size=32)
        assert game.width == 4
        assert game.height == 4
        assert game.pixel_size == 32

    def test_create_game_initializes_properly(self):
        """Test that created game is fully initialized."""
        game = create_game()
        assert len(game.snake) == 3
        assert game.food is not None
        assert game.score == 0
        assert game.game_over is False
