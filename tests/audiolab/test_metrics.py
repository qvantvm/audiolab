import numpy as np

from audiolab.audio.metrics import compare_audio


def test_metrics_run_on_simple_audio():
    sr = 22050
    t = np.arange(sr // 4) / sr
    a = 0.1 * np.sin(2 * np.pi * 440 * t)
    b = 0.1 * np.sin(2 * np.pi * 441 * t)
    metrics = compare_audio(a, b, sr)
    assert metrics["duration_difference"] == 0.0
    assert "rms_difference" in metrics
