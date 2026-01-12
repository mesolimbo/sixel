"""
System metrics collection module.

Collects CPU, memory, disk I/O, network, and battery metrics.
Uses psutil for cross-platform compatibility, with Windows-specific
enhancements where available.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from collections import deque

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# Maximum number of historical data points for graphs
MAX_HISTORY = 120  # About 2 minutes at 1 sample/sec


@dataclass
class CPUMetrics:
    """CPU usage metrics."""
    system_percent: float = 0.0
    user_percent: float = 0.0
    idle_percent: float = 0.0
    thread_count: int = 0
    process_count: int = 0
    # Historical data for graphs
    system_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))
    user_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))


@dataclass
class MemoryMetrics:
    """Memory usage metrics."""
    physical_total_gb: float = 0.0
    physical_used_gb: float = 0.0
    cached_gb: float = 0.0
    swap_used_gb: float = 0.0
    app_memory_gb: float = 0.0
    wired_memory_gb: float = 0.0
    compressed_gb: float = 0.0
    pressure_percent: float = 0.0
    # Historical data for graphs
    pressure_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))


@dataclass
class DiskIOMetrics:
    """Disk I/O metrics."""
    reads_total: int = 0
    writes_total: int = 0
    reads_per_sec: float = 0.0
    writes_per_sec: float = 0.0
    data_read_gb: float = 0.0
    data_written_gb: float = 0.0
    data_read_per_sec_mb: float = 0.0
    data_written_per_sec_mb: float = 0.0
    # Historical data for graphs
    read_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))
    write_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))


@dataclass
class NetworkMetrics:
    """Network I/O metrics."""
    packets_in_total: int = 0
    packets_out_total: int = 0
    packets_in_per_sec: float = 0.0
    packets_out_per_sec: float = 0.0
    data_received_gb: float = 0.0
    data_sent_gb: float = 0.0
    data_received_per_sec_kb: float = 0.0
    data_sent_per_sec_kb: float = 0.0
    # Historical data for graphs
    received_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))
    sent_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))


@dataclass
class BatteryMetrics:
    """Battery and energy metrics."""
    has_battery: bool = False
    charge_percent: float = 0.0
    is_charging: bool = False
    time_remaining_minutes: Optional[int] = None
    time_on_battery_minutes: int = 0
    power_plugged: bool = False
    # Historical data for energy impact graph
    energy_history: deque = field(default_factory=lambda: deque(maxlen=MAX_HISTORY))


class MetricsCollector:
    """
    Collects system metrics with historical data for graphs.

    Updates should be called periodically (e.g., once per second) to
    build up historical data for real-time graphs.
    """

    def __init__(self):
        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil is required for metrics collection. "
                             "Install with: pip install psutil")

        self.cpu = CPUMetrics()
        self.memory = MemoryMetrics()
        self.disk = DiskIOMetrics()
        self.network = NetworkMetrics()
        self.battery = BatteryMetrics()

        # For calculating per-second rates
        self._last_update: float = 0.0
        self._last_disk_read: int = 0
        self._last_disk_write: int = 0
        self._last_disk_read_bytes: int = 0
        self._last_disk_write_bytes: int = 0
        self._last_net_recv: int = 0
        self._last_net_sent: int = 0
        self._last_net_recv_bytes: int = 0
        self._last_net_sent_bytes: int = 0
        self._battery_start_time: float = time.time()
        self._was_on_battery: bool = False

        # Initialize with first sample
        self._init_baseline()

    def _init_baseline(self) -> None:
        """Initialize baseline values for rate calculations."""
        try:
            disk = psutil.disk_io_counters()
            if disk:
                self._last_disk_read = disk.read_count
                self._last_disk_write = disk.write_count
                self._last_disk_read_bytes = disk.read_bytes
                self._last_disk_write_bytes = disk.write_bytes
        except (AttributeError, RuntimeError):
            pass

        try:
            net = psutil.net_io_counters()
            if net:
                self._last_net_recv = net.packets_recv
                self._last_net_sent = net.packets_sent
                self._last_net_recv_bytes = net.bytes_recv
                self._last_net_sent_bytes = net.bytes_sent
        except (AttributeError, RuntimeError):
            pass

        self._last_update = time.time()

        # Prime the CPU percent calculation
        try:
            psutil.cpu_times_percent(interval=None)
        except (AttributeError, RuntimeError):
            pass

    def update(self) -> None:
        """Update all metrics. Call this periodically (e.g., once per second)."""
        current_time = time.time()
        elapsed = current_time - self._last_update
        if elapsed < 0.1:  # Minimum interval
            elapsed = 0.1

        self._update_cpu()
        self._update_memory()
        self._update_disk(elapsed)
        self._update_network(elapsed)
        self._update_battery()

        self._last_update = current_time

    def _update_cpu(self) -> None:
        """Update CPU metrics."""
        try:
            # Get CPU times breakdown
            cpu_times = psutil.cpu_times_percent(interval=None)
            self.cpu.system_percent = cpu_times.system
            self.cpu.user_percent = cpu_times.user
            self.cpu.idle_percent = cpu_times.idle

            # Add to history for graphs
            self.cpu.system_history.append(self.cpu.system_percent)
            self.cpu.user_history.append(self.cpu.user_percent)

            # Get process and thread counts
            self.cpu.process_count = len(psutil.pids())

            # Count threads (this can be slow, so we estimate)
            # On Windows, we can get thread count more efficiently
            thread_count = 0
            try:
                for proc in psutil.process_iter(['num_threads']):
                    try:
                        threads = proc.info.get('num_threads', 0)
                        if threads:
                            thread_count += threads
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception:
                thread_count = self.cpu.process_count * 4  # Rough estimate

            self.cpu.thread_count = thread_count

        except (AttributeError, RuntimeError) as e:
            pass

    def _update_memory(self) -> None:
        """Update memory metrics."""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            self.memory.physical_total_gb = mem.total / (1024 ** 3)
            self.memory.physical_used_gb = mem.used / (1024 ** 3)

            # Cached/buffered memory
            cached = getattr(mem, 'cached', 0) + getattr(mem, 'buffers', 0)
            self.memory.cached_gb = cached / (1024 ** 3)

            self.memory.swap_used_gb = swap.used / (1024 ** 3)

            # On Windows, "wired" approximates to non-paged pool
            # "app memory" is the active/used minus cached
            self.memory.app_memory_gb = (mem.used - cached) / (1024 ** 3)
            if self.memory.app_memory_gb < 0:
                self.memory.app_memory_gb = mem.used / (1024 ** 3)

            # Wired memory (kernel/system memory that can't be paged)
            # psutil doesn't directly expose this on Windows
            self.memory.wired_memory_gb = self.memory.physical_used_gb * 0.15  # Rough estimate

            # Compressed memory (Windows 10+ feature)
            self.memory.compressed_gb = 0  # Not easily available via psutil

            # Memory pressure: used percentage
            self.memory.pressure_percent = mem.percent

            # Add to history
            self.memory.pressure_history.append(self.memory.pressure_percent)

        except (AttributeError, RuntimeError):
            pass

    def _update_disk(self, elapsed: float) -> None:
        """Update disk I/O metrics."""
        try:
            disk = psutil.disk_io_counters()
            if not disk:
                return

            # Total counts
            self.disk.reads_total = disk.read_count
            self.disk.writes_total = disk.write_count
            self.disk.data_read_gb = disk.read_bytes / (1024 ** 3)
            self.disk.data_written_gb = disk.write_bytes / (1024 ** 3)

            # Calculate rates
            if elapsed > 0:
                read_diff = disk.read_count - self._last_disk_read
                write_diff = disk.write_count - self._last_disk_write
                read_bytes_diff = disk.read_bytes - self._last_disk_read_bytes
                write_bytes_diff = disk.write_bytes - self._last_disk_write_bytes

                self.disk.reads_per_sec = read_diff / elapsed
                self.disk.writes_per_sec = write_diff / elapsed
                self.disk.data_read_per_sec_mb = (read_bytes_diff / elapsed) / (1024 ** 2)
                self.disk.data_written_per_sec_mb = (write_bytes_diff / elapsed) / (1024 ** 2)

                # Add to history (use bytes/sec for graphs, normalized)
                # Normalize to 0-100 scale assuming 100 MB/s max
                max_mb_sec = 100.0
                self.disk.read_history.append(
                    min(100, (self.disk.data_read_per_sec_mb / max_mb_sec) * 100)
                )
                self.disk.write_history.append(
                    min(100, (self.disk.data_written_per_sec_mb / max_mb_sec) * 100)
                )

            # Save for next calculation
            self._last_disk_read = disk.read_count
            self._last_disk_write = disk.write_count
            self._last_disk_read_bytes = disk.read_bytes
            self._last_disk_write_bytes = disk.write_bytes

        except (AttributeError, RuntimeError):
            pass

    def _update_network(self, elapsed: float) -> None:
        """Update network I/O metrics."""
        try:
            net = psutil.net_io_counters()
            if not net:
                return

            # Total counts
            self.network.packets_in_total = net.packets_recv
            self.network.packets_out_total = net.packets_sent
            self.network.data_received_gb = net.bytes_recv / (1024 ** 3)
            self.network.data_sent_gb = net.bytes_sent / (1024 ** 3)

            # Calculate rates
            if elapsed > 0:
                recv_diff = net.packets_recv - self._last_net_recv
                sent_diff = net.packets_sent - self._last_net_sent
                recv_bytes_diff = net.bytes_recv - self._last_net_recv_bytes
                sent_bytes_diff = net.bytes_sent - self._last_net_sent_bytes

                self.network.packets_in_per_sec = recv_diff / elapsed
                self.network.packets_out_per_sec = sent_diff / elapsed
                self.network.data_received_per_sec_kb = (recv_bytes_diff / elapsed) / 1024
                self.network.data_sent_per_sec_kb = (sent_bytes_diff / elapsed) / 1024

                # Add to history (normalize to 0-100 scale)
                # Assuming 10 MB/s max for visualization
                max_kb_sec = 10000.0
                self.network.received_history.append(
                    min(100, (self.network.data_received_per_sec_kb / max_kb_sec) * 100)
                )
                self.network.sent_history.append(
                    min(100, (self.network.data_sent_per_sec_kb / max_kb_sec) * 100)
                )

            # Save for next calculation
            self._last_net_recv = net.packets_recv
            self._last_net_sent = net.packets_sent
            self._last_net_recv_bytes = net.bytes_recv
            self._last_net_sent_bytes = net.bytes_sent

        except (AttributeError, RuntimeError):
            pass

    def _update_battery(self) -> None:
        """Update battery/energy metrics."""
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                self.battery.has_battery = False
                # Simulate energy history with CPU usage
                total_cpu = self.cpu.system_percent + self.cpu.user_percent
                self.battery.energy_history.append(total_cpu)
                return

            self.battery.has_battery = True
            self.battery.charge_percent = battery.percent
            self.battery.power_plugged = battery.power_plugged
            self.battery.is_charging = battery.power_plugged

            # Time remaining (if available and on battery)
            if battery.secsleft > 0:
                self.battery.time_remaining_minutes = battery.secsleft // 60
            else:
                self.battery.time_remaining_minutes = None

            # Track time on battery
            on_battery = not battery.power_plugged
            if on_battery and not self._was_on_battery:
                # Just unplugged
                self._battery_start_time = time.time()
            elif on_battery:
                # Continue on battery
                elapsed = time.time() - self._battery_start_time
                self.battery.time_on_battery_minutes = int(elapsed / 60)
            else:
                # Plugged in
                self.battery.time_on_battery_minutes = 0

            self._was_on_battery = on_battery

            # Energy history (use CPU as proxy for energy impact)
            total_cpu = self.cpu.system_percent + self.cpu.user_percent
            self.battery.energy_history.append(total_cpu)

        except (AttributeError, RuntimeError):
            self.battery.has_battery = False

    def get_cpu_graph_data(self) -> Tuple[List[float], List[float]]:
        """Get CPU history data for graphing (user, system)."""
        return list(self.cpu.user_history), list(self.cpu.system_history)

    def get_memory_graph_data(self) -> List[float]:
        """Get memory pressure history for graphing."""
        return list(self.memory.pressure_history)

    def get_disk_graph_data(self) -> Tuple[List[float], List[float]]:
        """Get disk I/O history for graphing (read, write)."""
        return list(self.disk.read_history), list(self.disk.write_history)

    def get_network_graph_data(self) -> Tuple[List[float], List[float]]:
        """Get network history for graphing (received, sent)."""
        return list(self.network.received_history), list(self.network.sent_history)

    def get_energy_graph_data(self) -> List[float]:
        """Get energy impact history for graphing."""
        return list(self.battery.energy_history)
