"""Mock planner for deterministic tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MockPlanner:
    def __init__(self, fixture_path: str | Path | None = None, fixture_data: dict[str, Any] | None = None):
        self.fixture_path = Path(fixture_path) if fixture_path else None
        self.fixture_data = fixture_data

    def propose(self, context: dict[str, Any], prompt: str) -> dict[str, Any]:
        if self.fixture_data is not None:
            return dict(self.fixture_data)
        if self.fixture_path and self.fixture_path.is_file():
            return json.loads(self.fixture_path.read_text(encoding="utf-8"))
        raise ValueError("MockPlanner requires fixture_path or fixture_data")
