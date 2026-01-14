"""
End-to-end tests for sixel rendering.

These tests verify that the sixtop monitor actually renders valid sixel output
that could be displayed on a sixel-capable terminal.
"""

import re
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer import MetricsRenderer, MetricView, VIEW_TITLES
from sixel import (
    SIXEL_START,
    SIXEL_END,
    SIXEL_NEWLINE,
    SIXEL_CARRIAGE_RETURN,
    COLORS,
    COLOR_INDICES,
    generate_palette,
    create_pixel_buffer,
    fill_rect,
    draw_text,
    draw_line_graph,
    draw_bar_graph,
    pixels_to_sixel,
    rgb_to_sixel_color,
    _encode_rle,
    get_text_width,
)


class TestSixelEscapeSequences:
    """Test that sixel output has correct escape sequences."""

    def test_sixel_start_sequence(self):
        """Verify SIXEL_START is the correct DCS sequence."""
        assert SIXEL_START == "\x1bPq"

    def test_sixel_end_sequence(self):
        """Verify SIXEL_END is the correct ST sequence."""
        assert SIXEL_END == "\x1b\\"

    def test_basic_sixel_output_format(self):
        """Verify a minimal sixel output has correct structure."""
        pixels = create_pixel_buffer(6, 6, 0)
        output = pixels_to_sixel(pixels, 6, 6)

        assert output.startswith(SIXEL_START), "Sixel output must start with ESC P q"
        assert output.endswith(SIXEL_END), "Sixel output must end with ESC \\"

    def test_sixel_contains_raster_attributes(self):
        """Verify sixel output contains raster attributes (dimensions)."""
        pixels = create_pixel_buffer(10, 12, 0)
        output = pixels_to_sixel(pixels, 10, 12)

        assert '"1;1;10;12' in output, "Sixel should contain raster attributes"


class TestColorPalette:
    """Test color palette generation and format."""

    def test_all_monitor_colors_defined(self):
        """Verify all required monitor colors are in the palette."""
        required_colors = [
            "background",
            "panel_bg",
            "border",
            "border_highlight",
            "text",
            "text_dim",
            "text_cyan",
            "text_red",
            "text_green",
            "graph_cyan",
            "graph_red",
            "graph_green",
            "graph_blue",
            "graph_fill_cyan",
            "graph_fill_red",
            "graph_fill_green",
            "graph_fill_blue",
            "graph_yellow",
            "bg_dark",
        ]
        for color in required_colors:
            assert color in COLORS, f"Missing color: {color}"
            assert color in COLOR_INDICES, f"Missing color index: {color}"

    def test_color_indices_are_unique(self):
        """Verify all color indices are unique."""
        indices = list(COLOR_INDICES.values())
        assert len(indices) == len(set(indices)), "Color indices must be unique"

    def test_rgb_to_sixel_conversion(self):
        """Verify RGB values are converted to 0-100 range correctly."""
        assert rgb_to_sixel_color(0, 0, 0) == (0, 0, 0)
        assert rgb_to_sixel_color(255, 255, 255) == (100, 100, 100)
        r, g, b = rgb_to_sixel_color(128, 128, 128)
        assert 49 <= r <= 51
        assert 49 <= g <= 51
        assert 49 <= b <= 51

    def test_palette_format(self):
        """Verify palette uses correct sixel color definition format."""
        palette = generate_palette()

        for name, idx in COLOR_INDICES.items():
            pattern = rf"#{idx};2;\d+;\d+;\d+"
            assert re.search(pattern, palette), f"Missing palette entry for {name}"

    def test_palette_in_sixel_output(self):
        """Verify palette is included in sixel output."""
        pixels = create_pixel_buffer(6, 6, COLOR_INDICES["text_cyan"])
        output = pixels_to_sixel(pixels, 6, 6)

        assert f"#{COLOR_INDICES['text_cyan']};2;" in output


class TestRLEEncoding:
    """Test Run-Length Encoding optimization."""

    def test_rle_single_values(self):
        """Single values should not use RLE."""
        result = _encode_rle([1])
        assert result == "@"
        assert "!" not in result

    def test_rle_two_values(self):
        """Two identical values should not use RLE."""
        result = _encode_rle([1, 1])
        assert result == "@@"
        assert "!" not in result

    def test_rle_three_or_more_values(self):
        """Three or more identical values should use RLE."""
        result = _encode_rle([1, 1, 1])
        assert result == "!3@"

    def test_rle_large_run(self):
        """Large runs should use RLE notation."""
        result = _encode_rle([0] * 100)
        assert result == "!100?"

    def test_rle_mixed_runs(self):
        """Mixed values should encode correctly."""
        result = _encode_rle([1, 1, 1, 2, 2, 2, 2])
        assert "!3@" in result
        assert "!4A" in result


