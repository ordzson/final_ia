"""Genera world_custom.pt (YOLOv8s-World v2 con vocabulario propio) y lo exporta a OpenVINO.

Ejecutar desde models/:  ../.venv/bin/python ../tools/make_world.py
"""
from ultralytics import YOLO

VOCAB = ["person", "backpack", "spiral notebook", "book", "laptop", "pen", "cell phone", "desk", "chair", "bottle"]


def main() -> None:
    model = YOLO("yolov8s-worldv2.pt")
    model.set_classes(VOCAB)
    model.save("world_custom.pt")

    YOLO("world_custom.pt").export(format="openvino", imgsz=640)

    names = YOLO("world_custom_openvino_model", task="detect").names
    print("names:", names)
    missing = set(VOCAB) - set(names.values())
    assert not missing, f"Faltan clases en el modelo exportado: {missing}"
    print("OK")


if __name__ == "__main__":
    main()
