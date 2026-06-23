"""Compile-time guards against silent physical-to-signal fallback."""

from __future__ import annotations

from dsp_lab.blocks.metadata import get_port_spec
from dsp_lab.graph.connections import ClassifiedConnection, ConnectionEdgeKind
from dsp_lab.graph.execution_plan import ExecutionPlan
from dsp_lab.graph.physical.errors import misclassified_physical_edge_error, unsupported_subsystem_error
from dsp_lab.graph.physical.registry import SolverRegistry
from dsp_lab.graph.validator import split_endpoint


def assert_no_misclassified_physical_edges(
    classified: list[ClassifiedConnection],
) -> None:
    """Reject signal edges that substitute audio outputs for bidirectional physical ports."""
    for edge in classified:
        src = split_endpoint(edge.connection.from_)
        dst = split_endpoint(edge.connection.to)
        if src is None or dst is None:
            continue
        src_spec = get_port_spec(edge.src_block_type, src[1], is_output=True) if edge.src_block_type else None
        dst_spec = get_port_spec(edge.dst_block_type, dst[1], is_output=False) if edge.dst_block_type else None
        signal_src = src_spec is not None and src_spec.kind == "signal"
        bidirectional_dst = (
            dst_spec is not None
            and dst_spec.kind in {"physical", "wave"}
            and dst_spec.port_direction == "bidirectional"
        )
        if not signal_src or not bidirectional_dst:
            continue
        endpoint = f"{edge.connection.from_}->{edge.connection.to}"
        raise misclassified_physical_edge_error(
            connection_endpoint=endpoint,
            reason=(
                f"Connection {endpoint} routes a signal edge into physical port "
                f"'{dst[1]}' on {edge.dst_block_type}; use the declared bidirectional physical port "
                f"instead of substituting an audio output (e.g. string.bridge, not string.audio)."
            ),
        )


def assert_physical_computation_supported(
    execution_plan: ExecutionPlan,
    solver_registry: SolverRegistry,
    *,
    solver_hint: str | None = None,
) -> None:
    """Ensure every physical subsystem has a registered solver before render."""
    requires_solver = bool(execution_plan.physical_edges or execution_plan.wave_edges)
    if not requires_solver:
        return
    if not execution_plan.physical_subsystems:
        raise misclassified_physical_edge_error(
            connection_endpoint="",
            reason="Graph declares physical or wave-scattering edges but no physical subsystem was extracted.",
        )
    for subsystem in execution_plan.physical_subsystems:
        try:
            solver_registry.select_solver(subsystem, solver_hint=solver_hint)
        except Exception as exc:
            if hasattr(exc, "representation_valid"):
                raise exc
            raise unsupported_subsystem_error(
                subsystem,
                reason=str(exc),
                available_solvers=tuple(solver_registry.list_solvers()),
            ) from exc
