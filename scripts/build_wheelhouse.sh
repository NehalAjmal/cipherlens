#!/usr/bin/env bash
# CipherLens — Build Offline Wheelhouse
#
# Downloads all pip dependencies into a local wheelhouse/ directory
# for offline/air-gapped installation.

set -e

echo "Building CipherLens Offline Wheelhouse..."
mkdir -p wheelhouse

# We use the virtual environment's pip
source .venv/bin/activate || { echo "Please create and activate .venv first."; exit 1; }

# Download all required wheels into the wheelhouse directory
pip wheel --no-deps -r requirements-lock.txt -w wheelhouse/

echo "Wheelhouse successfully built at ./wheelhouse/"
echo "To install offline on the target air-gapped machine, run:"
echo "pip install --no-index --find-links=wheelhouse/ -r requirements-lock.txt"
