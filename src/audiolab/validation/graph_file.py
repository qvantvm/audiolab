"""Display-friendly validation facade for DSP Lab graph JSON files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from audiolab.graph.serialization import load_graph
from audiolab.graph.validator import validate_graph


@dataclass(frozen=True)
class GraphValidationIssue:
    level: str
    code: str
    message: str
    block: str | None = None
    port: str | None = None


@dataclass(frozen=True)
class GraphValidationReport:
    path: Path
    valid: bool
    issues: tuple[GraphValidationIssue, ...]

    def summary(self) -> str:
        if self.valid:
            return "Graph JSON is valid."
        errors = [issue for issue in self.issues if issue.level == "error"]
        count = len(errors) or len(self.issues)
        label = "error" if count == 1 else "errors"
        return f"Graph JSON has {count} {label}."


def looks_like_graph_json(path: str | Path) -> bool:
    target = Path(path)
    if target.suffix.lower() != ".json" or not target.exists():
        return False
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    graph_keys = {"blocks", "connections"}
    return bool(graph_keys.issubset(data) or data.get("schema_version"))


def validate_graph_file(path: str | Path) -> GraphValidationReport:
    target = Path(path)
    try:
        graph = load_graph(target)
    except json.JSONDecodeError as exc:
        return _single_error(
            target,
            "INVALID_JSON",
            f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}",
        )
    except ValidationError as exc:
        return _single_error(target, "SCHEMA_ERROR", str(exc))
    except Exception as exc:
        return _single_error(target, exc.__class__.__name__.upper(), str(exc))

    result = validate_graph(graph)
    issues = tuple(
        GraphValidationIssue(
            level=message.level,
            code=message.code,
            message=message.message,
            block=message.block,
            port=message.port,
        )
        for message in result.messages
    )
    return GraphValidationReport(path=target, valid=result.valid, issues=issues)


def _single_error(path: Path, code: str, message: str) -> GraphValidationReport:
    issue = GraphValidationIssue(level="error", code=code, message=message)
    return GraphValidationReport(path=path, valid=False, issues=(issue,))
