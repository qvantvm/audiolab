"""Registry for physical solver plugins."""

from __future__ import annotations

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

    def find_solver(self, subsystem: PhysicalSubsystem) -> PhysicalSolver | None:
        for solver in self._solvers:
            if solver.can_solve(subsystem):
                return solver
        return None


_DEFAULT_REGISTRY = SolverRegistry()


def get_default_solver_registry() -> SolverRegistry:
    return _DEFAULT_REGISTRY
