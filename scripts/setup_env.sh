#!/usr/bin/env bash
# CipherLens — Environment Setup (macOS / Linux)
# Usage: bash scripts/setup_env.sh
#
# Creates a Python virtual environment and installs all dependencies.
# Requires: Python 3.10–3.12 (see TRD.md §1). Python 3.13+ may have
# compatibility issues with ML dependencies (torch, numpy, etc.).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== CipherLens Environment Setup ==="
echo "Project root: $PROJECT_ROOT"

# Find a compatible Python (prefer 3.11, then 3.12, then 3.10, then generic python3)
find_python() {
    for candidate in python3.11 python3.12 python3.10 python3; do
        if command -v "$candidate" &> /dev/null; then
            local ver
            ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            local minor
            minor=$("$candidate" -c "import sys; print(sys.version_info.minor)")
            if [ "$minor" -ge 10 ] && [ "$minor" -le 12 ]; then
                echo "$candidate"
                return 0
            fi
        fi
    done
    return 1
}

PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
    PYTHON=$(find_python) || {
        echo "Error: No compatible Python 3.10–3.12 found."
        echo "Install Python 3.11 via Homebrew: brew install python@3.11"
        echo "Or set PYTHON=/path/to/python3.11 and re-run."
        exit 1
    }
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Using Python $PY_VERSION ($PYTHON)"

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR ..."
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate and install
echo "Installing dependencies ..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet

echo ""
echo "=== Setup complete ==="
echo "To activate the environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Quick verification:"
echo "  python -c 'import cipherlens; print(\"CipherLens OK\")'"
echo "  pytest"
