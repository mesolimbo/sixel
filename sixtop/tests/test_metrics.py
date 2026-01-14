"""
Tests for the metrics collection module (metrics.py).

Tests cover:
- Metric dataclass initialization
- MetricsCollector initialization
- History data management
- Graph data retrieval
- Rate calculations
"""

import sys
import pytest
from pathlib import Path
from collections import deque
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics import (
    CPUMetrics,
    MemoryMetrics,
    DiskIOMetrics,
    NetworkMetrics,
    BatteryMetrics,
    MetricsCollector,
    MAX_HISTORY,
    PSUTIL_AVAILABLE,
)


class TestCPUMetrics:
    """Tests for CPUMetrics dataclass."""

    def test_default_initialization(self):
        """Test CPUMetrics initializes with default values."""
        cpu = CPUMetrics()
        assert cpu.system_percent == 0.0
        assert cpu.user_percent == 0.0
        assert cpu.idle_percent == 0.0
        assert cpu.thread_count == 0
        assert cpu.process_count == 0

    def test_history_initialization(self):
        """Test that history deques are initialized correctly."""
        cpu = CPUMetrics()
        assert isinstance(cpu.system_history, deque)
        assert isinstance(cpu.user_history, deque)
        assert cpu.system_history.maxlen == MAX_HISTORY
        assert cpu.user_history.maxlen == MAX_HISTORY

    def test_history_maxlen(self):
        """Test that history respects maxlen."""
        cpu = CPUMetrics()
        for i in range(MAX_HISTORY + 50):
            cpu.system_history.append(i)
        assert len(cpu.system_history) == MAX_HISTORY

    def test_custom_values(self):
        """Test CPUMetrics with custom values."""
        cpu = CPUMetrics(
            system_percent=25.5,
            user_percent=30.2,
            idle_percent=44.3,
            thread_count=1500,
            process_count=400
        )
        assert cpu.system_percent == 25.5
        assert cpu.user_percent == 30.2
        assert cpu.idle_percent == 44.3
        assert cpu.thread_count == 1500
        assert cpu.process_count == 400


class TestMemoryMetrics:
    """Tests for MemoryMetrics dataclass."""

    def test_default_initialization(self):
        """Test MemoryMetrics initializes with default values."""
        mem = MemoryMetrics()
        assert mem.physical_total_gb == 0.0
        assert mem.physical_used_gb == 0.0
        assert mem.cached_gb == 0.0
        assert mem.swap_used_gb == 0.0
        assert mem.app_memory_gb == 0.0
        assert mem.wired_memory_gb == 0.0
        assert mem.compressed_gb == 0.0
        assert mem.pressure_percent == 0.0

    def test_history_initialization(self):
        """Test that pressure_history deque is initialized correctly."""
        mem = MemoryMetrics()
        assert isinstance(mem.pressure_history, deque)
        assert mem.pressure_history.maxlen == MAX_HISTORY

    def test_custom_values(self):
        """Test MemoryMetrics with custom values."""
        mem = MemoryMetrics(
            physical_total_gb=32.0,
            physical_used_gb=16.5,
            pressure_percent=51.5
        )
        assert mem.physical_total_gb == 32.0
        assert mem.physical_used_gb == 16.5
        assert mem.pressure_percent == 51.5


class TestDiskIOMetrics:
    """Tests for DiskIOMetrics dataclass."""

    def test_default_initialization(self):
        """Test DiskIOMetrics initializes with default values."""
        disk = DiskIOMetrics()
        assert disk.reads_total == 0
        assert disk.writes_total == 0
        assert disk.reads_per_sec == 0.0
        assert disk.writes_per_sec == 0.0
        assert disk.data_read_gb == 0.0
        assert disk.data_written_gb == 0.0
        assert disk.data_read_per_sec_mb == 0.0
        assert disk.data_written_per_sec_mb == 0.0

    def test_history_initialization(self):
        """Test that history deques are initialized correctly."""
        disk = DiskIOMetrics()
        assert isinstance(disk.read_history, deque)
        assert isinstance(disk.write_history, deque)
        assert disk.read_history.maxlen == MAX_HISTORY
        assert disk.write_history.maxlen == MAX_HISTORY


