"""Built-in physical solvers."""

from __future__ import annotations

from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solvers.excited_waveguide_string import ExcitedWaveguideStringSolver


def register_builtin_solvers(registry: SolverRegistry | None = None) -> None:
    registry = registry or get_default_solver_registry()
    if "excited_waveguide_string" not in registry.list_solvers():
        registry.register(ExcitedWaveguideStringSolver())


register_builtin_solvers()
