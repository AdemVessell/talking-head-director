#!/usr/bin/env bash
# Isolated Linux CPU install for this candidate.
# Creates a virtualenv and does not modify the system Python.
# Torch comes from the CPU wheel index so a CUDA build is not pulled in.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
venv="${THD_VENV:-$root/.venv}"
python3 -c 'import venv' 2>/dev/null || {
  echo "python3-venv is required (Debian/Ubuntu: apt install python3-venv)" >&2
  exit 1
}
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --upgrade pip
# stable-ts depends on torch and torchaudio with no upper bound. A plain resolve
# on 2026-11-10 replaced torch 2.8.0+cpu with torch 2.15.0+cu132. Pin both to the
# 2.8.0 CPU wheels, then install the other pins under that constraint.
cpu=https://download.pytorch.org/whl/cpu
"$venv/bin/python" -m pip install 'torch==2.8.0' 'torchaudio==2.8.0' --index-url "$cpu"
cat > "$venv/constraints-cpu.txt" << 'EOF'
torch==2.8.0+cpu
torchaudio==2.8.0+cpu
EOF
grep -v -E '^torch==' "$root/requirements.txt" > "$venv/requirements-notorch.txt"
"$venv/bin/python" -m pip install -c "$venv/constraints-cpu.txt" --extra-index-url "$cpu" -r "$venv/requirements-notorch.txt"
"$venv/bin/python" - << 'PY'
import torch
v = torch.__version__
print(f"torch {v}  cuda_available={torch.cuda.is_available()}")
if not v.startswith("2.8.0"):
    raise SystemExit(f"expected torch 2.8.0 CPU pin, got {v}")
PY
echo "THD_PYTHON=$venv/bin/python"
echo "Next: THD_PYTHON=$venv/bin/python $root/scripts/thd doctor"
