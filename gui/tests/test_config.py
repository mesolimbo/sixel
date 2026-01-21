"""Tests for the GUI configuration module."""

import sys
from pathlib import Path
import tempfile

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from config import (
    load_config,
    parse_layout,
    parse_bindings,
    build_gui_from_config,
    apply_bindings,
    get_widget_by_id,
    LayoutConfig,
    Binding,
    GUIConfig,
    PLATFORM_SCALE,
)
from gui import (
    Button,
    Checkbox,
    RadioButton,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    ImageDisplay,
)


class TestLayoutConfig:
    """Tests for layout configuration parsing."""

    def test_default_values(self):
        """Test that default layout values are applied (scaled for platform)."""
        layout = parse_layout({})
        scale = PLATFORM_SCALE
        assert layout.window_width == 240 * scale
        assert layout.window_height == 210 * scale
        assert layout.window_gap == 15 * scale
        assert layout.start_x == 15 * scale
        assert layout.start_y == 15 * scale
        assert layout.title_bar_height == 36 * scale
        assert layout.content_padding == 15 * scale

    def test_custom_values(self):
        """Test that custom layout values override defaults (scaled for platform)."""
        config = {
            'layout': {
                'window_width': 300,
                'window_height': 250,
                'window_gap': 20,
                'start_x': 10,
                'start_y': 10,
                'title_bar_height': 40,
                'content_padding': 20,
            }
        }
        layout = parse_layout(config)
        scale = PLATFORM_SCALE
        assert layout.window_width == 300 * scale
        assert layout.window_height == 250 * scale
        assert layout.window_gap == 20 * scale
        assert layout.start_x == 10 * scale
        assert layout.start_y == 10 * scale
        assert layout.title_bar_height == 40 * scale
        assert layout.content_padding == 20 * scale


class TestBindings:
    """Tests for binding configuration parsing."""

    def test_empty_bindings(self):
        """Test parsing empty bindings."""
        bindings = parse_bindings({})
        assert bindings == []

    def test_single_binding(self):
        """Test parsing a single binding."""
        config = {
            'bindings': [
                {'source': 'slider1', 'target': 'progress1', 'property': 'value'}
            ]
        }
        bindings = parse_bindings(config)
        assert len(bindings) == 1
        assert bindings[0].source_id == 'slider1'
        assert bindings[0].target_id == 'progress1'
        assert bindings[0].property_name == 'value'

    def test_default_property(self):
        """Test that default property is 'value'."""
        config = {
            'bindings': [
                {'source': 'a', 'target': 'b'}
            ]
        }
        bindings = parse_bindings(config)
        assert bindings[0].property_name == 'value'


class TestBuildGUI:
    """Tests for building GUI from configuration."""

    @pytest.fixture
    def simple_config_file(self):
        """Create a simple config file for testing."""
        config_content = """
layout:
  window_width: 200
  window_height: 150
  window_gap: 10
  start_x: 10
  start_y: 10
  title_bar_height: 30
  content_padding: 10

rows:
  - windows:
      - title: "TEST"
        widgets:
          - type: button
            id: btn1
            label: "CLICK"
            height: 40
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            return f.name

    def test_build_single_window(self, simple_config_file):
        """Test building a GUI with a single window (dimensions scaled for platform)."""
        gui, gui_config, width, height = build_gui_from_config(simple_config_file)
        scale = PLATFORM_SCALE

        assert len(gui.windows) == 1
        assert gui.windows[0].title == "TEST"
        assert gui.windows[0].x == 10 * scale
        assert gui.windows[0].y == 10 * scale
        assert gui.windows[0].width == 200 * scale
        assert gui.windows[0].height == 150 * scale

        Path(simple_config_file).unlink()

    def test_build_with_button(self, simple_config_file):
        """Test building a GUI with a button widget."""
        gui, gui_config, width, height = build_gui_from_config(simple_config_file)

        window = gui.windows[0]
        assert len(window.components) == 1
        assert isinstance(window.components[0], Button)
        assert window.components[0].label == "CLICK"

        Path(simple_config_file).unlink()

    def test_widget_registered_by_id(self, simple_config_file):
        """Test that widgets are registered by ID."""
        gui, gui_config, width, height = build_gui_from_config(simple_config_file)

        btn = get_widget_by_id(gui_config, 'btn1')
        assert btn is not None
        assert isinstance(btn, Button)
        assert btn.label == "CLICK"

        Path(simple_config_file).unlink()


class TestWidgetCreation:
    """Tests for creating different widget types."""

    @pytest.fixture
    def config_with_all_widgets(self):
        """Create a config with all widget types."""
        config_content = """
