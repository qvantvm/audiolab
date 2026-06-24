"""Built-in physical solvers."""

from __future__ import annotations

from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solvers.bell_modal_body import BellModalBodySolver
from dsp_lab.graph.physical.solvers.excited_waveguide_string import ExcitedWaveguideStringSolver
from dsp_lab.graph.physical.solvers.modal_bank_body import ModalBankBodySolver
from dsp_lab.graph.physical.solvers.polyphonic_waveguide import PolyphonicWaveguideSolver


def register_builtin_solvers(registry: SolverRegistry | None = None) -> None:
    registry = registry or get_default_solver_registry()
    if "excited_waveguide_string" not in registry.list_solvers():
        registry.register(ExcitedWaveguideStringSolver())
    if "modal_bank_body" not in registry.list_solvers():
        registry.register(ModalBankBodySolver())
    if "polyphonic_excited_waveguide" not in registry.list_solvers():
        registry.register(PolyphonicWaveguideSolver())
    if "bell_modal_body" not in registry.list_solvers():
        registry.register(BellModalBodySolver())


register_builtin_solvers()
