"""Structured errors for physical graph compilation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dsp_lab.graph.physical.subsystem import PhysicalSubsystem


@dataclass(frozen=True)
class UnsupportedPhysicalGraphError(Exception):
    subsystem_id: str
    subsystem_kind: str
    topology: str
    solver_family: str | None
    block_ids: tuple[str, ...]
    block_types: tuple[str, ...]
    connection_endpoints: tuple[str, ...]
    reason: str
    available_solvers: tuple[str, ...] = ()

    def __str__(self) -> str:
        blocks = ", ".join(
            f"{block_id} ({block_type})" for block_id, block_type in zip(self.block_ids, self.block_types)
        )
        connections = ", ".join(self.connection_endpoints)
        family_hint = f" solver_family={self.solver_family}" if self.solver_family else ""
        solver_hint = (
            f" Registered solvers: {', '.join(self.available_solvers)}."
            if self.available_solvers
            else " No physical solvers are registered."
        )
        return (
            f"Physical subsystem '{self.subsystem_id}' ({self.subsystem_kind}, topology={self.topology}{family_hint}) "
            f"with blocks [{blocks}] and connections [{connections}] cannot be executed: {self.reason}.{solver_hint}"
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def unsupported_subsystem_error(
    subsystem: PhysicalSubsystem,
    *,
    reason: str,
    available_solvers: tuple[str, ...] = (),
) -> UnsupportedPhysicalGraphError:
    block_types = tuple(subsystem.block_types[block_id] for block_id in subsystem.block_ids)
    connection_endpoints = tuple(
        f"{edge.connection.from_}->{edge.connection.to}" for edge in subsystem.internal_connections
    )
    return UnsupportedPhysicalGraphError(
        subsystem_id=subsystem.subsystem_id,
        subsystem_kind=subsystem.kind,
        topology=subsystem.topology,
        solver_family=subsystem.solver_family,
        block_ids=subsystem.block_ids,
        block_types=block_types,
        connection_endpoints=connection_endpoints,
        reason=reason,
        available_solvers=available_solvers,
    )
