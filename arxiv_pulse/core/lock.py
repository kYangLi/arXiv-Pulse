import fcntl
import os
from pathlib import Path


class ServiceLock:
    def __init__(self, data_dir: str):
        self.lock_file = Path(data_dir) / ".pulse.lock"
        self.lock_fd = None

    def acquire(self) -> bool:
        try:
            self.lock_fd = open(self.lock_file, "w")
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(f"{os.getpid()}\n")
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            return False

    def release(self):
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                self.lock_fd = None
            except:
                pass

    def get_pid(self) -> int | None:
        try:
            if self.lock_file.exists():
                with open(self.lock_file, "r") as f:
                    return int(f.read().strip())
        except:
            pass
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def check_and_acquire_lock(data_dir: str) -> ServiceLock | None:
    lock = ServiceLock(data_dir)
    if lock.acquire():
        return lock
    return None
