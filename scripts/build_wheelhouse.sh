#!/usr/bin/env bash
# CipherLens — Build Offline Wheelhouse
#
# Downloads all pip dependencies into a local wheelhouse/ directory
# for offline/air-gapped installation.
#
# Usage:
#     bash scripts/build_wheelhouse.sh
#
# Then on the air-gapped machine:
#     pip install --no-index --find-links=wheelhouse/ -r requirements-lock.txt
#
# See docs/HUMAN_TASKS.md for full instructions.

# Placeholder — implementation in Phase 11 (final packaging).
echo "Error: Wheelhouse build not yet implemented. See PLAN.md Phase 11."
exit 1
