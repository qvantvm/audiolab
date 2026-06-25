from pathlib import Path

from audiolab.cli import main


ROOT = Path(__file__).resolve().parents[2]


def test_cli_validate_works():
    assert main(["validate", str(ROOT / "examples/graphs/sine_test.json")]) == 0


def test_cli_render_works(tmp_path: Path):
    out = tmp_path / "render.wav"
    probes = tmp_path / "probes.npz"
    assert main(["render", str(ROOT / "examples/graphs/sine_test.json"), "--out", str(out), "--probes", str(probes)]) == 0
    assert out.exists()
    assert probes.exists()
