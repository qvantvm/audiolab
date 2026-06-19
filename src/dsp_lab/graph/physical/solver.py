"""Physical solver contract and compiled subsystem runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem

CausalityKind = Literal["instantaneous", "strictly_causal", "mixed"]


@dataclass(frozen=True)
class SolverDeclarations:
    latency_samples: int = 0
    causality: CausalityKind = "strictly_causal"
    deterministic: bool = True


class PhysicalSolver(ABC):
    """Solver plugin selected by the graph compiler for a physical subsystem."""

    name: str

    @abstractmethod
    def can_solve(self, subsystem: PhysicalSubsystem) -> bool: ...

    @abstractmethod
    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem: ...


class CompiledPhysicalSubsystem(ABC):
    """Runtime host for a compiled physical subsystem."""

    def __init__(
        self,
        *,
        subsystem: PhysicalSubsystem,
        solver_name: str,
        declarations: SolverDeclarations,
        sample_rate: int,
    ) -> None:
        self.subsystem = subsystem
        self.solver_name = solver_name
        self.declarations = declarations
        self.sample_rate = sample_rate

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def get_state_snapshot(self) -> dict[str, Any]: ...

    @abstractmethod
    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None: ...

    @abstractmethod
    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        """Process one audio block and return boundary output signals keyed by BoundaryPort.name."""
