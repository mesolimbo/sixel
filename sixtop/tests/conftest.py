"""
Pytest fixtures for sixtop system monitor tests.
"""

import sys
import pytest
from pathlib import Path
from typing import Optional, Tuple
from unittest.mock import MagicMock, patch
from collections import deque

# Add the sixtop package to the path
sixtop_dir = Path(__file__).parent.parent
sys.path.insert(0, str(sixtop_dir))

from terminals.base import Terminal, KeyEvent, KeyType
from renderer import MetricsRenderer, MetricView
from metrics import (
    MetricsCollector,
    CPUMetrics,
    MemoryMetrics,
    DiskIOMetrics,
    NetworkMetrics,
    BatteryMetrics,
    MAX_HISTORY,
)


class MockTerminal(Terminal):
    """Mock terminal for testing app loop and input processing."""

    def __init__(self):
        self.written_data = []
        self.key_queue = []
        self.cursor_pos = (1, 1)
        self.cursor_hidden = False
        self.in_alternate_screen = False
        self._is_raw = False
        self._size = (80, 24)

    def read_key(self, timeout: float = 0.0) -> Optional[KeyEvent]:
        if self.key_queue:
            return self.key_queue.pop(0)
        return None

    def add_key(self, key: KeyEvent) -> None:
        """Add a key to the input queue for testing."""
        self.key_queue.append(key)

    def write(self, data: str) -> None:
        self.written_data.append(data)

    def flush(self) -> None:
        pass

    def get_size(self) -> Tuple[int, int]:
        return self._size

    def set_size(self, cols: int, rows: int) -> None:
        """Set terminal size for testing."""
        self._size = (cols, rows)

    def hide_cursor(self) -> None:
        self.cursor_hidden = True

    def show_cursor(self) -> None:
        self.cursor_hidden = False

    def move_cursor(self, row: int, col: int) -> None:
        self.cursor_pos = (row, col)

    def move_cursor_home(self) -> None:
        self.cursor_pos = (1, 1)

    def clear_screen(self) -> None:
        self.written_data.append("<CLEAR>")

    def enter_alternate_screen(self) -> None:
        self.in_alternate_screen = True

    def exit_alternate_screen(self) -> None:
        self.in_alternate_screen = False

    def enter_raw_mode(self) -> None:
        self._is_raw = True

    def exit_raw_mode(self) -> None:
        self._is_raw = False

    @property
    def is_raw(self) -> bool:
        return self._is_raw


class MockMetricsCollector:
    """Mock metrics collector for testing renderer without psutil dependency."""

    def __init__(self):
        self.cpu = CPUMetrics()
        self.memory = MemoryMetrics()
        self.disk = DiskIOMetrics()
        self.network = NetworkMetrics()
        self.battery = BatteryMetrics()

        # Initialize with sample data
        self._populate_sample_data()

    def _populate_sample_data(self):
        """Populate with sample metrics data for testing."""
        # CPU metrics
        self.cpu.system_percent = 15.5
        self.cpu.user_percent = 25.3
        self.cpu.idle_percent = 59.2
        self.cpu.thread_count = 1234
        self.cpu.process_count = 345

        # Add history data
        for i in range(10):
            self.cpu.system_history.append(10 + i)
            self.cpu.user_history.append(20 + i)

        # Memory metrics
        self.memory.physical_total_gb = 16.0
        self.memory.physical_used_gb = 8.5
        self.memory.cached_gb = 2.1
        self.memory.swap_used_gb = 0.5
        self.memory.app_memory_gb = 6.4
        self.memory.wired_memory_gb = 2.4
        self.memory.compressed_gb = 0.8
        self.memory.pressure_percent = 53.1

        for i in range(10):
            self.memory.pressure_history.append(50 + i)

        # Disk I/O metrics
        self.disk.reads_total = 1234567
        self.disk.writes_total = 987654
        self.disk.reads_per_sec = 150.5
        self.disk.writes_per_sec = 75.3
        self.disk.data_read_gb = 123.4
        self.disk.data_written_gb = 56.7
        self.disk.data_read_per_sec_mb = 25.5
        self.disk.data_written_per_sec_mb = 12.3

        for i in range(10):
            self.disk.read_history.append(20 + i)
            self.disk.write_history.append(10 + i)

        # Network metrics
        self.network.packets_in_total = 9876543
        self.network.packets_out_total = 5432109
        self.network.packets_in_per_sec = 500.0
        self.network.packets_out_per_sec = 250.0
        self.network.data_received_gb = 45.6
        self.network.data_sent_gb = 12.3
        self.network.data_received_per_sec_kb = 1024.5
        self.network.data_sent_per_sec_kb = 512.3

        for i in range(10):
            self.network.received_history.append(30 + i)
            self.network.sent_history.append(15 + i)

        # Battery metrics
        self.battery.has_battery = True
        self.battery.charge_percent = 85.0
        self.battery.is_charging = False
        self.battery.time_remaining_minutes = 180
        self.battery.time_on_battery_minutes = 30
        self.battery.power_plugged = False

        for i in range(10):
            self.battery.energy_history.append(40 + i)

    def update(self):
        """Mock update method."""
        pass

    def get_cpu_graph_data(self):
        """Get CPU history data for graphing."""
        return list(self.cpu.user_history), list(self.cpu.system_history)

    def get_memory_graph_data(self):
        """Get memory pressure history for graphing."""
        return list(self.memory.pressure_history)

    def get_disk_graph_data(self):
        """Get disk I/O history for graphing."""
        return list(self.disk.read_history), list(self.disk.write_history)

    def get_network_graph_data(self):
        """Get network history for graphing."""
        return list(self.network.received_history), list(self.network.sent_history)

    def get_energy_graph_data(self):
        """Get energy impact history for graphing."""
        return list(self.battery.energy_history)


@pytest.fixture
def mock_terminal() -> MockTerminal:
    """Create a mock terminal for testing."""
    return MockTerminal()


@pytest.fixture
def mock_metrics() -> MockMetricsCollector:
    """Create a mock metrics collector with sample data."""
    return MockMetricsCollector()


@pytest.fixture
def renderer() -> MetricsRenderer:
    """Create a default metrics renderer."""
    return MetricsRenderer()


@pytest.fixture
def small_renderer() -> MetricsRenderer:
    """Create a smaller renderer for testing."""
    return MetricsRenderer(width=300, height=60)


@pytest.fixture
def custom_renderer():
    """Factory fixture to create renderers with custom parameters."""
    def _create(width=580, height=84, scale=1):
        return MetricsRenderer(width=width, height=height, scale=scale)
    return _create
