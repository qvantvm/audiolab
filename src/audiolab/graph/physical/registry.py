"""Registry for physical solver plugins."""

from __future__ import annotations

from audiolab.graph.physical.capabilities import (
    derive_subsystem_requirements,
    rank_physical_solvers,
    solver_matches_requirements,
)
from audiolab.graph.physical.errors import (
    UnsupportedPhysicalGraphError,
    ambiguous_solver_error,
    invalid_solver_hint_error,
    unsupported_subsystem_error,
)
from audiolab.graph.physical.solver import PhysicalSolver
from audiolab.graph.physical.subsystem import PhysicalSubsystem


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

    def find_solver(
        self,
        subsystem: PhysicalSubsystem,
        *,
        solver_hint: str | None = None,
    ) -> PhysicalSolver | None:
        try:
            return self.select_solver(subsystem, solver_hint=solver_hint)
        except UnsupportedPhysicalGraphError:
            return None

    def select_solver(
        self,
        subsystem: PhysicalSubsystem,
        *,
        solver_hint: str | None = None,
    ) -> PhysicalSolver:
        available = tuple(self.list_solvers())
        requirements = derive_subsystem_requirements(subsystem)

        if solver_hint is not None:
            hinted = [solver for solver in self._solvers if solver.name == solver_hint]
            if not hinted:
                raise invalid_solver_hint_error(
                    subsystem,
                    solver_hint=solver_hint,
                    available_solvers=available,
                    reason=f"solver_hint '{solver_hint}' is not registered",
                )
            solver = hinted[0]
            if not solver_matches_requirements(solver.capabilities, requirements):
                raise invalid_solver_hint_error(
                    subsystem,
                    solver_hint=solver_hint,
                    available_solvers=available,
                    reason=f"solver_hint '{solver_hint}' does not match subsystem requirements",
                )
            return solver

        matches = self.find_matching_solvers(subsystem)
        if not matches:
            partial = tuple(s.name for s in matches)
            raise unsupported_subsystem_error(
                subsystem,
                reason="No registered PhysicalSolver can execute this subsystem",
                available_solvers=available,
                candidate_solvers=partial,
            )

        warning_counts = {solver.name: len(solver.estimate_warnings(subsystem)) for solver in matches}
        winner, ambiguous = rank_physical_solvers(matches, requirements, warning_counts=warning_counts)
        if ambiguous:
            raise ambiguous_solver_error(
                subsystem,
                solver_names=tuple(solver.name for solver in ambiguous),
                available_solvers=available,
            )
        assert winner is not None
        return winner


_DEFAULT_REGISTRY = SolverRegistry()


def get_default_solver_registry() -> SolverRegistry:
    return _DEFAULT_REGISTRY
