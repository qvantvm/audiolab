"""Parallel execution helpers for CPU-bound DSP workloads."""

from __future__ import annotations

import os
from concurrent.futures import Executor, Future, ProcessPoolExecutor, as_completed
from typing import Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def _bootstrap_worker() -> None:
    import audiolab.blocks  # noqa: F401


def resolve_max_workers(max_workers: int | None, task_count: int) -> int:
    """Return worker count for ``task_count`` jobs (1 = sequential)."""
    if task_count <= 1:
        return 1
    if max_workers is not None and max_workers <= 0:
        return 1
    cap = max_workers if max_workers is not None else (os.cpu_count() or 1)
    return min(max(1, cap), task_count)


def resolve_trial_batch_size(
    trial_batch_size: int | None,
    max_workers: int | None,
    max_trials: int,
) -> int:
    """Default batch size matches worker cap when not set explicitly."""
    if trial_batch_size is not None and trial_batch_size > 0:
        return min(int(trial_batch_size), max_trials)
    workers = max_workers if max_workers is not None else (os.cpu_count() or 1)
    return max(1, min(workers, max_trials))


class ParallelWorkerPool:
    """Reusable process pool — avoids respawning workers on every parallel_map call."""

    def __init__(self, max_workers: int | None = None) -> None:
        self._requested = max_workers
        self._executor: ProcessPoolExecutor | None = None
        self._fallback = False

    def __enter__(self) -> ParallelWorkerPool:
        cap = self._requested if self._requested is not None else (os.cpu_count() or 1)
        workers = max(1, cap)
        try:
            self._executor = ProcessPoolExecutor(
                max_workers=workers,
                initializer=_bootstrap_worker,
            )
        except (NotImplementedError, OSError, PermissionError):
            self._fallback = True
        return self

    def __exit__(self, *args: object) -> None:
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None

    def map(
        self,
        fn: Callable[[T], R],
        items: list[T],
        *,
        on_complete: Callable[[], None] | None = None,
    ) -> list[R]:
        if not items:
            return []
        if self._fallback or self._executor is None:
            results: list[R] = []
            for item in items:
                results.append(fn(item))
                if on_complete is not None:
                    on_complete()
            return results

        futures: list[Future[R]] = [self._executor.submit(fn, item) for item in items]
        results: list[R] = []
        for future in as_completed(futures):
            results.append(future.result())
            if on_complete is not None:
                on_complete()
        return results


def parallel_map(
    fn: Callable[[T], R],
    items: list[T],
    *,
    max_workers: int | None = None,
    on_complete: Callable[[], None] | None = None,
    pool: ParallelWorkerPool | None = None,
) -> list[R]:
    """Map ``fn`` over ``items``; uses a process pool when workers > 1."""
    if pool is not None:
        return pool.map(fn, items, on_complete=on_complete)

    workers = resolve_max_workers(max_workers, len(items))
    if workers <= 1:
        results: list[R] = []
        for item in items:
            results.append(fn(item))
            if on_complete is not None:
                on_complete()
        return results
    try:
        with ProcessPoolExecutor(max_workers=workers, initializer=_bootstrap_worker) as executor:
            futures = [executor.submit(fn, item) for item in items]
            results: list[R] = []
            for future in as_completed(futures):
                results.append(future.result())
                if on_complete is not None:
                    on_complete()
            return results
    except (NotImplementedError, OSError, PermissionError):
        results = []
        for item in items:
            results.append(fn(item))
            if on_complete is not None:
                on_complete()
        return results


def parallel_map_ordered(
    fn: Callable[[T], R],
    items: list[T],
    *,
    max_workers: int | None = None,
    on_complete: Callable[[], None] | None = None,
    pool: ParallelWorkerPool | None = None,
) -> list[R]:
    """Like ``parallel_map`` but preserves input order in the result list."""
    if not items:
        return []
    if pool is not None:
        indexed_jobs = [(index, item) for index, item in enumerate(items)]
        indexed_results = pool.map(_indexed_apply, [(fn, pair) for pair in indexed_jobs], on_complete=on_complete)
        by_index = {index: result for index, result in indexed_results}
        return [by_index[i] for i in range(len(items))]

    workers = resolve_max_workers(max_workers, len(items))
    if workers <= 1:
        results: list[R] = []
        for item in items:
            results.append(fn(item))
            if on_complete is not None:
                on_complete()
        return results

    indexed_items = list(enumerate(items))
    try:
        with ProcessPoolExecutor(max_workers=workers, initializer=_bootstrap_worker) as executor:
            futures = [executor.submit(_indexed_apply, (fn, pair)) for pair in indexed_items]
            by_index: dict[int, R] = {}
            for future in as_completed(futures):
                index, result = future.result()
                by_index[index] = result
                if on_complete is not None:
                    on_complete()
            return [by_index[i] for i in range(len(items))]
    except (NotImplementedError, OSError, PermissionError):
        results = []
        for item in items:
            results.append(fn(item))
            if on_complete is not None:
                on_complete()
        return results


def _indexed_apply(payload: tuple[Callable[[T], R], tuple[int, T]]) -> tuple[int, R]:
    fn, (index, item) = payload
    return index, fn(item)
