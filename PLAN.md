# PLAN — VisionAI: Detector de Objetos en Tiempo Real

Documento maestro para instancias de Claude Code. Cada instancia ejecuta **una etapa**.
Léelo completo antes de tocar nada. Si algo aquí es ambiguo o resulta imposible, no improvises:
documenta el problema en `PROGRESO.md` y pregunta al usuario.

**Actualización autorizada — 2026-11-08:** el usuario pidió mejorar la detección y luego priorizó explícitamente distinguir laptop/cuaderno aunque bajen los FPS. Windows usa `accurate`: **YOLO26s 640 FP32**, conservando las 13 clases COCO de la app, BlazeFace y el puntaje. Linux conserva `detail`; `detail` 480 y `fast` 320 de YOLOv8n permanecen disponibles. La elección y sus limitaciones están en `VALIDACION_MODELO.md`; no hubo reentrenamiento. La meta de ≥15 FPS de la rúbrica sigue sin cumplirse con `accurate` (unos 3–4 FPS); esta prioridad temporal no cierra E5/E6 ni modifica el enunciado.

---

## 0. Cómo usar este plan

1. Lee este archivo completo y `PROGRESO.md`.
2. Ejecuta solo la etapa que el usuario te pidió ("Ejecuta la Etapa N de PLAN.md").
3. Comprueba en `PROGRESO.md` que las dependencias de tu etapa estén en estado `hecha`. Si no lo están, detente y avísale al usuario.
4. Al terminar:
   - Ejecuta **todos** los criterios de aceptación de tu etapa.
   - Actualiza `PROGRESO.md`: estado, fecha (AAAA-MM-DD), qué hiciste, mediciones, desviaciones del plan y problemas abiertos.
   - Marca `hecha` solo si todos los criterios pasan. Si alguno falla, marca `bloqueada` y explica por qué con la salida real del error.
5. No cambies las **Decisiones fijas** (sección 3) ni el alcance sin aprobación explícita del usuario.
6. Los pasos marcados **[USUARIO]** requieren al usuario: tú no puedes sostener objetos frente a la cámara, conectar hardware, ejecutar `sudo` ni mirar la pantalla en vivo. Pídeselos y espera su confirmación.
7. Tú no ves la cámara en vivo, pero puedes ver imágenes guardadas en disco con la herramienta Read. Todas las verificaciones visuales se hacen guardando PNG/JPG y leyéndolos.

---

## 1. Contexto del proyecto

Proyecto final de Visión por Computadora (Ingeniería en Sistemas, 9.º semestre), preparado para una demo en vivo de 15 minutos ante el docente. El contexto original mencionaba una entrega próxima y la Feria Académica de julio; no hay una fecha de entrega vigente confirmada en este registro.

### Requisitos del enunciado (resumen fiel)

- Aplicación con interfaz gráfica que abre la cámara, detecta objetos en tiempo real y dibuja **bounding boxes, etiqueta de clase y % de confianza** sobre el video.
- **Modo 1 — General:** personas, rostros, celulares, laptops, mochilas, libros, cuadernos y escritorios o mesas.
- **Modo 2 — "Listo para la Universidad":** suma puntos por cada objeto universitario visible, muestra el puntaje en tiempo real, un nivel y retroalimentación visual. Debe tener **al menos 4 objetos mapeados**. Tabla del enunciado:

  | Objeto   | Nivel asignado        | Puntos |
  |----------|-----------------------|--------|
  | Mochila  | Acceso a campus       | +10    |
  | Cuaderno | Alumno responsable    | +15    |
  | Libro    | Estudiante dedicado   | +20    |
  | Laptop   | Listo para el aula    | +25    |
  | Lapicero | Siempre preparado     | +5     |
  | Ninguno  | Aún no estás listo... | 0      |

- **Interfaz:** selector de modo, **botón de captura de pantalla**, **panel lateral de estadísticas de sesión** y controles para activar o desactivar cada tipo de detección.
- **≥ 15 FPS.** Interfaz moderna y atractiva, entendible por público no técnico.
- El equipo debe justificar el modelo elegido y explicar cómo funciona.

### Rúbrica

| Criterio | Puntos |
|---|---|
| Integración del modelo: bboxes, etiquetas y confianza | 30 |
| Modo universitario | 30 |
| Interfaz (≥ 15 FPS) | 30 |
| Demo | 10 |

Extra por feria: hasta 25 puntos (impacto visual, originalidad, FPS, poca luz, objetos parciales).

### Hecho clave que condiciona el diseño

**COCO-80**, el dataset con el que viene entrenado YOLOv8, **no tiene las clases cuaderno, lapicero ni rostro**. Sí tiene: `person`, `backpack`, `book`, `laptop`, `cell phone`, `dining table`, `chair` y `bottle`, entre otras. Por eso:

- **Rostros:** se detectan con un modelo aparte (MediaPipe).
- **Cuaderno y lapicero:** la Etapa 0 decide entre **Plan A** (solo COCO) y **Plan B** (YOLO-World con vocabulario propio). Ver la sección 3.1.

---

## 2. Entorno actual y referencia histórica

### Windows actual (verificado el 2026-11-07)

- Esta copia es un repositorio Git y está en `C:\Users\Ozzca\OneDrive\Documentos\IA\final_ia`.
- Python 3.12 de 64 bits en `.venv\Scripts\python.exe`; usa `-m pip` con ese intérprete. `setup.ps1` instala las versiones de `requirements.windows.lock.txt`.
- Hardware Windows confirmado el 2026-11-08: **AMD Ryzen 7 3700U**, 4 núcleos/8 hilos, batería al 100 % y cargador conectado. El plan de energía estaba en **Equilibrado**; no se modificó.
- Cámara integrada **Hy-FHD(B550)-Camera**, índice **1**, mediante **DirectShow**. El índice 0 no abre en este equipo; MSMF no está disponible en la rueda OpenCV instalada. Los índices pueden variar en otro equipo.
- Los permisos de cámara y aplicaciones de escritorio estaban habilitados y no se cambiaron.
- La línea base Windows fue General **7.5 FPS** y Universitario **9.3 FPS** a 1280×720. Consulta las mediciones posteriores de `PROGRESO.md`; los FPS Linux no acreditan el rendimiento Windows.
- Diagnóstico Windows del 2026-11-08: la captura 1280×720 entrega unos **10 FPS** aunque el driver acepte pedir 30. Pedir 960×540 devuelve 640×480 a unos **30 FPS**. Bajar la captura a VGA con modelo 480 dejó General **7.52 FPS** y Uni **8.25 FPS**; la inferencia de unos **100–125 ms** sigue siendo el principal coste. No confundir FPS de cámara con FPS de detección completa.
- Se conservan los perfiles YOLOv8n `detail` 480 y `fast` 320 FP32. La mejora posterior agrega `accurate` YOLO26s 640, predeterminado Windows para priorizar reconocimiento. Los resultados y fallos por vista constan en `VALIDACION_MODELO.md`; Linux conserva `detail`.
- Windows captura 640×480 por defecto; Linux conserva 1280×720. `--resolution` permite elegir explícitamente una de esas dos resoluciones, independiente del tamaño de entrada del detector.
- Comandos actuales: `.\.venv\Scripts\python.exe app.py --camera 1` y `.\.venv\Scripts\python.exe tests\test_scoring.py`.
- Los ejemplos Bash y las rutas `.venv/bin/` del plan corresponden al procedimiento Linux. En PowerShell usa el intérprete Windows indicado arriba. Las herramientas `tools/cam_check.py`, `tools/bench.py` y `tools/live_check.py` todavía usan V4L2 y son exclusivas de Linux.

### Linux histórico (verificado el 2026-10-20)

