"""Prueba los índices de cámara 0-5 y guarda un frame de cada uno que entregue imagen."""
from pathlib import Path

import cv2

OUT = Path(__file__).resolve().parent / "out"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i in range(6):
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        opened = cap.isOpened()
        ok, frame = cap.read() if opened else (False, None)
        # Las primeras lecturas pueden salir oscuras mientras la cámara ajusta la exposición
        for _ in range(10):
            if not ok:
                break
            ok, frame = cap.read()
        cap.release()
        if ok and frame is not None:
            h, w = frame.shape[:2]
            path = OUT / f"cam_{i}.jpg"
            cv2.imwrite(str(path), frame)
            print(f"[{i}] abrió=sí  frame=sí  {w}x{h}  brillo={frame.mean():.1f}  -> {path.name}")
        else:
            print(f"[{i}] abrió={'sí' if opened else 'no'}  frame=no")


if __name__ == "__main__":
    main()