class TestPixelBuffer:
    """Test pixel buffer operations."""

    def test_create_buffer_dimensions(self):
        """Buffer should have correct dimensions."""
        pixels = create_pixel_buffer(10, 20, 0)
        assert len(pixels) == 20
        assert len(pixels[0]) == 10

    def test_create_buffer_fill_value(self):
        """Buffer should be filled with specified value."""
        pixels = create_pixel_buffer(5, 5, 3)
        for row in pixels:
            assert all(p == 3 for p in row)

    def test_fill_rect_basic(self):
        """fill_rect should set pixels correctly."""
        pixels = create_pixel_buffer(10, 10, 0)
        fill_rect(pixels, 2, 2, 3, 3, 5)

        for y in range(2, 5):
            for x in range(2, 5):
                assert pixels[y][x] == 5

        assert pixels[0][0] == 0
        assert pixels[9][9] == 0

    def test_fill_rect_clipping(self):
        """fill_rect should clip to buffer bounds."""
        pixels = create_pixel_buffer(10, 10, 0)
        fill_rect(pixels, 8, 8, 5, 5, 1)

        assert pixels[8][8] == 1
        assert pixels[9][9] == 1


class TestGraphRendering:
    """Test graph rendering functions."""

    def test_line_graph_produces_pixels(self):
        """Line graph should produce non-zero pixels."""
        pixels = create_pixel_buffer(100, 50, 0)
        data = [10, 30, 50, 70, 90, 80, 60, 40, 20, 10]
        draw_line_graph(pixels, 0, 0, 100, 50, data, 1)

        has_pixels = any(p == 1 for row in pixels for p in row)
        assert has_pixels, "Line graph should produce pixels"

    def test_bar_graph_produces_pixels(self):
        """Bar graph should produce non-zero pixels."""
        pixels = create_pixel_buffer(100, 20, 0)
        draw_bar_graph(pixels, 0, 0, 100, 20, 75.0, 1)

        has_pixels = any(p == 1 for row in pixels for p in row)
        assert has_pixels, "Bar graph should produce pixels"


class TestTextRendering:
    """Test bitmap font text rendering."""

    def test_get_text_width(self):
        """Text width calculation should be correct."""
        width = get_text_width("AB", 1)
        assert width == 11

    def test_get_text_width_scaled(self):
        """Scaled text width should multiply correctly."""
        width_1x = get_text_width("A", 1)
        width_2x = get_text_width("A", 2)
        assert width_2x == width_1x * 2

    def test_draw_text_produces_pixels(self):
        """draw_text should produce non-zero pixels."""
        pixels = create_pixel_buffer(50, 20, 0)
        draw_text(pixels, 0, 0, "A", 1, 1)

        has_pixels = any(p == 1 for row in pixels for p in row)
        assert has_pixels, "Text should produce pixels"


class TestMetricsRenderer:
    """Test the metrics renderer produces valid sixel output."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer for testing."""
        return MetricsRenderer()

    def test_renderer_frame_dimensions(self, renderer):
        """Renderer should have correct frame dimensions."""
        assert renderer.width > 0
        assert renderer.height > 0

    def test_render_frame_returns_sixel(self, renderer, mock_metrics):
        """render_frame should return valid sixel string."""
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        assert len(output) > 100

    def test_render_frame_contains_colors(self, renderer, mock_metrics):
        """Rendered frame should use multiple colors."""
        output = renderer.render_frame(mock_metrics)

        # Should contain color palette entries
        assert "#" in output
        assert ";2;" in output

    def test_render_cpu_view(self, renderer, mock_metrics):
        """CPU view should render correctly."""
        renderer.current_view = MetricView.CPU
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_memory_view(self, renderer, mock_metrics):
        """Memory view should render correctly."""
        renderer.current_view = MetricView.MEMORY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_io_view(self, renderer, mock_metrics):
        """I/O view should render correctly."""
        renderer.current_view = MetricView.IO
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_network_view(self, renderer, mock_metrics):
        """Network view should render correctly."""
        renderer.current_view = MetricView.NETWORK
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_energy_view(self, renderer, mock_metrics):
        """Energy view should render correctly."""
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestFullMonitorRendering:
    """Integration tests for complete monitor rendering scenarios."""

    def test_render_all_views(self, mock_metrics):
        """All views should render without errors."""
        renderer = MetricsRenderer()

        for view in MetricView:
            renderer.current_view = view
            output = renderer.render_frame(mock_metrics)

            assert output.startswith(SIXEL_START), f"View {view.name} failed start"
            assert output.endswith(SIXEL_END), f"View {view.name} failed end"
            assert len(output) > 1000, f"View {view.name} too small"

    def test_render_views_with_stats_not_ready(self, mock_metrics):
        """Views should render correctly when stats not ready."""
        renderer = MetricsRenderer()

        for view in MetricView:
            renderer.current_view = view
            output = renderer.render_frame(mock_metrics, stats_ready=False)

            assert output.startswith(SIXEL_START)
            assert output.endswith(SIXEL_END)

    def test_render_multiple_frames(self, mock_metrics):
        """Multiple frames should render consistently."""
        renderer = MetricsRenderer()

        frames = []
        for _ in range(10):
            frames.append(renderer.render_frame(mock_metrics))
            renderer.next_view()

        for i, frame in enumerate(frames):
            assert frame.startswith(SIXEL_START), f"Frame {i} invalid start"
            assert frame.endswith(SIXEL_END), f"Frame {i} invalid end"

    def test_render_view_cycle(self, mock_metrics):
        """Cycling through all views should work correctly."""
        renderer = MetricsRenderer()
        start_view = renderer.current_view

        # Cycle through all views and back
        for _ in range(len(MetricView)):
            output = renderer.render_frame(mock_metrics)
            assert output.startswith(SIXEL_START)
            assert output.endswith(SIXEL_END)
            renderer.next_view()

        assert renderer.current_view == start_view