- Linux (kernel 6.14), sesión **X11** (`DISPLAY=:0`).
- Python 3.12.3, `git` y `curl` disponibles, 40 GB libres.
- Estas condiciones corresponden al equipo Linux original, antes de trasladar la copia al repositorio actual.
- CPU **Intel Core i5-1235U** (12 hilos), iGPU Iris Xe, 23 GB de RAM.
  - **No hay GPU NVIDIA, así que tampoco CUDA.** La inferencia corre en CPU con **OpenVINO**.
- **Cámara integrada:** Chicony Integrated Camera.
  - `/dev/video0` es la de captura (índice OpenCV 0).
  - `/dev/video1` es solo metadatos y no da imagen.
  - La cámara externa USB que usaremos en la demo suele aparecer como índice 2.
- Qt 6.5+ (PySide6) requiere `libxcb-cursor0` en X11. Su instalación formó parte de la Etapa 0; no es una dependencia de Windows.
- **Ruta del proyecto:** `/home/ordson/Documentos/Universidad/ia final`. Contiene un espacio, así que va **siempre entre comillas** en la shell.
- **Python en Linux:** usa `.venv/bin/python` y `.venv/bin/python -m pip` después de crear el entorno.
- No toques `.vscode/`.

### Restricciones del equipo (obligatorias)

El equipo Linux original tenía restricciones de red y navegación (referencia histórica: `/home/ordson/AGENTS.md`). En el entorno actual aplica las instrucciones disponibles y conserva estas restricciones del proyecto:

- **Nunca** modifiques, desactives ni evites DNS, `/etc/hosts`, proxies, VPN, políticas del navegador ni servicios del sistema.
- **Hugging Face está bloqueado.** Si una descarga necesita `huggingface.co` y falla, **no busques rodeos**: usa la alternativa del plan (Plan A).
- Fuentes de descarga previstas:
  - PyPI
  - `download.pytorch.org`
  - GitHub (pesos de Ultralytics y CLIP)
  - `openaipublic.azureedge.net` (pesos CLIP, solo Plan B)
  - `storage.googleapis.com` (modelo de rostros de MediaPipe)
  - `ultralytics.com` (imagen de prueba)

---

## 3. Decisiones fijas

| Tema | Decisión |
|---|---|
| Lenguaje | Python 3.12 en venv `.venv/` dentro del proyecto |
| Detector de objetos | Ultralytics **YOLO26s** COCO-80/OpenVINO en Windows `accurate`; YOLOv8n COCO/OpenVINO en los perfiles originales. No se activó Plan B |
| Rostros | **MediaPipe Tasks Face Detector**, modelo `blaze_face_short_range.tflite` |
| Interfaz | **PySide6** (Qt 6) |
| Dibujo de overlays | **QPainter** sobre `QImage`. Nunca `cv2.putText`, que no soporta tildes ni ñ |
| Captura de video | Windows: DirectShow (`CAP_DSHOW`), índice 1 verificado; respaldo MSMF solo si está disponible. Linux: `CAP_V4L2`; USB histórica en índice 2 |
| OpenCV instalado | **solo** `opencv-contrib-python-headless`. La versión con GUI trae plugins de Qt que chocan con PySide6 |
| PyTorch | variante **CPU** (`--index-url https://download.pytorch.org/whl/cpu`) para no bajar ~3 GB de CUDA |
| Perfiles COCO | `accurate`: YOLO26s 640, predeterminado Windows. `detail`: YOLOv8n 480, predeterminado Linux. `fast`: YOLOv8n 320. Todos FP32 y con las mismas 13 clases visibles; la calidad no mejora uniformemente |
| Bucle de video | Captura y dibujo en el hilo principal; detección en un `QThread`, con una sola inferencia en curso y descarte de resultados anteriores a un cambio de controles |
| Umbral "NIVEL UNIVERSITARIO" | puntaje **≥ 50** (aprobado por el usuario) |
| Idioma | Textos de la interfaz y comentarios en español; identificadores (variables, funciones, clases) en inglés |
| Espejo | El video se voltea horizontalmente (`cv2.flip(frame, 1)`) **antes** de detectar |

### 3.1 Plan A vs Plan B (lo decide la Etapa 0)

**Plan A — YOLOv8n COCO.** Es la opción por defecto y la segura.
- No existe la clase cuaderno: un cuaderno saldrá detectado como "Libro".
- El lapicero se reemplaza por **Celular ("Siempre conectado", +5)**. El docente cita `cell phone` como clase válida.
- Quedan 4 objetos universitarios y un puntaje máximo de 60.

**Plan B — YOLOv8s-World v2** (detector de vocabulario abierto: se le dicen en texto las clases a detectar).
- Cubre la tabla completa: cuaderno, lapicero, libro, laptop y mochila, con un puntaje máximo de 75.
- Suma originalidad para la feria.
- Solo se adopta si pasa los criterios de la Etapa 0.

### 3.2 Fuera de alcance (no hacer)

- Versión web o servidor
- Base de datos
- Tracking de objetos (ByteTrack, BoT-SORT)
- Docker
- Entrenamiento o fine-tuning
- Segmentación de silueta
- Empaquetado (.exe, AppImage)
- Frameworks de test (se usan `assert` planos)
- Más archivos o módulos que los listados en la sección 4

---

## 4. Estructura final del proyecto

```
ia final/
├── CLAUDE.md                 # puntero a este plan (ya existe)
├── PLAN.md                   # este archivo
├── PROGRESO.md               # bitácora de etapas (ya existe)
├── README.md                 # E5: instalación y ejecución para humanos
├── GUION_DEMO.md             # E6: guion de demo y defensa
├── setup.sh                  # E0: crea el venv, instala dependencias y ajusta OpenCV
├── setup.ps1                 # adaptación Windows; usa el lock de ese sistema
├── requirements.txt          # E0: dependencias de alto nivel
├── requirements.lock.txt     # snapshot Linux, usado como constraints del Plan A
├── requirements.windows.lock.txt # versiones comprobadas en Windows
├── config.py                 # E0: constantes (sección 6)
├── detector.py               # E1
├── scoring.py                # E2
├── app.py                    # E3 (modo general), E4 (modo universitario), E5 (pulido)
├── tests/
│   └── test_scoring.py       # E2
├── tools/                    # scripts de verificación (no se presentan)
│   ├── cam_check.py          # E0
│   ├── bench.py              # E0
│   ├── make_world.py         # E0 (solo si se prueba el Plan B)
│   ├── live_check.py         # E0
│   ├── detect_image.py       # E1
│   └── out/                  # imágenes y logs de salida
├── models/
│   ├── yolov8n.pt
│   ├── yolov8n_openvino_model/
│   ├── yolov8n_320_openvino_model/      # perfil fast, exportación separada FP32
│   ├── world_custom.pt                 # solo Plan B
│   ├── world_custom_openvino_model/    # solo Plan B
│   └── blaze_face_short_range.tflite
└── capturas/                 # capturas de pantalla de la app
```

---

## 5. Contrato entre módulos

Cumple estas firmas exactamente: hay etapas que se ejecutan en paralelo y dependen de ellas.

### `detector.py`

