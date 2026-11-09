"""Comprueba ambos modelos en CUDA con imágenes sintéticas, sin cámara ni ventana."""
import argparse
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import torch
import config
from detector import Detector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--half", action="store_true")
    args = parser.parse_args()
    config.MODEL_PATH, config.IMGSZ = config.MODEL_PROFILES["accurate"]
    detector = Detector(config.STATIONERY_MODEL_PATH, device="cuda", half=args.half)
    try:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        groups = {"objetos", "personas", "rostros"}
        detector.detect(frame, 0.35, groups)
        torch.cuda.synchronize()
        start = time.perf_counter()
        for _ in range(20):
            detector.detect(frame, 0.35, groups)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - start
        print(f"GPU: {torch.cuda.get_device_name(0)} | PyTorch: {torch.__version__} | CUDA: {torch.version.cuda}")
        print(f"Ambos YOLO + rostros OK: {20 / elapsed:.1f} inferencias/s con imagen sintética.")
        print("Esta medición no incluye cámara ni interfaz y no evalúa precisión.")
    finally:
        detector.face.close()


if __name__ == "__main__":
    main()
