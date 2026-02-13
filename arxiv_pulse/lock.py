#!/usr/bin/env python3
"""
Lock file management for preventing multiple service instances
"""

import json
import os
import socket
from datetime import UTC, datetime
from pathlib import Path


class ServiceLock:
    """Manages service lock file to prevent multiple instances"""

    def __init__(self, lock_dir: Path | None = None):
        if lock_dir is None:
            lock_dir = Path.cwd() / "data"
        self.lock_dir = Path(lock_dir)
        self.lock_file = self.lock_dir / ".pulse.lock"

    def _get_lock_info(self) -> dict | None:
        """Read lock file if exists and valid"""
        if not self.lock_file.exists():
            return None

        try:
            with open(self.lock_file) as f:
                data = json.load(f)

            # Check if process is still running
            pid = data.get("pid")
            if pid:
                try:
                    os.kill(pid, 0)  # Check if process exists
                    return data
                except OSError:
                    # Process not running, stale lock file
                    self._remove_lock()
                    return None
            return None
        except (json.JSONDecodeError, KeyError):
            self._remove_lock()
            return None

    def _remove_lock(self):
        """Remove lock file"""
        try:
            self.lock_file.unlink()
        except FileNotFoundError:
            pass

    def is_locked(self) -> tuple[bool, dict | None]:
        """Check if another instance is running

        Returns:
            Tuple of (is_locked, lock_info)
        """
        info = self._get_lock_info()
        return (info is not None, info)

    def acquire(self, host: str, port: int, pid: int | None = None) -> bool:
        """Acquire lock for this instance

        Args:
            host: Server host address
            port: Server port
            pid: Process ID (defaults to current process)

        Returns:
            True if lock acquired, False if already locked
        """
        is_locked, info = self.is_locked()
        if is_locked:
            return False

        self.lock_dir.mkdir(parents=True, exist_ok=True)

        lock_data = {
            "pid": pid or os.getpid(),
            "host": host,
            "port": port,
            "started_at": datetime.now(UTC).isoformat(),
            "hostname": socket.gethostname(),
        }

        with open(self.lock_file, "w") as f:
            json.dump(lock_data, f, indent=2)

        return True

    def release(self):
        """Release lock file"""
        self._remove_lock()

    def get_status_message(self, info: dict | None = None) -> str:
        """Get human-readable status message

        Args:
            info: Lock info dict (if None, reads from file)

        Returns:
            Formatted status message
        """
        if info is None:
            _, info = self.is_locked()

        if info is None:
            return "没有运行中的服务"

        started = info.get("started_at", "未知时间")
        if isinstance(started, str) and "T" in started:
            try:
                dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                started = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        return (
            f"服务已在运行中\n"
            f"  PID: {info.get('pid', '未知')}\n"
            f"  地址: http://{info.get('host', '127.0.0.1')}:{info.get('port', 8000)}\n"
            f"  主机: {info.get('hostname', '未知')}\n"
            f"  启动: {started}"
        )


def check_and_acquire_lock(directory: Path, host: str, port: int) -> tuple[bool, ServiceLock]:
    """Check for existing lock and acquire if possible

    Args:
        directory: Data directory path
        host: Server host
        port: Server port

    Returns:
        Tuple of (success, lock_instance)
    """
    lock = ServiceLock(directory / "data")
    is_locked, info = lock.is_locked()

    if is_locked:
        return False, lock

    acquired = lock.acquire(host, port)
    return acquired, lock
