"""
Sixel graphics generation module.

Sixel encodes 6 vertical pixels per character. Each character value is 63 + bitmask,
where bit 0 = top pixel, bit 5 = bottom pixel.
"""

from typing import List, Tuple, Dict

# Sixel escape sequences
SIXEL_START = "\x1bPq"
SIXEL_END = "\x1b\\"
SIXEL_NEWLINE = "-"
SIXEL_CARRIAGE_RETURN = "$"

# Color palette for the snake game
COLORS = {
    "background": (0, 0, 0),       # Black
    "snake_head": (0, 255, 0),     # Bright green
    "snake_body": (0, 180, 0),     # Green
    "food": (255, 50, 50),         # Red
    "border": (100, 100, 100),     # Gray
    "text": (200, 200, 200),       # Light gray for text
    "text_green": (0, 255, 0),     # Green text
    "debug_blue": (0, 100, 255),   # Blue for debug
}

COLOR_INDICES = {
    "background": 0,
    "snake_head": 1,
    "snake_body": 2,
    "food": 3,
    "border": 4,
    "text": 5,
    "text_green": 6,
    "debug_blue": 7,
}

# Simple 5x7 bitmap font (each char is 5 wide, 7 tall)
# Each entry is a list of 7 rows, each row is 5 bits (as int)
FONT = {
    ' ': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
    '0': [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
    '1': [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    '2': [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111],
    '3': [0b01110, 0b10001, 0b00001, 0b00110, 0b00001, 0b10001, 0b01110],
    '4': [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
    '5': [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
    '6': [0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
    '7': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000],
    '8': [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
    '9': [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100],
    'A': [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'B': [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
    'C': [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
    'D': [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
    'E': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
    'F': [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
    'G': [0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01110],
    'H': [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
    'I': [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
    'J': [0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100],
    'K': [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
    'L': [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
    'M': [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
    'N': [0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001],
    'O': [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'P': [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
    'Q': [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
    'R': [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
    'S': [0b01110, 0b10001, 0b10000, 0b01110, 0b00001, 0b10001, 0b01110],
    'T': [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
    'U': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
    'V': [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
    'W': [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001],
    'X': [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
    'Y': [0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100],
    'Z': [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
    ':': [0b00000, 0b00100, 0b00100, 0b00000, 0b00100, 0b00100, 0b00000],
    '!': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100],
    "'": [0b00100, 0b00100, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000],
    ',': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b01000],
    '-': [0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000],
}

FONT_WIDTH = 5
FONT_HEIGHT = 7


def rgb_to_sixel_color(r: int, g: int, b: int) -> Tuple[int, int, int]:
    """Convert 0-255 RGB to 0-100 sixel RGB."""
    return (r * 100 // 255, g * 100 // 255, b * 100 // 255)


def generate_palette() -> str:
    """Generate the sixel color palette definitions."""
    palette = []
    for name, (r, g, b) in COLORS.items():
        idx = COLOR_INDICES[name]
        sr, sg, sb = rgb_to_sixel_color(r, g, b)
        palette.append(f"#{idx};2;{sr};{sg};{sb}")
    return "".join(palette)


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
    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0
    for py in range(max(0, y), min(height, y + h)):
        for px in range(max(0, x), min(width, x + w)):
            pixels[py][px] = color_idx


def draw_text(
    pixels: List[List[int]],
    x: int, y: int,
    text: str,
    color_idx: int,
    scale: int = 1
) -> int:
    """
    Draw text onto the pixel buffer using the bitmap font.

    Args:
        pixels: The pixel buffer
        x, y: Top-left position
        text: Text to draw
        color_idx: Color index to use
        scale: Scale factor (1 = 5x7, 2 = 10x14, etc.)

    Returns:
        Width of the rendered text in pixels
    """
    cursor_x = x
    for char in text.upper():
        if char in FONT:
            glyph = FONT[char]
            for row_idx, row_bits in enumerate(glyph):
                for col_idx in range(FONT_WIDTH):
                    if row_bits & (1 << (FONT_WIDTH - 1 - col_idx)):
                        for sy in range(scale):
                            for sx in range(scale):
                                set_pixel(
                                    pixels,
                                    cursor_x + col_idx * scale + sx,
                                    y + row_idx * scale + sy,
                                    color_idx
                                )
            cursor_x += (FONT_WIDTH + 1) * scale
        else:
            cursor_x += (FONT_WIDTH + 1) * scale
    return cursor_x - x


def get_text_width(text: str, scale: int = 1) -> int:
    """Get the width of text in pixels."""
    return len(text) * (FONT_WIDTH + 1) * scale - scale


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
    # Raster attributes: "Pan;Pad;Ph;Pv - set 1:1 aspect ratio and dimensions
    parts.append(f'"1;1;{width};{height}')
    parts.append(generate_palette())

    # Get all colors used (including background for proper rendering)
    colors_used = set()
    colors_used.add(0)  # Always include background
    for row in pixels:
        for pixel in row:
            colors_used.add(pixel)

    # Process in bands of 6 rows
    for band_start in range(0, height, 6):
        if band_start > 0:
            parts.append(SIXEL_NEWLINE)

        # For each color, output the sixel data for this band
        first_color = True
        for color_idx in sorted(colors_used):
            if not first_color:
                parts.append(SIXEL_CARRIAGE_RETURN)
            first_color = False

            parts.append(f"#{color_idx}")

            # Build sixel characters for this color in this band
            for x in range(width):
                sixel_value = 0
                for bit in range(6):
                    y = band_start + bit
                    if y < height and pixels[y][x] == color_idx:
                        sixel_value |= (1 << bit)
                parts.append(chr(63 + sixel_value))

    parts.append(SIXEL_END)
    return "".join(parts)
