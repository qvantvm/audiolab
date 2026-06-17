#!/usr/bin/env python3
"""Agent-free entry point for PASP autoresearch (baseline, plan, full, promote)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DEFAULT_CONFIG = ROOT / "examples/autoresearch/pasp_autoresearch_fast.json"
DEFAULT_BASELINE_OUT = ROOT / "workspace/experiments/pasp_baseline_eval"
DEFAULT_REGISTRY = ROOT / "workspace/experiments/model_registry"
DEFAULT_POLICY = ROOT / "examples/governance/pasp_promotion_policy_v1.json"

sys.path.insert(0, str(SRC))
from dsp_lab.autoresearch.path_utils import resolve_baseline_eval_dir


def _env() -> dict[str, str]:
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    return env


def _run(cmd: list[str]) -> int:
    print(" ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, env=_env()).returncode


def _resolve(path: Path) -> Path:
    p = path.expanduser()
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


def _resolve_baseline(path: Path | None, config_path: Path) -> Path:
    if path is None:
        cfg = json.loads(_resolve(config_path).read_text(encoding="utf-8"))
        return resolve_baseline_eval_dir(_resolve(Path(cfg.get("baseline_eval", DEFAULT_BASELINE_OUT))), ROOT)
    return resolve_baseline_eval_dir(path, ROOT)


def _latest_cycle_dir(autoresearch_dir: Path) -> Path | None:
    cycles = sorted(autoresearch_dir.glob("pasp_cycle_*"))
    return cycles[-1] if cycles else None


def _cycle_output_dir(config_path: Path) -> Path:
    cfg = json.loads(_resolve(config_path).read_text(encoding="utf-8"))
    return _resolve(Path(cfg["output_dir"]))


def _append_cycle_runtime_flags(cmd: list[str], args: argparse.Namespace) -> None:
    if getattr(args, "workers", None) is not None:
        cmd.extend(["--workers", str(args.workers)])
    if getattr(args, "trial_batch_size", None) is not None:
        cmd.extend(["--trial-batch-size", str(args.trial_batch_size)])
    if getattr(args, "no_progress", False):
        cmd.append("--no-progress")


def _append_eval_runtime_flags(cmd: list[str], args: argparse.Namespace) -> None:
    if getattr(args, "workers", None) is not None:
        cmd.extend(["--workers", str(args.workers)])
    if getattr(args, "no_progress", False):
        cmd.append("--no-progress")


def _require_baseline(baseline: Path) -> int | None:
    clusters = baseline / "aggregate" / "failure_clusters.json"
    if clusters.is_file():
        return None
    expected = _resolve(Path("workspace/experiments/pasp_baseline_eval"))
    print(f"Baseline eval not found: {baseline}")
    if baseline != expected:
        print(f"Expected location: {expected}")
    print(
        "Run baseline eval first:\n"
        "  python examples/run_autoresearch_harness.py baseline "
        "--out workspace/experiments/pasp_baseline_eval"
    )
    return 1


def cmd_baseline(args: argparse.Namespace) -> int:
    out = _resolve(args.out)
    if args.dataset is None or args.graph is None:
        cfg = json.loads(_resolve(args.config).read_text(encoding="utf-8"))
        if args.dataset is None:
            args.dataset = _resolve(
                Path(cfg.get("dataset_manifest", "data/evaluation/datasets/pasp_phrase_eval_v1.json"))
            )
        if args.graph is None:
            args.graph = _resolve(Path(cfg.get("base_model_graph", "examples/graphs/pasp_performance_model_base.json")))
    else:
        args.dataset = _resolve(args.dataset)
        args.graph = _resolve(args.graph)
    cmd = [
        sys.executable,
        "examples/run_pasp_dataset_eval.py",
        "--dataset",
        str(args.dataset),
        "--graph",
        str(args.graph),
        "--out",
        str(out),
    ]
    if args.baseline:
        cmd.extend(["--baseline", str(_resolve_baseline(args.baseline, args.config))])
    if args.force:
        cmd.append("--force")
    _append_eval_runtime_flags(cmd, args)
    code = _run(cmd)
    if code == 0:
        print(f"Baseline eval written to {out}")
        print(f"Inspect: {out / 'aggregate/failure_clusters.json'}")
    return code


def cmd_plan(args: argparse.Namespace) -> int:
    config = _resolve(args.config)
    baseline = _resolve_baseline(args.baseline, config)
    preflight = _require_baseline(baseline)
    if preflight is not None:
        return preflight
    cmd = [
        sys.executable,
        "examples/run_pasp_autoresearch_cycle.py",
        "--config",
        str(config),
        "--plan-only",
        "--baseline",
        str(baseline),
    ]
    if args.no_memory:
        cmd.append("--no-memory")
    if args.no_planner:
        cmd.append("--no-planner")
    _append_cycle_runtime_flags(cmd, args)
    code = _run(cmd)
    if code == 0:
        cycle = _latest_cycle_dir(_cycle_output_dir(config))
        if cycle:
            print(f"Cycle dir: {cycle}")
            print(f"Read first: {cycle / 'agent_cycle_report.json'}")
    return code


def cmd_full(args: argparse.Namespace) -> int:
    config = _resolve(args.config)
    baseline = _resolve_baseline(args.baseline, config)
    preflight = _require_baseline(baseline)
    if preflight is not None:
        return preflight
    cmd = [
        sys.executable,
        "examples/run_pasp_autoresearch_cycle.py",
        "--config",
        str(config),
        "--run-calibration",
        "--run-evaluation",
        "--baseline",
        str(baseline),
    ]
    if args.no_memory:
        cmd.append("--no-memory")
    if args.no_planner:
        cmd.append("--no-planner")
    _append_cycle_runtime_flags(cmd, args)
    code = _run(cmd)
    if code == 0:
        cycle = _latest_cycle_dir(_cycle_output_dir(config))
        if cycle:
            print(f"Cycle dir: {cycle}")
            print(f"Decision: {cycle / 'decision.json'}")
    return code


def cmd_promote(args: argparse.Namespace) -> int:
    cycle_dir = args.cycle.resolve()
    registry = args.registry.resolve()
    policy = args.policy.resolve()

    reg_cmd = [
        sys.executable,
        "examples/register_pasp_model_candidate.py",
        "--cycle",
        str(cycle_dir),
        "--registry",
        str(registry),
    ]
    code = _run(reg_cmd)
    if code != 0:
        return code

    if args.model_id:
        model_id = args.model_id
    else:
        report_path = cycle_dir / "agent_cycle_report.json"
        if not report_path.is_file():
            print("No agent_cycle_report.json; pass --model-id")
            return 1
        report = json.loads(report_path.read_text(encoding="utf-8"))
        model_id = report.get("registered_model_id")
        if not model_id:
            print("No registered_model_id in report; pass --model-id")
            return 1

    promote_cmd = [
        sys.executable,
        "-m",
        "dsp_lab.governance.promote_model",
        "--model-id",
        model_id,
        "--registry",
        str(registry),
        "--policy",
        str(policy),
    ]
    if args.skip_human_review:
        promote_cmd.append("--skip-human-review")
    if args.override:
        promote_cmd.extend(["--override", "--reason", args.reason or "harness promote"])
    return _run(promote_cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="PASP autoresearch harness (no agents): baseline, plan, full, promote"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_base = sub.add_parser("baseline", help="Run dataset evaluation (scoreboard)")
    p_base.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p_base.add_argument("--dataset", type=Path, default=None)
    p_base.add_argument("--graph", type=Path, default=None)
    p_base.add_argument("--out", type=Path, default=DEFAULT_BASELINE_OUT)
    p_base.add_argument("--baseline", type=Path, default=None, help="Previous eval for regression")
    p_base.add_argument("--force", action="store_true")
    p_base.add_argument("--workers", type=int, default=None)
    p_base.add_argument("--no-progress", action="store_true")
    p_base.set_defaults(func=cmd_baseline, no_progress=False)

    p_plan = sub.add_parser("plan", help="Plan-only autoresearch cycle")
    p_plan.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p_plan.add_argument("--baseline", type=Path, default=None)
    p_plan.add_argument("--no-memory", action="store_true")
    p_plan.add_argument("--no-planner", action="store_true")
    p_plan.add_argument("--workers", type=int, default=None)
    p_plan.add_argument("--trial-batch-size", type=int, default=None)
    p_plan.add_argument("--no-progress", action="store_true")
    p_plan.set_defaults(func=cmd_plan, no_progress=False)

    p_full = sub.add_parser("full", help="Full cycle: calibration + dataset eval")
    p_full.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p_full.add_argument("--baseline", type=Path, default=None)
    p_full.add_argument("--no-memory", action="store_true")
    p_full.add_argument("--no-planner", action="store_true")
    p_full.add_argument("--workers", type=int, default=None)
    p_full.add_argument("--trial-batch-size", type=int, default=None)
    p_full.add_argument("--no-progress", action="store_true")
    p_full.set_defaults(func=cmd_full, no_progress=False)

    p_promote = sub.add_parser("promote", help="Register cycle candidate and optionally promote")
    p_promote.add_argument("--cycle", type=Path, required=True)
    p_promote.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    p_promote.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    p_promote.add_argument("--model-id", type=str, default=None)
    p_promote.add_argument("--skip-human-review", action="store_true")
    p_promote.add_argument("--override", action="store_true")
    p_promote.add_argument("--reason", type=str, default="")
    p_promote.set_defaults(func=cmd_promote)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
