"""Prepara una exportación YOLO de Roboflow para detectar lápices y cuadernos."""
import argparse
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import yaml


CLASSES = ("pencil", "notebook")
SPLITS = {"train": "train", "val": "valid", "test": "test"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def detection_box(values):
    if not all(0 <= v <= 1 for v in values):
        raise ValueError("coordenada fuera del rango [0, 1]")
    if len(values) == 4:
        x, y, w, h = values
    elif len(values) >= 6 and len(values) % 2 == 0:
        xs, ys = values[::2], values[1::2]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        x, y = min(xs) + w / 2, min(ys) + h / 2
    else:
        raise ValueError("se esperaba una caja YOLO o un polígono")
    if w <= 0 or h <= 0:
        raise ValueError("caja sin área")
    return x, y, w, h


def prepare(archive: Path, output: Path, reviewed_negatives: set[str] | None = None):
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"El destino ya existe: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as zip_file, TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp) / "dataset"
        configs = [entry for entry in zip_file.infolist() if entry.filename == "data.yaml"]
        if not configs or len({zip_file.read(entry) for entry in configs}) != 1:
            raise ValueError("Se esperaba una sola configuración data.yaml en la raíz del ZIP.")
        source = yaml.safe_load(zip_file.read(configs[0]))
        names = source["names"]
        if isinstance(names, list):
            names = dict(enumerate(names))
        ids = {int(i): str(name).strip().lower() for i, name in names.items()}
        if any(list(ids.values()).count(name) != 1 for name in CLASSES):
            raise ValueError("El ZIP debe contener las clases pencil y notebook.")
        remap = {i: CLASSES.index(name) for i, name in ids.items() if name in CLASSES}
        selected_negatives = set()
        report = {}
        for split, directory in SPLITS.items():
            images_dir, labels_dir = stage / directory / "images", stage / directory / "labels"
            images_dir.mkdir(parents=True)
            labels_dir.mkdir()
            counts = Counter()
            seen_labels = set()
            image_count = negatives = polygons = 0
            for entry in zip_file.infolist():
                image = PurePosixPath(entry.filename)
                if image.parts[:-1] != (directory, "images") or image.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                label = image.with_suffix(".txt").name
                if "\\" in image.name or ":" in image.name or label.casefold() in seen_labels:
                    raise ValueError(f"Nombre de imagen no válido o repetido: {entry.filename}")
                seen_labels.add(label.casefold())
                annotations = zip_file.read(f"{directory}/labels/{label}").decode("utf-8-sig")
                rows = []
                for number, row in enumerate(annotations.splitlines(), 1):
                    fields = row.split()
                    if not fields:
                        continue
                    try:
                        source_id = int(fields[0])
                        if source_id not in ids:
                            raise ValueError(f"clase desconocida {source_id}")
                        if source_id not in remap:
                            continue
                        class_id = remap[source_id]
                        box = detection_box([float(v) for v in fields[1:]])
                    except ValueError as exc:
                        raise ValueError(f"{directory}/labels/{label}, línea {number}: {exc}") from exc
                    rows.append(f"{class_id} " + " ".join(f"{v:.10g}" for v in box) + "\n")
                    counts[CLASSES[class_id]] += 1
                    polygons += len(fields) > 5
                if split == "train" and not rows and reviewed_negatives is not None:
                    if image.name not in reviewed_negatives:
                        continue
                    selected_negatives.add(image.name)
                (images_dir / image.name).write_bytes(zip_file.read(entry))
                (labels_dir / label).write_text("".join(rows), encoding="utf-8")
                image_count += 1
                negatives += not rows
            if any(counts[name] == 0 for name in CLASSES):
                raise ValueError(f"{directory}: faltan ejemplos de lápiz o cuaderno.")
            report[split] = {"images": image_count, "background_images": negatives,
                             "boxes": dict(counts), "polygons_converted": polygons}

        if reviewed_negatives is not None and selected_negatives != reviewed_negatives:
            missing = ", ".join(sorted(reviewed_negatives - selected_negatives))
            raise ValueError(f"No se encontraron como negativos de entrenamiento: {missing}")

        data = {"path": output.as_posix(), **{key: f"{value}/images" for key, value in SPLITS.items()},
                "names": dict(enumerate(CLASSES)), "roboflow": source.get("roboflow", {})}
        (stage / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        (stage / "counts.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        stage.rename(output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ZIP de Roboflow en formato YOLO")
    parser.add_argument("output", type=Path, help="directorio nuevo para el dataset de dos clases")
    parser.add_argument("--reviewed-negatives", type=Path, metavar="TXT",
                        help="conserva solo los negativos de entrenamiento listados por nombre de archivo")
    args = parser.parse_args()
    reviewed = None
    if args.reviewed_negatives is not None:
        reviewed = {line.strip() for line in args.reviewed_negatives.read_text(encoding="utf-8-sig").splitlines()
                    if line.strip()}
    print(json.dumps(prepare(args.archive, args.output, reviewed), indent=2))
