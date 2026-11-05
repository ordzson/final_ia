#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --upgrade pip
# PyTorch CPU: evita bajar ~3 GB de librerías CUDA (no hay GPU NVIDIA)
.venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
# ultralytics y mediapipe arrastran variantes de OpenCV con plugins Qt que chocan con PySide6
.venv/bin/pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless || true
.venv/bin/pip install opencv-contrib-python-headless
.venv/bin/pip freeze > requirements.lock.txt
