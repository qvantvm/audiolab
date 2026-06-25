"""Model registry store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audiolab.governance.schema import normalize_metadata


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class ModelRegistry:
    def __init__(self, registry_dir: Path) -> None:
        self.registry_dir = registry_dir.resolve()
        self.models_dir = self.registry_dir / "models"
        self.reports_dir = self.registry_dir / "reports"
        self.registry_path = self.registry_dir / "registry.json"
        self.history_path = self.registry_dir / "registry.jsonl"
        self.active_path = self.registry_dir / "active_model.json"
        self._index: dict[str, dict[str, Any]] = {}
        self._active: dict[str, Any] = {}

    @classmethod
    def load(cls, registry_dir: Path) -> ModelRegistry:
        reg = cls(registry_dir)
        reg._load()
        return reg

    def _load(self) -> None:
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        if self.registry_path.is_file():
            raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
            models = raw.get("models", [])
            self._index = {m["model_id"]: normalize_metadata(m) for m in models if m.get("model_id")}
        else:
            self.save()
        if self.active_path.is_file():
            self._active = json.loads(self.active_path.read_text(encoding="utf-8"))

    def save(self) -> None:
        _write_json(
            self.registry_path,
            {
                "schema_version": 1,
                "models": sorted(self._index.values(), key=lambda m: m.get("model_id", "")),
            },
        )

    def append_history(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    def next_model_id(self) -> str:
        existing = sorted(self._index.keys())
        if not existing:
            return "pasp_model_000001"
        last = existing[-1]
        try:
            num = int(last.split("_")[-1])
            return f"pasp_model_{num + 1:06d}"
        except ValueError:
            return f"pasp_model_{len(existing) + 1:06d}"

    def find_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        for meta in self._index.values():
            if meta.get("content_hash") == content_hash:
                return meta
        return None

    def get(self, model_id: str) -> dict[str, Any] | None:
        return self._index.get(model_id)

    def add(self, metadata: dict[str, Any]) -> dict[str, Any]:
        meta = normalize_metadata(metadata)
        self._index[meta["model_id"]] = meta
        model_dir = self.models_dir / meta["model_id"]
        model_dir.mkdir(parents=True, exist_ok=True)
        _write_json(model_dir / "model_metadata.json", meta)
        self.append_history({"event": "registered", "model_id": meta["model_id"], "status": meta["status"]})
        self.save()
        return meta

    def set_status(self, model_id: str, status: str, reason: str = "") -> dict[str, Any]:
        meta = self._index.get(model_id)
        if not meta:
            raise KeyError(f"Model not found: {model_id}")
        meta = dict(meta)
        meta["status"] = status
        if reason:
            meta.setdefault("decision", {})["reason"] = reason
        self._index[model_id] = normalize_metadata(meta)
        model_dir = self.models_dir / model_id
        _write_json(model_dir / "model_metadata.json", self._index[model_id])
        self.append_history({"event": "status_change", "model_id": model_id, "status": status, "reason": reason})
        self.save()
        return self._index[model_id]

    def update_metadata(self, model_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        meta = self._index.get(model_id)
        if not meta:
            raise KeyError(f"Model not found: {model_id}")
        merged = dict(meta)
        for key, val in updates.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val
        self._index[model_id] = normalize_metadata(merged)
        _write_json(self.models_dir / model_id / "model_metadata.json", self._index[model_id])
        self.save()
        return self._index[model_id]

    @property
    def active_model(self) -> dict[str, Any] | None:
        aid = self._active.get("active_model_id")
        if aid:
            return self.get(aid)
        return None

    @property
    def active_model_id(self) -> str | None:
        return self._active.get("active_model_id") or None

    def set_active(self, model_id: str) -> dict[str, Any]:
        meta = self.get(model_id)
        if not meta:
            raise KeyError(f"Model not found: {model_id}")
        self._active = {
            "active_model_id": model_id,
            "content_hash": meta.get("content_hash"),
            "status": meta.get("status"),
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "model_path": str(self.models_dir / model_id / "source_graph.json"),
            "evaluation_summary": str(self.models_dir / model_id / "evaluation_summary.json"),
        }
        _write_json(self.active_path, self._active)
        self.append_history({"event": "set_active", "model_id": model_id})
        return self._active

    def model_dir(self, model_id: str) -> Path:
        return self.models_dir / model_id

    def all_models(self) -> list[dict[str, Any]]:
        return list(self._index.values())

    def link_child(self, parent_id: str, child_id: str) -> None:
        parent = self._index.get(parent_id)
        if not parent:
            return
        children = list(parent.get("lineage", {}).get("children", []))
        if child_id not in children:
            children.append(child_id)
        parent = dict(parent)
        parent.setdefault("lineage", {})["children"] = children
        self._index[parent_id] = normalize_metadata(parent)
        _write_json(self.models_dir / parent_id / "model_metadata.json", self._index[parent_id])
        self.save()
