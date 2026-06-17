"""Tests for calibration trial batching and progress."""

from __future__ import annotations

from pathlib import Path

import pytest

from dsp_lab.autoresearch.calibration_plan import run_phrase_targeted_calibration
from dsp_lab.progress import TaskProgress


@pytest.fixture
def minimal_graph() -> dict:
    return {
        "sample_rate": 48000,
        "duration": 1.0,
        "blocks": [
            {
                "id": "performance",
                "type": "PASPPerformanceModel",
                "params": {
                    "output_gain": 0.8,
                    "events": [{"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5}],
                },
            }
        ],
    }


def test_run_phrase_targeted_calibration_uses_trial_batches(
    minimal_graph: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    batch_sizes: list[int] = []

    def fake_batch(
        graph_dict,
        panel_rows,
        tunable_paths,
        trials,
        iter_nums,
        reference_root,
        performance_block_id,
        max_workers,
        pool=None,
    ):
        batch_sizes.append(len(trials))
        return [(iter_num, 0.5, trial) for iter_num, trial in zip(iter_nums, trials)]

    monkeypatch.setattr(
        "dsp_lab.autoresearch.calibration_plan._evaluate_trial_batch",
        fake_batch,
    )
    monkeypatch.setattr(
        "dsp_lab.autoresearch.calibration_plan._evaluate_phrase_panel",
        lambda *args, **kwargs: 1.0,
    )

    result = run_phrase_targeted_calibration(
        minimal_graph,
        [{"events": [{"time_s": 0.0, "type": "note_on", "note": 60, "velocity_norm": 0.5}], "wav_path": "ref.wav"}],
        [{"path": "blocks.performance.params.output_gain", "min": 0.5, "max": 1.0}],
        Path("/tmp"),
        max_iters=5,
        max_workers=4,
        trial_batch_size=2,
        show_progress=False,
    )

    assert len(result["log"]) == 6
    assert batch_sizes == [2, 2]
    assert result["trial_batch_size"] == 2


def test_task_progress_disabled_does_not_write() -> None:
    progress = TaskProgress("test", total=3, enabled=False)
    progress.update(1)
    progress.update(1)
    progress.close()
