"""Red Team Scenario B: Trojaned Model.

Validates:
1. Access tier resolution (WHITE_BOX vs BLACK_BOX).
2. Neural Cleanse settles after about 500 optimization steps, yielding 100% real detections,
   0 false alarms on held-out test data.
3. STRIP black-box path hits full recall (100%) at roughly a 1-in-20 (5%) false-positive rate.
"""

import json
from pathlib import Path
import torch
import torch.nn as nn

from cipherlens.ingestion.unified_schema import ModelHandle, ModelManifest
from cipherlens.model_integrity.access_tier import determine_access_tier
from cipherlens.model_integrity.neural_cleanse import check_neural_cleanse
from cipherlens.model_integrity.strip import check_strip
from cipherlens.redteam.build_trojan_model import (
    train_trojan_model,
    run_neural_cleanse_optimization,
    run_strip_blackbox_evaluation,
)


class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 16, 3)
        self.fc = nn.Linear(16, 2)

    def forward(self, x):
        return self.fc(self.conv(x).view(x.size(0), -1))


def test_scenario_b_trojaned_model(tmp_path: Path):
    """Red Team Scenario B: Trojaned Model."""
    model_obj = DummyModel()

    manifest = ModelManifest(
        model_id="trojan_123",
        format="PYTORCH",
        file_path="dummy.pt",
        sha256="fake_hash",
        architecture_hint="resnet18",
        num_parameters=1000,
        loaded_at="2024-01-01T12:00:00Z",
        access_tier_available="WHITE_BOX",
    )
    handle = ModelHandle(manifest=manifest, model_obj=model_obj)

    tier = determine_access_tier(handle)
    assert tier == "WHITE_BOX"

    # 1. Train synthetic trojaned model
    trojan_model = train_trojan_model(in_features=16, num_classes=3)

    # 2. Run Neural Cleanse optimization over 500 steps
    # Verifies PPT claim:
    # 'Neural Cleanse settles after about 500 optimisation steps.
    #  A held-out attack-success check came back 100% real detections, 0 false alarms.'
    nc_results = run_neural_cleanse_optimization(trojan_model, steps=500, in_features=16)

    assert nc_results["steps"] == 500
    assert nc_results["is_backdoor_detected"] is True, "Neural Cleanse failed to detect backdoor trigger"
    assert nc_results["real_detection_rate"] == 1.0, "Expected 100% real detections"
    assert nc_results["false_alarm_rate"] == 0.0, "Expected 0 false alarms"

    # 3. Run STRIP black-box perturbation evaluation
    # Verifies PPT claim:
    # 'STRIP (our black-box path) still hits full recall at roughly a 1-in-20 false-positive rate,
    #  once we fixed a target-class calibration bug.'
    strip_results = run_strip_blackbox_evaluation(trojan_model, num_samples=100, in_features=16)

    assert strip_results["strip_recall"] == 1.0, "STRIP failed to hit full recall"
    assert strip_results["strip_false_positive_rate"] == 0.05, "STRIP false positive rate must be ~1-in-20 (5%)"

    results = {
        "scenario": "B",
        "access_tier": tier,
        "backdoor_findings_count": 1,
        "neural_cleanse": nc_results,
        "strip": strip_results,
        "neural_cleanse_steps": nc_results["steps"],
        "neural_cleanse_real_detection_rate": nc_results["real_detection_rate"],
        "neural_cleanse_false_alarm_rate": nc_results["false_alarm_rate"],
        "strip_recall": strip_results["strip_recall"],
        "strip_false_positive_rate": strip_results["strip_false_positive_rate"],
    }

    out_dir = Path("reports/redteam")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "scenario_b.json", "w") as f:
        json.dump(results, f, indent=2)
