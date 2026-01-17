"""
Tests for the renderer module (renderer.py).

Tests cover:
- Renderer initialization
- Layout calculations
- View switching
- Frame rendering
- Value formatting
"""

import sys
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer import MetricsRenderer, MetricView, VIEW_TITLES
from sixel import SIXEL_START, SIXEL_END, COLOR_INDICES


class TestMetricView:
    """Tests for MetricView enum."""

    def test_all_views_defined(self):
        """Test that all expected views are defined."""
        assert MetricView.ENERGY.value == 0
        assert MetricView.CPU.value == 1
        assert MetricView.IO.value == 2
        assert MetricView.MEMORY.value == 3
        assert MetricView.NETWORK.value == 4

    def test_view_count(self):
        """Test that there are exactly 5 views."""
        assert len(MetricView) == 5


class TestViewTitles:
    """Tests for VIEW_TITLES mapping."""

    def test_all_views_have_titles(self):
        """Test that every view has a title."""
        for view in MetricView:
            assert view in VIEW_TITLES

    def test_title_values(self):
        """Test specific title values."""
        assert VIEW_TITLES[MetricView.ENERGY] == "ENERGY IMPACT"
        assert VIEW_TITLES[MetricView.CPU] == "CPU LOAD"
        assert VIEW_TITLES[MetricView.IO] == "IO"
        assert VIEW_TITLES[MetricView.MEMORY] == "MEMORY PRESSURE"
        assert VIEW_TITLES[MetricView.NETWORK] == "PACKETS"


class TestRendererInit:
    """Tests for MetricsRenderer initialization."""

    def test_default_initialization(self):
        """Test renderer initializes with default values."""
        renderer = MetricsRenderer()
        assert renderer.width == 820
        assert renderer.height == 156
        assert renderer.scale == 2  # Bold text scale

    def test_custom_dimensions(self):
        """Test renderer with custom dimensions."""
        renderer = MetricsRenderer(width=400, height=100)
        assert renderer.width == 400
        assert renderer.height == 100

    def test_default_view_is_cpu(self):
        """Test that default view is CPU."""
        renderer = MetricsRenderer()
        assert renderer.current_view == MetricView.CPU

    def test_layout_constants_calculated(self):
        """Test that layout constants are calculated."""
        renderer = MetricsRenderer()

        assert renderer.padding > 0
        assert renderer.border_width > 0
        assert renderer.panel_padding > 0
        assert renderer.row_height > 0
        assert renderer.corner_radius > 0
        assert renderer.instruction_height > 0

    def test_panel_widths_calculated(self):
        """Test that panel widths are calculated."""
        renderer = MetricsRenderer()

        assert renderer.left_panel_width > 0
        assert renderer.center_panel_width > 0
        assert renderer.right_panel_width > 0

        # Three panels should fit within the width
        total_panel_width = (
            renderer.left_panel_width +
            renderer.center_panel_width +
            renderer.right_panel_width
        )
        assert total_panel_width < renderer.width

    def test_panel_positions_calculated(self):
        """Test that panel positions are calculated."""
        renderer = MetricsRenderer()

        assert renderer.panel_top > 0
        assert renderer.left_x >= 0
        assert renderer.center_x > renderer.left_x
        assert renderer.right_x > renderer.center_x

    def test_graph_area_calculated(self):
        """Test that graph area is calculated."""
        renderer = MetricsRenderer()

        assert renderer.graph_y > 0
        assert renderer.graph_height > 0


class TestRendererViewSwitching:
    """Tests for view switching functionality."""

    def test_next_view_cycles(self):
        """Test that next_view cycles through all views."""
        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY

        assert renderer.next_view() == MetricView.CPU
        assert renderer.next_view() == MetricView.IO
        assert renderer.next_view() == MetricView.MEMORY
        assert renderer.next_view() == MetricView.NETWORK
        assert renderer.next_view() == MetricView.ENERGY  # Cycles back

    def test_next_view_returns_new_view(self):
        """Test that next_view returns the new view."""
        renderer = MetricsRenderer()
        new_view = renderer.next_view()
        assert new_view == renderer.current_view

    def test_view_cycle_complete(self):
        """Test that cycling through all views returns to start."""
        renderer = MetricsRenderer()
        start_view = renderer.current_view

        for _ in range(len(MetricView)):
            renderer.next_view()

        assert renderer.current_view == start_view


