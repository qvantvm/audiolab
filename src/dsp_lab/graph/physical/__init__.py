"""Physical subsystem extraction and solver hosting."""

from dsp_lab.graph.physical.errors import UnsupportedPhysicalGraphError
from dsp_lab.graph.physical.events import TimedEvent, collect_timed_events
from dsp_lab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from dsp_lab.graph.physical.solver import (
    CompiledPhysicalSubsystem,
    PhysicalSolver,
    SolverDeclarations,
)
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem, extract_physical_subsystems

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
    "extract_physical_subsystems",
    "get_default_solver_registry",
]
