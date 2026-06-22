"""Physical subsystem extraction and solver hosting."""

from dsp_lab.graph.physical.errors import UnsupportedPhysicalGraphError
from dsp_lab.graph.physical.events import TimedEvent, collect_timed_events
from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solver import (
    CompiledPhysicalSubsystem,
    PhysicalSolver,
    SolverDeclarations,
)
from dsp_lab.graph.physical.subsystem import (
    BoundaryPort,
    PhysicalSubsystem,
    extract_all_physical_subsystems,
    extract_physical_subsystems,
    infer_solver_family,
)

__all__ = [
    "BoundaryPort",
    "CompiledPhysicalSubsystem",
    "PhysicalSolver",
    "PhysicalSubsystem",
    "SolverDeclarations",
    "SolverRegistry",
    "TimedEvent",
    "UnsupportedPhysicalGraphError",
    "collect_timed_events",
    "extract_all_physical_subsystems",
    "extract_physical_subsystems",
    "get_default_solver_registry",
    "infer_solver_family",
]
