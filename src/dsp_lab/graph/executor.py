"""Whole-buffer offline graph execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from dsp_lab.graph.compiler import CompiledGraph, compile_graph
from dsp_lab.graph.physical.registry import SolverRegistry
from dsp_lab.graph.physical.events import collect_timed_events, events_for_block
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem
from dsp_lab.graph.schema import GraphSpec
from dsp_lab.graph.validator import split_endpoint


@dataclass
class RenderResult:
    audio: np.ndarray
    sample_rate: int
    probes: dict[str, Any]
    block_outputs: dict[str, dict[str, Any]]
    block_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    structured_warnings: list[dict[str, Any]] = field(default_factory=list)
    physical_subsystem_states: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def metadata(self) -> dict[str, Any]:
        frames = int(self.audio.shape[0]) if self.audio.ndim >= 1 else int(self.audio.size)
        channels = int(self.audio.shape[1]) if self.audio.ndim == 2 else 1
        return {
            "sample_rate": self.sample_rate,
            "frames": frames,
            "channels": channels,
            "duration": float(frames / self.sample_rate),
            "peak": float(np.max(np.abs(self.audio))) if self.audio.size else 0.0,
            "rms": float(np.sqrt(np.mean(self.audio**2))) if self.audio.size else 0.0,
            "warnings": list(self.warnings),
            "structured_warnings": list(self.structured_warnings),
            "physical_subsystem_states": dict(self.physical_subsystem_states),
        }


def render_graph(
    graph: GraphSpec | CompiledGraph,
    *,
    collect_block_states: bool = False,
    solver_registry: SolverRegistry | None = None,
) -> RenderResult:
    compiled = (
        compile_graph(graph, solver_registry=solver_registry)
        if isinstance(graph, GraphSpec)
        else graph
    )
    spec = compiled.spec
    n_frames = int(round(spec.sample_rate * spec.duration))

    compiled.initialize_block_states()
    timed_events = collect_timed_events(spec, spec.sample_rate)

    values: dict[str, Any] = {f"inputs.{name}": value for name, value in spec.inputs.items()}
    block_outputs: dict[str, dict[str, Any]] = {}
    block_states: dict[str, dict[str, Any]] = {}
    physical_subsystem_states: dict[str, dict[str, Any]] = {}

    schedule = _render_schedule(compiled)
    for block_id in schedule:
        if block_id not in compiled.solver_hosted_blocks:
            block = compiled.blocks[block_id]
            inputs = _gather_block_inputs(compiled, block_id, values)
            outputs = block.process(inputs, n_frames)
            block_outputs[block_id] = outputs
            if collect_block_states:
                state = block.get_state()
                if state:
                    block_states[block_id] = state
            for name, value in outputs.items():
                endpoint = f"{block_id}.{name}"
                if endpoint not in compiled.solver_owned_endpoints:
                    values[endpoint] = value

        for subsystem in compiled.physical_subsystem_triggers.get(block_id, ()):
            _process_physical_subsystem(
                compiled=compiled,
                subsystem=subsystem,
                n_frames=n_frames,
                timed_events=timed_events,
                values=values,
                block_outputs=block_outputs,
                physical_subsystem_states=physical_subsystem_states,
                collect_block_states=collect_block_states,
            )

    output_endpoint = f"{compiled.output_blocks[-1]}.audio"
    audio = np.asarray(values[output_endpoint], dtype=np.float32)
    if audio.ndim not in {1, 2}:
        raise ValueError(f"Render output must be mono or stereo audio, got shape {audio.shape}")
    if audio.ndim == 2 and audio.shape[1] not in {1, 2}:
        raise ValueError(f"Render output supports at most two channels, got shape {audio.shape}")
    if not np.all(np.isfinite(audio)):
        raise ValueError("Render produced NaN or infinite values")

    probes: dict[str, Any] = {}
    for probe in spec.probes:
        if probe in values:
            probes[probe] = values[probe]
        else:
            owner_port = split_endpoint(probe)
            if owner_port and owner_port[0] in block_outputs:
                probes[probe] = block_outputs[owner_port[0]].get(owner_port[1])

    return RenderResult(
        audio=np.nan_to_num(audio).astype(np.float32),
        sample_rate=spec.sample_rate,
        probes=probes,
        block_outputs=block_outputs,
        block_states=block_states,
        warnings=list(compiled.warnings),
        structured_warnings=list(compiled.structured_warnings),
        physical_subsystem_states=physical_subsystem_states,
    )


def _process_physical_subsystem(
    *,
    compiled: CompiledGraph,
    subsystem: CompiledPhysicalSubsystem,
    n_frames: int,
    timed_events: list,
    values: dict[str, Any],
    block_outputs: dict[str, dict[str, Any]],
    physical_subsystem_states: dict[str, dict[str, Any]],
    collect_block_states: bool,
) -> None:
    control_inputs: dict[str, Any] = {}
    signal_inputs: dict[str, np.ndarray] = {}
    for port in subsystem.subsystem.boundary_inputs:
        value = _boundary_source_value(compiled, port.endpoint, values)
        if port.kind == "control":
            control_inputs[port.name] = value
        elif port.kind == "signal":
            signal_inputs[port.name] = np.asarray(value, dtype=np.float32)

    block_events = events_for_block(timed_events, block_start=0, num_frames=n_frames)

    outputs = subsystem.process_block(
        n_frames,
        block_events,
        control_inputs,
        signal_inputs,
    )

    for port in subsystem.subsystem.boundary_outputs:
        if port.name not in outputs:
            continue
        values[port.endpoint] = outputs[port.name]
        owner_port = split_endpoint(port.endpoint)
        if owner_port:
            block_outputs.setdefault(owner_port[0], {})[owner_port[1]] = outputs[port.name]

    if collect_block_states:
        physical_subsystem_states[subsystem.subsystem.subsystem_id] = subsystem.get_state_snapshot()


def _boundary_source_value(compiled: CompiledGraph, endpoint: str, values: dict[str, Any]) -> Any:
    if endpoint in values:
        return values[endpoint]
    parsed = split_endpoint(endpoint)
    if parsed is None:
        raise ValueError(f"Missing boundary value for physical subsystem endpoint '{endpoint}'")
    block_id, port_name = parsed
    connection = compiled.input_connections.get((block_id, port_name))
    if connection is not None and connection.from_ in values:
        return values[connection.from_]
    raise ValueError(f"Missing boundary value for physical subsystem endpoint '{endpoint}'")


def _render_schedule(compiled: CompiledGraph) -> list[str]:
    event_ids = [instance.block_id for instance in compiled.event_schedule]
    signal_ids = [instance.block_id for instance in compiled.signal_schedule]
    if event_ids or signal_ids:
        seen: set[str] = set()
        schedule: list[str] = []
        for block_id in event_ids + signal_ids:
            if block_id in seen:
                continue
            seen.add(block_id)
            schedule.append(block_id)
        return schedule
    return compiled.order


def _gather_block_inputs(
    compiled: CompiledGraph,
    block_id: str,
    values: dict[str, Any],
) -> dict[str, Any]:
    block = compiled.blocks[block_id]
    inputs: dict[str, Any] = {}
    for port_name in block.input_ports:
        if (block_id, port_name) in compiled.solver_managed_ports:
            continue
        connection = compiled.input_connections.get((block_id, port_name))
        if connection is not None:
            inputs[port_name] = values[connection.from_]
    return inputs
