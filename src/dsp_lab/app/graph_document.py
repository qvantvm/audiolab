"""In-memory editable graph document used by the GUI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import dsp_lab.blocks  # noqa: F401 - bootstrap registry
from dsp_lab.blocks.registry import get_block_class, list_block_types
from dsp_lab.graph.schema import BlockSpec, ConnectionSpec, GraphSpec, NodeLayout, UISpec
from dsp_lab.graph.serialization import graph_to_dict, load_graph, save_graph
from dsp_lab.graph.validator import ValidationResult, split_endpoint, validate_graph


class GraphDocument:
    def __init__(self, graph: GraphSpec | None = None, path: str | Path | None = None):
        self.graph = graph or GraphSpec(name="untitled")
        self.path = Path(path) if path else None
        self.dirty = False

    @classmethod
    def load(cls, path: str | Path) -> "GraphDocument":
        return cls(load_graph(path), path)

    def validate(self) -> ValidationResult:
        return validate_graph(self.graph)

    def to_json(self) -> str:
        return json.dumps(graph_to_dict(self.graph), indent=2, sort_keys=False) + "\n"

    def apply_json(self, text: str) -> None:
        self.graph = GraphSpec.model_validate(json.loads(text))
        self.dirty = True

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path) if path else self.path
        if target is None:
            raise ValueError("No save path selected")
        save_graph(self.graph, target)
        self.path = target
        self.dirty = False
        return target

    def reload(self) -> None:
        if self.path is None:
            raise ValueError("No path to reload")
        self.graph = load_graph(self.path)
        self.dirty = False

    def add_block(self, block_type: str, x: float = 100.0, y: float = 100.0) -> BlockSpec:
        cls = get_block_class(block_type)
        block_id = self._unique_block_id(block_type)
        block = BlockSpec(id=block_id, type=block_type, params=cls.default_params())
        self.graph.blocks.append(block)
        self._ensure_ui().nodes[block_id] = NodeLayout(x=x, y=y)
        self.dirty = True
        return block

    def delete_block(self, block_id: str) -> None:
        self.graph.blocks = [block for block in self.graph.blocks if block.id != block_id]
        self.graph.connections = [
            connection
            for connection in self.graph.connections
            if not _endpoint_refs_block(connection.from_, block_id) and not _endpoint_refs_block(connection.to, block_id)
        ]
        self.graph.probes = [probe for probe in self.graph.probes if not _endpoint_refs_block(probe, block_id)]
        if self.graph.ui:
            self.graph.ui.nodes.pop(block_id, None)
        self.dirty = True

    def move_node(self, block_id: str, x: float, y: float) -> None:
        self._ensure_ui().nodes[block_id] = NodeLayout(x=x, y=y)
        self.dirty = True

    def update_params(self, block_id: str, params: dict[str, Any]) -> None:
        block = self.block(block_id)
        block.params = dict(params)
        self.dirty = True

    def add_connection(self, from_endpoint: str, to_endpoint: str) -> None:
        self.graph.connections.append(ConnectionSpec.model_validate({"from": from_endpoint, "to": to_endpoint}))
        result = self.validate()
        if not result.valid:
            self.graph.connections.pop()
            errors = "; ".join(message.message for message in result.messages if message.level == "error")
            raise ValueError(errors)
        self.dirty = True

    def delete_connection(self, index: int) -> None:
        del self.graph.connections[index]
        self.dirty = True

    def block(self, block_id: str) -> BlockSpec:
        for block in self.graph.blocks:
            if block.id == block_id:
                return block
        raise KeyError(block_id)

    def available_block_types(self) -> list[str]:
        return list_block_types()

    def _ensure_ui(self) -> UISpec:
        if self.graph.ui is None:
            self.graph.ui = UISpec()
        return self.graph.ui

    def _unique_block_id(self, block_type: str) -> str:
        base = "".join(char.lower() if char.isalnum() else "_" for char in block_type).strip("_") or "block"
        existing = {block.id for block in self.graph.blocks}
        if base not in existing:
            return base
        index = 2
        while f"{base}_{index}" in existing:
            index += 1
        return f"{base}_{index}"


def _endpoint_refs_block(endpoint: str, block_id: str) -> bool:
    parsed = split_endpoint(endpoint)
    return bool(parsed and parsed[0] == block_id)
