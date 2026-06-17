"""Content hashing for model artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def hash_graph_dict(graph: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json(graph).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def hash_model_artifact(graph: dict[str, Any], extra: dict[str, Any] | None = None) -> str:
    payload = {"graph": graph}
    if extra:
        payload["extra"] = extra
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
