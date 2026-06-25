"""Agent-facing audio comparison wrapper."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from audiolab.audio.io import load_wav
from audiolab.audio.metrics.compare import compare_audio as _compare_audio_arrays


@dataclass
class CompareResult:
    candidate_wav: str
    reference_wav: str
    sample_rate: int
    peak_candidate: float
    peak_reference: float
    rms_candidate: float
    rms_reference: float
    crest_factor_candidate: float
    crest_factor_reference: float
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _crest_factor(audio) -> float:
    import numpy as np

    arr = np.asarray(audio, dtype=np.float64)
    if arr.size == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(arr**2)))
    peak = float(np.max(np.abs(arr)))
    return float(peak / rms) if rms > 1e-12 else 0.0


def compare_audio(
    candidate_wav: str,
    reference_wav: str,
    output_json_path: str | None = None,
) -> CompareResult:
    """Compare two WAV files and return JSON-serializable metrics."""
    candidate, candidate_sr = load_wav(candidate_wav)
    reference, reference_sr = load_wav(reference_wav)
    if candidate_sr != reference_sr:
        raise ValueError(f"Sample rates differ: candidate={candidate_sr}, reference={reference_sr}")

    import numpy as np

    metrics = _compare_audio_arrays(reference, candidate, candidate_sr)
    result = CompareResult(
        candidate_wav=str(Path(candidate_wav).resolve()),
        reference_wav=str(Path(reference_wav).resolve()),
        sample_rate=int(candidate_sr),
        peak_candidate=float(np.max(np.abs(candidate))) if candidate.size else 0.0,
        peak_reference=float(np.max(np.abs(reference))) if reference.size else 0.0,
        rms_candidate=float(np.sqrt(np.mean(candidate**2))) if candidate.size else 0.0,
        rms_reference=float(np.sqrt(np.mean(reference**2))) if reference.size else 0.0,
        crest_factor_candidate=_crest_factor(candidate),
        crest_factor_reference=_crest_factor(reference),
        metrics=metrics,
    )
    if output_json_path:
        out = Path(output_json_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as handle:
            json.dump(result.to_dict(), handle, indent=2, sort_keys=True)
    return result


compare_audio_files = compare_audio
