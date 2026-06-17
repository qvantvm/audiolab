"""Tests for parallel execution helpers."""

from __future__ import annotations

from dsp_lab.parallel import resolve_max_workers, resolve_trial_batch_size


def test_resolve_max_workers_sequential_for_single_task() -> None:
    assert resolve_max_workers(None, 1) == 1
    assert resolve_max_workers(8, 1) == 1


def test_resolve_max_workers_caps_at_task_count() -> None:
    assert resolve_max_workers(8, 3) == 3


def test_resolve_max_workers_zero_means_sequential() -> None:
    assert resolve_max_workers(0, 5) == 1


def test_resolve_trial_batch_size_explicit() -> None:
    assert resolve_trial_batch_size(3, 8, 40) == 3


def test_resolve_trial_batch_size_defaults_to_workers() -> None:
    assert resolve_trial_batch_size(None, 8, 40) == 8
    assert resolve_trial_batch_size(None, 8, 5) == 5
