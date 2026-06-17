"""Base types for offline DSP blocks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class Port:
    name: str
    kind: str
    required: bool = True


class DSPBlock(ABC):
    block_type: ClassVar[str] = "DSPBlock"
    category: ClassVar[str] = "Core"
    description: ClassVar[str] = ""
    input_ports: ClassVar[dict[str, Port]] = {}
    output_ports: ClassVar[dict[str, Port]] = {}

    def __init__(self, block_id: str, params: dict[str, Any] | None = None):
        self.block_id = block_id
        self.params = params or {}
        self.sample_rate = 48000
        self.block_size = 64
        self.duration = 1.0

    def prepare(self, sample_rate: int, block_size: int, duration: float) -> None:
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.duration = duration

    def reset(self) -> None:
        pass

    @abstractmethod
    def process(self, inputs: dict[str, Any], n_frames: int) -> dict[str, Any]:
        pass

    def get_state(self) -> dict[str, Any]:
        return {}

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {}

    @classmethod
    def param_schema(cls) -> dict[str, dict[str, Any]]:
        return {}
