#!/usr/bin/env python3
"""Download reference backbone (ResNet-18 or MobileNetV3) for CipherLens.

This is a ONE-TIME setup script that requires internet access.
It downloads pretrained weights from PyTorch Hub and caches them locally.
Nothing inside cipherlens/ ever calls this script — it is run manually once.

Usage:
    python scripts/download_reference_backbone.py

See docs/HUMAN_TASKS.md §3 for details.
"""

# Placeholder — implementation in Phase 3 (data integrity module).
raise NotImplementedError(
    "Backbone download not yet implemented. See PLAN.md Phase 3."
)
