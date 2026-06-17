#!/usr/bin/env python3
"""Run a PASP autoresearch cycle from a JSON config."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dsp_lab.autoresearch.run_cycle import main


if __name__ == "__main__":
    raise SystemExit(main())
