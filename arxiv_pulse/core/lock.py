import json
import os
from datetime import datetime
from pathlib import Path


class ServiceLock:
    def __init__(self, data_dir: Path | str):
        self.lock_file = Path(data_dir) / ".pulse.lock"

    def is_locked(self) -> tuple[bool, dict | None]:
        if not self.lock_file.exists():
            return False, None

        try:
            with open(self.lock_file, "r") as f:
                content = f.read().strip()
                if not content:
                    return False, None
                info = json.loads(content)
                if info.get("pid"):
                    try:
                        os.kill(info["pid"], 0)
                        return True, info
                    except ProcessLookupError:
                        self.release()
                        return False, None
                return True, info
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return False, None

    def acquire(self, host: str, port: int, pid: int | None = None, allow_non_localhost: bool = False) -> bool:
        try:
            info = {
                "pid": pid or os.getpid(),
                "host": host,
                "port": port,
                "allow_non_localhost": allow_non_localhost,
                "started_at": datetime.now().isoformat(),
            }
            with open(self.lock_file, "w") as f:
                json.dump(info, f, indent=2)
            return True
        except Exception:
            return False

    def release(self):
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception:
            pass

    def get_status_message(self, info: dict | None) -> str:
        if not info:
            return "服务状态未知"

        host = info.get("host", "unknown")
        port = info.get("port", "unknown")
        pid = info.get("pid", "unknown")
        started_at = info.get("started_at", "unknown")

        lines = [
            f"🌐 访问地址: http://{host}:{port}",
            f"🔢 进程 PID: {pid}",
            f"⏰ 启动时间: {started_at}",
        ]

        if info.get("allow_non_localhost"):
            lines.append("⚠️  非本地访问模式 (已启用)")

        return "\n".join(lines)


def check_and_acquire_lock(data_dir: str) -> ServiceLock | None:
    lock = ServiceLock(data_dir)
    is_locked, _ = lock.is_locked()
    if not is_locked:
        return lock
    return None
