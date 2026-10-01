"""Unified schema definitions for the ingestion layer.

Defines the stable in-memory representations for datasets, models,
and inference logs as specified in BACKEND_SCHEMA.md §2 and §3.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class AcquisitionMeta:
    """Metadata about data acquisition."""
    timestamp: str | None = None
    sensor: str | None = None
    notes: str | None = None


@dataclass
class Annotation:
    """A single object bounding box / segmentation."""
    category_id: int
    category_name: str
    bbox_xywh: list[float]
    segmentation: list[list[float]] | None = None


@dataclass
class DatasetItem:
    """A single image and its annotations, mapped from COCO/YOLO."""
    item_id: str
    image_path: str
    image_sha256: str
    width: int
    height: int
    annotations: list[Annotation]
    contributor_id: str
    batch_id: str
    source_format: str
    acquisition_meta: AcquisitionMeta


@dataclass
class ModelManifest:
    """Metadata for a loaded model, persisting exactly BACKEND_SCHEMA.md §3."""
    model_id: str
    format: str  # PYTORCH | ONNX
    file_path: str
    sha256: str
    architecture_hint: str
    num_parameters: int | None
    loaded_at: str
    access_tier_available: str  # WHITE_BOX | BLACK_BOX


@dataclass
class ModelHandle:
    """Runtime wrapper around a loaded model and its manifest."""
    manifest: ModelManifest
    model_obj: Any  # The PyTorch model or ONNX InferenceSession


@dataclass
class InferenceRecord:
    """A single recorded inference event from logs."""
    record_id: str
    timestamp_utc: str
    image_path: str
    model_id: str
    config_hash: str
    outputs: list[Any]
