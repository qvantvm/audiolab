"""Automatic failure tagging for dataset evaluation items."""

from __future__ import annotations

from typing import Any

Severity = str  # info | warning | error | critical


def _safe_float(val: object) -> float | None:
    if val is None:
        return None
    if isinstance(val, dict):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def tag_failures(
    metrics: dict[str, Any],
    diagnostics: dict[str, Any],
    *,
    reference_missing: bool = False,
) -> list[dict[str, Any]]:
    tags: list[dict[str, Any]] = []

    def add(tag: str, severity: Severity, evidence: dict[str, Any]) -> None:
        tags.append({"tag": tag, "severity": severity, "evidence": evidence})

    if reference_missing:
        add("reference_missing", "warning", {"reference_wav": metrics.get("reference_wav", "")})

    if diagnostics.get("unstable_render_detected") or metrics.get("unstable_render_detected"):
        add("unstable_render", "critical", {"unstable_render_detected": True})

    if diagnostics.get("clipping_detected") or metrics.get("clipping_detected"):
        add("clipping", "error", {"clipping_detected": True})

    output_energy = float(metrics.get("output_energy", 0.0))
    if output_energy < 1e-8:
        add("silent_render", "critical", {"output_energy": output_energy})

    symp = float(metrics.get("sympathetic_energy_ratio", diagnostics.get("sympathetic_energy_ratio", 0.0)))
    if symp > 0.5 and output_energy > 1e-8:
        add("sympathetic_too_strong", "error", {"sympathetic_energy_ratio": symp})

    if metrics.get("polyphony_exceeded") or diagnostics.get("polyphony_exceeded"):
        add("polyphony_energy_explosion", "error", {"polyphony_exceeded": True})

    tail_err = _safe_float(metrics.get("tail_energy_error"))
    if tail_err is not None and tail_err > 0.35:
        add("bad_tail", "warning", {"tail_energy_error": tail_err})

    decay_tail = _safe_float(metrics.get("decay_tail_error"))
    if decay_tail is not None and decay_tail > 0.35:
        add("bad_tail", "warning", {"decay_tail_error": decay_tail})

    stft = _safe_float(metrics.get("multi_res_stft_loss"))
    if stft is not None and stft > 0.5:
        add("spectral_mismatch", "warning", {"multi_res_stft_loss": stft})

    envelope_err = _safe_float(metrics.get("rms_envelope_error"))
    if envelope_err is not None and envelope_err > 0.4:
        add("bad_attack", "warning", {"rms_envelope_error": envelope_err})

    release_err = _safe_float(metrics.get("release_timing_error"))
    if release_err is not None and release_err > 0.2:
        add("bad_release", "warning", {"release_timing_error": release_err})

    body_ratio = float(metrics.get("shared_body_energy_ratio", 0.0))
    if body_ratio > 5.0:
        add("body_energy_anomaly", "warning", {"shared_body_energy_ratio": body_ratio})

    per_voice = diagnostics.get("per_voice", [])
    if isinstance(per_voice, list):
        for voice in per_voice:
            if not isinstance(voice, dict):
                continue
            transitions = voice.get("state_transitions", [])
            states = [s for _, s in transitions] if transitions else []
            if voice.get("note_off_time_s") and states and states[-1] not in ("finished", "damped", "released"):
                add("note_never_finished", "error", {"voice_id": voice.get("voice_id")})
            if voice.get("note_off_time_s") and "released" not in states and "damped" not in states:
                add("voice_management_failure", "warning", {"voice_id": voice.get("voice_id")})

    item_tags = metrics.get("tags", diagnostics.get("tags", []))
    if isinstance(item_tags, list) and "repeated_note" in item_tags:
        if any(t.get("tag") == "voice_management_failure" for t in tags):
            add("repeated_note_failure", "warning", {"tags": item_tags})

    if "pedal" in str(metrics.get("pedal", diagnostics.get("pedal", {}))) or metrics.get("pedal_sustain_energy_ratio", 0) > 0.8:
        pedal_intervals = []
        pedal = diagnostics.get("pedal", {})
        if isinstance(pedal, dict):
            pedal_intervals = pedal.get("pedal_down_intervals", [])
        if pedal_intervals and any(t.get("tag") == "bad_tail" for t in tags):
            add("pedal_failure", "warning", {"pedal_down_intervals": pedal_intervals})

    low_err = _safe_float(metrics.get("low_band_energy_error"))
    if low_err is not None and low_err > 0.4:
        add("low_frequency_error", "warning", {"low_band_energy_error": low_err})

    high_err = _safe_float(metrics.get("high_band_energy_error"))
    if high_err is not None and high_err > 0.4:
        add("high_frequency_error", "warning", {"high_band_energy_error": high_err})

    centroid_err = _safe_float(metrics.get("spectral_centroid_trajectory_error"))
    if centroid_err is not None:
        if centroid_err > 500:
            add("spectral_too_bright", "warning", {"spectral_centroid_trajectory_error": centroid_err})
        elif centroid_err < -500:
            add("spectral_too_dark", "warning", {"spectral_centroid_trajectory_error": centroid_err})

    for key in metrics:
        if key.endswith("_unavailable") or (
            isinstance(metrics.get(key), dict) and metrics[key].get("status") == "unavailable"
        ):
            add("metric_unavailable", "info", {"metric": key})

    return tags


def has_critical_failure(tags: list[dict[str, Any]]) -> bool:
    return any(t.get("severity") == "critical" for t in tags)


def has_error_failure(tags: list[dict[str, Any]]) -> bool:
    return any(t.get("severity") in ("critical", "error") for t in tags)
