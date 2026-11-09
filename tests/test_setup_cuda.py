"""Contrato del instalador CUDA sin descargar paquetes ni tocar el entorno real."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import setup_cuda


class SetupTests(unittest.TestCase):
    def test_filters_cpu_pins_and_checks_gpu_on_both_platforms(self):
        for platform in ("linux", "win32"):
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                executable = root / ".venv" / ("Scripts/python.exe" if platform == "win32" else "bin/python")
                executable.parent.mkdir(parents=True)
                executable.touch()
                lock = root / ("requirements.windows.lock.txt" if platform == "win32" else "requirements.lock.txt")
                lock_text = "torch==2.14.1+cpu\ntorchvision==0.29.1+cpu\nopencv-contrib-python-headless==5.0.0.93\nultralytics==8.4.183\nclip @ git+https://example.com/clip\n"
                lock.write_text(lock_text)
                calls = []

                def record(command, check):
                    self.assertTrue(check)
                    calls.append(command)
                    if "-c" in command and "-r" in command:
                        constraints = Path(command[command.index("-c") + 1]).read_text()
                        self.assertNotIn("+cpu", constraints)
                        self.assertNotIn("clip @", constraints)
                        self.assertIn("ultralytics==8.4.183", constraints)

                with patch.object(setup_cuda, "ROOT", root), \
                     patch.object(setup_cuda.sys, "platform", platform), \
                     patch.object(setup_cuda.os, "chdir"), \
                     patch.object(setup_cuda.subprocess, "run", side_effect=record):
                    setup_cuda.main()
                cuda_install = next(call for call in calls if "torchvision" in call)
                self.assertIn("https://download.pytorch.org/whl/cu126", cuda_install)
                self.assertEqual(calls[-1][-1], "tools/check_gpu.py")
                self.assertTrue(any("torch.cuda.is_available()" in arg for call in calls for arg in call))
                self.assertEqual(lock.read_text(), lock_text)


if __name__ == "__main__":
    unittest.main()
