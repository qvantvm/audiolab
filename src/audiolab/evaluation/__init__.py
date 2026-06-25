"""Dataset-scale PASP phrase evaluation."""

from audiolab.evaluation.batch_runner import run_dataset_evaluation
from audiolab.evaluation.dataset_manifest import DatasetManifest, DatasetItem

__all__ = ["DatasetItem", "DatasetManifest", "run_dataset_evaluation"]
