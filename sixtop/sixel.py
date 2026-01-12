"""
Sixel graphics generation module for sixtop.

Sixel encodes 6 vertical pixels per character. Each character value is 63 + bitmask,
where bit 0 = top pixel, bit 5 = bottom pixel.

Extended color palette for system monitoring infographics.
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

# Color palette for system monitoring (matching Activity Monitor style)
COLORS = {
    "background": (30, 30, 30),         # Dark gray background
    "panel_bg": (45, 45, 45),           # Slightly lighter panel background
    "border": (80, 80, 80),             # Gray border
    "border_highlight": (0, 180, 180),  # Cyan border highlight
    "text": (200, 200, 200),            # Light gray text
    "text_dim": (120, 120, 120),        # Dimmed text
    "text_cyan": (0, 200, 200),         # Cyan text (values)
    "text_red": (255, 80, 80),          # Red text (alerts/values)
    "text_green": (80, 200, 80),        # Green text
    "graph_cyan": (0, 180, 220),        # Cyan for graphs (user CPU, data in)
    "graph_red": (220, 80, 80),         # Red for graphs (system CPU, data out)
    "graph_green": (80, 180, 80),       # Green for memory pressure
    "graph_blue": (80, 120, 220),       # Blue for energy
    "graph_fill_cyan": (0, 100, 120),   # Fill color for cyan graphs
    "graph_fill_red": (120, 40, 40),    # Fill color for red graphs
    "graph_fill_green": (40, 100, 40),  # Fill color for green graphs
    "title_line": (60, 60, 60),         # Title underline
}

COLOR_INDICES = {name: idx for idx, name in enumerate(COLORS.keys())}

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
    '.': [0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00100],
    '/': [0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000],
    '%': [0b11001, 0b11010, 0b00100, 0b00100, 0b01011, 0b10011, 0b00000],
    '(': [0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010],
    ')': [0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000],
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


def draw_rounded_corner(
    pixels: List[List[int]],
    x: int, y: int,
    radius: int,
    color_idx: int,
    corner: str
) -> None:
    """
    Draw a rounded corner.

    Args:
        pixels: The pixel buffer
        x, y: Position of the corner point
        radius: Radius of the curve
        color_idx: Color index for the corner
        corner: One of 'tl' (top-left), 'tr' (top-right),
                'bl' (bottom-left), 'br' (bottom-right)
    """
    # Draw a quarter circle arc using simple pixel approximation
    for i in range(radius + 1):
        for j in range(radius + 1):
            # Check if point is on the edge of the circle
            dist_sq = i * i + j * j
            if (radius - 1) ** 2 <= dist_sq <= (radius + 1) ** 2:
                if corner == 'tl':
                    set_pixel(pixels, x + radius - i, y + radius - j, color_idx)
                elif corner == 'tr':
                    set_pixel(pixels, x + i, y + radius - j, color_idx)
                elif corner == 'bl':
                    set_pixel(pixels, x + radius - i, y + j, color_idx)
                elif corner == 'br':
                    set_pixel(pixels, x + i, y + j, color_idx)


def draw_rounded_rect_border(
    pixels: List[List[int]],
    x: int, y: int,
    w: int, h: int,
    radius: int,
    color_idx: int,
    corners: str = "tltrblbr"
) -> None:
    """
    Draw a rectangle border with rounded corners.

    Args:
        pixels: The pixel buffer
        x, y: Top-left position
        w, h: Width and height
        radius: Corner radius
        color_idx: Color index for the border
        corners: Which corners to round (e.g., "tltr" for top corners only)
    """
    # Draw horizontal lines (excluding corners)
    # Top line
    draw_horizontal_line(pixels, x + radius, y, w - 2 * radius, color_idx)
    # Bottom line
    draw_horizontal_line(pixels, x + radius, y + h - 1, w - 2 * radius, color_idx)

    # Draw vertical lines (excluding corners)
    # Left line
    draw_vertical_line(pixels, x, y + radius, h - 2 * radius, color_idx)
    # Right line
    draw_vertical_line(pixels, x + w - 1, y + radius, h - 2 * radius, color_idx)

    # Draw rounded corners
    if 'tl' in corners:
        draw_rounded_corner(pixels, x, y, radius, color_idx, 'tl')
    else:
        # Square corner
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


def draw_line_graph(
    pixels: List[List[int]],
    x: int, y: int,
    width: int, height: int,
    data: List[float],
    line_color: int,
    fill_color: Optional[int] = None,
    max_value: float = 100.0
) -> None:
    """
    Draw a line graph with optional fill.

    Args:
        pixels: The pixel buffer
        x, y: Top-left corner of the graph area
        width, height: Size of the graph area
        data: List of values (0 to max_value)
        line_color: Color index for the line
        fill_color: Optional color index for fill under the line
        max_value: Maximum value for scaling (default 100)
    """
    if not data or width <= 0 or height <= 0:
        return

    # Sample data to fit width
    num_points = min(len(data), width)
    if len(data) > width:
        # Downsample: take last 'width' points
        data = data[-width:]

    # Calculate y positions for each data point
    y_positions = []
    for val in data:
        # Clamp value to valid range
        val = max(0, min(val, max_value))
        # Convert to pixel position (inverted: 0 at bottom, max at top)
        pixel_y = y + height - 1 - int((val / max_value) * (height - 1))
        y_positions.append(pixel_y)

    # Calculate x positions
    if num_points == 1:
        x_positions = [x + width - 1]
    else:
        step = (width - 1) / (num_points - 1) if num_points > 1 else 0
        x_positions = [x + int(i * step) for i in range(num_points)]

    # Draw fill if requested
    if fill_color is not None:
        for i, (px, py) in enumerate(zip(x_positions, y_positions)):
            # Fill from the line down to the bottom
            for fill_y in range(py, y + height):
                set_pixel(pixels, px, fill_y, fill_color)
            # Fill gaps between points
            if i > 0:
                prev_x, prev_y = x_positions[i-1], y_positions[i-1]
                for gx in range(prev_x + 1, px):
                    # Interpolate y
                    t = (gx - prev_x) / (px - prev_x)
                    gy = int(prev_y + t * (py - prev_y))
                    for fill_y in range(gy, y + height):
                        set_pixel(pixels, gx, fill_y, fill_color)

    # Draw the line
    for i in range(len(x_positions)):
        px, py = x_positions[i], y_positions[i]
        set_pixel(pixels, px, py, line_color)
        # Connect to previous point
        if i > 0:
            prev_x, prev_y = x_positions[i-1], y_positions[i-1]
            # Bresenham-style line drawing
            dx = abs(px - prev_x)
            dy = abs(py - prev_y)
            sx = 1 if prev_x < px else -1
            sy = 1 if prev_y < py else -1
            err = dx - dy
            cx, cy = prev_x, prev_y
            while cx != px or cy != py:
                set_pixel(pixels, cx, cy, line_color)
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    cx += sx
                if e2 < dx:
                    err += dx
                    cy += sy


def draw_dual_line_graph(
    pixels: List[List[int]],
    x: int, y: int,
    width: int, height: int,
    data1: List[float],
    data2: List[float],
    line_color1: int,
    line_color2: int,
    fill_color1: Optional[int] = None,
    fill_color2: Optional[int] = None,
    max_value: float = 100.0
) -> None:
    """
    Draw two line graphs overlaid (like CPU user/system).

    Args:
        pixels: The pixel buffer
        x, y: Top-left corner of the graph area
        width, height: Size of the graph area
        data1, data2: Lists of values for each line
        line_color1, line_color2: Color indices for each line
        fill_color1, fill_color2: Optional fill colors
        max_value: Maximum value for scaling
    """
    # Draw the first line (background, typically larger values)
    if data1:
        draw_line_graph(pixels, x, y, width, height, data1,
                       line_color1, fill_color1, max_value)
    # Draw the second line (foreground)
    if data2:
        draw_line_graph(pixels, x, y, width, height, data2,
                       line_color2, fill_color2, max_value)


def draw_bar_graph(
    pixels: List[List[int]],
    x: int, y: int,
    width: int, height: int,
    value: float,
    bar_color: int,
    max_value: float = 100.0
) -> None:
    """
    Draw a horizontal bar graph.

    Args:
        pixels: The pixel buffer
        x, y: Top-left corner of the bar
        width, height: Maximum size of the bar
        value: Current value
        bar_color: Color index for the bar
        max_value: Maximum value for scaling
    """
    value = max(0, min(value, max_value))
    bar_width = int((value / max_value) * width)
    if bar_width > 0:
        fill_rect(pixels, x, y, bar_width, height, bar_color)


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


def _encode_rle(sixel_chars: List[int]) -> str:
    """
    Encode a list of sixel values using Run-Length Encoding.

    In sixel, !n<char> means repeat <char> n times.
    This dramatically reduces output size for solid-color areas.
    """
    if not sixel_chars:
        return ""

    result = []
    i = 0
    while i < len(sixel_chars):
        char = sixel_chars[i]
        count = 1

        # Count consecutive identical values
        while i + count < len(sixel_chars) and sixel_chars[i + count] == char:
            count += 1

        sixel_char = chr(63 + char)
        if count >= 3:
            # Use RLE for 3+ repetitions
            result.append(f"!{count}{sixel_char}")
        else:
            # Output individual characters for short runs
            result.append(sixel_char * count)

        i += count

    return "".join(result)


def pixels_to_sixel(pixels: List[List[int]], width: int, height: int) -> str:
    """
    Convert a 2D pixel buffer to a sixel string.

    Uses RLE compression for efficient encoding of large solid-color areas.

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
            # Build sixel values for this color in this band
            sixel_values = []
            for x in range(width):
                sixel_value = 0
                for bit in range(6):
                    y = band_start + bit
                    if y < height and pixels[y][x] == color_idx:
                        sixel_value |= (1 << bit)
                sixel_values.append(sixel_value)

            # Skip this color if all values are zero (no pixels of this color)
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
    """
    Convert a 2D pixel buffer to a PNG image.

    Args:
        pixels: 2D array of color indices [y][x]
        output_path: Optional path to save the PNG file

    Returns:
        PIL Image object if PIL is available, None otherwise
    """
    if not PIL_AVAILABLE:
        return None

    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    if width == 0 or height == 0:
        return None

    # Create RGB image
    img = Image.new("RGB", (width, height))
    color_map = _get_color_index_to_rgb()

    # Convert pixel buffer to image
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
