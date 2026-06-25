"""Lightweight terminal progress for long-running DSP jobs (no extra dependencies)."""

from __future__ import annotations

import sys
import time


class TaskProgress:
    """Single-line progress bar written to stderr."""

    def __init__(self, label: str, total: int, *, enabled: bool = True) -> None:
        self.label = label
        self.total = max(1, int(total))
        self.completed = 0
        self.enabled = enabled
        self._start = time.monotonic()
        self._extra = ""

    def update(self, n: int = 1, **extra: object) -> None:
        self.completed = min(self.total, self.completed + n)
        if extra:
            parts = [f"{key}={value}" for key, value in extra.items()]
            self._extra = " | " + ", ".join(parts)
        if self.enabled:
            self._render()

    def _render(self) -> None:
        pct = self.completed / self.total
        width = 28
        filled = int(width * pct)
        bar = "=" * filled + "-" * (width - filled)
        elapsed = time.monotonic() - self._start
        rate = self.completed / elapsed if elapsed > 0 else 0.0
        eta = (self.total - self.completed) / rate if rate > 0 else 0.0
        msg = (
            f"\r{self.label} [{bar}] {self.completed}/{self.total} "
            f"({pct:.0%}) {elapsed:.0f}s elapsed, ~{eta:.0f}s left{self._extra}"
        )
        sys.stderr.write(msg)
        sys.stderr.flush()

    def close(self) -> None:
        if self.enabled:
            sys.stderr.write("\n")
            sys.stderr.flush()
