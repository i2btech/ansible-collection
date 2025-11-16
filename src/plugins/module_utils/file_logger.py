from __future__ import annotations
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, TextIO
import sys

# /workspace/src/plugins/module_utils/file_logger.py


class FileLogger:
    """
    Simple file-based logger with levels, thread-safety, optional size-based rotation,
    and context-manager support.

    Example:
        logger = FileLogger("/var/log/myapp/log.txt", level="DEBUG", max_bytes=10_000_000)
        logger.info("Started")
        logger.close()
    """

    LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

    def __init__(
        self,
        path: str = "/tmp/ansible.log",
        level: str = "INFO",
        encoding: str = "utf-8",
        mode: str = "a",
        max_bytes: Optional[int] = 10_000_000,
    ) -> None:
        """
        Initialize logger.

        - path: file path to write logs to (directories will be created).
        - level: minimum level to record ("DEBUG","INFO","WARNING","ERROR","CRITICAL").
        - encoding: file encoding.
        - mode: file open mode, typically "a" (append).
        - max_bytes: if set, rotate file when size exceeds this (simple rename with timestamp).
        """
        self.path = Path(path)
        self.encoding = encoding
        self.mode = mode
        self.max_bytes = max_bytes if (max_bytes and max_bytes > 0) else None
        self._lock = threading.RLock()
        self._file: Optional[TextIO] = None
        self._level = self._level_value(level)
        self._ensure_dir()
        self._open_file()

    def _level_value(self, level: str | int) -> int:
        if isinstance(level, int):
            return level
        return self.LEVELS.get(str(level).upper(), 20)

    def _ensure_dir(self) -> None:
        parent = self.path.parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

    def _open_file(self) -> None:
        # Open file handle lazily and keep it open for performance
        self._file = open(self.path, self.mode, encoding=self.encoding)

    def _should_rotate(self) -> bool:
        if not self.max_bytes:
            return False
        try:
            return self.path.exists() and self.path.stat().st_size >= self.max_bytes
        except OSError:
            return False

    def _rotate(self) -> None:
        # Close current, rename with timestamp, reopen new empty file
        if self._file:
            try:
                self._file.flush()
                self._file.close()
            except Exception:
                pass
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        rotated = self.path.with_name(f"{self.path.name}.{timestamp}")
        try:
            self.path.replace(rotated)
        except Exception:
            # fallback to rename if replace fails
            try:
                os.rename(self.path, rotated)
            except Exception:
                # give up rotating
                pass
        self._open_file()

    def _format(self, level_name: str, message: str) -> str:
        ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        return f"{ts} [{level_name}] {message}\n"

    def log(self, level: str | int, message: str) -> None:
        """
        Write a log entry if level >= configured level.
        """
        lv = self._level_value(level)
        if lv < self._level:
            return
        level_name = (
            next((k for k, v in self.LEVELS.items() if v == lv), str(level).upper())
            if isinstance(level, int)
            else str(level).upper()
        )
        entry = self._format(level_name, message)
        with self._lock:
            try:
                if self._should_rotate():
                    self._rotate()
                if not self._file:
                    self._open_file()
                self._file.write(entry)
                self._file.flush()
            except Exception:
                # avoid raising from logger; best-effort write
                try:
                    # fallback to stderr if file write fails
                    sys.stderr.write("Logger write failed\n")
                except Exception:
                    pass

    # Convenience methods
    def debug(self, message: str) -> None:
        self.log("DEBUG", message)

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def warning(self, message: str) -> None:
        self.log("WARNING", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    def critical(self, message: str) -> None:
        self.log("CRITICAL", message)

    def set_level(self, level: str | int) -> None:
        with self._lock:
            self._level = self._level_value(level)

    def close(self) -> None:
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                except Exception:
                    pass
                self._file = None

    # Context manager support
    def __enter__(self) -> "FileLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # Ensure file closed on deletion
    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass