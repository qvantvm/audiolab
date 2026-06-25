"""Structured errors for physical graph compilation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from audiolab.graph.physical.capabilities import derive_subsystem_requirements
from audiolab.graph.physical.subsystem import PhysicalSubsystem

_REPRESENTATION_VALID_PREFIX = "Valid representation, unsupported computation"


@dataclass
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
    candidate_solvers: tuple[str, ...] = ()
    requirements: dict[str, Any] = field(default_factory=dict)
    requested_solver_hint: str | None = None
    code: str = "UNSUPPORTED_PHYSICAL_GRAPH"
    representation_valid: bool = False

    def __str__(self) -> str:
        blocks = ", ".join(
            f"{block_id} ({block_type})" for block_id, block_type in zip(self.block_ids, self.block_types)
        )
        connections = ", ".join(self.connection_endpoints)
        family_hint = f" solver_family={self.solver_family}" if self.solver_family else ""
        hint_hint = f" requested_solver_hint={self.requested_solver_hint}" if self.requested_solver_hint else ""
        candidate_hint = (
            f" Partial matches: {', '.join(self.candidate_solvers)}."
            if self.candidate_solvers
            else ""
        )
        solver_hint = (
            f" Registered solvers: {', '.join(self.available_solvers)}."
            if self.available_solvers
            else " No physical solvers are registered."
        )
        prefix = f"{_REPRESENTATION_VALID_PREFIX}: " if self.representation_valid else ""
        return (
            f"{prefix}Physical subsystem '{self.subsystem_id}' ({self.subsystem_kind}, topology={self.topology}{family_hint}{hint_hint}) "
            f"with blocks [{blocks}] and connections [{connections}] cannot be executed: {self.reason}."
            f"{candidate_hint}{solver_hint}"
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UnsupportedComputationError(UnsupportedPhysicalGraphError):
    code: str = "UNSUPPORTED_COMPUTATION"
    representation_valid: bool = True

    def __str__(self) -> str:
        blocks = ", ".join(
            f"{block_id} ({block_type})" for block_id, block_type in zip(self.block_ids, self.block_types)
        )
        connections = ", ".join(self.connection_endpoints)
        if self.subsystem_id:
            family_hint = f" solver_family={self.solver_family}" if self.solver_family else ""
            candidate_hint = (
                f" Partial matches: {', '.join(self.candidate_solvers)}."
                if self.candidate_solvers
                else ""
            )
            solver_hint = (
                f" Registered solvers: {', '.join(self.available_solvers)}."
                if self.available_solvers
                else " No physical solvers are registered."
            )
            return (
                f"{_REPRESENTATION_VALID_PREFIX}: "
                f"Physical subsystem '{self.subsystem_id}' ({self.subsystem_kind}, topology={self.topology}{family_hint}) "
                f"with blocks [{blocks}] and connections [{connections}] cannot be executed: {self.reason}."
                f"{candidate_hint}{solver_hint}"
            )
        if connections:
            return f"{_REPRESENTATION_VALID_PREFIX}: {self.reason} (connections: {connections})."
        return f"{_REPRESENTATION_VALID_PREFIX}: {self.reason}."


def unsupported_subsystem_error(
    subsystem: PhysicalSubsystem,
    *,
    reason: str,
    available_solvers: tuple[str, ...] = (),
    candidate_solvers: tuple[str, ...] = (),
    requested_solver_hint: str | None = None,
) -> UnsupportedComputationError:
    block_types = tuple(subsystem.block_types[block_id] for block_id in subsystem.block_ids)
    connection_endpoints = tuple(
        f"{edge.connection.from_}->{edge.connection.to}" for edge in subsystem.internal_connections
    )
    requirements = derive_subsystem_requirements(subsystem)
    return UnsupportedComputationError(
        subsystem_id=subsystem.subsystem_id,
        subsystem_kind=subsystem.kind,
        topology=subsystem.topology,
        solver_family=subsystem.solver_family,
        block_ids=subsystem.block_ids,
        block_types=block_types,
        connection_endpoints=connection_endpoints,
        reason=reason,
        available_solvers=available_solvers,
        candidate_solvers=candidate_solvers,
        requirements=requirements.to_dict(),
        requested_solver_hint=requested_solver_hint,
    )


def misclassified_physical_edge_error(
    *,
    connection_endpoint: str,
    reason: str,
) -> UnsupportedComputationError:
    return UnsupportedComputationError(
        subsystem_id="",
        subsystem_kind="misclassified_edge",
        topology="",
        solver_family=None,
        block_ids=(),
        block_types=(),
        connection_endpoints=(connection_endpoint,),
        reason=reason,
    )


def ambiguous_solver_error(
    subsystem: PhysicalSubsystem,
    *,
    solver_names: tuple[str, ...],
    available_solvers: tuple[str, ...] = (),
) -> UnsupportedComputationError:
    names = ", ".join(solver_names)
    return unsupported_subsystem_error(
        subsystem,
        reason=(
            f"Multiple physical solvers matched with equal priority: {names}. "
            f'Set "solver_hint" on the graph to one of: {names}'
        ),
        available_solvers=available_solvers,
        candidate_solvers=solver_names,
    )


def invalid_solver_hint_error(
    subsystem: PhysicalSubsystem,
    *,
    solver_hint: str,
    available_solvers: tuple[str, ...] = (),
    reason: str,
) -> UnsupportedComputationError:
    return unsupported_subsystem_error(
        subsystem,
        reason=reason,
        available_solvers=available_solvers,
        requested_solver_hint=solver_hint,
    )
