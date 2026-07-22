import os
import threading
from pathlib import Path

from platformdirs import user_cache_dir, user_downloads_dir

DEFAULT_CACHE_SUBDIRECTORY = "jlog"


class SimpleFileLock:
    """
    Cross-platform file lock.
    """

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(f"pid:{os.getpid()}\n")
        return self

    def __exit__(self, execution_type, execution_value, execution_traceback):
        try:
            if self.path.exists():
                try:
                    self.path.unlink()
                except Exception:
                    pass
        finally:
            self._lock.release()


def _resolve_directory(path_string: str | None, default: Path) -> Path:
    if path_string:
        try:
            path = Path(path_string).expanduser().resolve()
            path.mkdir(parents=True, exist_ok=True)
            return path
        except TypeError, ValueError, OSError:
            pass
    default.mkdir(parents=True, exist_ok=True)
    return default


def resolve_output_directory(output_directory: str | None = None) -> Path:
    """
    Figures out where to place the output files.
    """

    default = Path(user_downloads_dir())
    return _resolve_directory(output_directory, default)


def resolve_cache_directory(cache_directory: str | None = None) -> Path:
    """
    Figures out where to place the cache files.
    """

    default = Path(user_cache_dir())
    return _resolve_directory(cache_directory, default)
