"""Registry for physical solver plugins."""

from __future__ import annotations

from dsp_lab.graph.physical.capabilities import (
    derive_subsystem_requirements,
    score_solver_specificity,
    solver_matches_requirements,
)
from dsp_lab.graph.physical.solver import PhysicalSolver
from dsp_lab.graph.physical.subsystem import PhysicalSubsystem


class SolverRegistry:
    def __init__(self) -> None:
        self._solvers: list[PhysicalSolver] = []

    def register(self, solver: PhysicalSolver) -> None:
        if any(existing.name == solver.name for existing in self._solvers):
            raise ValueError(f"Physical solver '{solver.name}' is already registered")
        self._solvers.append(solver)

    def list_solvers(self) -> list[str]:
        return [solver.name for solver in self._solvers]

    def list_capabilities(self) -> dict[str, dict]:
        return {solver.name: solver.capabilities.to_dict() for solver in self._solvers}

    def find_matching_solvers(self, subsystem: PhysicalSubsystem) -> list[PhysicalSolver]:
        requirements = derive_subsystem_requirements(subsystem)
        return [
            solver
            for solver in self._solvers
            if solver_matches_requirements(solver.capabilities, requirements)
        ]

    def find_solver(self, subsystem: PhysicalSubsystem) -> PhysicalSolver | None:
        requirements = derive_subsystem_requirements(subsystem)
        matches = [
            solver
            for solver in self._solvers
            if solver_matches_requirements(solver.capabilities, requirements)
        ]
        if not matches:
            return None
        return max(matches, key=lambda solver: score_solver_specificity(solver.capabilities, requirements))


_DEFAULT_REGISTRY = SolverRegistry()


def get_default_solver_registry() -> SolverRegistry:
    return _DEFAULT_REGISTRY