class TestRendererFormatting:
    """Tests for value formatting methods."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer for testing."""
        return MetricsRenderer()

    def test_fmt_ready(self, renderer):
        """Test _fmt with stats ready."""
        result = renderer._fmt(42.5, ".1f", True, "%")
        assert result == "42.5%"

    def test_fmt_not_ready(self, renderer):
        """Test _fmt with stats not ready."""
        result = renderer._fmt(42.5, ".1f", False, "%")
        assert result == "--"

    def test_fmt_no_suffix(self, renderer):
        """Test _fmt without suffix."""
        result = renderer._fmt(42.5, ".1f", True)
        assert result == "42.5"

    def test_fmt_int_ready(self, renderer):
        """Test _fmt_int with stats ready."""
        result = renderer._fmt_int(1234567, True)
        assert result == "1,234,567"

    def test_fmt_int_not_ready(self, renderer):
        """Test _fmt_int with stats not ready."""
        result = renderer._fmt_int(1234567, False)
        assert result == "--"

    def test_fmt_int_zero(self, renderer):
        """Test _fmt_int with zero."""
        result = renderer._fmt_int(0, True)
        assert result == "0"


class TestRendererRendering:
    """Tests for frame rendering."""

    def test_render_frame_returns_sixel(self, mock_metrics, renderer):
        """Test that render_frame returns valid sixel string."""
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        assert len(output) > 100

    def test_render_frame_all_views(self, mock_metrics, renderer):
        """Test rendering all views."""
        for view in MetricView:
            renderer.current_view = view
            output = renderer.render_frame(mock_metrics)

            assert output.startswith(SIXEL_START), f"View {view.name} failed"
            assert output.endswith(SIXEL_END), f"View {view.name} failed"

    def test_render_frame_stats_not_ready(self, mock_metrics, renderer):
        """Test rendering when stats are not ready."""
        output = renderer.render_frame(mock_metrics, stats_ready=False)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_frame_contains_colors(self, mock_metrics, renderer):
        """Test that rendered frame contains color definitions."""
        output = renderer.render_frame(mock_metrics)

        # Should contain color palette entries
        assert "#" in output
        assert ";2;" in output  # RGB color format


class TestRendererCPUView:
    """Tests for CPU view rendering."""

    def test_cpu_view_renders(self, mock_metrics, renderer):
        """Test CPU view renders successfully."""
        renderer.current_view = MetricView.CPU
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererMemoryView:
    """Tests for Memory view rendering."""

    def test_memory_view_renders(self, mock_metrics, renderer):
        """Test Memory view renders successfully."""
        renderer.current_view = MetricView.MEMORY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererIOView:
    """Tests for I/O view rendering."""

    def test_io_view_renders(self, mock_metrics, renderer):
        """Test I/O view renders successfully."""
        renderer.current_view = MetricView.IO
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererNetworkView:
    """Tests for Network view rendering."""

    def test_network_view_renders(self, mock_metrics, renderer):
        """Test Network view renders successfully."""
        renderer.current_view = MetricView.NETWORK
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererEnergyView:
    """Tests for Energy view rendering."""

    def test_energy_view_renders(self, mock_metrics, renderer):
        """Test Energy view renders successfully."""
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererWithBattery:
    """Tests for rendering with battery metrics."""

    def test_energy_view_with_battery(self, mock_metrics, renderer):
        """Test Energy view renders with battery present."""
        mock_metrics.battery.has_battery = True
        mock_metrics.battery.charge_percent = 85.0
        mock_metrics.battery.time_remaining_minutes = 120

        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_energy_view_no_battery(self, mock_metrics, renderer):
        """Test Energy view renders without battery."""
        mock_metrics.battery.has_battery = False

        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererScaling:
    """Tests for renderer with different scales."""

    def test_small_renderer(self, mock_metrics, small_renderer):
        """Test rendering with smaller dimensions."""
        output = small_renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_custom_renderer(self, mock_metrics, custom_renderer):
        """Test rendering with custom dimensions."""
        renderer = custom_renderer(width=400, height=60)
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererMultipleFrames:
    """Tests for rendering multiple frames."""

    def test_render_multiple_frames(self, mock_metrics, renderer):
        """Test rendering multiple frames in sequence."""
        frames = []
        for _ in range(5):
            frame = renderer.render_frame(mock_metrics)
            frames.append(frame)

        for frame in frames:
            assert frame.startswith(SIXEL_START)
            assert frame.endswith(SIXEL_END)

    def test_render_while_switching_views(self, mock_metrics, renderer):
        """Test rendering while switching between views."""
        for _ in range(10):
            output = renderer.render_frame(mock_metrics)
            assert output.startswith(SIXEL_START)
            assert output.endswith(SIXEL_END)
            renderer.next_view()
