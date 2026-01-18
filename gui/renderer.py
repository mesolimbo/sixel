"""
Renderer module for GUI demo.

Renders GUI components and windows as sixel graphics.
Uses the component state to determine visual appearance.
"""

from typing import List, Optional, Tuple

from sixel import (
    create_pixel_buffer,
    clear_pixel_buffer,
    pixels_to_sixel,
    fill_rect,
    draw_rect_border,
    draw_text,
    draw_rounded_rect_filled,
    draw_rounded_rect_border,
    draw_checkmark,
    draw_circle,
    draw_progress_bar,
    draw_slider,
    draw_horizontal_line,
    get_text_width,
    COLOR_INDICES,
    FONT_HEIGHT,
)
from gui import (
    GUIState,
    Window,
    Component,
    ComponentState,
    Button,
    Checkbox,
    RadioButton,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    ImageDisplay,
)


class GUIRenderer:
    """
    Renders GUI state to sixel graphics.

    Handles rendering of all component types with proper styling
    based on component state (normal, hover, pressed, disabled).
    """

    def __init__(self, width: int = 1200, height: int = 400):
        """
        Initialize the renderer.

        Args:
            width: Frame width in pixels
            height: Frame height in pixels
        """
        self.width = width
        self.height = height
        self.scale = 2  # Larger font for better readability
        self.bold = True

        # Layout constants (1.5x scale for better display on macOS)
        self.padding = 12
        self.corner_radius = 6
        self.title_bar_height = 36
        self.component_padding = 9

        # Reusable pixel buffer (created once, cleared each frame)
        self._pixels = create_pixel_buffer(width, height, COLOR_INDICES["background"])
        self._bg_color = COLOR_INDICES["background"]

    def render_frame(self, gui_state: GUIState) -> str:
        """
        Render the GUI state as a sixel string.

        Args:
            gui_state: The GUI state to render

        Returns:
            Sixel escape sequence string
        """
        # Clear and reuse pixel buffer
        clear_pixel_buffer(self._pixels, self._bg_color)

        # Render all windows
        for window in gui_state.windows:
            self._render_window(self._pixels, window)

        # Draw instructions at bottom
        self._draw_instructions(self._pixels)

        return pixels_to_sixel(self._pixels, self.width, self.height)

    def get_window_rows(self, gui_state: GUIState) -> List[List[int]]:
        """
        Group windows by their vertical position into rows.

        Returns:
            List of lists, where each inner list contains window indices in that row.
        """
        if not gui_state.windows:
            return []

        # Group windows by their y position
        rows_dict = {}
        for i, window in enumerate(gui_state.windows):
            # Round y to nearest 50 pixels to group windows in same row
            row_key = window.y // 50
            if row_key not in rows_dict:
                rows_dict[row_key] = []
            rows_dict[row_key].append(i)

        # Sort by row key and return just the lists
        return [rows_dict[k] for k in sorted(rows_dict.keys())]

    def _draw_instructions(self, pixels: List[List[int]]) -> None:
        """Draw instruction text at the bottom of the frame."""
        y = self.height - 30
        x = self.padding

        # Instructions
        text = "TAB=WINDOW  UP/DOWN=ITEM  LEFT/RIGHT=ADJUST  SPACE=SELECT  Q=QUIT"
        draw_text(pixels, x, y, text, COLOR_INDICES["text_dim"], self.scale, False)

    def _draw_focus_indicator(
        self, pixels: List[List[int]], component: Component
    ) -> None:
        """Draw a focus indicator border around a focused component."""
        if component.state != ComponentState.FOCUSED:
            return

        b = component.bounds
        # Draw a highlight border 3 pixels outside the component (1.5x)
        focus_color = COLOR_INDICES["input_focus"]

        # Draw outer border (3 pixels thick)
        for offset in range(3):
            x = b.x - 3 + offset
            y = b.y - 3 + offset
            w = b.width + 6 - offset * 2
            h = b.height + 6 - offset * 2
            draw_rect_border(pixels, x, y, w, h, focus_color)

    def _render_window(self, pixels: List[List[int]], window: Window) -> None:
        """Render a window and its components."""
        x, y = window.x, window.y
        w, h = window.width, window.height
        radius = self.corner_radius

        # Window background with rounded corners
        draw_rounded_rect_filled(
            pixels, x, y, w, h, radius,
            COLOR_INDICES["window_bg"]
        )

        # Title bar background with rounded top corners only
        title_bg = COLOR_INDICES["window_title_active"] if window.active else COLOR_INDICES["window_title_bg"]
        # Draw rounded rect for title, then fill in bottom part to square it off
        draw_rounded_rect_filled(
            pixels, x, y, w, self.title_bar_height + radius, radius,
            title_bg
        )
        # Fill the bottom portion to make bottom corners square
        fill_rect(pixels, x, y + self.title_bar_height, w, radius, title_bg)

        # Title text
        title_x = x + self.padding
        title_y = y + (self.title_bar_height - FONT_HEIGHT * self.scale) // 2
        draw_text(pixels, title_x, title_y, window.title,
                 COLOR_INDICES["text_highlight"], self.scale, self.bold)

        # Window border with rounded corners
        draw_rounded_rect_border(pixels, x, y, w, h, radius, COLOR_INDICES["window_border"])

        # Render each component
        for component in window.components:
            if component.visible:
                self._render_component(pixels, component)

    def _render_component(self, pixels: List[List[int]], component: Component) -> None:
        """Dispatch to the appropriate component renderer."""
        # Draw focus indicator first (behind component)
        self._draw_focus_indicator(pixels, component)

        if isinstance(component, Button):
            self._render_button(pixels, component)
        elif isinstance(component, Checkbox):
            self._render_checkbox(pixels, component)
        elif isinstance(component, RadioButton):
            self._render_radio_button(pixels, component)
        elif isinstance(component, TextInput):
            self._render_text_input(pixels, component)
        elif isinstance(component, Slider):
            self._render_slider(pixels, component)
        elif isinstance(component, ProgressBar):
            self._render_progress_bar(pixels, component)
        elif isinstance(component, ListBox):
            self._render_list_box(pixels, component)
        elif isinstance(component, ImageDisplay):
            self._render_image_display(pixels, component)

    def _get_button_colors(self, state: ComponentState) -> Tuple[int, int, int]:
        """Get background, border, and text colors for button state."""
        if state == ComponentState.DISABLED:
            return (
                COLOR_INDICES["button_bg"],
                COLOR_INDICES["button_border"],
                COLOR_INDICES["text_disabled"]
            )
        elif state == ComponentState.PRESSED:
            return (
                COLOR_INDICES["button_pressed"],
                COLOR_INDICES["accent"],
                COLOR_INDICES["text"]
            )
        elif state == ComponentState.HOVER:
            return (
                COLOR_INDICES["button_hover"],
                COLOR_INDICES["accent_hover"],
                COLOR_INDICES["text_highlight"]
            )
        else:
            return (
                COLOR_INDICES["button_bg"],
                COLOR_INDICES["button_border"],
                COLOR_INDICES["text"]
            )

    def _render_button(self, pixels: List[List[int]], button: Button) -> None:
        """Render a button component."""
        # Use pressed colors if button is toggled on
        if button.toggled:
            bg_color = COLOR_INDICES["button_pressed"]
            border_color = COLOR_INDICES["accent"]
            text_color = COLOR_INDICES["text_highlight"]
        else:
            bg_color, border_color, text_color = self._get_button_colors(button.state)

        # Draw rounded rectangle
        draw_rounded_rect_filled(
            pixels, button.x, button.y,
            button.width, button.height,
            self.corner_radius, bg_color, border_color
        )

        # Draw label centered
        label_width = get_text_width(button.label, self.scale, self.bold)
        label_x = button.x + (button.width - label_width) // 2
        label_y = button.y + (button.height - FONT_HEIGHT * self.scale) // 2
        draw_text(pixels, label_x, label_y, button.label, text_color, self.scale, self.bold)

    def _render_checkbox(self, pixels: List[List[int]], checkbox: Checkbox) -> None:
        """Render a checkbox component."""
        box_size = 24  # 1.5x from 16
        box_x = checkbox.x
        box_y = checkbox.y + (checkbox.height - box_size) // 2

        # Checkbox box
        if checkbox.checked:
            fill_rect(pixels, box_x, box_y, box_size, box_size,
                     COLOR_INDICES["checkbox_checked"])
            # Draw checkmark
            draw_checkmark(pixels, box_x + 3, box_y + 3, box_size - 6,
                          COLOR_INDICES["text_highlight"])
        else:
            fill_rect(pixels, box_x, box_y, box_size, box_size,
                     COLOR_INDICES["checkbox_bg"])

        # Border
        draw_rect_border(pixels, box_x, box_y, box_size, box_size,
                        COLOR_INDICES["checkbox_border"])

        # Label
        label_x = box_x + box_size + 12  # 1.5x from 8
        label_y = checkbox.y + (checkbox.height - FONT_HEIGHT * self.scale) // 2
        text_color = COLOR_INDICES["text"] if checkbox.enabled else COLOR_INDICES["text_disabled"]
        draw_text(pixels, label_x, label_y, checkbox.label, text_color, self.scale, self.bold)

    def _render_radio_button(self, pixels: List[List[int]], radio: RadioButton) -> None:
        """Render a radio button component."""
        circle_radius = 10  # 1.5x from 7
        circle_cx = radio.x + circle_radius + 3  # 1.5x from 2
        circle_cy = radio.y + radio.height // 2

        # Outer circle
        draw_circle(pixels, circle_cx, circle_cy, circle_radius,
                   COLOR_INDICES["checkbox_border"], filled=False)

        # Inner circle if selected
        if radio.selected:
            draw_circle(pixels, circle_cx, circle_cy, circle_radius - 4,
                       COLOR_INDICES["checkbox_checked"], filled=True)

        # Label
        label_x = radio.x + circle_radius * 2 + 15  # 1.5x from 10
        label_y = radio.y + (radio.height - FONT_HEIGHT * self.scale) // 2
        text_color = COLOR_INDICES["text"] if radio.enabled else COLOR_INDICES["text_disabled"]
        draw_text(pixels, label_x, label_y, radio.label, text_color, self.scale, self.bold)

    def _render_text_input(self, pixels: List[List[int]], text_input: TextInput) -> None:
        """Render a text input component."""
        # Background
        fill_rect(pixels, text_input.x, text_input.y,
                 text_input.width, text_input.height,
                 COLOR_INDICES["input_bg"])

        # Border (focused or not)
        border_color = (COLOR_INDICES["input_focus"] if text_input.has_focus
                       else COLOR_INDICES["input_border"])
        draw_rect_border(pixels, text_input.x, text_input.y,
                        text_input.width, text_input.height, border_color)

        # Text content
        text_x = text_input.x + self.component_padding
        text_y = text_input.y + (text_input.height - FONT_HEIGHT * self.scale) // 2

        if text_input.text:
            draw_text(pixels, text_x, text_y, text_input.text,
                     COLOR_INDICES["text"], self.scale, False)

            # Cursor if focused
            if text_input.has_focus:
                cursor_offset = get_text_width(
                    text_input.text[:text_input.cursor_pos], self.scale, False
                )
                cursor_x = text_x + cursor_offset + 3  # 1.5x from 2
                fill_rect(pixels, cursor_x, text_y, 3,  # 1.5x cursor width
                         FONT_HEIGHT * self.scale, COLOR_INDICES["input_cursor"])
        else:
            # Show placeholder or cursor
            if text_input.has_focus:
                fill_rect(pixels, text_x, text_y, 3,  # 1.5x cursor width
                         FONT_HEIGHT * self.scale, COLOR_INDICES["input_cursor"])
            else:
                draw_text(pixels, text_x, text_y, text_input.placeholder,
                         COLOR_INDICES["text_dim"], self.scale, False)

    def _render_slider(self, pixels: List[List[int]], slider: Slider) -> None:
        """Render a slider component."""
        thumb_width = 15  # 1.5x from 10
        draw_slider(
            pixels, slider.x, slider.y,
            slider.width, slider.height,
            slider.percentage,
            COLOR_INDICES["slider_track"],
            COLOR_INDICES["slider_fill"],
            COLOR_INDICES["slider_thumb"],
            thumb_width=thumb_width,
            max_value=100.0
        )

        # Draw value label
        value_text = f"{slider.value:.0f}"
        value_x = slider.x + slider.width + 12  # 1.5x from 8
        value_y = slider.y + (slider.height - FONT_HEIGHT * self.scale) // 2
        draw_text(pixels, value_x, value_y, value_text,
                 COLOR_INDICES["text"], self.scale, False)

    def _render_progress_bar(self, pixels: List[List[int]], progress: ProgressBar) -> None:
        """Render a progress bar component."""
        # Determine fill color based on value
        if progress.percentage >= 100:
            fill_color = COLOR_INDICES["success"]
        elif progress.percentage >= 70:
            fill_color = COLOR_INDICES["progress_fill"]
        elif progress.percentage >= 30:
            fill_color = COLOR_INDICES["progress_fill_warning"]
        else:
            fill_color = COLOR_INDICES["progress_fill_error"]

        draw_progress_bar(
            pixels, progress.x, progress.y,
            progress.width, progress.height,
            progress.percentage,
            COLOR_INDICES["progress_bg"],
            fill_color,
            border_color=COLOR_INDICES["list_border"],
            max_value=100.0
        )

        # Draw percentage text
        pct_text = f"{progress.percentage:.0f}%"
        pct_width = get_text_width(pct_text, self.scale, False)
        pct_x = progress.x + (progress.width - pct_width) // 2
        pct_y = progress.y + (progress.height - FONT_HEIGHT * self.scale) // 2
        draw_text(pixels, pct_x, pct_y, pct_text,
                 COLOR_INDICES["text_highlight"], self.scale, False)

    def _render_list_box(self, pixels: List[List[int]], listbox: ListBox) -> None:
        """Render a list box component."""
        # Background
        fill_rect(pixels, listbox.x, listbox.y,
                 listbox.width, listbox.height,
                 COLOR_INDICES["list_bg"])

        # Border
        draw_rect_border(pixels, listbox.x, listbox.y,
                        listbox.width, listbox.height,
                        COLOR_INDICES["list_border"])

        # Items
        visible_items = listbox.height // listbox.item_height
        for i, item in enumerate(listbox.items[:visible_items]):
            item_y = listbox.y + i * listbox.item_height

            # Item background
            if i == listbox.selected_index:
                fill_rect(pixels, listbox.x + 1, item_y,
                         listbox.width - 2, listbox.item_height,
                         COLOR_INDICES["list_item_selected"])
            elif i == listbox.hover_index:
                fill_rect(pixels, listbox.x + 1, item_y,
                         listbox.width - 2, listbox.item_height,
                         COLOR_INDICES["list_item_hover"])

            # Item text
            text_x = listbox.x + self.component_padding
            text_y = item_y + (listbox.item_height - FONT_HEIGHT * self.scale) // 2
            text_color = (COLOR_INDICES["text_highlight"]
                         if i == listbox.selected_index
                         else COLOR_INDICES["text"])
            draw_text(pixels, text_x, text_y, item.label,
                     text_color, self.scale, False)

            # Draw separator line between items
            if i < len(listbox.items) - 1:
                line_y = item_y + listbox.item_height - 1
                draw_horizontal_line(pixels, listbox.x + 1, line_y,
                                    listbox.width - 2,
                                    COLOR_INDICES["window_border"])

    def _render_image_display(self, pixels: List[List[int]], img_display: ImageDisplay) -> None:
        """Render an image display component with zoom support."""
        # Background
        fill_rect(pixels, img_display.x, img_display.y,
                 img_display.width, img_display.height,
                 COLOR_INDICES["list_bg"])

        # Border
        draw_rect_border(pixels, img_display.x, img_display.y,
                        img_display.width, img_display.height,
                        COLOR_INDICES["list_border"])

        # Get image data
        image_data = img_display.image_data
        if not image_data:
            # No image loaded - draw placeholder text
            text = "NO IMAGE"
            text_width = get_text_width(text, self.scale, False)
            text_x = img_display.x + (img_display.width - text_width) // 2
            text_y = img_display.y + (img_display.height - FONT_HEIGHT * self.scale) // 2
            draw_text(pixels, text_x, text_y, text,
                     COLOR_INDICES["text_dim"], self.scale, False)
            return

        # Build indexed data cache if not present
        if img_display.indexed_data is None:
            self._build_indexed_cache(img_display)

        indexed_data = img_display.indexed_data
        zoom_factor = img_display.zoom_factor
        src_width = img_display.image_width
        src_height = img_display.image_height

        # Calculate displayed size after zoom
        display_width = int(src_width * zoom_factor)
        display_height = int(src_height * zoom_factor)

        # Calculate content area (inside border)
        content_x = img_display.x + 2
        content_y = img_display.y + 2
        content_width = img_display.width - 4
        content_height = img_display.height - 4 - 18  # 1.5x from 12

        # Center the image in the content area
        start_x = content_x + (content_width - display_width) // 2
        start_y = content_y + (content_height - display_height) // 2

        # Render the image with zoom using cached indexed data
        self._blit_indexed_zoomed(
            pixels, indexed_data,
            start_x, start_y,
            content_x, content_y,
            content_width, content_height,
            zoom_factor
        )

        # Draw zoom level label at the bottom
        if zoom_factor >= 1:
            zoom_text = f"{int(zoom_factor)}X"
        else:
            zoom_text = f"1/{int(1/zoom_factor)}X"
        text_width = get_text_width(zoom_text, self.scale, False)
        text_x = img_display.x + (img_display.width - text_width) // 2
        text_y = img_display.y + img_display.height - 16  # 1.5x from 11
        draw_text(pixels, text_x, text_y, zoom_text,
                 COLOR_INDICES["text"], self.scale, False)

    def _build_indexed_cache(self, img_display: ImageDisplay) -> None:
        """Build palette-indexed cache for an image using its registered color map."""
        image_data = img_display.image_data
        if not image_data:
            return

        color_map = img_display.color_map
        indexed = []
        for row in image_data:
            indexed_row = []
            for rgb in row:
                # Use direct color mapping if available (registered image colors)
                if color_map and rgb in color_map:
                    indexed_row.append(color_map[rgb])
                else:
                    # Fallback to closest color for any unregistered colors
                    indexed_row.append(self._find_closest_color(*rgb))
            indexed.append(indexed_row)
        img_display.indexed_data = indexed

    def _blit_indexed_zoomed(
        self,
        pixels: List[List[int]],
        indexed_data: List[List[int]],
        start_x: int, start_y: int,
        clip_x: int, clip_y: int,
        clip_width: int, clip_height: int,
        zoom_factor: float
    ) -> None:
        """Blit indexed image data to pixel buffer with zoom and clipping."""
        src_height = len(indexed_data)
        src_width = len(indexed_data[0]) if src_height > 0 else 0
        buf_height = len(pixels)
        buf_width = len(pixels[0]) if buf_height > 0 else 0

        # Clipping bounds
        clip_x2 = clip_x + clip_width
        clip_y2 = clip_y + clip_height

        if zoom_factor >= 1:
            # Zoom in: each source pixel becomes multiple destination pixels
            scale = int(zoom_factor)
            for src_y in range(src_height):
                for src_x in range(src_width):
                    color_idx = indexed_data[src_y][src_x]

                    # Draw scaled pixel
                    for dy in range(scale):
                        for dx in range(scale):
                            dst_x = start_x + src_x * scale + dx
                            dst_y = start_y + src_y * scale + dy

                            # Clip to content area and buffer
                            if (clip_x <= dst_x < clip_x2 and
                                clip_y <= dst_y < clip_y2 and
                                0 <= dst_x < buf_width and
                                0 <= dst_y < buf_height):
                                pixels[dst_y][dst_x] = color_idx
        else:
            # Zoom out: sample source pixels
            scale = int(1 / zoom_factor)
            display_width = src_width // scale
            display_height = src_height // scale

            for dst_y_off in range(display_height):
                for dst_x_off in range(display_width):
                    # Sample from source (use top-left pixel of each block)
                    src_x = dst_x_off * scale
                    src_y = dst_y_off * scale

                    if src_y < src_height and src_x < src_width:
                        color_idx = indexed_data[src_y][src_x]

                        dst_x = start_x + dst_x_off
                        dst_y = start_y + dst_y_off

                        # Clip to content area and buffer
                        if (clip_x <= dst_x < clip_x2 and
                            clip_y <= dst_y < clip_y2 and
                            0 <= dst_x < buf_width and
                            0 <= dst_y < buf_height):
                            pixels[dst_y][dst_x] = color_idx

    def _find_closest_color(self, r: int, g: int, b: int) -> int:
        """Find the closest color index in the palette for an RGB value."""
        from sixel import COLORS, COLOR_INDICES

        best_idx = 0
        best_dist = float('inf')

        for name, (pr, pg, pb) in COLORS.items():
            # Simple Euclidean distance in RGB space
            dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
            if dist < best_dist:
                best_dist = dist
                best_idx = COLOR_INDICES[name]

        return best_idx