```python
from dataclasses import dataclass

@dataclass
class Det:
    key: str                         # nombre exacto de la clase en model.names (p. ej. "laptop") o config.FACE_KEY
    label: str                       # etiqueta en español (config.LABELS_ES[key] o config.FACE_LABEL)
    conf: float                      # 0..1
    box: tuple[int, int, int, int]   # x1, y1, x2, y2 en píxeles del frame, recortados a sus bordes
    group: str                       # "objetos" | "personas" | "rostros"

class Detector:
    def __init__(self) -> None:
        """Carga YOLO desde config.MODEL_PATH y el detector de rostros desde config.FACE_MODEL_PATH."""

    @property
    def available_keys(self) -> set[str]:
        """Claves de config.LABELS_ES que existen en model.names. No incluye FACE_KEY."""

    def detect(self, frame_bgr, conf: float, groups: set[str],
               only_keys: set[str] | None = None) -> list[Det]:
        """
        groups: subconjunto de {"objetos", "personas", "rostros"}.
        only_keys: si no es None, restringe las clases YOLO a esas claves (lo usa el modo universitario).
        - Clases YOLO a pedir: available_keys cuyo grupo esté en groups (∩ only_keys si se dio).
          El grupo es "personas" si key in config.PERSON_KEYS y "objetos" en otro caso.
        - Si esa lista queda vacía, NO se llama a YOLO. Nunca pases classes=[] ni classes=None.
        - Los rostros se detectan solo si "rostros" in groups.
        - Devuelve una lista sin orden garantizado. Nunca lanza excepción por un frame vacío.
        """
```

### `scoring.py`

Lógica pura. **No importa** Qt, cv2, ultralytics ni `detector.py`; solo `config`. Trabaja con claves (`str`), no con `Det`.

```python
class PresenceTracker:
    """Quita el parpadeo de las detecciones: un objeto cuenta como presente si se ve de forma estable."""

    def __init__(self, enter_s: float = config.PRESENCE_ENTER_S,
                 hold_s: float = config.PRESENCE_HOLD_S) -> None: ...

    def update(self, keys: set[str], now: float) -> tuple[set[str], set[str]]:
        """Devuelve (present, entered). entered = claves que pasaron de ausente a presente en esta llamada."""

    def reset(self) -> None: ...

@dataclass
class UniState:
    score: int                # suma de los puntos de los ítems guardados en la ronda
    max_score: int            # suma de puntos de los UNI_ITEMS disponibles en el modelo
    level_text: str           # título del ítem guardado con más puntos; config.NO_ITEMS_TEXT si no hay ninguno
    badge: bool               # score >= config.UNI_THRESHOLD
    present: list[str]        # claves presentes ahora, en el orden de config.UNI_ITEMS
    entered: list[str]        # claves que se guardaron en este frame, en el orden de config.UNI_ITEMS
    collected: list[str]      # claves guardadas en la ronda, en el orden de config.UNI_ITEMS
    phase: str                # "waiting" | "running" | "result"
    time_left: float          # segundos que quedan de la ronda; al terminar queda congelado
    result_left: float        # en "result", segundos hasta volver a 0; si no, 0

class UniScorer:
    def __init__(self, available_keys: set[str]) -> None:
        """Solo cuenta los ítems de config.UNI_ITEMS cuya clave esté en available_keys."""

    def update(self, keys: set[str], now: float) -> UniState: ...
    def reset(self) -> None: ...
```

**Algoritmo exacto de `PresenceTracker.update(keys, now)`:**

```
estado por clave: first (inicio de la racha) y last (última vez vista)
para cada k en keys:
    si k no tiene estado, o now - estado[k].last > hold_s:
        estado[k] = (first=now, last=now)      # comienza una racha nueva
    si no:
        estado[k].last = now
present = { k : now - last <= hold_s  y  last - first >= enter_s }
entered = present - present_anterior
present_anterior = present
borrar los estados con now - last > hold_s
return present, entered
```

**Reglas de puntaje:**
- Cada clave suma **una sola vez**: dos libros siguen siendo +20.
- `score` es la suma de los puntos de las claves **guardadas** en la ronda (ver abajo).

**Ronda del modo universitario** (cambio aprobado por el usuario el 2026-10-25; antes `score` era la suma de las claves presentes y bajaba al retirar un objeto):
- `waiting`: puntaje 0 y reloj en `UNI_ROUND_S`. La ronda arranca cuando **entra** una clave (`entered` del tracker). Las que siguen a la vista desde la ronda anterior no la arrancan, para que las rondas no se encadenen.
- `running`: cada clave presente se guarda en `collected` y no se pierde aunque se retire. Termina al guardar todas las disponibles (el tiempo restante queda congelado) o al cumplirse `UNI_ROUND_S` (lo que aparezca después no cuenta).
- `result`: puntaje congelado durante `UNI_RESULT_S`; luego vuelve a `waiting` con `collected` vacío.

---

## 6. Referencia de `config.py` (Etapa 0, con adaptaciones posteriores)

El Plan A quedó elegido en E0. El bloque siguiente conserva la referencia de configuración; no reemplaces con él los ajustes posteriores medidos de rendimiento. `config.py` y la evidencia en `PROGRESO.md` determinan los valores vigentes. Los perfiles `detail` y `fast` pertenecen al mismo Plan A; no actives además una variante Plan B sin autorización.

```python
"""Constantes del proyecto VisionAI. Única fuente de verdad para clases, puntos y umbrales."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- Modelos ---
# Los tres perfiles conservan las clases de la app y los puntos.
MODEL_PROFILES = {
    "accurate": (ROOT / "models" / "yolo26s_640_openvino_model", 640),
    "detail": (ROOT / "models" / "yolov8n_openvino_model", 480),
    "fast": (ROOT / "models" / "yolov8n_320_openvino_model", 320),
}
DEFAULT_QUALITY = "accurate" if sys.platform == "win32" else "detail"
MODEL_PATH, IMGSZ = MODEL_PROFILES[DEFAULT_QUALITY]
FACE_MODEL_PATH = ROOT / "models" / "blaze_face_short_range.tflite"
CONF_DEFAULT = 0.35
FACE_MIN_CONF = 0.5

# --- Cámara ---
CAMERA_INDEX_DEFAULT = 1 if sys.platform == "win32" else 2
FRAME_W, FRAME_H = (640, 480) if sys.platform == "win32" else (1280, 720)
MIRROR = True

# --- Clases: clave = nombre EXACTO en model.names → etiqueta en español ---
# Las claves que no existan en el modelo se ignoran solas (Detector.available_keys).
LABELS_ES = {
    "person": "Persona",
    "backpack": "Mochila",
    "handbag": "Bolso",
    "cell phone": "Celular",
    "laptop": "Laptop",
    "book": "Libro / Cuaderno",
    "dining table": "Mesa / Escritorio",
    "chair": "Silla",
    "bottle": "Botella",
    "cup": "Taza",
    "keyboard": "Teclado",
    "mouse": "Mouse",
    "scissors": "Tijeras",
    # Solo existen en Plan B (las claves deben ser idénticas a los textos usados en set_classes):
    "spiral notebook": "Cuaderno",
    "pen": "Lapicero",
    "desk": "Escritorio",
}
FACE_KEY = "face"
FACE_LABEL = "Rostro"
PERSON_KEYS = {"person"}  # grupo "personas"; el resto de LABELS_ES pertenece al grupo "objetos"

# --- Modo universitario: clave → (título de nivel, puntos). El orden define el orden de los chips. ---
# Plan A:
UNI_ITEMS = {
    "backpack": ("Acceso a campus", 10),
    "book": ("Estudiante dedicado", 20),
    "laptop": ("Listo para el aula", 25),
    "cell phone": ("Siempre conectado", 5),
}
# Plan B:
# UNI_ITEMS = {
#     "backpack": ("Acceso a campus", 10),
#     "spiral notebook": ("Alumno responsable", 15),
#     "book": ("Estudiante dedicado", 20),
#     "laptop": ("Listo para el aula", 25),
#     "pen": ("Siempre preparado", 5),
# }
UNI_THRESHOLD = 50
NO_ITEMS_TEXT = "Aún no estás listo..."
UNI_BADGE_TEXT = "NIVEL UNIVERSITARIO"
UNI_ROUND_S = 60          # ronda: segundos para mostrar todos los objetos (agregado 2026-10-25)
UNI_RESULT_S = 5          # segundos que se muestra el resultado antes de volver a 0

# --- Antiparpadeo ---
PRESENCE_ENTER_S = 0.3    # tiempo visible de forma estable para contar como presente
PRESENCE_HOLD_S = 0.7     # tiempo que sigue contando como presente tras dejar de verse

# --- Poca luz ---
LOW_LIGHT_MEAN = 60       # brillo medio en gris (0-255) por debajo del cual se avisa

# --- Colores (hex) ---
COLORS = {"personas": "#4f8cff", "rostros": "#ff5fa2", "objetos": "#3ddc97", "uni": "#ffc94d"}
THEME = {
    "bg": "#0f1220", "panel": "#171a2b", "accent": "#4f8cff",
    "gold": "#ffc94d", "text": "#e8eaf6", "muted": "#8a90b3",
}

CAPTURES_DIR = ROOT / "capturas"
```

