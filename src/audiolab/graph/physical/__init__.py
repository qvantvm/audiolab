"""Physical subsystem extraction and solver hosting."""

from audiolab.graph.physical.capabilities import (
    SolverCapabilities,
    SubsystemRequirements,
    derive_subsystem_requirements,
    rank_physical_solvers,
    score_solver_specificity,
    solver_matches_requirements,
    solver_selection_rank,
    topology_exact_match,
)
from audiolab.graph.physical.errors import UnsupportedPhysicalGraphError
from audiolab.graph.physical.events import TimedEvent, collect_timed_events
from audiolab.graph.physical.registry import SolverRegistry, get_default_solver_registry
from audiolab.graph.physical.solver import (
    CompiledPhysicalSubsystem,
    PhysicalSolver,
    SolverDeclarations,
)
from audiolab.graph.physical.subsystem import (
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
    "SolverCapabilities",
    "SolverDeclarations",
    "SolverRegistry",
    "SubsystemRequirements",
    "TimedEvent",
    "UnsupportedPhysicalGraphError",
    "collect_timed_events",
    "derive_subsystem_requirements",
    "extract_all_physical_subsystems",
    "extract_physical_subsystems",
    "get_default_solver_registry",
    "infer_solver_family",
    "rank_physical_solvers",
    "score_solver_specificity",
    "solver_matches_requirements",
    "solver_selection_rank",
    "topology_exact_match",
]