layout:
  window_width: 300
  window_height: 400
  content_padding: 10

rows:
  - windows:
      - title: "ALL WIDGETS"
        widgets:
          - type: button
            id: btn1
            label: "BUTTON"
            height: 40
            enabled: false

          - type: checkbox
            id: cb1
            label: "CHECK"
            height: 30
            checked: true

          - type: radio
            id: rb1
            label: "RADIO"
            height: 30
            selected: true
            group: test_group

          - type: text_input
            id: input1
            placeholder: "TYPE..."
            height: 35
            max_length: 50

          - type: slider
            id: slider1
            height: 25
            min_value: 10
            max_value: 200
            value: 100

          - type: progress_bar
            id: progress1
            height: 30
            value: 75
            max_value: 100

          - type: listbox
            id: list1
            height: 100
            items:
              - "ITEM A"
              - "ITEM B"
            selected_index: 1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            return f.name

    def test_button_creation(self, config_with_all_widgets):
        """Test button widget creation with properties."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        btn = get_widget_by_id(gui_config, 'btn1')

        assert isinstance(btn, Button)
        assert btn.label == "BUTTON"
        assert btn.enabled is False

        Path(config_with_all_widgets).unlink()

    def test_checkbox_creation(self, config_with_all_widgets):
        """Test checkbox widget creation with properties."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        cb = get_widget_by_id(gui_config, 'cb1')

        assert isinstance(cb, Checkbox)
        assert cb.label == "CHECK"
        assert cb.checked is True

        Path(config_with_all_widgets).unlink()

    def test_radio_button_and_group(self, config_with_all_widgets):
        """Test radio button creation and group registration."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        rb = get_widget_by_id(gui_config, 'rb1')

        assert isinstance(rb, RadioButton)
        assert rb.label == "RADIO"
        assert rb.selected is True
        assert 'test_group' in gui_config.radio_groups

        Path(config_with_all_widgets).unlink()

    def test_text_input_creation(self, config_with_all_widgets):
        """Test text input widget creation with properties."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        input_widget = get_widget_by_id(gui_config, 'input1')

        assert isinstance(input_widget, TextInput)
        assert input_widget.placeholder == "TYPE..."
        assert input_widget.max_length == 50

        Path(config_with_all_widgets).unlink()

    def test_slider_creation(self, config_with_all_widgets):
        """Test slider widget creation with properties."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        slider = get_widget_by_id(gui_config, 'slider1')

        assert isinstance(slider, Slider)
        assert slider.min_value == 10
        assert slider.max_value == 200
        assert slider.value == 100

        Path(config_with_all_widgets).unlink()

    def test_progress_bar_creation(self, config_with_all_widgets):
        """Test progress bar widget creation with properties."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        progress = get_widget_by_id(gui_config, 'progress1')

        assert isinstance(progress, ProgressBar)
        assert progress.value == 75
        assert progress.percentage == 75  # 75/100 = 75%

        Path(config_with_all_widgets).unlink()

    def test_listbox_creation(self, config_with_all_widgets):
        """Test listbox widget creation with properties."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_all_widgets)
        listbox = get_widget_by_id(gui_config, 'list1')

        assert isinstance(listbox, ListBox)
        assert len(listbox.items) == 2
        assert listbox.selected_index == 1

        Path(config_with_all_widgets).unlink()


class TestBindingsApplication:
    """Tests for applying bindings between widgets."""

    @pytest.fixture
    def config_with_bindings(self):
        """Create a config with slider-to-progress binding."""
        config_content = """
bindings:
  - source: slider1
    target: progress1
    property: value

rows:
  - windows:
      - title: "BINDING TEST"
        widgets:
          - type: slider
            id: slider1
            height: 30
            value: 50

          - type: progress_bar
            id: progress1
            height: 30
            value: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            return f.name

    def test_binding_syncs_values(self, config_with_bindings):
        """Test that bindings sync values between widgets."""
        gui, gui_config, _, _ = build_gui_from_config(config_with_bindings)

        slider = get_widget_by_id(gui_config, 'slider1')
        progress = get_widget_by_id(gui_config, 'progress1')

        # Initially different
        assert slider.value == 50
        assert progress.value == 0

        # Apply bindings
        sync_callback = apply_bindings(gui_config)
        sync_callback(0.016)  # Simulate one frame

        # After sync, progress should match slider
        assert progress.value == 50

        # Change slider value
        slider.value = 75
        sync_callback(0.016)

        # Progress should update
        assert progress.value == 75

        Path(config_with_bindings).unlink()