Si en el Plan B la Etapa 0 elige otros textos de vocabulario (por ejemplo `"notebook"` en lugar de `"spiral notebook"`), cámbialos en `LABELS_ES` y `UNI_ITEMS` para que coincidan **exactamente** con `model.names`.

---

## 7. Etapas

```
E0 ──► E1 ─┐
   └─► E2 ─┴─► E3 ──► E4 ──► E5 ──► E6
```

- E1 y E2 se pueden ejecutar **en paralelo** en dos instancias distintas: tocan archivos diferentes y ambas dependen solo de `config.py`.
- Calendario objetivo:
  - **Día 1:** E0, E1, E2
  - **Día 2:** E3, E4
  - **Día 3:** E5, E6

---

### Etapa 0 — Entorno, modelos y decisión Plan A/B

**Depende de:** nada.
**Requiere al usuario:** sí (instalar el paquete con sudo y sostener objetos frente a la cámara).
**Crea:** `setup.sh`, `requirements.txt`, `requirements.lock.txt`, `config.py`, `models/*`, `tools/cam_check.py`, `tools/bench.py`, `tools/live_check.py` y, si se prueba el Plan B, `tools/make_world.py`.

**Pasos:**

1. **[USUARIO]** Pide al usuario que ejecute `sudo apt install libxcb-cursor0` y espera su confirmación. Sin ese paquete PySide6 no abre ventanas.

2. Crea `requirements.txt`:
   ```
   ultralytics
   openvino
   mediapipe
   PySide6
   ```