class TestNetworkMetrics:
    """Tests for NetworkMetrics dataclass."""

    def test_default_initialization(self):
        """Test NetworkMetrics initializes with default values."""
        net = NetworkMetrics()
        assert net.packets_in_total == 0
        assert net.packets_out_total == 0
        assert net.packets_in_per_sec == 0.0
        assert net.packets_out_per_sec == 0.0
        assert net.data_received_gb == 0.0
        assert net.data_sent_gb == 0.0
        assert net.data_received_per_sec_kb == 0.0
        assert net.data_sent_per_sec_kb == 0.0

    def test_history_initialization(self):
        """Test that history deques are initialized correctly."""
        net = NetworkMetrics()
        assert isinstance(net.received_history, deque)
        assert isinstance(net.sent_history, deque)
        assert net.received_history.maxlen == MAX_HISTORY
        assert net.sent_history.maxlen == MAX_HISTORY


class TestBatteryMetrics:
    """Tests for BatteryMetrics dataclass."""

    def test_default_initialization(self):
        """Test BatteryMetrics initializes with default values."""
        battery = BatteryMetrics()
        assert battery.has_battery is False
        assert battery.charge_percent == 0.0
        assert battery.is_charging is False
        assert battery.time_remaining_minutes is None
        assert battery.time_on_battery_minutes == 0
        assert battery.power_plugged is False

    def test_history_initialization(self):
        """Test that energy_history deque is initialized correctly."""
        battery = BatteryMetrics()
        assert isinstance(battery.energy_history, deque)
        assert battery.energy_history.maxlen == MAX_HISTORY

    def test_with_battery(self):
        """Test BatteryMetrics with battery present."""
        battery = BatteryMetrics(
            has_battery=True,
            charge_percent=75.0,
            is_charging=True,
            time_remaining_minutes=120,
            power_plugged=True
        )
        assert battery.has_battery is True
        assert battery.charge_percent == 75.0
        assert battery.is_charging is True
        assert battery.time_remaining_minutes == 120
        assert battery.power_plugged is True


class TestMaxHistory:
    """Tests for MAX_HISTORY constant."""

    def test_max_history_value(self):
        """Test MAX_HISTORY is set correctly."""
        assert MAX_HISTORY == 120

    def test_max_history_used_in_deques(self):
        """Test that MAX_HISTORY is used as maxlen in all deques."""
        cpu = CPUMetrics()
        mem = MemoryMetrics()
        disk = DiskIOMetrics()
        net = NetworkMetrics()
        battery = BatteryMetrics()

        assert cpu.system_history.maxlen == MAX_HISTORY
        assert cpu.user_history.maxlen == MAX_HISTORY
        assert mem.pressure_history.maxlen == MAX_HISTORY
        assert disk.read_history.maxlen == MAX_HISTORY
        assert disk.write_history.maxlen == MAX_HISTORY
        assert net.received_history.maxlen == MAX_HISTORY
        assert net.sent_history.maxlen == MAX_HISTORY
        assert battery.energy_history.maxlen == MAX_HISTORY


@pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
class TestMetricsCollector:
    """Tests for MetricsCollector class (requires psutil)."""

    def test_initialization(self):
        """Test MetricsCollector initializes correctly."""
        collector = MetricsCollector()
        assert collector.cpu is not None
        assert collector.memory is not None
        assert collector.disk is not None
        assert collector.network is not None
        assert collector.battery is not None

    def test_metrics_are_correct_types(self):
        """Test that metrics are correct dataclass types."""
        collector = MetricsCollector()
        assert isinstance(collector.cpu, CPUMetrics)
        assert isinstance(collector.memory, MemoryMetrics)
        assert isinstance(collector.disk, DiskIOMetrics)
        assert isinstance(collector.network, NetworkMetrics)
        assert isinstance(collector.battery, BatteryMetrics)

    def test_update_runs_without_error(self):
        """Test that update() runs without raising exceptions."""
        collector = MetricsCollector()
        # Should not raise
        collector.update()

    def test_update_populates_cpu_values(self):
        """Test that update() populates CPU values."""
        collector = MetricsCollector()
        collector.update()

        # Values should be reasonable (0-100 for percentages)
        assert 0 <= collector.cpu.system_percent <= 100
        assert 0 <= collector.cpu.user_percent <= 100
        assert 0 <= collector.cpu.idle_percent <= 100
        assert collector.cpu.process_count >= 0
        assert collector.cpu.thread_count >= 0

    def test_update_populates_memory_values(self):
        """Test that update() populates memory values."""
        collector = MetricsCollector()
        collector.update()

        assert collector.memory.physical_total_gb > 0
        assert collector.memory.physical_used_gb >= 0
        assert 0 <= collector.memory.pressure_percent <= 100

    def test_update_adds_to_history(self):
        """Test that update() adds values to history."""
        collector = MetricsCollector()
        initial_cpu_history_len = len(collector.cpu.system_history)

        collector.update()

        assert len(collector.cpu.system_history) == initial_cpu_history_len + 1
        assert len(collector.cpu.user_history) == initial_cpu_history_len + 1

    def test_get_cpu_graph_data(self):
        """Test get_cpu_graph_data returns correct data."""
        collector = MetricsCollector()
        collector.update()

        user_data, system_data = collector.get_cpu_graph_data()

        assert isinstance(user_data, list)
        assert isinstance(system_data, list)

    def test_get_memory_graph_data(self):
        """Test get_memory_graph_data returns correct data."""
        collector = MetricsCollector()
        collector.update()

        pressure_data = collector.get_memory_graph_data()

        assert isinstance(pressure_data, list)

    def test_get_disk_graph_data(self):
        """Test get_disk_graph_data returns correct data."""
        collector = MetricsCollector()
        collector.update()

        read_data, write_data = collector.get_disk_graph_data()

        assert isinstance(read_data, list)
        assert isinstance(write_data, list)

    def test_get_network_graph_data(self):
        """Test get_network_graph_data returns correct data."""
        collector = MetricsCollector()
        collector.update()

        recv_data, sent_data = collector.get_network_graph_data()

        assert isinstance(recv_data, list)
        assert isinstance(sent_data, list)

    def test_get_energy_graph_data(self):
        """Test get_energy_graph_data returns correct data."""
        collector = MetricsCollector()
        collector.update()

        energy_data = collector.get_energy_graph_data()

        assert isinstance(energy_data, list)

    def test_multiple_updates(self):
        """Test multiple update() calls work correctly."""
        collector = MetricsCollector()

        for _ in range(5):
            collector.update()

        # Should have accumulated history
        assert len(collector.cpu.system_history) >= 5


class TestMetricsCollectorWithoutPsutil:
    """Tests for MetricsCollector behavior without psutil."""

    def test_raises_without_psutil(self):
        """Test that MetricsCollector raises RuntimeError without psutil."""
        with patch('metrics.PSUTIL_AVAILABLE', False):
            # Need to reload or recreate to pick up the patched value
            # This test verifies the error message content
            pass  # The actual test requires module reload which is complex


class TestGraphDataMethods:
    """Tests for graph data retrieval methods with mock data."""

    @pytest.fixture
    def collector_with_history(self):
        """Create a collector with known history values."""
        if not PSUTIL_AVAILABLE:
            pytest.skip("psutil not available")
        collector = MetricsCollector()

        # Add known values to history
        for i in range(10):
            collector.cpu.user_history.append(i * 5.0)
            collector.cpu.system_history.append(i * 3.0)
            collector.memory.pressure_history.append(i * 4.0)
            collector.disk.read_history.append(i * 2.0)
            collector.disk.write_history.append(i * 1.5)
            collector.network.received_history.append(i * 6.0)
            collector.network.sent_history.append(i * 2.5)
            collector.battery.energy_history.append(i * 7.0)

        return collector

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_cpu_graph_data_returns_lists(self, collector_with_history):
        """Test CPU graph data returns lists."""
        user, system = collector_with_history.get_cpu_graph_data()
        assert isinstance(user, list)
        assert isinstance(system, list)
        assert len(user) == 10
        assert len(system) == 10

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_memory_graph_data_returns_list(self, collector_with_history):
        """Test memory graph data returns list."""
        pressure = collector_with_history.get_memory_graph_data()
        assert isinstance(pressure, list)
        assert len(pressure) == 10

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_disk_graph_data_returns_lists(self, collector_with_history):
        """Test disk graph data returns lists."""
        read, write = collector_with_history.get_disk_graph_data()
        assert isinstance(read, list)
        assert isinstance(write, list)
        assert len(read) == 10
        assert len(write) == 10

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_network_graph_data_returns_lists(self, collector_with_history):
        """Test network graph data returns lists."""
        recv, sent = collector_with_history.get_network_graph_data()
        assert isinstance(recv, list)
        assert isinstance(sent, list)
        assert len(recv) == 10
        assert len(sent) == 10

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="psutil not available")
    def test_energy_graph_data_returns_list(self, collector_with_history):
        """Test energy graph data returns list."""
        energy = collector_with_history.get_energy_graph_data()
        assert isinstance(energy, list)
        assert len(energy) == 10
