"""Configuration loader for CipherLens.

Loads default.yaml into strictly typed Pydantic models.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel


class ExecutionConfig(BaseModel):
    parallel: bool = True
    device: str = "cpu"


class ThresholdsConfig(BaseModel):
    spectral_signature_iqr_multiplier: float = 1.5
    dedup_cosine_distance_max: float = 0.02
    neural_cleanse_anomaly_index_min: float = 2.0
    strip_perturbation_grid: int = 10
    mmd_kernel_bandwidths: list[float] = [1.0, 2.0, 4.0, 8.0, 16.0]
    energy_ood_temperature: float = 1.0


class DispositionConfig(BaseModel):
    severity_weight: dict[str, int] = {
        "INFO": 0,
        "LOW": 1,
        "MEDIUM": 3,
        "HIGH": 7,
        "CRITICAL": 15,
    }
    review_threshold: int = 5
    quarantine_threshold: int = 12
    critical_override_confidence: float = 0.9


class LedgerConfig(BaseModel):
    checkpoint_every_n_entries: int = 25
    db_path: str = "reports/ledger.sqlite3"


class PathsConfig(BaseModel):
    backbone_cache: str = "models_cache/backbone/"
    reports_dir: str = "reports/assurance/"


class CipherLensConfig(BaseModel):
    execution: ExecutionConfig
    thresholds: ThresholdsConfig
    disposition: DispositionConfig
    ledger: LedgerConfig
    paths: PathsConfig

    @classmethod
    def load(cls, config_path: str | Path = "configs/default.yaml") -> "CipherLensConfig":
        """Load configuration from a YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found at {path}")
            
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if not data:
            data = {}
            
        return cls(**data)


# Global singleton config
_CONFIG = None

def get_config() -> CipherLensConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = CipherLensConfig.load()
    return _CONFIG
