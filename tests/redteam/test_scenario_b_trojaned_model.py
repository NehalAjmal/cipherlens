import json
import torch
import torch.nn as nn
from pathlib import Path

from cipherlens.model_integrity.access_tier import determine_access_tier
from cipherlens.model_integrity.strip import check_strip
from cipherlens.model_integrity.neural_cleanse import check_neural_cleanse
from cipherlens.ingestion.unified_schema import ModelHandle, ModelManifest

class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(3, 16, 3)
        self.fc = nn.Linear(16, 2)
    def forward(self, x):
        return self.fc(self.conv(x).view(x.size(0), -1))

def test_scenario_b_trojaned_model(tmp_path: Path):
    """Red Team Scenario B: Trojaned Model.
    
    Generates a dummy trojaned model (or simulates the execution of the integrity
    checks on a model) to ensure the runtime completes successfully and identifies
    the correct access tier (WHITE_BOX vs BLACK_BOX) and executes the sweeps.
    """
    model_obj = DummyModel()
    
    # We wrap it in a ModelHandle
    manifest = ModelManifest(
        model_id="trojan_123",
        format="PYTORCH",
        file_path="dummy.pt",
        sha256="fake_hash",
        architecture_hint="resnet18",
        num_parameters=1000,
        loaded_at="2024-01-01T12:00:00Z",
        access_tier_available="WHITE_BOX"
    )
    handle = ModelHandle(manifest=manifest, model_obj=model_obj)
    
    # Determine access tier (should be WHITE_BOX for PyTorch classification)
    tier = determine_access_tier(handle)
    
    findings = []
    if tier == "WHITE_BOX":
        # We run Neural Cleanse
        findings.extend(check_neural_cleanse(handle, access_tier=tier))
    else:
        findings.extend(check_strip(handle, access_tier=tier))
        
    nc_findings = [f for f in findings if f.category == "BACKDOOR_TRIGGER"]
    
    results = {
        "scenario": "B",
        "access_tier": tier,
        "backdoor_findings_count": len(nc_findings)
    }
    
    out_dir = Path("reports/redteam")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "scenario_b.json", "w") as f:
        json.dump(results, f)
        
    assert tier == "WHITE_BOX"
