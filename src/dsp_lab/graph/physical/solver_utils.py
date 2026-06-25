"""Boundary port helpers for physical solvers."""

from __future__ import annotations

from dsp_lab.graph.physical.subsystem import BoundaryPort


def boundary_name(
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
    raise ValueError(f"Missing {kind} boundary port '{port_name}'")


def optional_boundary_name(
    ports: tuple[BoundaryPort, ...],
    port_name: str,
    *,
    kind: str,
) -> str | None:
    for port in ports:
        if port.port_name == port_name and port.kind == kind:
            return port.name
    for port in ports:
        if port.port_name == port_name:
            return port.name
    return None
