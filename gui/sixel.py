"""
Sixel graphics generation module for GUI demo.

Sixel encodes 6 vertical pixels per character. Each character value is 63 + bitmask,
where bit 0 = top pixel, bit 5 = bottom pixel.

Provides GUI-oriented color palette and drawing primitives for interactive components.
"""

from typing import List, Tuple, Dict, Optional
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Sixel escape sequences
SIXEL_START = "\x1bPq"
SIXEL_END = "\x1b\\"
SIXEL_NEWLINE = "-"
SIXEL_CARRIAGE_RETURN = "$"

# GUI-focused color palette
COLORS = {
    # Base colors
    "background": (35, 35, 40),           # Dark background
    "window_bg": (50, 50, 55),            # Window background
    "window_border": (80, 80, 90),        # Window border
    "window_title_bg": (60, 60, 70),      # Title bar background
    "window_title_active": (70, 120, 180),  # Active window title

    # Text colors
    "text": (220, 220, 220),              # Primary text
    "text_dim": (140, 140, 150),          # Secondary text
    "text_disabled": (100, 100, 110),     # Disabled text
    "text_highlight": (255, 255, 255),    # Highlighted text

    # Interactive elements
    "button_bg": (70, 70, 80),            # Button background
    "button_hover": (90, 90, 100),        # Button hover state
    "button_pressed": (50, 50, 60),       # Button pressed state
    "button_border": (100, 100, 110),     # Button border

    # Accent colors
    "accent": (70, 130, 200),             # Primary accent (blue)
    "accent_hover": (90, 150, 220),       # Accent hover
    "accent_pressed": (50, 110, 180),     # Accent pressed

    # Checkbox/Radio
    "checkbox_bg": (60, 60, 70),          # Unchecked background
    "checkbox_checked": (70, 140, 210),   # Checked state
    "checkbox_border": (120, 120, 130),   # Checkbox border

    # Input fields
    "input_bg": (45, 45, 50),             # Input background
    "input_border": (90, 90, 100),        # Input border
    "input_focus": (70, 130, 200),        # Focused border
    "input_cursor": (255, 255, 255),      # Text cursor

    # Slider
    "slider_track": (60, 60, 70),         # Slider track
    "slider_fill": (70, 140, 210),        # Filled portion
    "slider_thumb": (180, 180, 190),      # Slider thumb
    "slider_thumb_hover": (210, 210, 220),

    # Progress bar
    "progress_bg": (50, 50, 60),          # Progress background
    "progress_fill": (70, 180, 120),      # Progress fill (green)
    "progress_fill_warning": (220, 160, 60),  # Warning (yellow)
    "progress_fill_error": (200, 70, 70),     # Error (red)

    # List/Dropdown
    "list_bg": (50, 50, 55),              # List background
    "list_item_hover": (70, 70, 80),      # Hovered item
    "list_item_selected": (60, 100, 150), # Selected item
    "list_border": (90, 90, 100),         # List border

    # Status colors
    "success": (70, 180, 120),            # Success green
    "warning": (220, 160, 60),            # Warning yellow
    "error": (200, 70, 70),               # Error red
    "info": (70, 140, 210),               # Info blue
}

COLOR_INDICES = {name: idx for idx, name in enumerate(COLORS.keys())}

