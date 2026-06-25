"""Structured warnings for physical solvers and compile-time parameter gaps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED = "PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED"
PARAM_LEGACY_MAPPED = "PARAM_LEGACY_MAPPED"

SOLVER_IGNORED_PARAMS: dict[str, frozenset[str]] = {
    "polyphonic_excited_waveguide": frozenset({"inharmonicity_B"}),
}

_SOLVER_DISPLAY_NAMES: dict[str, str] = {
    "excited_waveguide_string": "ExcitedWaveguideStringSolver",
    "polyphonic_excited_waveguide": "PolyphonicWaveguideSolver",
}


@dataclass(frozen=True)
class PhysicalWarning:
    code: str
    message: str
    node: str | None = None
    param: str | None = None
    solver: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "node": self.node,
            "param": self.param,
            "solver": self.solver,
        }


def _solver_display_name(solver: str) -> str:
    return _SOLVER_DISPLAY_NAMES.get(solver, solver)


def param_not_implemented(*, node: str, param: str, solver: str, detail: str) -> PhysicalWarning:
    display = _solver_display_name(solver)
    message = f"{display} accepts {param} for schema compatibility but does not yet implement {detail}."
    return PhysicalWarning(
        code=PARAM_ACCEPTED_BUT_NOT_IMPLEMENTED,
        message=message,
        node=node,
        param=param,
        solver=solver,
    )


def param_legacy_mapped(*, node: str, param: str, solver: str, detail: str) -> PhysicalWarning:
    display = _solver_display_name(solver)
    message = f"{display}: {detail}"
    return PhysicalWarning(
        code=PARAM_LEGACY_MAPPED,
        message=message,
        node=node,
        param=param,
        solver=solver,
    )


def _param_is_active(param: str, value: Any) -> bool:
    if param == "inharmonicity_B":
        return float(value) != 0.0
    return value is not None


def warnings_for_ignored_params(
    *,
    block_id: str,
    params: Mapping[str, Any],
    solver: str,
) -> tuple[PhysicalWarning, ...]:
    ignored = SOLVER_IGNORED_PARAMS.get(solver, frozenset())
    warnings: list[PhysicalWarning] = []
    for param in sorted(ignored):
        if param not in params:
            continue
        if not _param_is_active(param, params[param]):
            continue
        detail = "dispersion" if param == "inharmonicity_B" else "this effect"
        warnings.append(
            param_not_implemented(node=block_id, param=param, solver=solver, detail=detail)
        )
    return tuple(warnings)


def warning_messages(warnings: tuple[PhysicalWarning, ...] | list[PhysicalWarning]) -> list[str]:
    return [warning.message for warning in warnings]