class TestMultiRowLayout:
    """Tests for multi-row layouts."""

    @pytest.fixture
    def multi_row_config(self):
        """Create a config with multiple rows."""
        config_content = """
layout:
  window_width: 100
  window_height: 100
  window_gap: 10
  start_x: 5
  start_y: 5

rows:
  - windows:
      - title: "ROW1-WIN1"
        widgets: []
      - title: "ROW1-WIN2"
        widgets: []
  - windows:
      - title: "ROW2-WIN1"
        widgets: []
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            return f.name

    def test_window_positions(self, multi_row_config):
        """Test that windows are positioned correctly in rows (scaled for platform)."""
        gui, gui_config, width, height = build_gui_from_config(multi_row_config)
        scale = PLATFORM_SCALE

        assert len(gui.windows) == 3

        # Row 1, Window 1
        assert gui.windows[0].title == "ROW1-WIN1"
        assert gui.windows[0].x == 5 * scale
        assert gui.windows[0].y == 5 * scale

        # Row 1, Window 2
        assert gui.windows[1].title == "ROW1-WIN2"
        assert gui.windows[1].x == 115 * scale  # 5 + 100 + 10
        assert gui.windows[1].y == 5 * scale

        # Row 2, Window 1
        assert gui.windows[2].title == "ROW2-WIN1"
        assert gui.windows[2].x == 5 * scale
        assert gui.windows[2].y == 115 * scale  # 5 + 100 + 10

        Path(multi_row_config).unlink()

    def test_frame_dimensions(self, multi_row_config):
        """Test that frame dimensions are calculated correctly (scaled for platform)."""
        gui, gui_config, width, height = build_gui_from_config(multi_row_config)
        scale = PLATFORM_SCALE

        # Width: 2 windows * 100 + 1 gap * 10 + 2 margins * 5 = 220 (then scaled)
        assert width == 220 * scale

        # Height: 2 rows * 100 + 1 gap * 10 + 2 margins * 5 + 30 (extra) = 250 (then scaled)
        assert height == 250 * scale

        Path(multi_row_config).unlink()


class TestDemoConfig:
    """Tests for the demo.yaml configuration file."""

    def test_demo_config_loads(self):
        """Test that the demo config file loads successfully (dimensions scaled for platform)."""
        demo_path = Path(__file__).parent.parent / 'demo.yaml'
        if not demo_path.exists():
            pytest.skip("demo.yaml not found")

        gui, gui_config, width, height = build_gui_from_config(str(demo_path))
        scale = PLATFORM_SCALE

        # Should have 8 windows (4 per row, 2 rows)
        assert len(gui.windows) == 8

        # Check frame dimensions match expected (scaled for platform)
        # Base dimensions are 1035x495 (unscaled)
        assert width == 1035 * scale
        assert height == 495 * scale

    def test_demo_config_widgets(self):
        """Test that demo config creates all expected widgets."""
        demo_path = Path(__file__).parent.parent / 'demo.yaml'
        if not demo_path.exists():
            pytest.skip("demo.yaml not found")

        gui, gui_config, _, _ = build_gui_from_config(str(demo_path))

        # Check expected widget IDs exist
        expected_ids = [
            'btn_primary', 'btn_secondary', 'btn_disabled',
            'cb_option_a', 'cb_option_b', 'cb_option_c',
            'rb_small', 'rb_medium', 'rb_large',
            'input_name', 'input_email', 'input_password',
            'slider1', 'slider2', 'slider3',
            'progress1', 'progress2', 'progress3',
            'item_list', 'image_display',
        ]

        for widget_id in expected_ids:
            assert widget_id in gui_config.widgets_by_id, f"Missing widget: {widget_id}"

    def test_demo_config_bindings(self):
        """Test that demo config creates slider-to-progress bindings."""
        demo_path = Path(__file__).parent.parent / 'demo.yaml'
        if not demo_path.exists():
            pytest.skip("demo.yaml not found")

        gui, gui_config, _, _ = build_gui_from_config(str(demo_path))

        # Should have 3 bindings (slider1->progress1, etc.)
        assert len(gui_config.bindings) == 3

        # Verify binding sources and targets
        binding_pairs = [(b.source_id, b.target_id) for b in gui_config.bindings]
        assert ('slider1', 'progress1') in binding_pairs
        assert ('slider2', 'progress2') in binding_pairs
        assert ('slider3', 'progress3') in binding_pairs
