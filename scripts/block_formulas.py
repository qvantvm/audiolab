"""Formula markdown snippets for docs/audiolab/blocks.md."""

from __future__ import annotations

import json
from pathlib import Path

_FORMULAS_PATH = Path(__file__).with_name('block_formulas.json')
BLOCK_FORMULAS: dict[str, str] = json.loads(_FORMULAS_PATH.read_text(encoding='utf-8'))

