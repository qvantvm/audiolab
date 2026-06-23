"""Pydantic models for DSP Lab graph JSON."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NodeLayout(BaseModel):
    x: float = 0.0
    y: float = 0.0


class UISpec(BaseModel):
    nodes: dict[str, NodeLayout] = Field(default_factory=dict)


class BlockSpec(BaseModel):
    id: str
    type: str
    params: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "type")
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be empty")
        return value


class ConnectionSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    to: str


class GraphSpec(BaseModel):
    schema_version: str = "0.1"
    name: str
    sample_rate: int = 48000
    duration: float = 1.0
    block_size: int = 64
    inputs: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    blocks: list[BlockSpec] = Field(default_factory=list)
    connections: list[ConnectionSpec] = Field(default_factory=list)
    probes: list[str] = Field(default_factory=list)
    ui: UISpec | None = None
    solver_hint: str | None = None

    @field_validator("sample_rate", "block_size")
    @classmethod
    def positive_int(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator("duration")
    @classmethod
    def positive_duration(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("duration must be positive")
        return value


PortKind = Literal["audio", "control", "event"]
