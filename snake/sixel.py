"""
Sixel graphics generation module.

Sixel encodes 6 vertical pixels per character. Each character value is 63 + bitmask,
where bit 0 = top pixel, bit 5 = bottom pixel.
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


def decode_sixel(sixel_data: str) -> Optional[List[List[Tuple[int, int, int]]]]:
    """
    Decode a sixel string back into a 2D array of RGB tuples.

    This parses actual sixel output to verify the encoding is correct.

    Args:
        sixel_data: The sixel escape sequence string

    Returns:
        2D array of RGB tuples [y][x], or None if parsing fails
    """
    # Strip the DCS introducer and ST terminator
    if sixel_data.startswith(SIXEL_START):
        sixel_data = sixel_data[len(SIXEL_START):]
    if sixel_data.endswith(SIXEL_END):
        sixel_data = sixel_data[:-len(SIXEL_END)]

    # Parse raster attributes to get dimensions
    width, height = 0, 0
    palette: Dict[int, Tuple[int, int, int]] = {}

    # State for parsing
    current_color = 0
    x, y = 0, 0
    pixels: List[List[Tuple[int, int, int]]] = []

    i = 0
    while i < len(sixel_data):
        char = sixel_data[i]

        if char == '"':
            # Raster attributes: "Pan;Pad;Ph;Pv
            i += 1
            end = i
            while end < len(sixel_data) and sixel_data[end] not in '#-$?\x1b':
                end += 1
            parts = sixel_data[i:end].split(';')
            if len(parts) >= 4:
                width = int(parts[2])
                height = int(parts[3])
                # Initialize pixel buffer with black
                pixels = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]
            i = end

        elif char == '#':
            # Color definition or selection
            i += 1
            end = i
            while end < len(sixel_data) and sixel_data[end] in '0123456789;':
                end += 1
            color_spec = sixel_data[i:end]
            parts = color_spec.split(';')

            if len(parts) >= 5 and parts[1] == '2':
                # Color definition: #Pc;2;Pr;Pg;Pb (RGB mode)
                color_idx = int(parts[0])
                r = int(parts[2]) * 255 // 100
                g = int(parts[3]) * 255 // 100
                b = int(parts[4]) * 255 // 100
                palette[color_idx] = (r, g, b)
            elif len(parts) == 1:
                # Color selection: #Pc
                current_color = int(parts[0])

            i = end

        elif char == '!':
            # RLE: !<count><char>
            i += 1
            end = i
            while end < len(sixel_data) and sixel_data[end].isdigit():
                end += 1
            count = int(sixel_data[i:end])
            i = end
            if i < len(sixel_data):
                sixel_char = sixel_data[i]
                sixel_value = ord(sixel_char) - 63
                color = palette.get(current_color, (0, 0, 0))
                for _ in range(count):
                    if x < width:
                        for bit in range(6):
                            py = y + bit
                            if py < height and (sixel_value & (1 << bit)):
                                pixels[py][x] = color
                        x += 1
                i += 1

        elif char == '-':
            # Graphics new line (move to next band)
            y += 6
            x = 0
            i += 1

        elif char == '$':
            # Graphics carriage return (back to start of band)
            x = 0
            i += 1

        elif '?' <= char <= '~':
            # Sixel data character
            sixel_value = ord(char) - 63
            color = palette.get(current_color, (0, 0, 0))
            if x < width:
                for bit in range(6):
                    py = y + bit
                    if py < height and (sixel_value & (1 << bit)):
                        pixels[py][x] = color
                x += 1
            i += 1

        else:
            i += 1

    return pixels if pixels else None


def sixel_to_png(
    sixel_data: str,
    output_path: str
) -> bool:
    """
    Decode a sixel string and save it as a PNG image.

    This tests the full round-trip: the sixel output that would be
    sent to a terminal is decoded back into pixels and saved.

    Args:
        sixel_data: The sixel escape sequence string
        output_path: Path to save the PNG file

    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        return False

    pixels = decode_sixel(sixel_data)
    if not pixels:
        return False

    height = len(pixels)
    width = len(pixels[0]) if height > 0 else 0

    if width == 0 or height == 0:
        return False

    img = Image.new("RGB", (width, height))
    img_data = [pixel for row in pixels for pixel in row]
    img.putdata(img_data)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)

    return True
