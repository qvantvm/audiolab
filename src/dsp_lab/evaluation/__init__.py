"""Dataset-scale PASP phrase evaluation."""

from dsp_lab.evaluation.batch_runner import run_dataset_evaluation
from dsp_lab.evaluation.dataset_manifest import DatasetManifest, DatasetItem

__all__ = ["DatasetItem", "DatasetManifest", "run_dataset_evaluation"]
