"""Built-in physical solvers."""

from __future__ import annotations

from audiolab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from audiolab.graph.physical.solvers.bell_modal_body import BellModalBodySolver
from audiolab.graph.physical.solvers.bow_string_contact import BowStringContactSolver
from audiolab.graph.physical.solvers.excited_waveguide_string import ExcitedWaveguideStringSolver
from audiolab.graph.physical.solvers.hammer_string_contact_decomposed import HammerStringContactDecomposedSolver
from audiolab.graph.physical.solvers.lip_reed_bore_coupled import LipReedBoreCoupledSolver
from audiolab.graph.physical.solvers.membrane_shell_modal import MembraneShellModalSolver
from audiolab.graph.physical.solvers.modal_bank_body import ModalBankBodySolver
from audiolab.graph.physical.solvers.nonlinear_hammer_string_contact import NonlinearHammerStringContactSolver
from audiolab.graph.physical.solvers.pasp_lifecycle_piano import PASPLifecyclePianoSolver
from audiolab.graph.physical.solvers.polyphonic_waveguide import PolyphonicWaveguideSolver
from audiolab.graph.physical.solvers.struck_bar_body import StruckBarBodySolver
from audiolab.graph.physical.solvers.string_termination_impedance import StringTerminationImpedanceSolver


def register_builtin_solvers(registry: SolverRegistry | None = None) -> None:
    registry = registry or get_default_solver_registry()
    for name, solver in (
        ("excited_waveguide_string", ExcitedWaveguideStringSolver()),
        ("modal_bank_body", ModalBankBodySolver()),
        ("polyphonic_excited_waveguide", PolyphonicWaveguideSolver()),
        ("bell_modal_body", BellModalBodySolver()),
        ("struck_bar_body", StruckBarBodySolver()),
        ("nonlinear_hammer_string_contact", NonlinearHammerStringContactSolver()),
        ("pasp_lifecycle_piano", PASPLifecyclePianoSolver()),
        ("hammer_string_contact_decomposed", HammerStringContactDecomposedSolver()),
        ("bow_string_contact", BowStringContactSolver()),
        ("membrane_shell_modal", MembraneShellModalSolver()),
        ("lip_reed_bore_coupled", LipReedBoreCoupledSolver()),
        ("string_termination_impedance", StringTerminationImpedanceSolver()),
    ):
        if name not in registry.list_solvers():
            registry.register(solver)


register_builtin_solvers()
