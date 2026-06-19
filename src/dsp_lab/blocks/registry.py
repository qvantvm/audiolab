"""Block registry used by the engine, CLI, and GUI."""

from __future__ import annotations

from typing import Any

from dsp_lab.blocks.base import DSPBlock
from dsp_lab.blocks.metadata import BlockTypeSpec, NodeValidationError, build_block_type_spec, validate_node_params


BLOCK_REGISTRY: dict[str, type[DSPBlock]] = {}


def register_block(cls: type[DSPBlock]) -> type[DSPBlock]:
    BLOCK_REGISTRY[cls.block_type] = cls
    return cls


def get_block_class(block_type: str) -> type[DSPBlock]:
    if block_type not in BLOCK_REGISTRY:
        raise KeyError(f"Unknown block type: {block_type}")
    return BLOCK_REGISTRY[block_type]


def list_block_types() -> list[str]:
    return sorted(BLOCK_REGISTRY)


def list_blocks() -> list[BlockTypeSpec]:
    return [get_block_spec(block_type) for block_type in list_block_types()]


def get_block_spec(block_type: str) -> BlockTypeSpec:
    return build_block_type_spec(get_block_class(block_type))


def validate_node(node: dict[str, Any]) -> list[NodeValidationError]:
    errors: list[NodeValidationError] = []
    block_id = str(node.get("id", "")).strip()
    block_type = str(node.get("type", "")).strip()
    if not block_id:
        errors.append(NodeValidationError("error", "MISSING_NODE_ID", "Block node is missing a non-empty 'id'"))
    if not block_type:
        errors.append(
            NodeValidationError("error", "MISSING_BLOCK_TYPE", "Block node is missing a non-empty 'type'", block_id)
        )
        return errors
    if block_type not in BLOCK_REGISTRY:
        errors.append(
            NodeValidationError("error", "UNKNOWN_BLOCK_TYPE", f"Unknown block type '{block_type}'", block_id)
        )
        return errors
    params = node.get("params", {})
    if not isinstance(params, dict):
        errors.append(
            NodeValidationError("error", "INVALID_PARAMS", "Block 'params' must be an object", block_id)
        )
        return errors
    for message in validate_node_params(block_type, params):
        message.block_id = block_id
        errors.append(message)
    return errors


def inspect_block(block_type: str) -> dict[str, Any]:
    cls = get_block_class(block_type)
    spec = get_block_spec(block_type)
    data = spec.to_dict()
    # Backward-compatible keys used by CLI, GUI, and legacy tests.
    data["type"] = spec.block_type
    data["category"] = spec.legacy_category
    data["migration_category"] = spec.category
    data["inputs"] = [
        {
            "name": port.name,
            "kind": port.runtime_kind,
            "required": port.required,
            "metadata_kind": port.kind,
            "domain": port.domain,
            "variables": list(port.variables),
        }
        for port in spec.input_ports
        if not port.proposed
    ]
    data["outputs"] = [
        {
            "name": port.name,
            "kind": port.runtime_kind,
            "required": port.required,
            "metadata_kind": port.kind,
            "domain": port.domain,
            "variables": list(port.variables),
        }
        for port in spec.output_ports
        if not port.proposed
    ]
    data["default_params"] = cls.default_params()
    data["param_schema"] = cls.param_schema()
    return data
