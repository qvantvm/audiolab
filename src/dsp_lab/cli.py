"""Command line interface for DSP Lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import dsp_lab.blocks  # noqa: F401 - bootstrap registry
from dsp_lab.audio.io import load_wav, save_wav
from dsp_lab.audio.metrics import compare_audio
from dsp_lab.experiments.reports import run_experiment, write_report
from dsp_lab.graph.executor import render_graph
from dsp_lab.graph.serialization import load_graph
from dsp_lab.graph.validator import validate_graph
from dsp_lab.blocks.registry import inspect_block, list_block_types


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dsp-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("graph")
    validate_parser.add_argument("--json", action="store_true")

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("graph")
    render_parser.add_argument("--out", required=True)
    render_parser.add_argument("--probes")

    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--real", required=True)
    compare_parser.add_argument("--synthetic", required=True)
    compare_parser.add_argument("--out", required=True)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--experiment", required=True)

    experiment_parser = subparsers.add_parser("run-experiment")
    experiment_parser.add_argument("--graph", required=True)
    experiment_parser.add_argument("--real")
    experiment_parser.add_argument("--out", required=True)

    subparsers.add_parser("list-blocks")
    inspect_parser = subparsers.add_parser("inspect-block")
    inspect_parser.add_argument("block_type")

    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return _cmd_validate(args)
        if args.command == "render":
            return _cmd_render(args)
        if args.command == "compare":
            return _cmd_compare(args)
        if args.command == "report":
            report = write_report(args.experiment)
            print(report)
            return 0
        if args.command == "run-experiment":
            print(json.dumps(run_experiment(args.graph, args.real, args.out), indent=2, sort_keys=True))
            return 0
        if args.command == "list-blocks":
            current_category = None
            block_types = sorted(list_block_types(), key=lambda item: (inspect_block(item)["category"], item))
            for block_type in block_types:
                info = inspect_block(block_type)
                if info["category"] != current_category:
                    current_category = info["category"]
                    print(f"\n{current_category}")
                print(f"  {block_type}: {info['description']}")
            return 0
        if args.command == "inspect-block":
            print(json.dumps(inspect_block(args.block_type), indent=2, sort_keys=True))
            return 0
    except Exception as exc:
        print(f"error: {exc}")
        return 1
    return 1


def _cmd_validate(args: argparse.Namespace) -> int:
    graph = load_graph(args.graph)
    result = validate_graph(graph)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        if result.valid:
            print("valid")
        for message in result.messages:
            location = ".".join(part for part in [message.block, message.port] if part)
            suffix = f" ({location})" if location else ""
            print(f"{message.level}: {message.code}: {message.message}{suffix}")
    return 0 if result.valid else 1


def _cmd_render(args: argparse.Namespace) -> int:
    graph = load_graph(args.graph)
    result = render_graph(graph)
    metadata = save_wav(args.out, result.audio, result.sample_rate)
    print(json.dumps(metadata, indent=2, sort_keys=True))
    if args.probes:
        Path(args.probes).parent.mkdir(parents=True, exist_ok=True)
        np.savez(args.probes, **{key.replace(".", "__"): value for key, value in result.probes.items()})
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    real, real_sr = load_wav(args.real)
    synthetic, synthetic_sr = load_wav(args.synthetic)
    if real_sr != synthetic_sr:
        raise ValueError(f"Sample rates differ: {real_sr} != {synthetic_sr}")
    metrics = compare_audio(real, synthetic, real_sr)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