3. **Instalación por sistema:** usa `setup.ps1` en Windows y `setup.sh` en Linux. Los instaladores crean o reutilizan `.venv`, usan PyTorch CPU y dejan una sola variante OpenCV (`opencv-contrib-python-headless`).
   - Windows instala `requirements.windows.lock.txt` cuando existe.
   - Linux usa `requirements.lock.txt` como [constraints de pip](https://pip.pypa.io/en/stable/user_guide/#constraints-files) de las dependencias de Plan A: fija sus versiones sin instalar CLIP ni extras descartados solo por estar en el freeze histórico. Usa el índice adicional CPU y reinstala headless con su versión exacta.
   - Los instaladores **no sobrescriben** los locks. Un cambio de versiones se registra después de comprobarlo y por separado para cada sistema.
   - `pip check` puede indicar que ultralytics requiere `opencv-python`: corresponde a la sustitución deliberada por la variante contrib headless. No ignores otros conflictos.

4. Verifica:
   ```bash
   .venv/bin/python -c "import cv2, mediapipe, ultralytics, openvino, PySide6; print(cv2.__version__, ultralytics.__version__, mediapipe.__version__, openvino.__version__, PySide6.__version__)"
   .venv/bin/python -c "import cv2; from PySide6.QtWidgets import QApplication, QLabel; a=QApplication([]); w=QLabel('ok'); w.show(); print('qt+cv2 ok')"
   .venv/bin/pip list 2>/dev/null | grep -i opencv   # debe mostrar SOLO opencv-contrib-python-headless
   ```
   - Si `mediapipe` no instala o no importa en Python 3.12: **detente**, documenta el error y pregunta al usuario. No cambies de librería por tu cuenta.
   - Si Qt se queja de plugins "xcb", prueba con `os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)` después de `import cv2`. Si funciona, anótalo en PROGRESO para que E3 lo aplique.

5. Descarga y exporta los modelos. Los siguientes son comandos **Bash/Linux**; consulta README para Windows. Ejecuta desde `models/` para que los pesos queden ahí:
   ```bash
   mkdir -p models && cd models
   ../.venv/bin/python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='openvino', imgsz=480)"
   curl -L -o blaze_face_short_range.tflite https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
   ```
   Debe quedar `models/yolov8n.pt`, `models/yolov8n_openvino_model/` (con `metadata.yaml`) y `models/blaze_face_short_range.tflite`. El tamaño de exportación debe coincidir con `config.IMGSZ`; E0 eligió 480.
   Después, vuelve a ejecutar la verificación de OpenCV del paso 4: un export puede autoinstalar paquetes.

6. Escribe `tools/cam_check.py`:
   - Prueba los índices 0 a 5 con `cv2.VideoCapture(i, cv2.CAP_V4L2)`.
   - Para cada uno imprime si abrió, si leyó un frame y su resolución.
   - Guarda `tools/out/cam_<i>.jpg` de cada índice que dé imagen.

   Ejecútalo y **mira las imágenes con Read** para confirmar que no salen negras. Si el usuario tiene la cámara externa, pídele **[USUARIO]** que la conecte y repite la prueba. Anota los índices en PROGRESO.

7. Escribe `tools/bench.py`:
   - Argumentos: `--camera IDX --frames 100 --model PATH [--imgsz 640]`.
   - Captura los frames desde la cámara.
   - Hace 5 inferencias de calentamiento y luego mide el promedio en ms de `model.predict(frame, imgsz=..., verbose=False)`.
   - Mide también el promedio de `detect_for_video` de MediaPipe sobre los mismos frames.
   - Imprime los ms promedio y los FPS equivalentes.

   Ejecútalo con `models/yolov8n.pt` y con `models/yolov8n_openvino_model` y anota los cuatro números. Si OpenVINO a 640 promedia más de 50 ms:
   - Re-exporta con `imgsz=480`, que sobreescribe la carpeta.
   - Vuelve a medir.
   - Si mejora, usa `IMGSZ = 480` en config.

8. Escribe `tools/live_check.py`:
   - Argumentos: `--model PATH --camera IDX --seconds 30 [--imgsz 640]`.
   - Corre la detección en vivo sin ventana.
   - Cada segundo escribe en `tools/out/live_<nombre_modelo>.txt` las clases detectadas con su confianza.
   - Cada 2 s guarda `tools/out/live_<nombre_modelo>_<NN>.jpg` usando `results[0].plot()` (aquí las etiquetas en inglés valen; es una herramienta de depuración).
   - Al final imprime el ms promedio de inferencia y, por clase, en cuántos segundos apareció.

9. **Prueba del Plan B.** Tiempo máximo: 30 minutos de tu trabajo. Si se pasa, adopta el Plan A.
   1. Escribe `tools/make_world.py`. Ejecútalo desde `models/`. Debe:
      - Cargar `YOLO("yolov8s-worldv2.pt")`, que se descarga solo.
      - Llamar a `set_classes(VOCAB)` con `VOCAB = ["person", "backpack", "spiral notebook", "book", "laptop", "pen", "cell phone", "desk", "chair", "bottle"]`.
      - Guardar con `save("world_custom.pt")`.
      - Cargar `YOLO("world_custom.pt")` y exportar con `export(format="openvino", imgsz=640)`, lo que genera `world_custom_openvino_model/`.
      - Comprobar que `YOLO("world_custom_openvino_model", task="detect").names` contiene el VOCAB.
      - Ultralytics instalará CLIP desde GitHub y bajará sus pesos. Si cualquier descarga falla (incluido un bloqueo de red), **adopta el Plan A** sin buscar alternativas.
      - Si el export a OpenVINO falla, puedes medir `world_custom.pt` directamente. Si da menos de 15 FPS, adopta el Plan A.
   2. **[USUARIO]** Pide al usuario que tenga a mano: mochila, libro, cuaderno, laptop, lapicero y celular, con buena luz y a unos 50–80 cm de la cámara. Dile que durante 30 s debe mostrar cada objeto unos 5 s, uno tras otro, y al final todos juntos. Espera su "listo".
   3. Ejecuta `tools/live_check.py` con `world_custom_openvino_model`.
   4. Repite la misma prueba con `yolov8n_openvino_model` para comparar: ahí deberían detectarse libro, laptop, mochila y celular.
   5. Revisa los logs y varias imágenes con Read.
   6. Si "spiral notebook" falla o se confunde con laptop o libro, puedes probar **una sola** variante: `"notebook"` o `"exercise book"`, y `"ballpoint pen"` para el lapicero. Regenera y repite.

10. **Criterios para adoptar el Plan B.** Deben cumplirse todos:
    - La inferencia promedio en OpenVINO es ≤ 55 ms.
    - El cuaderno aparece con su etiqueta correcta en la mayoría de los segundos en que se mostró.
    - El cuaderno no "roba" las detecciones de libro ni de laptop.
    - Mochila, libro y laptop siguen detectándose.
    - El lapicero **no** es requisito: es difícil de detectar. Si el cuaderno funciona, se adopta el Plan B aunque el lapicero falle, y se anota.
    - Si no se cumplen todos: **Plan A**.

11. Escribe `config.py` según la sección 6, con el Plan elegido, el `IMGSZ` final y `CAMERA_INDEX_DEFAULT` igual al índice que funcionó. Si el Plan B usó otros textos, cámbialos en LABELS_ES y UNI_ITEMS. Verifica con `.venv/bin/python -c "import config; print(config.MODEL_PATH, config.UNI_ITEMS)"`.

12. Completa la sección "Decisiones de Etapa 0" de `PROGRESO.md`.

**Criterios de aceptación de E0:**
- [ ] `./setup.sh` termina sin error. Los dos comandos de verificación del paso 4 imprimen OK. `pip list` muestra solo `opencv-contrib-python-headless`.
- [ ] Existen los archivos de modelo del Plan elegido y `blaze_face_short_range.tflite`.
- [ ] Al menos un índice de cámara entrega imagen real (verificada con Read).
- [ ] Benchmark anotado. El modelo elegido en OpenVINO promedia ≤ 66 ms (≥ 15 FPS de inferencia).
- [ ] Decisión A/B anotada con su justificación y los números.
- [ ] `import config` funciona y contiene una sola variante.

---

### Etapa 1 — `detector.py`

**Depende de:** E0.
**Requiere al usuario:** mínimo (estar frente a la cámara para la prueba de rostro).
**Crea:** `detector.py` y `tools/detect_image.py`.

**Pasos:**

1. Implementa `Det` y `Detector` según el contrato de la sección 5.
   - Carga el modelo con `YOLO(str(config.MODEL_PATH), task="detect")`.
   - Calcula `available_keys` y un mapa `clave → id` a partir de `model.names`.
   - Llamada a YOLO: `model.predict(frame_bgr, imgsz=config.IMGSZ, conf=conf, classes=ids, verbose=False, **predict_options)[0]`. Windows fija `device="intel:CPU"` y `torch.set_num_threads(1)`; Linux conserva su selección anterior. Calienta antes de consultar `model.names` para evitar una carga/compilación redundante. Estos ajustes no cambian clases ni puntaje.
   - Lee `r.boxes.xyxy`, `r.boxes.conf` y `r.boxes.cls` (pásalos a numpy con `.cpu().numpy()`).
   - Rostros con MediaPipe, en modo VIDEO (ver la sección 8). El timestamp en ms debe ser **estrictamente creciente**: usa `int(time.monotonic()*1000)` y, si no supera al anterior, súmale 1.
   - Recorta las cajas a los bordes del frame.
2. `tools/detect_image.py`:
   - Argumentos: `--image PATH` o `--camera IDX`; en ese caso toma un frame y lo voltea si `config.MIRROR`.
   - Ejecuta `Detector().detect(frame, config.CONF_DEFAULT, {"objetos", "personas", "rostros"})`.
   - Imprime cada `Det` y el tiempo total en ms.
   - Guarda `tools/out/detect_result.jpg` con rectángulos de cv2. Basta con imprimir `key` en ASCII, ya que es una herramienta de depuración.
3. Descarga la imagen de prueba: `curl -L -o tools/out/bus.jpg https://ultralytics.com/images/bus.jpg`.

**Criterios de aceptación de E1:**
- [ ] Con `tools/detect_image.py --image tools/out/bus.jpg` salen ≥ 3 `Det` con `key="person"` y `conf > 0.5`.
- [ ] **[USUARIO]** Con el usuario frente a la cámara, `--camera N` devuelve al menos un `Det` con `key="face"` y otro con `key="person"`. Revisa `detect_result.jpg` con Read.
- [ ] `detect(frame, 0.35, set())` devuelve `[]` sin llamar a YOLO ni lanzar errores.
- [ ] `detect(frame, 0.35, {"objetos"}, only_keys=set(config.UNI_ITEMS))` solo devuelve claves de UNI_ITEMS.
- [ ] Ninguna etiqueta queda en inglés: todo `Det.label` sale de LABELS_ES o FACE_LABEL.

---

### Etapa 2 — `scoring.py` y tests

**Depende de:** E0 (solo `config.py`). Se puede ejecutar en paralelo con E1.
**Requiere al usuario:** no.
**Crea:** `scoring.py` y `tests/test_scoring.py`.

**Pasos:**

1. Implementa `PresenceTracker`, `UniState` y `UniScorer` siguiendo exactamente la sección 5.
2. `tests/test_scoring.py`:
   - Se ejecuta con `.venv/bin/python tests/test_scoring.py`. Agrega la raíz del proyecto a `sys.path` al inicio.
   - Usa `assert` planos e imprime `OK` al final.
   - Construye los escenarios con tiempos simulados en pasos de 0.05 s y compara tiempos con margen: verifica en 0.25 s y en 0.35 s, no exactamente en 0.30 s.

   Casos obligatorios:
   1. Sin claves: score 0, `level_text == NO_ITEMS_TEXT`, `badge False`.
   2. "laptop" visto de forma continua desde t = 0: no está presente en t = 0.25 y sí en t = 0.35. `entered` del scorer contiene "laptop" **una sola vez por ronda**.
   3. Un hueco de 0.5 s sin verlo lo mantiene presente. Un hueco de 0.8 s lo vuelve ausente, y al reaparecer necesita otros 0.3 s.
   4. "backpack", "book" y "laptop" presentes: score 55, `badge True`, `level_text == "Listo para el aula"`.
   5. `max_score` es la suma de los puntos de los UNI_ITEMS que están en `available_keys`. Pruébalo con un `available_keys` reducido.
   6. Una clave que no está en `available_keys` no suma.
   7. `reset()` deja todo en cero.
   8. La ronda acumula objetos aunque se retiren, finaliza al cumplirse 60 s o reunir todos, conserva el resultado 5 s y evita encadenar rondas por objetos que siguen visibles. Los objetos que entran después del minuto no suman a la ronda terminada.

**Criterios de aceptación de E2:**
- [ ] `.venv/bin/python tests/test_scoring.py` imprime `OK`.
- [ ] `grep -E "import (cv2|PySide6|ultralytics)|from (PySide6|ultralytics|detector)" scoring.py` no devuelve nada.

---

### Etapa 3 — `app.py`: ventana y modo General

**Depende de:** E1 y E2.
**Requiere al usuario:** sí (estar frente a la cámara; prueba manual de los controles).
**Crea:** `app.py`.

**Diseño de la ventana:**

```
┌──────────────────────────────────────────────────────────────┬────────────────┐
│ VisionAI   Cámara [Cámara 0 ▾]   [ General | Universitario ] │  SESIÓN        │
│ [✓] Objetos [✓] Personas [✓] Rostros  Confianza [──●──] 35%  │  FPS  24.3     │
│                                   [Capturar] [Reiniciar]     │  Tiempo 03:12  │
├──────────────────────────────────────────────────────────────┤  Modo General  │
│                                                              │  EN PANTALLA   │
│                     VIDEO (QLabel)                           │  Persona 92%   │
│              boxes + etiqueta + % (QPainter)                 │  Laptop  81%   │
│                                                              │  APARICIONES   │
│                                                              │  Persona   3   │
│                                                              │  Capturas  2   │
└──────────────────────────────────────────────────────────────┴────────────────┘
 barra de estado: "Captura guardada: capturas/20261021_101530.png"
```

**Especificación:**

- **Ventana:** `QMainWindow`, título `"VisionAI — Detector de Objetos en Tiempo Real"`, tamaño inicial 1440×860 y mínimo 1100×700.
- **Fila de controles:**
  - **Selector de cámara:** `QComboBox`. Un `--camera N` explícito abre esa cámara directamente. Sin el argumento usa `CAMERA_INDEX_DEFAULT` o una disponible si no abre. Al desplegar la lista vuelve a buscar índices 0–5 y lista los que entregan imagen como `"Cámara N (ancho×alto)"`. Al cambiar de opción, libera la cámara actual y abre la nueva.
  - **Selector de modo:** dos `QPushButton` checables en un `QButtonGroup` exclusivo, con aspecto de botón segmentado.
  - **Interruptores:** `QCheckBox` Objetos, Personas y Rostros, todos activos por defecto.
  - **Confianza:** `QSlider` horizontal de 10 a 90, por defecto `CONF_DEFAULT*100`, con una etiqueta que muestra el %.
  - **Botones** `Capturar` y `Reiniciar`.
- **Apertura de cámara:**
  - Windows usa `cv2.VideoCapture(idx, cv2.CAP_DSHOW)`; MSMF solo sirve de respaldo si está disponible. Linux usa `cv2.CAP_V4L2`.
  - Configura `CAP_PROP_FOURCC` = MJPG, `FRAME_W`×`FRAME_H` y `CAP_PROP_BUFFERSIZE` = 1.
  - Si la cámara no soporta esa resolución, usa la que entregue.
- **Bucle:** `QTimer` preciso con intervalo de 1 ms. Si no hay una inferencia en curso:
  1. En el hilo de interfaz: `cap.read()` → `cv2.flip(frame, 1)` si `MIRROR`.
  2. Se envía un frame propio y una copia de los controles al worker `QThread`, que ejecuta `detector.detect`.
  3. Al recibir el resultado en la interfaz, se descarta si cambió la generación de controles. Se envía el siguiente trabajo antes de dibujar, sin acumular una cola.
  4. Se actualizan estadísticas y puntaje con el reloj actual, se convierte a `QImage` RGB32 y se dibuja con QPainter **a la resolución del frame**.
  5. Se muestra en el `QLabel` con `KeepAspectRatio` y se emite `frame_processed`; solo un resultado nuevo aceptado y dibujado cuenta para los FPS.
- **Dibujo en modo General:**
  - Escala de tamaños `s = alto_frame / 720`.
  - Rectángulo de 3·s px, del color de su grupo en `config.COLORS`.
  - Encima, una "píldora" rellena del mismo color con texto blanco en negrita de 16·s px: `"Mochila 87%"`. Si no cabe arriba, va dentro de la caja.
  - Antialiasing activado.
- **Panel lateral:** `QFrame` de 320 px de ancho. Se actualiza **cada 250 ms** con un QTimer propio, no en cada frame. Contiene:
  - FPS: media móvil exponencial con α = 0.1 sobre el tiempo entre resultados nuevos dibujados.
  - Tiempo de sesión en mm:ss.
  - Modo actual.
  - "En pantalla": detecciones actuales con su %, ordenadas por confianza, máximo 8.
  - "Apariciones en la sesión": etiqueta y conteo, de mayor a menor.
  - Número de capturas.
- **Capturar:**
  - Guarda la `QImage` ya dibujada, a resolución completa y sin escalar, en `config.CAPTURES_DIR / f"{AAAAMMDD_HHMMSS}.png"`. Crea la carpeta si no existe.
  - Muestra el mensaje en la barra de estado durante 3 s.
  - Suma 1 a "Capturas".
  - Activa un destello blanco con alfa de 180 a 0 durante 0.25 s, dibujado **después** de guardar para que no salga en el PNG.
- **Reiniciar:** pone en cero el tiempo de sesión, las apariciones, el mejor puntaje y las capturas, y resetea los trackers.
- **Atajos de teclado:**
  - `Espacio`: capturar
  - `M`: alternar modo
  - `R`: reiniciar
  - `Ctrl+Q`: salir
- **Sin cámara:** si no hay ninguna, o si `read()` falla 15 veces seguidas, dibuja en el área de video un mensaje centrado: `"Cámara no disponible — conecta una cámara o elige otra en el selector"`. La app no debe cerrarse.
- **Tema base:** QSS oscuro con los colores de `config.THEME`.
  - Botones con bordes redondeados de 8 px.
  - Panel con fondo `panel` y bordes de 12 px.
  - Botón de modo activo con color `accent`.
  - Este estilo se pule en E5.
- **Argumentos de línea de comandos** (`argparse`), para que los agentes puedan verificar:
  - `--camera N`: índice inicial.
  - `--mode general|uni`: modo inicial. En E3 basta con aceptar `general`; `uni` se implementa en E4.
  - `--quality accurate|detail|fast`: selecciona YOLO26s 640, YOLOv8n 480 o YOLOv8n 320. Conserva controles, las 13 clases visibles, rostros y puntaje. `accurate` prioriza distinguir cuaderno/laptop en Windows, con menor velocidad y sin garantizar mejora en cada clase.
  - `--resolution 640x480|1280x720`: resolución solicitada a la cámara, independiente de la entrada del modelo. El driver puede entregar otro tamaño; anotar el efectivo.
  - `--autoshot SEG`:
    - A los SEG segundos guarda `self.grab()` (la ventana completa) en `capturas/autoshot.png`.
    - Imprime en stdout `AUTOSHOT fps=<promedio> frames=<n> path=capturas/autoshot.png`. El promedio son los frames procesados después de los 2 primeros segundos divididos entre su tiempo.
    - Sale con código 0.

**Criterios de aceptación de E3:**
- [ ] `.venv/bin/python app.py --autoshot 8` sale con código 0 e imprime la línea AUTOSHOT con **fps ≥ 15**. Pide al usuario que se siente frente a la cámara.
- [ ] Al revisar `capturas/autoshot.png` con Read se ven: el video, cajas con etiquetas en español y %, el panel con FPS y listas, y todos los controles.
- [ ] **[USUARIO]** Prueba manual: cambiar de cámara funciona; cada interruptor oculta y muestra su grupo; el slider cambia la cantidad de detecciones; Capturar crea un PNG en `capturas/`; Reiniciar pone las estadísticas en cero; los atajos funcionan.
- [ ] Desconectar una cámara USB o elegir un índice no disponible muestra el mensaje y la app no se cierra. No uses el índice 1 como prueba de error en Windows: es la cámara integrada verificada.

---

### Etapa 4 — Modo "Listo para la Universidad"

**Depende de:** E3.
**Requiere al usuario:** sí (objetos frente a la cámara).
**Modifica:** `app.py`.

**Especificación:**

- **Al entrar al modo Universitario:**
  - Se llama a `uni_scorer.reset()`.
  - Los checkboxes Objetos, Personas y Rostros se **deshabilitan** con el tooltip `"Solo en modo General"`.
  - La detección es `detector.detect(frame, conf, {"objetos"}, only_keys=set(config.UNI_ITEMS))`: sin personas ni rostros, para ganar FPS.
- **En cada tick:** `state = uni_scorer.update({d.key for d in dets}, now)`. El mejor puntaje de la sesión es `max(best, state.score)`.
- **Cajas:** color `COLORS["uni"]`, con la píldora `"Laptop +25 · 87%"` (etiqueta, puntos y confianza).
- **HUD:** franja superior negra con alfa 160 y 120·s px de alto, dibujada con QPainter.
  - **Izquierda:** puntaje grande, `"55"` en negrita a 44·s px, con `"de 60 pts"` debajo en Plan A (usa `state.max_score`).
  - **Centro:** barra de progreso redondeada de ancho 50 % del frame y alto 18·s px.
    - El valor mostrado se anima con `disp += (score - disp) * 0.15` en cada frame.
    - Relleno `accent` si score < `UNI_THRESHOLD` y `gold` si es igual o mayor.
    - Debajo, `state.level_text` a 22·s px.
  - **Fila de chips:** uno por cada ítem de UNI_ITEMS disponible, `"Mochila +10"`. Encendido (fondo `gold`, texto oscuro) si está guardado en `state.collected`; apagado si aún no se guardó. Retirar el objeto no apaga su chip dentro de la ronda.
- **Badge:** si `state.badge`, se dibuja un rectángulo redondeado centrado en el tercio inferior del frame.
  - Fondo `gold`, texto oscuro `UNI_BADGE_TEXT` en negrita a 44·s px.
  - La opacidad pulsa: `alpha = 200 + 55*sin(t*4)`.
- **"+X pts" flotantes:**
  - Por cada clave en `state.entered`, se crea una animación anclada al centro superior de la caja `Det` de esa clave con mayor confianza.
  - Dura 1.0 s: el texto `"+25 pts"` sube 60·s px y su alfa baja de 255 a 0.
  - Va en `gold`, en negrita a 32·s px, con una sombra oscura desplazada 2 px.
  - Las animaciones vencidas se eliminan.
- **Panel lateral en este modo:** agrega "Puntaje actual", "Mejor puntaje de la sesión", "Tiempo de la ronda" e "Ítems guardados" con su título de nivel. La lista "En pantalla" refleja las detecciones actuales, separada de lo acumulado.
- `--mode uni` debe funcionar.

**Criterios de aceptación de E4:**
- [ ] `tests/test_scoring.py` sigue imprimiendo `OK`.
- [ ] **[USUARIO]** Sin objetos: `app.py --mode uni --autoshot 8` → en el PNG se ven `0`, `"Aún no estás listo..."`, todos los chips apagados y fps ≥ 15.
- [ ] **[USUARIO]** Con mochila, libro y laptop visibles, en el mismo comando el PNG muestra ≥ 55, `"Listo para el aula"`, el badge `NIVEL UNIVERSITARIO` y sus chips encendidos.
- [ ] **[USUARIO]** En vivo: al mostrar un objeto estable, el puntaje sube en menos de 1 s y aparece "+X pts". Al retirarlo, su caja y "En pantalla" se actualizan, mientras el puntaje y el chip guardado se mantienen. La barra se anima suave y la interfaz no parpadea. Comprobar fin por tiempo, fin al reunir los 4, resultado durante 5 s y siguiente ronda sin arranque automático por objetos heredados.

---

### Etapa 5 — Pulido, robustez y README

**Depende de:** E4.
**Requiere al usuario:** sí (checklist final).
**Modifica:** `app.py`. **Crea:** `README.md`.

**Pasos:**

1. **Poca luz:**
   - En cada frame, calcula el brillo medio de `cv2.cvtColor(cv2.resize(frame, (64, 36)), cv2.COLOR_BGR2GRAY)`.
   - Si se mantiene menor que `LOW_LIGHT_MEAN` durante más de 1 s, dibuja una franja inferior amarilla: `"Poca luz: la detección puede fallar. Acerca una lámpara."`.
   - En el panel, agrega un indicador "Luz: OK / Baja".
2. **Ajuste de FPS.** Mide con `--autoshot` en ambos modos y separa captura, inferencia y dibujo. No copies un ajuste Linux sin medirlo en Windows. Si alguno da menos de 15, evalúa estas medidas y detente cuando se cumpla con evidencia real:
   1. La exportación 480 ya fue elegida en E0. En Windows se compara con el perfil `fast` 320, exportado en carpeta separada y con los mismos pesos FP32. Verificar las clases, detecciones de referencia, objetos reales y FPS; no asumir que conserva la precisión para objetos pequeños ni activarlo por defecto sin esa validación.
   2. Medir captura a 640×480 y 1280×720 con `--resolution`; en esta cámara Windows pedir 960×540 entrega realmente 640×480. No modificar la resolución Linux basándose solo en ese resultado Windows.
   3. La detección ya se trasladó a un `QThread`, con un solo trabajo en curso. DirectShow conserva captura y cierre en el hilo de interfaz. Medir el resultado completo; un repintado no acredita una detección nueva.

   Anota cada medición en PROGRESO.
3. **Pulido visual del QSS:**
   - Tipografía del sistema a 11 pt.
   - Títulos del panel en `muted`, en mayúsculas y 9 pt.
   - Valores del panel a 14 pt en negrita.
   - Hover en los botones.
   - Slider con color `accent`.
   - Verifícalo con un autoshot. Nada de librerías de temas externas.
4. **`README.md`**, para humanos y en español:
   - Requisitos por sistema; `libxcb-cursor0` solo en Linux.
   - Instaladores `setup.ps1` (Windows) y `setup.sh` (Linux), con sus locks separados.
   - Cómo descargar o exportar los modelos (los comandos de E0).
   - `.\.venv\Scripts\python.exe app.py --camera 1` en Windows; `.venv/bin/python app.py [--camera N]` en Linux.
   - Atajos de teclado y descripción de los modos.
   - Problemas comunes: cámara equivocada, poca luz, error del plugin Qt xcb.
5. **[USUARIO]** Checklist final (anota el resultado):
   - Arranque en frío con la cámara del equipo de demo (integrada índice 1 en Windows; USB índice 2 en el equipo Linux histórico).
   - Ambos modos.
   - Cada interruptor.
   - Captura.
   - Reiniciar.
   - Poca luz (tapar parcialmente la cámara).
   - Objeto parcialmente fuera del cuadro.
   - Quitar y poner objetos rápido.
   - Desconectar y reconectar una cámara USB, si se dispone de ella. La integrada no se puede desenchufar físicamente: registra esta limitación, sin dar por hecha una prueba que no se realizó.
   - 10 minutos seguidos sin errores ni fuga de memoria evidente (revisa con `top`).

**Criterios de aceptación de E5:**
- [ ] FPS finales ≥ 15 en ambos modos, anotados en PROGRESO.
- [ ] Checklist final aprobado por el usuario.
- [ ] Siguiendo el README desde cero se llega a la app abierta.

---

### Etapa 6 — Preparación de la demo y defensa

**Depende de:** E5. El guion puede empezarse antes, pero se cierra con los datos reales de E5.
**Requiere al usuario:** sí (grabar el video de respaldo).
**Crea:** `GUION_DEMO.md`.

**Contenido de `GUION_DEMO.md`** (en español, para que lo lean los integrantes del equipo):

1. **Pitch de 5 minutos para público mixto (feria):** qué es, demo en vivo del modo General, demo del modo Universitario con los objetos entrando uno por uno hasta el badge, y cierre.
2. **Estructura de la demo de 15 minutos ante el docente**, con tiempos por bloque y quién habla. Deja los nombres como `[Integrante 1]`, etc.
3. **Preguntas y respuestas de defensa** usando los datos de la sección 9:
   - ¿Por qué YOLOv8n y no SSD o MediaPipe?
   - ¿Cómo funciona YOLO por dentro?
   - ¿Qué es OpenVINO y por qué se usa?
   - ¿Por qué MediaPipe para los rostros?
   - ¿Por qué no se detectan cuadernos y lapiceros (Plan A), o cómo se logró (Plan B, YOLO-World)?
   - ¿Qué hace el antiparpadeo?
   - ¿Cuáles son las limitaciones?
   - Incluye los FPS reales de PROGRESO.
4. **Checklist del día de la demo:**
   - Cámara externa y su índice.
   - Lámpara o aro de luz.
   - Kit de objetos.
   - Laptop cargada y con el cargador.
   - App abierta y probada 10 minutos antes.
   - Fondo despejado.
   - Video de respaldo listo para reproducir si falla la cámara.
5. **Instrucciones para grabar el video de respaldo** **[USUARIO]**: 2 a 3 minutos mostrando ambos modos. En Windows, el guion explica Xbox Game Bar y una alternativa con celular. SimpleScreenRecorder corresponde al equipo Linux histórico; no presupongas que hay GNOME, OBS u otro grabador instalado. El agente no graba ni da por grabado el video con una prueba automática.

**Criterios de aceptación de E6:**
- [ ] `GUION_DEMO.md` completo, con los FPS reales y el Plan (A o B) correctos.
- [ ] **[USUARIO]** Video de respaldo grabado y anotado en PROGRESO.

---

## 8. Notas técnicas y fragmentos de referencia

**YOLO con OpenVINO:**
```python
from ultralytics import YOLO
model = YOLO(str(config.MODEL_PATH), task="detect")
names = model.names                                    # dict[int, str]
r = model.predict(frame_bgr, imgsz=config.IMGSZ, conf=conf, classes=ids, verbose=False)[0]
xyxy = r.boxes.xyxy.cpu().numpy().astype(int)
confs = r.boxes.conf.cpu().numpy()
cls = r.boxes.cls.cpu().numpy().astype(int)
```

**MediaPipe Face Detector (Tasks API, modo VIDEO):**
```python
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

options = vision.FaceDetectorOptions(
    base_options=mp_tasks.BaseOptions(model_asset_path=str(config.FACE_MODEL_PATH)),
    running_mode=vision.RunningMode.VIDEO,
    min_detection_confidence=config.FACE_MIN_CONF,
)
face = vision.FaceDetector.create_from_options(options)
rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)        # contiguo; no uses frame[:, ::-1]
res = face.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts_ms)
for d in res.detections:
    b = d.bounding_box          # origin_x, origin_y, width, height (px)
    score = d.categories[0].score
```

**Frame → QImage → QPainter → QLabel:**
```python
rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
h, w, _ = rgb.shape
img = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()  # copy: no depender del buffer numpy
p = QPainter(img)
p.setRenderHint(QPainter.RenderHint.Antialiasing)
# ... dibujar cajas, píldoras, HUD ...
p.end()
video_label.setPixmap(QPixmap.fromImage(img).scaled(
    video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
```

Trampa: el `QLabel` del video necesita `setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)` y `setMinimumSize(640, 360)`. Si no, cada pixmap escalado agranda el layout y la ventana crece sin fin.

**Otros problemas conocidos:**
- `Could not load the Qt platform plugin "xcb"`: si es por xcb-cursor, falta `libxcb-cursor0` ([USUARIO], sudo). Si apunta a `cv2/qt/plugins`, quedó instalado un OpenCV no headless: vuelve a ejecutar `./setup.sh`.
- **Nunca** ejecutes `pip install ultralytics` (ni un upgrade) suelto sin volver a correr `./setup.sh`, porque reinstala `opencv-python`.
- Si un agente no tiene pantalla (`DISPLAY` vacío), puede verificar con `QT_QPA_PLATFORM=offscreen .venv/bin/python app.py --autoshot 8`.

---

## 9. Datos para la defensa (los usa E6)

**YOLOv8n (Ultralytics, 2023)**
- Detector de una sola etapa y sin anchors.
- Flujo interno:
   1. *Letterbox*: redimensiona a la entrada configurada manteniendo la proporción: 480 en `detail`, 320 en `fast`.
  2. *Backbone* CSPDarknet con bloques C2f.
  3. *Neck* PAN-FPN, que mezcla las 3 escalas.
   4. *Head* desacoplado, que predice cajas (DFL) y puntajes de clase en 3 escalas (strides 8/16/32 → **2100 candidatos** con entrada cuadrada 320; **4725** con 480; **8400** con 640).
  5. Filtro por confianza.
  6. NMS (IoU 0.7 por defecto en Ultralytics).
- Tamaño y precisión: 3.2 M parámetros, 8.7 GFLOPs, mAP50-95 de 37.3 en COCO val2017 (a 640).

**Comparación de modelos**
- **SSD MobileNet v2:** ~20–22 mAP en COCO. Es más rápido en móviles, pero bastante menos preciso.
- **MediaPipe:** excelente para rostros y manos, pero su detector de objetos genérico (EfficientDet-Lite) es menos preciso que YOLOv8.

**Decisión**
- YOLOv8n para objetos.
- MediaPipe BlazeFace para rostros: "BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs", Bazarevsky et al., 2019. Se necesita porque COCO no tiene la clase rostro.

**OpenVINO**
- Toolkit de Intel que optimiza el grafo del modelo para CPU y GPU Intel.
- El benchmark Linux de E0 obtuvo 26–28 ms a 480, frente a 31.1 ms con PyTorch; a 640 OpenVINO fue más lento. La entrada de 480 y el turbo también influyeron. No atribuyas a OpenVINO por sí solo el cumplimiento de 15 FPS ni traslades esos números al equipo Windows.

**YOLO-World (solo Plan B)**
- "YOLO-World: Real-Time Open-Vocabulary Object Detection", Cheng et al., CVPR 2024.
- Codifica el texto de cada clase con CLIP y lo fusiona con las características visuales (RepVL-PAN).
- Así detecta clases que no están en COCO (cuaderno, lapicero) sin reentrenar.

**Antiparpadeo**
- Un objeto cuenta como presente tras 0.3 s estable y deja de contar 0.7 s después de dejar de verse.
- Filtra entradas breves y mantiene la presencia durante huecos cortos. La ronda acumula puntos y no los resta al retirar objetos; esa conservación no es consecuencia del hold de 0.7 s.

Si hay acceso web, verifica estos números en la documentación oficial antes de cerrar E6. Si no, úsalos tal cual.

---

## 10. Mapa de requisitos → dónde se cumplen

| Requisito | Etapa |
|---|---|
| Cámara en tiempo real, bboxes, etiqueta y % | E1, E3 |
| Modo General con personas, rostros y objetos | E1, E3 |
| Interruptores por tipo de detección | E3 |
| Modo Universitario: ≥ 4 objetos, puntaje en vivo, nivel y retroalimentación | E2, E4 |
| Botón de captura de pantalla | E3 |
| Panel lateral de estadísticas de sesión | E3, E4 |
| ≥ 15 FPS | E0 (benchmark), E3, E5 |
| Poca luz y objetos parciales (feria) | E2 (antiparpadeo), E5 |
| Justificación del modelo y explicación interna | E6 |
