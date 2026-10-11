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
    signature: str | None = None
    public_key: str | None = None
    raw_dict: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        d = {
            "record_id": self.record_id,
            "timestamp_utc": self.timestamp_utc,
            "image_path": self.image_path,
            "model_id": self.model_id,
            "config_hash": self.config_hash,
            "outputs": self.outputs,
        }
        if self.signature is not None:
            d["signature"] = self.signature
        if self.public_key is not None:
            d["public_key"] = self.public_key
        return d

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access helper."""
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like item access."""
        if hasattr(self, key):
            return getattr(self, key)
        if key == "timestamp":
            return self.timestamp_utc
        raise KeyError(key)
