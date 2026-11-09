"""Instala VisionAI con PyTorch CUDA 12.6 en Windows o Linux (Python 3.12)."""
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import venv

ROOT = Path(__file__).resolve().parent


def main():
    if sys.version_info[:2] != (3, 12) or struct.calcsize("P") != 8:
        raise SystemExit("Ejecuta este instalador con Python 3.12 de 64 bits.")
    os.chdir(ROOT)
    env = ROOT / ".venv"
    if not env.exists():
        venv.create(env, with_pip=True)
    python = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.is_file():
        raise SystemExit(".venv pertenece a otro sistema. Renómbrala y vuelve a ejecutar el instalador.")

    def run(*args):
        subprocess.run([str(python), *args], check=True)

    run("-c", "import sys; assert sys.version_info[:2] == (3, 12), 'Se necesita Python 3.12'")
    lock = ROOT / ("requirements.windows.lock.txt" if sys.platform == "win32" else "requirements.lock.txt")
    # Conserva las dependencias del proyecto sin imponer las ruedas +cpu del lock.
    lines = [line for line in lock.read_text(encoding="utf-8-sig").splitlines()
             if not line.startswith(("torch==", "torchvision==", "clip @"))]
    opencv = next(line for line in lines if line.startswith("opencv-contrib-python-headless=="))
    run("-m", "pip", "install", "--upgrade", "pip")
    run("-m", "pip", "install", "--upgrade", "torch", "torchvision",
        "--index-url", "https://download.pytorch.org/whl/cu126")
    with tempfile.TemporaryDirectory(dir=env) as directory:
        constraints = Path(directory) / "cuda-constraints.txt"
        constraints.write_text("\n".join(lines) + "\n", encoding="utf-8")
        run("-m", "pip", "install", "-c", str(constraints), "-r", "requirements.txt", opencv)
    run("-m", "pip", "uninstall", "-y", "opencv-python", "opencv-contrib-python",
        "opencv-python-headless", "opencv-contrib-python-headless")
    run("-m", "pip", "install", opencv)
    run("-c", "import torch; assert torch.cuda.is_available(), "
        "'CUDA no disponible: instala o actualiza el controlador NVIDIA y reinicia'; "
        "x=torch.ones(32, device='cuda'); print('CUDA OK:', torch.cuda.get_device_name(0), x.sum().item())")
    run("tools/check_gpu.py")
    print("Instalación CUDA lista. Ejecuta app.py --device cuda --quality accurate --half")


if __name__ == "__main__":
    main()
