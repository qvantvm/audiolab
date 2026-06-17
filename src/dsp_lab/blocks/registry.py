"""Block registry used by the engine, CLI, and GUI."""

from __future__ import annotations

from typing import Any

from dsp_lab.blocks.base import DSPBlock


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


def inspect_block(block_type: str) -> dict[str, Any]:
    cls = get_block_class(block_type)
    return {
        "type": cls.block_type,
        "category": cls.category,
        "description": cls.description,
        "inputs": [vars(port) for port in cls.input_ports.values()],
        "outputs": [vars(port) for port in cls.output_ports.values()],
        "default_params": cls.default_params(),
        "param_schema": cls.param_schema(),
    }
