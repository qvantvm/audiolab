# CLI

Use `python -m audiolab.cli` or the `audiolab` console script.

Commands: `validate`, `render`, `compare`, `report`, `run-experiment`, `list-blocks`, and `inspect-block`.

There is no separate `calibrate` subcommand yet. Run calibration via Python:

```bash
python examples/run_calibration_example.py
```

Or:

```python
from audiolab.experiments.calibration import run_calibration_cycle
run_calibration_cycle("examples/graphs/calibration_minimal_c4.json", out_dir="out/cal")
```

See [calibration.md](calibration.md) for tunable paths, optimizers, and artifacts.
