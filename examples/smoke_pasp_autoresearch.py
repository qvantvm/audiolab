#!/usr/bin/env python3
"""No-agent green-path smoke test for PASP autoresearch stack."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def run_step(name: str, cmd: list[str], *, cwd: Path = ROOT) -> bool:
    print(f"\n=== {name} ===")
    print(" ".join(cmd))
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(SRC)}
    result = subprocess.run(cmd, cwd=cwd, env=env)
    ok = result.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test PASP autoresearch without agents")
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-dataset-eval", action="store_true")
    parser.add_argument("--skip-cycle", action="store_true")
    args = parser.parse_args(argv)

    results: list[tuple[str, bool]] = []

    if not args.skip_pytest:
        ok = run_step(
            "pytest autoresearch suite",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/dsp_lab/test_pasp_dataset_evaluation.py",
                "tests/dsp_lab/test_pasp_autoresearch_loop.py",
                "tests/dsp_lab/test_pasp_llm_planner.py",
                "tests/dsp_lab/test_pasp_experiment_memory.py",
                "tests/dsp_lab/test_pasp_active_learning.py",
                "tests/dsp_lab/test_pasp_model_governance.py",
                "-q",
            ],
        )
        results.append(("pytest", ok))

    if not args.skip_render:
        with tempfile.TemporaryDirectory() as tmp:
            out_wav = Path(tmp) / "smoke_note.wav"
            ok = run_step(
                "PASP note render",
                [
                    sys.executable,
                    "examples/run_pasp_note_example.py",
                    "--graph",
                    "examples/graphs/pasp_single_note_sound.json",
                    "--out",
                    str(out_wav),
                ],
            )
            results.append(("render", ok and out_wav.is_file() and out_wav.stat().st_size > 0))

    if not args.skip_dataset_eval:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "eval"
            ok = run_step(
                "tiny dataset eval",
                [
                    sys.executable,
                    "examples/run_pasp_dataset_eval.py",
                    "--dataset",
                    "data/evaluation/datasets/test_phrase_eval_tiny.json",
                    "--graph",
                    "examples/graphs/pasp_performance_model_base.json",
                    "--out",
                    str(out_dir),
                ],
            )
            has_summary = (out_dir / "summary.json").is_file()
            results.append(("dataset_eval", ok and has_summary))

    if not args.skip_cycle:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            out_autoresearch = tmp_root / "autoresearch"
            config = {
                "schema_version": 1,
                "name": "smoke_cycle",
                "baseline_eval": str(ROOT / "tests/fixtures/autoresearch/baseline_eval"),
                "dataset_manifest": str(ROOT / "data/evaluation/datasets/test_phrase_eval_tiny.json"),
                "base_model_graph": str(ROOT / "examples/graphs/pasp_performance_model_base.json"),
                "output_dir": str(out_autoresearch),
                "max_clusters_per_cycle": 1,
                "selection_policy": {
                    "primary": "highest_severity",
                    "secondary": "largest_regression_or_loss",
                    "prefer_unresolved": True,
                    "avoid_recently_failed": False,
                    "allow_reference_missing_clusters": False,
                },
                "allowed_subsystems": ["hammer/felt", "bridge/body"],
                "calibration": {
                    "max_trials": 5,
                    "time_budget_s": 60,
                    "strict_physical_bounds": True,
                    "allow_arbitrary_eq": False,
                    "allow_output_compression": False,
                    "optimizer": "random_search",
                },
                "decision_policy": {
                    "require_target_cluster_improvement": True,
                    "max_allowed_global_regression": 0.02,
                    "max_new_critical_failures": 0,
                    "require_physical_plausibility_non_worse": True,
                    "human_review_on_ambiguous": True,
                },
                "journal": {
                    "path": str(out_autoresearch / "research_journal.md"),
                    "jsonl_path": str(out_autoresearch / "research_journal.jsonl"),
                    "append": True,
                },
                "planner": {"enabled": True, "mode": "template", "max_proposals": 2},
                "memory": {"enabled": False},
                "active_learning": {"enabled": False},
                "governance": {"enabled": False},
            }
            import json

            cfg_path = tmp_root / "smoke_cycle.json"
            cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            ok = run_step(
                "plan-only autoresearch cycle",
                [
                    sys.executable,
                    "examples/run_pasp_autoresearch_cycle.py",
                    "--config",
                    str(cfg_path),
                    "--plan-only",
                    "--no-memory",
                ],
            )
            cycle_dirs = list(out_autoresearch.glob("pasp_cycle_*"))
            has_report = any((d / "agent_cycle_report.json").is_file() for d in cycle_dirs)
            results.append(("plan_only_cycle", ok and has_report))

    print("\n=== Summary ===")
    all_ok = True
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
        if not ok:
            all_ok = False

    if not results:
        print("No steps run (all skipped).")
        return 0
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