# Simple 5x7 bitmap font
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
    '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100],
    '/': [0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000],
    '%': [0b11001, 0b11010, 0b00100, 0b00100, 0b01011, 0b10011, 0b00000],
    '(': [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ')': [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
    '[': [0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110],
    ']': [0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110],
    '<': [0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010],
    '>': [0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000],
    '=': [0b00000, 0b00000, 0b11111, 0b00000, 0b11111, 0b00000, 0b00000],
    '+': [0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000],
    '_': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111],
    '|': [0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
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


def draw_horizontal_line(
    pixels: List[List[int]],
    x: int, y: int,
    length: int,
    color_idx: int
) -> None:
    """Draw a horizontal line."""
    fill_rect(pixels, x, y, length, 1, color_idx)


def draw_vertical_line(
    pixels: List[List[int]],
    x: int, y: int,
    length: int,
    color_idx: int
) -> None:
    """Draw a vertical line."""
    fill_rect(pixels, x, y, 1, length, color_idx)


def draw_rect_border(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    color_idx: int
) -> None:
    """Draw a rectangle border (not filled)."""
    draw_horizontal_line(pixels, x, y, w, color_idx)
    draw_horizontal_line(pixels, x, y + h - 1, w, color_idx)
    draw_vertical_line(pixels, x, y, h, color_idx)
    draw_vertical_line(pixels, x + w - 1, y, h, color_idx)


def draw_rounded_corner(
    pixels: List[List[int]],
    x: int, y: int,
    radius: int,
    color_idx: int,
    corner: str
) -> None:
    """
    Draw a rounded corner using Bresenham's circle algorithm.

    Args:
        corner: One of 'tl', 'tr', 'bl', 'br'
    """
    cx = radius
    cy = 0
    d = 1 - radius

    while cx >= cy:
        if corner == 'tl':
            set_pixel(pixels, x + radius - cx, y + radius - cy, color_idx)
            set_pixel(pixels, x + radius - cy, y + radius - cx, color_idx)
        elif corner == 'tr':
            set_pixel(pixels, x + cx, y + radius - cy, color_idx)
            set_pixel(pixels, x + cy, y + radius - cx, color_idx)
        elif corner == 'bl':
            set_pixel(pixels, x + radius - cx, y + cy, color_idx)
            set_pixel(pixels, x + radius - cy, y + cx, color_idx)
        elif corner == 'br':
            set_pixel(pixels, x + cx, y + cy, color_idx)
            set_pixel(pixels, x + cy, y + cx, color_idx)

        cy += 1
        if d < 0:
            d += 2 * cy + 1
        else:
            cx -= 1
            d += 2 * (cy - cx) + 1


def draw_rounded_rect_border(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    radius: int,
    color_idx: int,
    corners: str = "tltrblbr"
) -> None:
    """Draw a rectangle border with rounded corners."""
    # Draw horizontal lines (excluding corners)
    draw_horizontal_line(pixels, x + radius, y, w - 2 * radius, color_idx)
    draw_horizontal_line(pixels, x + radius, y + h - 1, w - 2 * radius, color_idx)

    # Draw vertical lines (excluding corners)
    draw_vertical_line(pixels, x, y + radius, h - 2 * radius, color_idx)
    draw_vertical_line(pixels, x + w - 1, y + radius, h - 2 * radius, color_idx)

    # Draw corners
    if 'tl' in corners:
        draw_rounded_corner(pixels, x, y, radius, color_idx, 'tl')
    else:
        draw_horizontal_line(pixels, x, y, radius, color_idx)
        draw_vertical_line(pixels, x, y, radius, color_idx)

    if 'tr' in corners:
        draw_rounded_corner(pixels, x + w - 1 - radius, y, radius, color_idx, 'tr')
    else:
        draw_horizontal_line(pixels, x + w - radius, y, radius, color_idx)
        draw_vertical_line(pixels, x + w - 1, y, radius, color_idx)

    if 'bl' in corners:
        draw_rounded_corner(pixels, x, y + h - 1 - radius, radius, color_idx, 'bl')
    else:
        draw_horizontal_line(pixels, x, y + h - 1, radius, color_idx)
        draw_vertical_line(pixels, x, y + h - radius, radius, color_idx)

    if 'br' in corners:
        draw_rounded_corner(pixels, x + w - 1 - radius, y + h - 1 - radius, radius, color_idx, 'br')
    else:
        draw_horizontal_line(pixels, x + w - radius, y + h - 1, radius, color_idx)
        draw_vertical_line(pixels, x + w - 1, y + h - radius, radius, color_idx)


def draw_rounded_rect_filled(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    radius: int,
    fill_color: int,
    border_color: Optional[int] = None
) -> None:
    """Draw a filled rounded rectangle with optional border."""
    # Fill the main body (excluding corners)
    fill_rect(pixels, x + radius, y, w - 2 * radius, h, fill_color)
    fill_rect(pixels, x, y + radius, w, h - 2 * radius, fill_color)

    # Fill corners with circular arcs
    for cy in range(radius):
        for cx in range(radius):
            # Check if point is inside the circle
            dist_sq = (radius - cx - 0.5) ** 2 + (radius - cy - 0.5) ** 2
            if dist_sq <= radius ** 2:
                # Top-left
                set_pixel(pixels, x + cx, y + cy, fill_color)
                # Top-right
                set_pixel(pixels, x + w - 1 - cx, y + cy, fill_color)
                # Bottom-left
                set_pixel(pixels, x + cx, y + h - 1 - cy, fill_color)
                # Bottom-right
                set_pixel(pixels, x + w - 1 - cx, y + h - 1 - cy, fill_color)

    # Draw border if specified
    if border_color is not None:
        draw_rounded_rect_border(pixels, x, y, w, h, radius, border_color)


def draw_checkmark(
    pixels: List[List[int]],
    x: int, y: int,
    size: int,
    color_idx: int
) -> None:
    """Draw a checkmark symbol."""
    # Draw checkmark as two lines forming a check shape
    # Short line going down-left, long line going up-right
    mid_x = x + size // 3
    mid_y = y + size * 2 // 3

    # Short leg (going from mid point up-left)
    for i in range(size // 3):
        set_pixel(pixels, mid_x - i, mid_y - i, color_idx)
        set_pixel(pixels, mid_x - i, mid_y - i - 1, color_idx)

    # Long leg (going from mid point up-right)
    for i in range(size * 2 // 3):
        set_pixel(pixels, mid_x + i, mid_y - i, color_idx)
        set_pixel(pixels, mid_x + i, mid_y - i - 1, color_idx)


def draw_circle(
    pixels: List[List[int]],
    cx: int, cy: int,
    radius: int,
    color_idx: int,
    filled: bool = False
) -> None:
    """Draw a circle, optionally filled."""
    x = radius
    y = 0
    d = 1 - radius

    while x >= y:
        if filled:
            draw_horizontal_line(pixels, cx - x, cy + y, 2 * x + 1, color_idx)
            draw_horizontal_line(pixels, cx - x, cy - y, 2 * x + 1, color_idx)
            draw_horizontal_line(pixels, cx - y, cy + x, 2 * y + 1, color_idx)
            draw_horizontal_line(pixels, cx - y, cy - x, 2 * y + 1, color_idx)
        else:
            set_pixel(pixels, cx + x, cy + y, color_idx)
            set_pixel(pixels, cx - x, cy + y, color_idx)
            set_pixel(pixels, cx + x, cy - y, color_idx)
            set_pixel(pixels, cx - x, cy - y, color_idx)
            set_pixel(pixels, cx + y, cy + x, color_idx)
            set_pixel(pixels, cx - y, cy + x, color_idx)
            set_pixel(pixels, cx + y, cy - x, color_idx)
            set_pixel(pixels, cx - y, cy - x, color_idx)

        y += 1
        if d < 0:
            d += 2 * y + 1
        else:
            x -= 1
            d += 2 * (y - x) + 1


def draw_text(
    pixels: List[List[int]],
    x: int, y: int,
    text: str,
    color_idx: int,
    scale: int = 1,
    bold: bool = False
) -> int:
    """
    Draw text onto the pixel buffer using the bitmap font.

    Returns:
        Width of the rendered text in pixels
    """
    cursor_x = x
    extra_width = 1 if bold else 0
    for char in text.upper():
        if char in FONT:
            glyph = FONT[char]
            for row_idx, row_bits in enumerate(glyph):
                for col_idx in range(FONT_WIDTH):
                    if row_bits & (1 << (FONT_WIDTH - 1 - col_idx)):
                        for sy in range(scale):
                            for sx in range(scale + extra_width):
                                set_pixel(
                                    pixels,
                                    cursor_x + col_idx * scale + sx,
                                    y + row_idx * scale + sy,
                                    color_idx
                                )
            cursor_x += (FONT_WIDTH + 1) * scale + extra_width
        else:
            cursor_x += (FONT_WIDTH + 1) * scale
    return cursor_x - x


def get_text_width(text: str, scale: int = 1, bold: bool = False) -> int:
    """Get the width of text in pixels."""
    extra_width = 1 if bold else 0
    return len(text) * ((FONT_WIDTH + 1) * scale + extra_width) - scale - extra_width


def draw_progress_bar(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    value: float,
    bg_color: int,
    fill_color: int,
    border_color: Optional[int] = None,
    max_value: float = 100.0,
    radius: int = 3
) -> None:
    """Draw a progress bar with rounded corners."""
    value = max(0, min(value, max_value))

    # Background with rounded corners
    draw_rounded_rect_filled(pixels, x, y, w, h, radius, bg_color)

    # Fill with rounded corners
    fill_width = int((value / max_value) * w)
    if fill_width > 0:
        # Use rounded corners if there's enough width, otherwise square
        if fill_width >= 2 * radius:
            draw_rounded_rect_filled(pixels, x, y, fill_width, h, radius, fill_color)
        else:
            fill_rect(pixels, x + radius, y, fill_width, h, fill_color)
            # Fill the left rounded corner area
            for cy in range(radius):
                for cx in range(radius):
                    dist_sq = (radius - cx - 0.5) ** 2 + (radius - cy - 0.5) ** 2
                    if dist_sq <= radius ** 2:
                        set_pixel(pixels, x + cx, y + cy, fill_color)
                        set_pixel(pixels, x + cx, y + h - 1 - cy, fill_color)

    # Border with rounded corners
    if border_color is not None:
        draw_rounded_rect_border(pixels, x, y, w, h, radius, border_color)


def draw_slider(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    value: float,
    track_color: int,
    fill_color: int,
    thumb_color: int,
    thumb_width: int = 8,
    max_value: float = 100.0,
    thumb_radius: int = 3
) -> int:
    """
    Draw a slider control.

    Returns:
        X position of the thumb center.
    """
    value = max(0, min(value, max_value))

    # Track
    track_y = y + h // 2 - 2
    fill_rect(pixels, x, track_y, w, 4, track_color)

    # Filled portion
    fill_width = int((value / max_value) * w)
    if fill_width > 0:
        fill_rect(pixels, x, track_y, fill_width, 4, fill_color)

    # Thumb position
    thumb_x = x + int((value / max_value) * (w - thumb_width))

    # Draw thumb with rounded corners
    draw_rounded_rect_filled(pixels, thumb_x, y, thumb_width, h, thumb_radius, thumb_color)

    return thumb_x + thumb_width // 2


def _encode_rle(sixel_chars: List[int]) -> str:
    """Encode a list of sixel values using Run-Length Encoding."""
    if not sixel_chars:
        return ""

    result = []
    i = 0
    while i < len(sixel_chars):
        char = sixel_chars[i]
        count = 1

        while i + count < len(sixel_chars) and sixel_chars[i + count] == char:
            count += 1

        sixel_char = chr(63 + char)
        if count >= 3:
            result.append(f"!{count}{sixel_char}")
        else:
            result.append(sixel_char * count)

        i += count

    return "".join(result)


def pixels_to_sixel(pixels: List[List[int]], width: int, height: int) -> str:
    """Convert a 2D pixel buffer to a sixel string."""
    parts = [SIXEL_START]
    parts.append(f'"1;1;{width};{height}')
    parts.append(generate_palette())

    colors_used = set()
    colors_used.add(0)
    for row in pixels:
        for pixel in row:
            colors_used.add(pixel)

    for band_start in range(0, height, 6):
        if band_start > 0:
            parts.append(SIXEL_NEWLINE)

        first_color = True
        for color_idx in sorted(colors_used):
            sixel_values = []
            for x in range(width):
                sixel_value = 0
                for bit in range(6):
                    y = band_start + bit
                    if y < height and pixels[y][x] == color_idx:
                        sixel_value |= (1 << bit)
                sixel_values.append(sixel_value)

            if all(v == 0 for v in sixel_values):
                continue

            if not first_color:
                parts.append(SIXEL_CARRIAGE_RETURN)
            first_color = False

            parts.append(f"#{color_idx}")
            parts.append(_encode_rle(sixel_values))

    parts.append(SIXEL_END)
    return "".join(parts)


def _get_color_index_to_rgb() -> Dict[int, Tuple[int, int, int]]:
    """Create a mapping from color index to RGB tuple."""
    return {idx: COLORS[name] for name, idx in COLOR_INDICES.items()}


def pixels_to_png(
    pixels: List[List[int]],
    output_path: Optional[str] = None
) -> Optional["Image.Image"]:
    """Convert a 2D pixel buffer to a PNG image."""
    if not PIL_AVAILABLE:
        return None

    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    if width == 0 or height == 0:
        return None

    img = Image.new("RGB", (width, height))
    color_map = _get_color_index_to_rgb()

    img_data = []
    for row in pixels:
        for color_idx in row:
            rgb = color_map.get(color_idx, (0, 0, 0))
            img_data.append(rgb)

    img.putdata(img_data)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)

    return img
