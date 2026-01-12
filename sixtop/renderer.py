"""
Renderer module for sixtop system monitor.

Renders system metrics as sixel graphics infographics.
Supports five views: Energy, CPU, I/O, Memory, Network.
"""

from enum import Enum
from typing import List, Optional, Tuple

from sixel import (
    create_pixel_buffer,
    pixels_to_sixel,
    fill_rect,
    draw_text,
    draw_line_graph,
    draw_dual_line_graph,
    draw_bar_graph,
    draw_horizontal_line,
    draw_vertical_line,
    get_text_width,
    COLOR_INDICES,
    FONT_HEIGHT,
)
from metrics import MetricsCollector


class MetricView(Enum):
    """Available metric views."""
    ENERGY = 0
    CPU = 1
    IO = 2
    MEMORY = 3
    NETWORK = 4


VIEW_TITLES = {
    MetricView.ENERGY: "ENERGY IMPACT",
    MetricView.CPU: "CPU LOAD",
    MetricView.IO: "IO",
    MetricView.MEMORY: "MEMORY PRESSURE",
    MetricView.NETWORK: "PACKETS",
}


class MetricsRenderer:
    """
    Renders system metrics as sixel graphics.

    Provides Activity Monitor-style infographic panels with
    real-time updating graphs.
    """

    def __init__(self, width: int = 580, height: int = 108, scale: int = 1):
        """
        Initialize the renderer.

        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            scale: Text scale factor
        """
        self.width = width
        self.height = height
        self.scale = scale

        # Layout constants - compact spacing
        self.padding = 5
        self.border_width = 1
        self.panel_padding = 4
        self.row_height = 11  # Compact row spacing

        # Three-column layout
        self.left_panel_width = (width - 4 * self.padding) // 3
        self.center_panel_width = self.left_panel_width
        self.right_panel_width = self.left_panel_width

        # Panel positions
        self.left_x = self.padding
        self.center_x = self.left_x + self.left_panel_width + self.padding
        self.right_x = self.center_x + self.center_panel_width + self.padding

        # Graph area - adjusted for compact height
        self.graph_y = 22
        self.graph_height = height - 32

        # Current view
        self.current_view = MetricView.CPU

    def next_view(self) -> MetricView:
        """Switch to the next view."""
        views = list(MetricView)
        current_idx = views.index(self.current_view)
        self.current_view = views[(current_idx + 1) % len(views)]
        return self.current_view

    def render_frame(self, metrics: MetricsCollector) -> str:
        """
        Render the current view as a sixel string.

        Args:
            metrics: MetricsCollector with current system metrics

        Returns:
            Sixel escape sequence string
        """
        # Create pixel buffer with background
        pixels = create_pixel_buffer(
            self.width,
            self.height,
            COLOR_INDICES["background"]
        )

        # Draw frame border
        self._draw_frame_border(pixels)

        # Render the appropriate view
        if self.current_view == MetricView.ENERGY:
            self._render_energy_view(pixels, metrics)
        elif self.current_view == MetricView.CPU:
            self._render_cpu_view(pixels, metrics)
        elif self.current_view == MetricView.IO:
            self._render_io_view(pixels, metrics)
        elif self.current_view == MetricView.MEMORY:
            self._render_memory_view(pixels, metrics)
        elif self.current_view == MetricView.NETWORK:
            self._render_network_view(pixels, metrics)

        return pixels_to_sixel(pixels, self.width, self.height)

    def _draw_frame_border(self, pixels: List[List[int]]) -> None:
        """Draw the outer frame border."""
        color = COLOR_INDICES["border"]

        # Top and bottom
        fill_rect(pixels, 0, 0, self.width, self.border_width, color)
        fill_rect(pixels, 0, self.height - self.border_width,
                 self.width, self.border_width, color)
        # Left and right
        fill_rect(pixels, 0, 0, self.border_width, self.height, color)
        fill_rect(pixels, self.width - self.border_width, 0,
                 self.border_width, self.height, color)

    def _draw_panel_border(
        self,
        pixels: List[List[int]],
        x: int, y: int,
        w: int, h: int,
        highlight: bool = False
    ) -> None:
        """Draw a panel border."""
        color = COLOR_INDICES["border_highlight"] if highlight else COLOR_INDICES["border"]

        # Top and bottom
        draw_horizontal_line(pixels, x, y, w, color)
        draw_horizontal_line(pixels, x, y + h - 1, w, color)
        # Left and right
        draw_vertical_line(pixels, x, y, h, color)
        draw_vertical_line(pixels, x + w - 1, y, h, color)

    def _draw_title(
        self,
        pixels: List[List[int]],
        x: int, y: int,
        width: int,
        title: str
    ) -> None:
        """Draw a section title with underline."""
        # Draw title line
        line_y = y + FONT_HEIGHT * self.scale + 2
        draw_horizontal_line(pixels, x, line_y, width, COLOR_INDICES["title_line"])

        # Draw title text centered
        title_width = get_text_width(title, self.scale)
        title_x = x + (width - title_width) // 2
        draw_text(pixels, title_x, y, title, COLOR_INDICES["text_dim"], self.scale)

    def _render_energy_view(
        self,
        pixels: List[List[int]],
        metrics: MetricsCollector
    ) -> None:
        """Render the Energy Impact view."""
        row = self.row_height

        # Left panel: Energy Impact graph
        self._draw_panel_border(pixels, self.left_x, self.padding,
                               self.left_panel_width, self.height - 2 * self.padding)
        self._draw_title(pixels, self.left_x + self.panel_padding,
                        self.padding + self.panel_padding,
                        self.left_panel_width - 2 * self.panel_padding,
                        "ENERGY IMPACT")

        # Draw energy graph
        graph_x = self.left_x + self.panel_padding
        graph_width = self.left_panel_width - 2 * self.panel_padding
        energy_data = metrics.get_energy_graph_data()
        draw_line_graph(
            pixels, graph_x, self.graph_y, graph_width, self.graph_height,
            energy_data, COLOR_INDICES["graph_blue"],
            fill_color=None, max_value=100.0
        )

        # Center panel: Battery stats
        stat_y = self.padding + self.panel_padding
        stat_x = self.center_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "CHARGE:",
                 COLOR_INDICES["text"], self.scale)
        charge_str = f"{metrics.battery.charge_percent:.0f}%" if metrics.battery.has_battery else "N/A"
        draw_text(pixels, stat_x + 60, stat_y, charge_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "REMAINING:",
                 COLOR_INDICES["text"], self.scale)
        if metrics.battery.time_remaining_minutes is not None:
            time_str = f"{metrics.battery.time_remaining_minutes // 60}:{metrics.battery.time_remaining_minutes % 60:02d}"
        else:
            time_str = "..."
        draw_text(pixels, stat_x + 80, stat_y, time_str,
                 COLOR_INDICES["text"], self.scale)

        stat_y += row
        battery_mins = metrics.battery.time_on_battery_minutes
        time_on_str = f"{battery_mins // 60}:{battery_mins % 60:02d}"
        draw_text(pixels, stat_x, stat_y, "ON BATTERY:",
                 COLOR_INDICES["text"], self.scale)
        draw_text(pixels, stat_x + 90, stat_y, time_on_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        # Right panel: Battery level visualization
        self._draw_panel_border(pixels, self.right_x, self.padding,
                               self.right_panel_width, self.height - 2 * self.padding,
                               highlight=True)
        self._draw_title(pixels, self.right_x + self.panel_padding,
                        self.padding + self.panel_padding,
                        self.right_panel_width - 2 * self.panel_padding,
                        "BATTERY")

    def _render_cpu_view(
        self,
        pixels: List[List[int]],
        metrics: MetricsCollector
    ) -> None:
        """Render the CPU Load view."""
        row = self.row_height

        # Left panel: CPU stats
        self._draw_panel_border(pixels, self.left_x, self.padding,
                               self.left_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.left_x + self.panel_padding

        # System CPU
        draw_text(pixels, stat_x, stat_y, "SYSTEM:",
                 COLOR_INDICES["text"], self.scale)
        sys_str = f"{metrics.cpu.system_percent:.2f}%"
        draw_text(pixels, stat_x + 65, stat_y, sys_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        # User CPU
        stat_y += row
        draw_text(pixels, stat_x, stat_y, "USER:",
                 COLOR_INDICES["text"], self.scale)
        user_str = f"{metrics.cpu.user_percent:.2f}%"
        draw_text(pixels, stat_x + 65, stat_y, user_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        # Idle CPU
        stat_y += row
        draw_text(pixels, stat_x, stat_y, "IDLE:",
                 COLOR_INDICES["text"], self.scale)
        idle_str = f"{metrics.cpu.idle_percent:.2f}%"
        draw_text(pixels, stat_x + 65, stat_y, idle_str,
                 COLOR_INDICES["text"], self.scale)

        # Center panel: CPU Load graph
        self._draw_panel_border(pixels, self.center_x, self.padding,
                               self.center_panel_width, self.height - 2 * self.padding)
        self._draw_title(pixels, self.center_x + self.panel_padding,
                        self.padding + self.panel_padding,
                        self.center_panel_width - 2 * self.panel_padding,
                        "CPU LOAD")

        # Draw CPU graph with user (cyan) and system (red)
        graph_x = self.center_x + self.panel_padding
        graph_width = self.center_panel_width - 2 * self.panel_padding
        user_data, system_data = metrics.get_cpu_graph_data()

        # Combine for total visualization
        draw_dual_line_graph(
            pixels, graph_x, self.graph_y, graph_width, self.graph_height,
            user_data, system_data,
            COLOR_INDICES["graph_cyan"], COLOR_INDICES["graph_red"],
            COLOR_INDICES["graph_fill_cyan"], COLOR_INDICES["graph_fill_red"],
            max_value=100.0
        )

        # Right panel: Thread/Process counts
        self._draw_panel_border(pixels, self.right_x, self.padding,
                               self.right_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.right_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "THREADS:",
                 COLOR_INDICES["text"], self.scale)
        thread_str = f"{metrics.cpu.thread_count:,}"
        draw_text(pixels, stat_x + 70, stat_y, thread_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "PROCS:",
                 COLOR_INDICES["text"], self.scale)
        proc_str = f"{metrics.cpu.process_count:,}"
        draw_text(pixels, stat_x + 70, stat_y, proc_str,
                 COLOR_INDICES["text_cyan"], self.scale)

    def _render_io_view(
        self,
        pixels: List[List[int]],
        metrics: MetricsCollector
    ) -> None:
        """Render the I/O (Disk) view."""
        row = self.row_height

        # Left panel: Read stats
        self._draw_panel_border(pixels, self.left_x, self.padding,
                               self.left_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.left_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "READS:",
                 COLOR_INDICES["text"], self.scale)
        reads_str = f"{metrics.disk.reads_total:,}"
        draw_text(pixels, stat_x + 55, stat_y, reads_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "WRITES:",
                 COLOR_INDICES["text"], self.scale)
        writes_str = f"{metrics.disk.writes_total:,}"
        draw_text(pixels, stat_x + 60, stat_y, writes_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "R/SEC:",
                 COLOR_INDICES["text"], self.scale)
        rps_str = f"{metrics.disk.reads_per_sec:.0f}"
        draw_text(pixels, stat_x + 55, stat_y, rps_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "W/SEC:",
                 COLOR_INDICES["text"], self.scale)
        wps_str = f"{metrics.disk.writes_per_sec:.0f}"
        draw_text(pixels, stat_x + 55, stat_y, wps_str,
                 COLOR_INDICES["text_red"], self.scale)

        # Center panel: I/O graph
        self._draw_panel_border(pixels, self.center_x, self.padding,
                               self.center_panel_width, self.height - 2 * self.padding)
        self._draw_title(pixels, self.center_x + self.panel_padding,
                        self.padding + self.panel_padding,
                        self.center_panel_width - 2 * self.panel_padding,
                        "IO")

        # Draw I/O graph
        graph_x = self.center_x + self.panel_padding
        graph_width = self.center_panel_width - 2 * self.panel_padding
        read_data, write_data = metrics.get_disk_graph_data()

        draw_dual_line_graph(
            pixels, graph_x, self.graph_y, graph_width, self.graph_height,
            read_data, write_data,
            COLOR_INDICES["graph_cyan"], COLOR_INDICES["graph_red"],
            None, None,
            max_value=100.0
        )

        # Right panel: Data read/written
        self._draw_panel_border(pixels, self.right_x, self.padding,
                               self.right_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.right_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "READ:",
                 COLOR_INDICES["text"], self.scale)
        dr_str = f"{metrics.disk.data_read_gb:.1f} GB"
        draw_text(pixels, stat_x + 50, stat_y, dr_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "WRITE:",
                 COLOR_INDICES["text"], self.scale)
        dw_str = f"{metrics.disk.data_written_gb:.1f} GB"
        draw_text(pixels, stat_x + 55, stat_y, dw_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "R/S:",
                 COLOR_INDICES["text"], self.scale)
        drs_str = f"{metrics.disk.data_read_per_sec_mb:.1f} MB"
        draw_text(pixels, stat_x + 35, stat_y, drs_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "W/S:",
                 COLOR_INDICES["text"], self.scale)
        dws_str = f"{metrics.disk.data_written_per_sec_mb:.0f} KB"
        draw_text(pixels, stat_x + 35, stat_y, dws_str,
                 COLOR_INDICES["text_cyan"], self.scale)

    def _render_memory_view(
        self,
        pixels: List[List[int]],
        metrics: MetricsCollector
    ) -> None:
        """Render the Memory Pressure view."""
        row = self.row_height

        # Left panel: Memory pressure bar
        self._draw_panel_border(pixels, self.left_x, self.padding,
                               self.left_panel_width, self.height - 2 * self.padding)
        self._draw_title(pixels, self.left_x + self.panel_padding,
                        self.padding + self.panel_padding,
                        self.left_panel_width - 2 * self.panel_padding,
                        "MEMORY PRESSURE")

        # Draw pressure bar
        bar_x = self.left_x + self.panel_padding
        bar_y = self.height - self.padding - 25
        bar_width = self.left_panel_width - 2 * self.panel_padding
        bar_height = 15

        # Background
        fill_rect(pixels, bar_x, bar_y, bar_width, bar_height, COLOR_INDICES["panel_bg"])

        # Pressure bar
        draw_bar_graph(
            pixels, bar_x, bar_y, bar_width, bar_height,
            metrics.memory.pressure_percent, COLOR_INDICES["graph_green"]
        )

        # Center panel: Memory stats
        stat_y = self.padding + self.panel_padding
        stat_x = self.center_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "PHYSICAL:",
                 COLOR_INDICES["text"], self.scale)
        pm_str = f"{metrics.memory.physical_total_gb:.2f} GB"
        draw_text(pixels, stat_x + 80, stat_y, pm_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "USED:",
                 COLOR_INDICES["text"], self.scale)
        mu_str = f"{metrics.memory.physical_used_gb:.2f} GB"
        draw_text(pixels, stat_x + 80, stat_y, mu_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "CACHED:",
                 COLOR_INDICES["text"], self.scale)
        cf_str = f"{metrics.memory.cached_gb:.2f} GB"
        draw_text(pixels, stat_x + 80, stat_y, cf_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "SWAP:",
                 COLOR_INDICES["text"], self.scale)
        su_str = f"{metrics.memory.swap_used_gb:.2f} GB"
        draw_text(pixels, stat_x + 80, stat_y, su_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        # Right panel: App/System memory breakdown
        self._draw_panel_border(pixels, self.right_x, self.padding,
                               self.right_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.right_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "APP:",
                 COLOR_INDICES["text"], self.scale)
        am_str = f"{metrics.memory.app_memory_gb:.2f} GB"
        draw_text(pixels, stat_x + 40, stat_y, am_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "WIRED:",
                 COLOR_INDICES["text"], self.scale)
        wm_str = f"{metrics.memory.wired_memory_gb:.2f} GB"
        draw_text(pixels, stat_x + 55, stat_y, wm_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "COMP:",
                 COLOR_INDICES["text"], self.scale)
        cm_str = f"{metrics.memory.compressed_gb:.2f} GB"
        draw_text(pixels, stat_x + 50, stat_y, cm_str,
                 COLOR_INDICES["text_cyan"], self.scale)

    def _render_network_view(
        self,
        pixels: List[List[int]],
        metrics: MetricsCollector
    ) -> None:
        """Render the Network (Packets) view."""
        row = self.row_height

        # Left panel: Packet counts
        self._draw_panel_border(pixels, self.left_x, self.padding,
                               self.left_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.left_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "PKT IN:",
                 COLOR_INDICES["text"], self.scale)
        pi_str = f"{metrics.network.packets_in_total:,}"
        draw_text(pixels, stat_x + 60, stat_y, pi_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "PKT OUT:",
                 COLOR_INDICES["text"], self.scale)
        po_str = f"{metrics.network.packets_out_total:,}"
        draw_text(pixels, stat_x + 70, stat_y, po_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "IN/SEC:",
                 COLOR_INDICES["text"], self.scale)
        pis_str = f"{metrics.network.packets_in_per_sec:.0f}"
        draw_text(pixels, stat_x + 60, stat_y, pis_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "OUT/SEC:",
                 COLOR_INDICES["text"], self.scale)
        pos_str = f"{metrics.network.packets_out_per_sec:.0f}"
        draw_text(pixels, stat_x + 70, stat_y, pos_str,
                 COLOR_INDICES["text_red"], self.scale)

        # Center panel: Network graph
        self._draw_panel_border(pixels, self.center_x, self.padding,
                               self.center_panel_width, self.height - 2 * self.padding)
        self._draw_title(pixels, self.center_x + self.panel_padding,
                        self.padding + self.panel_padding,
                        self.center_panel_width - 2 * self.panel_padding,
                        "PACKETS")

        # Draw network graph
        graph_x = self.center_x + self.panel_padding
        graph_width = self.center_panel_width - 2 * self.panel_padding
        recv_data, sent_data = metrics.get_network_graph_data()

        draw_dual_line_graph(
            pixels, graph_x, self.graph_y, graph_width, self.graph_height,
            recv_data, sent_data,
            COLOR_INDICES["graph_cyan"], COLOR_INDICES["graph_red"],
            None, None,
            max_value=100.0
        )

        # Right panel: Data sent/received
        self._draw_panel_border(pixels, self.right_x, self.padding,
                               self.right_panel_width, self.height - 2 * self.padding)

        stat_y = self.padding + self.panel_padding
        stat_x = self.right_x + self.panel_padding

        draw_text(pixels, stat_x, stat_y, "RECV:",
                 COLOR_INDICES["text"], self.scale)
        dr_str = f"{metrics.network.data_received_gb:.2f} GB"
        draw_text(pixels, stat_x + 50, stat_y, dr_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "SENT:",
                 COLOR_INDICES["text"], self.scale)
        ds_str = f"{metrics.network.data_sent_gb:.2f} GB"
        draw_text(pixels, stat_x + 50, stat_y, ds_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "R/SEC:",
                 COLOR_INDICES["text"], self.scale)
        drs_str = f"{metrics.network.data_received_per_sec_kb:.0f} KB"
        draw_text(pixels, stat_x + 55, stat_y, drs_str,
                 COLOR_INDICES["text_cyan"], self.scale)

        stat_y += row
        draw_text(pixels, stat_x, stat_y, "S/SEC:",
                 COLOR_INDICES["text"], self.scale)
        dss_str = f"{metrics.network.data_sent_per_sec_kb:.0f} KB"
        draw_text(pixels, stat_x + 55, stat_y, dss_str,
                 COLOR_INDICES["text_cyan"], self.scale)
