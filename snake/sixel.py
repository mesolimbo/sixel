"""
Sixel graphics generation module.

Sixel is a graphics format that encodes 6 vertical pixels per character.
This module provides utilities to convert pixel buffers to sixel sequences.
"""

from typing import List, Tuple

# Sixel escape sequences
SIXEL_START = "\x1bPq"
SIXEL_END = "\x1b\\"
SIXEL_NEWLINE = "-"

# Color palette for the snake game
COLORS = {
    "background": (0, 0, 0),       # Black
    "snake_head": (0, 200, 0),     # Bright green
    "snake_body": (0, 150, 0),     # Green
    "food": (255, 50, 50),         # Red
    "border": (100, 100, 100),     # Gray
}

COLOR_INDICES = {
    "background": 0,
    "snake_head": 1,
    "snake_body": 2,
    "food": 3,
    "border": 4,
}


def rgb_to_sixel_color(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """Convert 0-255 RGB to 0-100 sixel RGB."""
    return (r * 100 // 255, g * 100 // 255, b * 100 // 255)


def define_color(index: int, r: int, g: int, b: int) -> str:
    """Generate a sixel color definition string."""
    sr, sg, sb = rgb_to_sixel_color(r, g, b)
    return f"#{index};2;{sr};{sg};{sb}"


def generate_palette() -> str:
    """Generate the sixel color palette definitions."""
    palette = []
    for name, (r, g, b) in COLORS.items():
        idx = COLOR_INDICES[name]
        palette.append(define_color(idx, r, g, b))
    return "".join(palette)


def encode_sixel_row(pixels: List[List[int]], start_y: int, width: int) -> str:
    """
    Encode a row of 6 vertical pixels into sixel characters.

    Args:
        pixels: 2D array of color indices [y][x]
        start_y: Starting y coordinate (top of the 6-pixel band)
        width: Width of the image

    Returns:
        Sixel string for this row, with color switching
    """
    height = len(pixels)

    # Group by color to minimize color switches
    color_data = {}

    for x in range(width):
        # Build the sixel value for this column
        for color_idx in COLOR_INDICES.values():
            sixel_value = 0
            for bit in range(6):
                y = start_y + bit
                if y < height and pixels[y][x] == color_idx:
                    sixel_value |= (1 << bit)

            if sixel_value > 0:
                if color_idx not in color_data:
                    color_data[color_idx] = [0] * width
                color_data[color_idx][x] = sixel_value

    # Build output string with RLE compression
    result = []
    for color_idx in sorted(color_data.keys()):
        result.append(f"#{color_idx}")
        data = color_data[color_idx]

        # Simple output without RLE for clarity
        for val in data:
            result.append(chr(63 + val))

        # Carriage return to start of line for next color
        result.append("$")

    return "".join(result)


def pixels_to_sixel(pixels: List[List[int]], width: int, height: int) -> str:
    """
    Convert a 2D pixel buffer to a sixel string.

    Args:
        pixels: 2D array of color indices [y][x]
        width: Width of the image
        height: Height of the image

    Returns:
        Complete sixel escape sequence string
    """
    parts = [SIXEL_START]
    parts.append(generate_palette())

    # Process in bands of 6 rows
    for start_y in range(0, height, 6):
        if start_y > 0:
            parts.append(SIXEL_NEWLINE)
        parts.append(encode_sixel_row(pixels, start_y, width))

    parts.append(SIXEL_END)
    return "".join(parts)


def create_pixel_buffer(width: int, height: int, fill: int = 0) -> List[List[int]]:
    """Create a 2D pixel buffer filled with a color index."""
    return [[fill for _ in range(width)] for _ in range(height)]


def set_pixel(pixels: List[List[int]], x: int, y: int, color_idx: int) -> None:
    """Set a pixel in the buffer to a color index."""
    if 0 <= y < len(pixels) and 0 <= x < len(pixels[0]):
        pixels[y][x] = color_idx


def fill_rect(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    color_idx: int
) -> None:
    """Fill a rectangle in the pixel buffer."""
    for py in range(y, y + h):
        for px in range(x, x + w):
            set_pixel(pixels, px, py, color_idx)
