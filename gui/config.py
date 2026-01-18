"""
GUI Configuration Module

Parses YAML configuration files to build GUI layouts with windows and widgets.
Supports variable bindings between widgets for reactive updates.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field

import yaml

# Platform detection
IS_MACOS = sys.platform == 'darwin'
IS_ITERM2 = os.environ.get('TERM_PROGRAM', '').lower() == 'iterm.app'

# UI scaling: 2x on macOS with iTerm2 (native protocol is fast enough)
# 1x elsewhere (sixel is slower, let terminal handle HiDPI)
PLATFORM_SCALE = 2 if (IS_MACOS and IS_ITERM2) else 1

from gui import (
    GUIState,
    Window,
    Button,
    Checkbox,
    RadioButton,
    RadioGroup,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    ImageDisplay,
    Component,
)


@dataclass
class LayoutConfig:
    """Layout configuration for the GUI."""
    window_width: int = 240
    window_height: int = 210
    window_gap: int = 15
    start_x: int = 15
    start_y: int = 15
    title_bar_height: int = 36
    content_padding: int = 15


@dataclass
class Binding:
    """Represents a binding between two widgets."""
    source_id: str
    target_id: str
    property_name: str = "value"


@dataclass
class GUIConfig:
    """Complete GUI configuration."""
    layout: LayoutConfig
    variables: Dict[str, Any] = field(default_factory=dict)
    bindings: List[Binding] = field(default_factory=list)
    widgets_by_id: Dict[str, Component] = field(default_factory=dict)
    radio_groups: Dict[str, RadioGroup] = field(default_factory=dict)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def parse_layout(config: Dict[str, Any]) -> LayoutConfig:
    """Parse layout configuration from YAML with platform scaling."""
    layout_data = config.get('layout', {})
    scale = PLATFORM_SCALE
    return LayoutConfig(
        window_width=layout_data.get('window_width', 240) * scale,
        window_height=layout_data.get('window_height', 210) * scale,
        window_gap=layout_data.get('window_gap', 15) * scale,
        start_x=layout_data.get('start_x', 15) * scale,
        start_y=layout_data.get('start_y', 15) * scale,
        title_bar_height=layout_data.get('title_bar_height', 36) * scale,
        content_padding=layout_data.get('content_padding', 15) * scale,
    )


def parse_bindings(config: Dict[str, Any]) -> List[Binding]:
    """Parse widget bindings from YAML."""
    bindings_data = config.get('bindings', [])
    bindings = []
    for binding in bindings_data:
        bindings.append(Binding(
            source_id=binding['source'],
            target_id=binding['target'],
            property_name=binding.get('property', 'value'),
        ))
    return bindings


def create_widget(
    widget_config: Dict[str, Any],
    x: int,
    y: int,
    default_width: int,
    gui_config: GUIConfig,
    config_dir: Path,
) -> Optional[Component]:
    """Create a widget from configuration."""
    widget_type = widget_config.get('type')
    widget_id = widget_config.get('id')
    scale = PLATFORM_SCALE
    height = widget_config.get('height', 36) * scale

    # Calculate width - can be adjusted with width_offset (also scaled)
    width_offset = widget_config.get('width_offset', 0) * scale
    width = default_width + width_offset

    widget: Optional[Component] = None

    if widget_type == 'button':
        widget = Button(
            x=x, y=y,
            width=width, height=height,
            label=widget_config.get('label', ''),
            toggle=widget_config.get('toggle', False),
        )
        if not widget_config.get('enabled', True):
            widget.enabled = False

    elif widget_type == 'checkbox':
        widget = Checkbox(
            x=x, y=y,
            width=width, height=height,
            label=widget_config.get('label', ''),
            checked=widget_config.get('checked', False),
        )

    elif widget_type == 'radio':
        widget = RadioButton(
            x=x, y=y,
            width=width, height=height,
            label=widget_config.get('label', ''),
            selected=widget_config.get('selected', False),
        )
        # Add to radio group if specified
        group_name = widget_config.get('group')
        if group_name:
            if group_name not in gui_config.radio_groups:
                gui_config.radio_groups[group_name] = RadioGroup()
            gui_config.radio_groups[group_name].add_button(widget)

    elif widget_type == 'text_input':
        widget = TextInput(
            x=x, y=y,
            width=width, height=height,
            placeholder=widget_config.get('placeholder', ''),
            max_length=widget_config.get('max_length', 20),
        )

    elif widget_type == 'slider':
        widget = Slider(
            x=x, y=y,
            width=width, height=height,
            min_value=widget_config.get('min_value', 0.0),
            max_value=widget_config.get('max_value', 100.0),
            value=widget_config.get('value', 50.0),
        )

    elif widget_type == 'progress_bar':
        widget = ProgressBar(
            x=x, y=y,
            width=width, height=height,
            value=widget_config.get('value', 0.0),
            max_value=widget_config.get('max_value', 100.0),
        )

    elif widget_type == 'listbox':
        items = widget_config.get('items', [])
        widget = ListBox(
            x=x, y=y,
            width=width, height=height,
            items=items,
        )
        selected_index = widget_config.get('selected_index')
        if selected_index is not None:
            widget.select_index(selected_index)

    elif widget_type == 'image':
        image_path = widget_config.get('image_path', '')
        # Resolve relative paths from config directory
        if image_path and not Path(image_path).is_absolute():
            image_path = str(config_dir / image_path)
        widget = ImageDisplay(
            x=x, y=y,
            width=width, height=height,
            image_path=image_path if image_path else None,
        )

    # Register widget by ID
    if widget and widget_id:
        gui_config.widgets_by_id[widget_id] = widget

    return widget


def calculate_widget_spacing(widget_config: Dict[str, Any]) -> int:
    """Calculate vertical spacing for a widget based on its type and height."""
    widget_type = widget_config.get('type')
    scale = PLATFORM_SCALE
    height = widget_config.get('height', 36) * scale

    # Different widget types have different default spacing (scaled)
    spacing_map = {
        'button': 11 * scale,      # 42 + 11 = 53 (from original: 68 - 15 = 53)
        'checkbox': 9 * scale,     # 36 + 9 = 45
        'radio': 9 * scale,        # 36 + 9 = 45
        'text_input': 15 * scale,  # 42 + 15 = 57
        'slider': 22 * scale,      # 30 + 22 = 52
        'progress_bar': 16 * scale, # 36 + 16 = 52
        'listbox': 0,
        'image': 0,
    }

    base_spacing = spacing_map.get(widget_type, 10 * scale)
    return height + base_spacing


def build_gui_from_config(config_path: str) -> tuple[GUIState, GUIConfig, int, int]:
    """
    Build a complete GUI from a YAML configuration file.

    Returns:
        Tuple of (GUIState, GUIConfig, frame_width, frame_height)
    """
    config_dir = Path(config_path).parent
    config = load_config(config_path)

    layout = parse_layout(config)
    bindings = parse_bindings(config)
    variables = config.get('variables', {})

    gui_config = GUIConfig(
        layout=layout,
        variables=variables,
        bindings=bindings,
    )

    gui = GUIState()
    rows = config.get('rows', [])

    # Track max windows per row for frame size calculation
    max_windows_per_row = 0

    for row_index, row in enumerate(rows):
        windows = row.get('windows', [])
        max_windows_per_row = max(max_windows_per_row, len(windows))

        # Calculate row Y position
        row_y = layout.start_y + row_index * (layout.window_height + layout.window_gap)

        for window_index, window_config in enumerate(windows):
            # Calculate window position
            window_x = layout.start_x + window_index * (layout.window_width + layout.window_gap)

            window = Window(
                title=window_config.get('title', ''),
                x=window_x,
                y=row_y,
                width=layout.window_width,
                height=layout.window_height,
            )

            # Content area starts after title bar and padding
            content_x = window_x + layout.content_padding
            content_y = row_y + layout.title_bar_height + layout.content_padding
            content_width = layout.window_width - 2 * layout.content_padding

            # Add extra Y offset for certain widget types (sliders, progress bars)
            widgets = window_config.get('widgets', [])
            if widgets:
                first_widget_type = widgets[0].get('type')
                if first_widget_type in ('slider', 'progress_bar'):
                    content_y += 7 * PLATFORM_SCALE  # Extra top offset for sliders/progress bars

            current_y = content_y

            for widget_config in widgets:
                widget = create_widget(
                    widget_config,
                    x=content_x,
                    y=current_y,
                    default_width=content_width,
                    gui_config=gui_config,
                    config_dir=config_dir,
                )

                if widget:
                    window.add_component(widget)
                    current_y += calculate_widget_spacing(widget_config)

            gui.add_window(window)

    # Calculate frame dimensions
    num_rows = len(rows)
    frame_width = (
        max_windows_per_row * layout.window_width +
        (max_windows_per_row - 1) * layout.window_gap +
        2 * layout.start_x
    )
    frame_height = (
        num_rows * layout.window_height +
        (num_rows - 1) * layout.window_gap +
        2 * layout.start_y +
        30 * PLATFORM_SCALE  # Extra space for instructions
    )

    return gui, gui_config, frame_width, frame_height


def apply_bindings(gui_config: GUIConfig) -> Callable[[float], None]:
    """
    Create a sync callback that applies bindings between widgets.

    Returns a callback function suitable for the animation loop.
    """
    prev_values: Dict[str, Any] = {}

    def sync_callback(delta_time: float) -> None:
        for binding in gui_config.bindings:
            source = gui_config.widgets_by_id.get(binding.source_id)
            target = gui_config.widgets_by_id.get(binding.target_id)

            if source is None or target is None:
                continue

            # Get source value
            source_value = getattr(source, binding.property_name, None)
            if source_value is None:
                continue

            # Check if value changed
            cache_key = f"{binding.source_id}.{binding.property_name}"
            if prev_values.get(cache_key) == source_value:
                continue

            # Update target
            if hasattr(target, binding.property_name):
                setattr(target, binding.property_name, source_value)
                prev_values[cache_key] = source_value

    return sync_callback


def get_widget_by_id(gui_config: GUIConfig, widget_id: str) -> Optional[Component]:
    """Get a widget by its ID."""
    return gui_config.widgets_by_id.get(widget_id)


def get_variable(gui_config: GUIConfig, name: str) -> Any:
    """Get a variable value."""
    return gui_config.variables.get(name)


def set_variable(gui_config: GUIConfig, name: str, value: Any) -> None:
    """Set a variable value."""
    gui_config.variables[name] = value
