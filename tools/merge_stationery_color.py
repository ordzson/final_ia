"""Combina exportaciones YOLO de School supplies y detector_de_utiles."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import yaml

from prepare_stationery import detection_box, IMAGE_EXTENSIONS, SPLITS


CLASSES = ("pencil", "notebook", "pen")
ALIASES = {"pencil": "pencil", "notebook": "notebook", "cuaderno": "notebook",
           "pen": "pen", "lapicero": "pen"}


def merge(archives, output):
    output = output.resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sources = []
    seen = set()
    report = {}
    with TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp) / "dataset"
        # Prioriza la evaluación cuando aparece la misma imagen en dos particiones.
        for split, folder in reversed(SPLITS.items()):
            image_dir, label_dir = stage / folder / "images", stage / folder / "labels"
            image_dir.mkdir(parents=True)
            label_dir.mkdir()
            counts = Counter()
            images = negatives = duplicates = 0
            for source_number, archive in enumerate(archives):
                with ZipFile(archive) as z:
                    config = yaml.safe_load(z.read("data.yaml"))
                    if split == "test":
                        sources.append(config.get("roboflow", {}))
                    names = config["names"]
                    if isinstance(names, list):
                        names = dict(enumerate(names))
                    classes = {int(i): ALIASES.get(str(name).strip().lower()) for i, name in names.items()}
                    for member in z.infolist():
                        path = PurePosixPath(member.filename)
                        if path.parts[:-1] != (folder, "images") or path.suffix.lower() not in IMAGE_EXTENSIONS:
                            continue
                        label = path.with_suffix(".txt").name
                        rows = []
                        for line in z.read(f"{folder}/labels/{label}").decode("utf-8-sig").splitlines():
                            fields = line.split()
                            if not fields:
                                continue
                            key = classes[int(fields[0])]
                            if key is None:
                                continue
                            box = detection_box([float(value) for value in fields[1:]])
                            rows.append((key, box))
                        image = z.read(member)
                        digest = sha256(image).hexdigest()
                        if digest in seen:
                            duplicates += 1
                            continue
                        seen.add(digest)
                        stem = f"{source_number}_{digest[:24]}"
                        (image_dir / (stem + path.suffix.lower())).write_bytes(image)
                        lines = [f"{CLASSES.index(key)} " + " ".join(f"{v:.10g}" for v in box)
                                 for key, box in rows]
                        (label_dir / (stem + ".txt")).write_text("\n".join(lines), encoding="utf-8")
                        counts.update(key for key, _ in rows)
                        images += 1
                        negatives += not rows
            if any(counts[name] == 0 for name in CLASSES):
                raise ValueError(f"Faltan ejemplos de una clase en {split}.")
            report[split] = {"images": images, "background_images": negatives,
                             "boxes": dict(counts), "duplicates_removed": duplicates}
        data = {"path": output.as_posix(), **{split: f"{folder}/images" for split, folder in SPLITS.items()},
                "names": dict(enumerate(CLASSES)), "sources": sources}
        (stage / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        (stage / "counts.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        stage.rename(output)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("archives", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps(merge(args.archives, args.output), indent=2))
