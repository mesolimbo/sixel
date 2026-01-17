"""
Renderer module for GUI demo.

Renders GUI components and windows as sixel graphics.
Uses the component state to determine visual appearance.
"""

from typing import List, Optional, Tuple

from sixel import (
    create_pixel_buffer,
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
        self.scale = 1
        self.bold = True

        # Layout constants
        self.padding = 8
        self.corner_radius = 4
        self.title_bar_height = 24
        self.component_padding = 6

    def render_frame(self, gui_state: GUIState) -> str:
        """
        Render the entire GUI state as a sixel string.

        Args:
            gui_state: The GUI state to render

        Returns:
            Sixel escape sequence string
        """
        # Create pixel buffer with background
        pixels = create_pixel_buffer(
            self.width,
            self.height,
            COLOR_INDICES["background"]
        )

        # Render each window
        for window in gui_state.windows:
            self._render_window(pixels, window)

        # Draw instructions at bottom
        self._draw_instructions(pixels)

        return pixels_to_sixel(pixels, self.width, self.height)

    def _draw_instructions(self, pixels: List[List[int]]) -> None:
        """Draw instruction text at the bottom of the frame."""
        y = self.height - 20
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
        # Draw a highlight border 2 pixels outside the component
        focus_color = COLOR_INDICES["input_focus"]

        # Draw outer border (2 pixels thick)
        for offset in range(2):
            x = b.x - 2 + offset
            y = b.y - 2 + offset
            w = b.width + 4 - offset * 2
            h = b.height + 4 - offset * 2
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

        # Show click count if clicked
        if button.click_count > 0:
            count_text = str(button.click_count)
            count_x = button.x + button.width - 12
            count_y = button.y + 2
            draw_text(pixels, count_x, count_y, count_text,
                     COLOR_INDICES["accent"], 1, False)

    def _render_checkbox(self, pixels: List[List[int]], checkbox: Checkbox) -> None:
        """Render a checkbox component."""
        box_size = 16
        box_x = checkbox.x
        box_y = checkbox.y + (checkbox.height - box_size) // 2

        # Checkbox box
        if checkbox.checked:
            fill_rect(pixels, box_x, box_y, box_size, box_size,
                     COLOR_INDICES["checkbox_checked"])
            # Draw checkmark
            draw_checkmark(pixels, box_x + 2, box_y + 2, box_size - 4,
                          COLOR_INDICES["text_highlight"])
        else:
            fill_rect(pixels, box_x, box_y, box_size, box_size,
                     COLOR_INDICES["checkbox_bg"])

        # Border
        draw_rect_border(pixels, box_x, box_y, box_size, box_size,
                        COLOR_INDICES["checkbox_border"])

        # Label
        label_x = box_x + box_size + 8
        label_y = checkbox.y + (checkbox.height - FONT_HEIGHT * self.scale) // 2
        text_color = COLOR_INDICES["text"] if checkbox.enabled else COLOR_INDICES["text_disabled"]
        draw_text(pixels, label_x, label_y, checkbox.label, text_color, self.scale, self.bold)

    def _render_radio_button(self, pixels: List[List[int]], radio: RadioButton) -> None:
        """Render a radio button component."""
        circle_radius = 7
        circle_cx = radio.x + circle_radius + 2
        circle_cy = radio.y + radio.height // 2

        # Outer circle
        draw_circle(pixels, circle_cx, circle_cy, circle_radius,
                   COLOR_INDICES["checkbox_border"], filled=False)

        # Inner circle if selected
        if radio.selected:
            draw_circle(pixels, circle_cx, circle_cy, circle_radius - 3,
                       COLOR_INDICES["checkbox_checked"], filled=True)

        # Label
        label_x = radio.x + circle_radius * 2 + 10
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
                cursor_x = text_x + cursor_offset + 2
                fill_rect(pixels, cursor_x, text_y, 2,
                         FONT_HEIGHT * self.scale, COLOR_INDICES["input_cursor"])
        else:
            # Show placeholder or cursor
            if text_input.has_focus:
                fill_rect(pixels, text_x, text_y, 2,
                         FONT_HEIGHT * self.scale, COLOR_INDICES["input_cursor"])
            else:
                draw_text(pixels, text_x, text_y, text_input.placeholder,
                         COLOR_INDICES["text_dim"], self.scale, False)

    def _render_slider(self, pixels: List[List[int]], slider: Slider) -> None:
        """Render a slider component."""
        thumb_width = 10
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
        value_x = slider.x + slider.width + 8
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
