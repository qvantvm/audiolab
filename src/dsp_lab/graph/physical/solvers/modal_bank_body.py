"""Modal bank body physical solver for soundboard/body resonance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from dsp_lab.graph.physical.capabilities import SolverCapabilities
from dsp_lab.graph.physical.events import TimedEvent
from dsp_lab.graph.physical.modal_bank_body import (
    DEFAULT_MODAL_FREQUENCIES,
    DEFAULT_MODAL_GAINS,
    render_modal_bank_body,
)
from dsp_lab.graph.physical.solver import CompiledPhysicalSubsystem, PhysicalSolver, SolverDeclarations
from dsp_lab.graph.physical.subsystem import BoundaryPort, PhysicalSubsystem


@dataclass(frozen=True)
class ModalBankBodyConfig:
    block_id: str
    frequencies: tuple[float, ...]
    gains: tuple[float, ...]
    mix: float
    audio_input_port: str
    audio_output_port: str


class CompiledModalBankBody(CompiledPhysicalSubsystem):
    def __init__(self, subsystem: PhysicalSubsystem, sample_rate: int, config: ModalBankBodyConfig) -> None:
        super().__init__(
            subsystem=subsystem,
            solver_name="modal_bank_body",
            declarations=SolverDeclarations(
                latency_samples=0,
                causality="strictly_causal",
                deterministic=True,
                hosts_internal_blocks=True,
            ),
            sample_rate=sample_rate,
        )
        self.config = config

    def reset(self) -> None:
        return None

    def get_state_snapshot(self) -> dict[str, Any]:
        return {}

    def set_state_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        del snapshot

    def process_block(
        self,
        num_frames: int,
        events: Sequence[TimedEvent],
        control_inputs: Mapping[str, Any],
        signal_inputs: Mapping[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        del events, control_inputs
        audio = signal_inputs.get(self.config.audio_input_port)
        if audio is None:
            audio = np.zeros(num_frames, dtype=np.float32)
        out = render_modal_bank_body(
            np.asarray(audio, dtype=np.float32),
            sample_rate=self.sample_rate,
            frequencies=self.config.frequencies,
            gains=self.config.gains,
            mix=self.config.mix,
        )
        return {self.config.audio_output_port: out}


class ModalBankBodySolver(PhysicalSolver):
    name = "modal_bank_body"
    capabilities = SolverCapabilities(
        allowed_node_types=frozenset({"ModalBankBody"}),
        required_node_types=frozenset(),
        min_nodes=1,
        max_nodes=1,
        allowed_topologies=frozenset({"isolated_host"}),
        input_boundary_kinds=frozenset({"signal"}),
        output_boundary_kinds=frozenset({"signal"}),
        required_input_ports=frozenset({"audio"}),
        required_output_ports=frozenset({"audio"}),
        supports_bidirectional_physical=False,
        supports_wave_scattering=False,
        supports_nonlinear_contact=False,
        supports_multi_string_coupling=False,
        supports_soundboard_feedback=False,
        supports_sample_accurate_events=False,
        supported_families=frozenset({"modal_bank_body"}),
        priority=10,
    )

    def compile(self, subsystem: PhysicalSubsystem, sample_rate: int) -> CompiledPhysicalSubsystem:
        block_id = subsystem.block_ids[0]
        params = dict(subsystem.block_params.get(block_id, {}))
        frequencies = tuple(float(value) for value in params.get("frequencies", DEFAULT_MODAL_FREQUENCIES))
        gains = tuple(float(value) for value in params.get("gains", DEFAULT_MODAL_GAINS))
        config = ModalBankBodyConfig(
            block_id=block_id,
            frequencies=frequencies,
            gains=gains,
            mix=float(params.get("mix", 1.0)),
            audio_input_port=_boundary_name(subsystem.boundary_inputs, "audio", kind="signal"),
            audio_output_port=_boundary_name(subsystem.boundary_outputs, "audio", kind="signal"),
        )
        return CompiledModalBankBody(subsystem, sample_rate, config)


def _boundary_name(
    ports: tuple[BoundaryPort, ...],
    port_name: str,
    *,
    kind: str,
) -> str:
    for port in ports:
        if port.port_name == port_name and port.kind == kind:
            return port.name
    for port in ports:
        if port.port_name == port_name:
            return port.name
    if ports:
        for port in ports:
            if port.kind == kind:
                return port.name
    raise ValueError(f"Missing {kind} boundary port '{port_name}' for modal bank body subsystem")
