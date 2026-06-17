"""Path resolution helpers for autoresearch cycles."""

from __future__ import annotations

from pathlib import Path


def resolve_baseline_eval_dir(path: Path, repo_root: Path | None = None) -> Path:
    """Resolve baseline eval dir; map legacy ``experiments/`` to ``workspace/experiments/`` when needed."""

    raw = path.expanduser()
    if raw.is_absolute():
        resolved = raw.resolve()
        clusters = resolved / "aggregate" / "failure_clusters.json"
        if resolved.is_dir() and clusters.is_file():
            return resolved
        return resolved

    root = (repo_root or Path.cwd()).resolve()
    rel = raw.as_posix().lstrip("./")
    candidates = [root / rel]
    if rel.startswith("experiments/"):
        candidates.append(root / "workspace" / rel)

    for candidate in candidates:
        clusters = candidate / "aggregate" / "failure_clusters.json"
        if candidate.is_dir() and clusters.is_file():
            return candidate.resolve()

    if rel.startswith("experiments/"):
        return (root / "workspace" / rel).resolve()
    return candidates[0].resolve()
