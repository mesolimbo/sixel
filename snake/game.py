"""
Snake game logic module.

Contains the game state and rules, independent of rendering and input handling.
"""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


@dataclass
class GameState:
    """Represents the complete state of the snake game."""
    width: int
    height: int
    snake: List[Tuple[int, int]] = field(default_factory=list)
    direction: Direction = Direction.RIGHT
    next_direction: Direction = Direction.RIGHT  # Queued direction for next tick
    food: Tuple[int, int] = (0, 0)
    score: int = 0
    game_over: bool = False
    pixel_size: int = 16  # Each game cell is 16x16 pixels

    def __post_init__(self):
        if not self.snake:
            # Start snake in the middle
            center_x = self.width // 2
            center_y = self.height // 2
            self.snake = [
                (center_x, center_y),
                (center_x - 1, center_y),
                (center_x - 2, center_y),
            ]
            self._spawn_food()

    def _spawn_food(self) -> None:
        """Spawn food at a random location not occupied by the snake."""
        available = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if (x, y) not in self.snake:
                    available.append((x, y))

        if available:
            self.food = random.choice(available)

    def change_direction(self, new_direction: Direction) -> None:
        """Change the snake's direction, preventing 180-degree turns.

        Direction changes are queued and only applied on the next update().
        This prevents rapid key presses from causing the snake to reverse
        into itself through a sequence of perpendicular turns.
        """
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }
        # Check against current committed direction to prevent reversal
        if new_direction != opposite.get(self.direction):
            self.next_direction = new_direction

    def update(self) -> bool:
        """
        Update the game state by one tick.

        Returns:
            True if the game is still running, False if game over.
        """
        if self.game_over:
            return False

        # Apply queued direction change (only one change per tick)
        self.direction = self.next_direction

        # Calculate new head position
        dx, dy = self.direction.value
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        # Check wall collision
        if (new_head[0] <= 0 or new_head[0] >= self.width - 1 or
                new_head[1] <= 0 or new_head[1] >= self.height - 1):
            self.game_over = True
            return False

        # Check self collision
        if new_head in self.snake:
            self.game_over = True
            return False

        # Move snake
        self.snake.insert(0, new_head)

        # Check food collision
        if new_head == self.food:
            self.score += 1
            self._spawn_food()
        else:
            self.snake.pop()

        return True

    def reset(self) -> None:
        """Reset the game to initial state."""
        center_x = self.width // 2
        center_y = self.height // 2
        self.snake = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x - 2, center_y),
        ]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.score = 0
        self.game_over = False
        self._spawn_food()


def create_game(
    pixel_width: int = 128,
    pixel_height: int = 128,
    pixel_size: int = 16
) -> GameState:
    """
    Create a new game state.

    Args:
        pixel_width: Total width in pixels
        pixel_height: Total height in pixels
        pixel_size: Size of each game cell in pixels

    Returns:
        A new GameState instance
    """
    game_width = pixel_width // pixel_size
    game_height = pixel_height // pixel_size

    return GameState(
        width=game_width,
        height=game_height,
        pixel_size=pixel_size
    )