class TestSixelOutputParsing:
    """Test that sixel output can be parsed and validated."""

    def test_sixel_band_structure(self):
        """Sixel output should have proper band structure."""
        pixels = create_pixel_buffer(10, 18, 0)
        output = pixels_to_sixel(pixels, 10, 18)

        content = output[len(SIXEL_START):-len(SIXEL_END)]

        # Should have band separators for 3 bands
        assert content.count(SIXEL_NEWLINE) >= 2

    def test_sixel_color_switching(self):
        """Multi-color output should switch colors correctly."""
        pixels = create_pixel_buffer(10, 6, 0)
        fill_rect(pixels, 0, 0, 5, 6, COLOR_INDICES["text_cyan"])
        fill_rect(pixels, 5, 0, 5, 6, COLOR_INDICES["text_red"])
        output = pixels_to_sixel(pixels, 10, 6)

        assert output.count("#") >= 2


class TestCrossPlatformRendering:
    """Test rendering works across different configurations."""

    @pytest.mark.parametrize("dimensions", [(580, 84), (400, 60), (800, 120)])
    def test_different_renderer_sizes(self, dimensions, mock_metrics):
        """Monitor should render at different sizes."""
        width, height = dimensions
        renderer = MetricsRenderer(width=width, height=height)
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        assert len(output) > 100

    @pytest.mark.parametrize("view", list(MetricView))
    def test_each_view_renders(self, view, mock_metrics):
        """Each metric view should render correctly."""
        renderer = MetricsRenderer()
        renderer.current_view = view
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)


class TestRendererWithEmptyData:
    """Test rendering with minimal/empty data."""

    def test_render_with_no_history(self, mock_metrics):
        """Renderer should handle empty history gracefully."""
        # Clear all history
        mock_metrics.cpu.system_history.clear()
        mock_metrics.cpu.user_history.clear()
        mock_metrics.memory.pressure_history.clear()
        mock_metrics.disk.read_history.clear()
        mock_metrics.disk.write_history.clear()
        mock_metrics.network.received_history.clear()
        mock_metrics.network.sent_history.clear()
        mock_metrics.battery.energy_history.clear()

        renderer = MetricsRenderer()
        for view in MetricView:
            renderer.current_view = view
            output = renderer.render_frame(mock_metrics)

            assert output.startswith(SIXEL_START)
            assert output.endswith(SIXEL_END)


class TestRendererBattery:
    """Test rendering with different battery states."""

    def test_render_no_battery(self, mock_metrics):
        """Renderer should handle no battery gracefully."""
        mock_metrics.battery.has_battery = False

        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_battery_charging(self, mock_metrics):
        """Renderer should handle charging battery."""
        mock_metrics.battery.has_battery = True
        mock_metrics.battery.is_charging = True
        mock_metrics.battery.power_plugged = True
        mock_metrics.battery.charge_percent = 50.0

        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_battery_discharging(self, mock_metrics):
        """Renderer should handle discharging battery."""
        mock_metrics.battery.has_battery = True
        mock_metrics.battery.is_charging = False
        mock_metrics.battery.power_plugged = False
        mock_metrics.battery.charge_percent = 25.0
        mock_metrics.battery.time_remaining_minutes = 60

        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)

    def test_render_battery_level_high(self, mock_metrics):
        """Battery bar should render green for high charge (>50%)."""
        mock_metrics.battery.has_battery = True
        mock_metrics.battery.charge_percent = 75.0

        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        # Should contain the green graph color
        assert f"#{COLOR_INDICES['graph_green']}" in output

    def test_render_battery_level_medium(self, mock_metrics):
        """Battery bar should render yellow for medium charge (21-50%)."""
        mock_metrics.battery.has_battery = True
        mock_metrics.battery.charge_percent = 35.0

        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        # Should contain the yellow graph color
        assert f"#{COLOR_INDICES['graph_yellow']}" in output

    def test_render_battery_level_low(self, mock_metrics):
        """Battery bar should render red for low charge (<=20%)."""
        mock_metrics.battery.has_battery = True
        mock_metrics.battery.charge_percent = 15.0

        renderer = MetricsRenderer()
        renderer.current_view = MetricView.ENERGY
        output = renderer.render_frame(mock_metrics)

        assert output.startswith(SIXEL_START)
        assert output.endswith(SIXEL_END)
        # Should contain the red graph color
        assert f"#{COLOR_INDICES['graph_red']}" in output
