#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
if [ ! -x .venv/bin/python ]; then
    echo "La carpeta .venv existente no contiene un entorno Linux. Conserva o renombra ese entorno antes de ejecutar setup.sh." >&2
    exit 1
fi
.venv/bin/python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 'Se necesita Python 3.12.')"
if [ ! -f requirements.lock.txt ]; then
    echo "Falta requirements.lock.txt: no se puede reproducir el entorno Linux verificado." >&2
    exit 1
fi
# Comprueba los pins CPU y conserva la version exacta de OpenCV tras limpiar variantes.
opencv_requirement=$(.venv/bin/python - <<'PY'
from pathlib import Path

lines = Path("requirements.lock.txt").read_text(encoding="utf-8-sig").splitlines()
for name in ("torch", "torchvision", "opencv-contrib-python-headless"):
    pins = [line.strip() for line in lines if line.startswith(name + "==")]
    if len(pins) != 1 or (name != "opencv-contrib-python-headless" and not pins[0].endswith("+cpu")):
        raise SystemExit(f"requirements.lock.txt necesita un pin exacto para {name} (CPU en PyTorch).")
    if name == "opencv-contrib-python-headless":
        print(pins[0])
PY
)
# Constraints fija las dependencias de Plan A sin instalar extras historicos como CLIP.
# Los pins +cpu requieren el indice adicional; las demas dependencias vienen de PyPI.
.venv/bin/python -m pip install --extra-index-url https://download.pytorch.org/whl/cpu \
    -c requirements.lock.txt -r requirements.txt torch torchvision "$opencv_requirement"
# ultralytics y mediapipe arrastran variantes de OpenCV con plugins Qt que chocan con PySide6
.venv/bin/python -m pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless
.venv/bin/python -m pip install "$opencv_requirement"
.venv/bin/python -c "import cv2, mediapipe, ultralytics, openvino, PySide6; print('Dependencias OK')"
