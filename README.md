# VisionAI — Detector de Objetos en Tiempo Real

Aplicación de escritorio que abre la cámara, detecta objetos en vivo y dibuja sobre el video una caja, la etiqueta en español y el porcentaje de confianza de cada detección.

- **Objetos:** YOLOv8n (preentrenado en COCO), acelerado en CPU con OpenVINO.
- **Rostros:** MediaPipe BlazeFace.
- **Interfaz:** PySide6 (Qt 6).

Tiene dos modos:

- **General:** personas, rostros, celulares, laptops, mochilas, libros, mesas y otros objetos comunes.
- **Listo para la Universidad:** en una ronda de 1 minuto, suma puntos por cada objeto universitario que se muestra frente a la cámara.

---

## 1. Requisitos

- Linux con sesión X11 (probado en Ubuntu con kernel 6.14).
- Python 3.12 (`python3 --version`).
- Una cámara web. Sirve la integrada o una USB.
- Conexión a internet para la instalación. Se descarga de PyPI, `download.pytorch.org`, GitHub y `storage.googleapis.com`.
- El paquete del sistema `libxcb-cursor0`. **Sin él, Qt no puede abrir la ventana:**

  ```bash
  sudo apt install libxcb-cursor0
  ```

No hace falta GPU: todo corre en la CPU.

## 2. Instalación

Ejecuta los comandos desde la carpeta del proyecto. La ruta tiene un espacio (`ia final`), así que va siempre entre comillas:

```bash
cd "/ruta/a/ia final"
./setup.sh
```

`setup.sh` hace cuatro cosas:

1. Crea el entorno virtual `.venv/`.
2. Instala PyTorch en su versión para CPU (así evita descargar unos 3 GB de CUDA).
3. Instala `requirements.txt`.
4. Deja instalado **solo** `opencv-contrib-python-headless`.

El paso 4 es necesario porque las otras variantes de OpenCV traen plugins de Qt que chocan con PySide6. Puedes ejecutar el script todas las veces que quieras.

Al final, `pip check` avisará de que ultralytics pide `opencv-python`. **Es normal y se puede ignorar.**

## 3. Modelos

Si la carpeta `models/` ya trae los modelos, sáltate este paso. Si no, descárgalos y expórtalos:

```bash
mkdir -p models && cd models
../.venv/bin/python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='openvino', imgsz=480)"
curl -L -o blaze_face_short_range.tflite https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite
cd ..
```

Debes terminar con:

- `models/yolov8n.pt`
- `models/yolov8n_openvino_model/`
- `models/blaze_face_short_range.tflite`

El `imgsz=480` del export debe coincidir con `IMGSZ` en `config.py`.

La exportación puede instalar paquetes por su cuenta. Comprueba después que siga habiendo un solo OpenCV:

```bash
.venv/bin/pip list 2>/dev/null | grep -i opencv   # solo debe salir opencv-contrib-python-headless
```

Si sale otro, vuelve a ejecutar `./setup.sh`.

## 4. Antes de ejecutar: rendimiento

La meta es **15 FPS o más**. En este equipo (Intel Core i5-1235U, sin GPU NVIDIA) solo se alcanza si se cumplen dos condiciones:

1. **La laptop está enchufada.** Con batería, la CPU baja de frecuencia y la detección tarda el doble (unos 10 FPS).
2. **El turbo de la CPU está activo.** Compruébalo:

   ```bash
   cat /sys/devices/system/cpu/intel_pstate/no_turbo   # debe dar 0
   ```

   Si da `1`, actívalo. El cambio se pierde al reiniciar el equipo, así que repítelo antes de cada demo:

   ```bash
   echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
   echo performance | sudo tee /sys/firmware/acpi/platform_profile
   ```

Estas rutas existen en laptops Intel con el driver `intel_pstate`. En otro equipo pueden no existir: en ese caso, sáltate este paso.

## 5. Ejecutar

```bash
.venv/bin/python app.py                 # cámara USB (índice 2) o, si no está, la primera disponible
.venv/bin/python app.py --camera 2      # otra cámara, p. ej. una USB externa
.venv/bin/python app.py --mode uni      # arranca en modo Universitario
```

La ventana tarda unos segundos en abrir, porque carga los modelos al iniciar.

Hay una opción extra para verificar sin interactuar: `--autoshot SEG`. A los SEG segundos guarda la ventana en `capturas/autoshot.png`, imprime los FPS promedio y se cierra.

## 6. Cómo se usa

### Controles

| Control | Qué hace |
|---|---|
| **Cámara** | Elige la cámara. Cada vez que abres la lista, vuelve a buscar cámaras, así que aparecen también las que conectes con la app abierta. |
| **General / Universitario** | Cambia de modo. |
| **Objetos / Personas / Rostros** | Muestran u ocultan cada tipo de detección. Solo funcionan en modo General. |
| **Confianza** | Confianza mínima para mostrar una detección. Más alta: menos detecciones, pero más seguras. |
| **Capturar** | Guarda la imagen con las detecciones en `capturas/AAAAMMDD_HHMMSS.png`. |
| **Reiniciar** | Pone en cero las estadísticas de la sesión. |

### Atajos de teclado

| Tecla | Acción |
|---|---|
| `Espacio` | Capturar |
| `M` | Cambiar de modo |
| `R` | Reiniciar estadísticas |
| `Ctrl+Q` | Salir |

### Modo General

Cada detección se dibuja con el color de su grupo:

- **Azul:** personas.
- **Rosa:** rostros.
- **Verde:** objetos.

El panel lateral muestra:

- FPS, tiempo de sesión, modo y estado de la luz.
- Lo que hay en pantalla ahora.
- Cuántas veces apareció cada cosa en la sesión.
- El número de capturas.

### Modo "Listo para la Universidad"

Es una ronda de **1 minuto**. Los objetos se pueden mostrar uno a uno o de a varios: cada uno suma una sola vez y **queda guardado** aunque se retire (dos libros siguen valiendo +20):

| Objeto | Nivel | Puntos |
|---|---|---|
| Mochila | Acceso a campus | +10 |
| Libro / Cuaderno | Estudiante dedicado | +20 |
| Laptop | Listo para el aula | +25 |
| Celular | Siempre conectado | +5 |

- **Arriba:** el puntaje (máximo 60), una barra de progreso, el nivel alcanzado, un chip por objeto y el reloj de la ronda. Los chips encendidos son los objetos ya guardados; los apagados, los que faltan. En los últimos 10 s el reloj se pone rojo.
- **Ronda:** el reloj arranca con el primer objeto que se detecta al entrar al modo. Termina al acabarse el minuto o, antes, al juntar los 4 objetos. El resultado (**¡TIEMPO!** o **¡COMPLETO!**, con el tiempo que tardó) se muestra 5 s; luego el puntaje vuelve a 0 y espera el siguiente objeto. Los objetos que siguen en cuadro desde la ronda anterior no arrancan otra solos: hay que mostrar uno nuevo, o retirarlo y volver a mostrarlo. Las duraciones están en `config.py` (`UNI_ROUND_S` y `UNI_RESULT_S`).
- **Insignia:** con **50 puntos o más** aparece la insignia **NIVEL UNIVERSITARIO**.
- **Antiparpadeo:** un objeto se guarda solo después de verse 0.3 s seguidos. Así un falso positivo de un frame no suma puntos.
- **Cuadernos y lapiceros:** el modelo está entrenado con COCO, que no tiene esas clases. Por eso un cuaderno se detecta con la clase libro (la etiqueta dice **Libro / Cuaderno**), y el lapicero se reemplazó por el **celular**.

### Poca luz

Si la imagen se mantiene oscura más de 1 segundo:

- Aparece una franja amarilla abajo: *"Poca luz: la detección puede fallar. Acerca una lámpara."*
- El panel muestra **Luz: Baja**.

### Si se desconecta la cámara

Se muestra un aviso en lugar del video y la app sigue abierta. Cada 2 s intenta abrir de nuevo la misma cámara, así que al reconectarla el video vuelve solo.

## 7. Problemas comunes

**Se abre la cámara equivocada o no hay imagen.**
- Prueba otro índice con `--camera N` o con el selector.
- En esta laptop, la integrada es el índice **0**. El índice 1 solo da metadatos, nunca imagen. Una cámara USB suele quedar en el **2**.
- Para ver qué índices dan imagen: `.venv/bin/python tools/cam_check.py`. Guarda una foto por índice en `tools/out/`.

**Poca luz o detecciones pobres.**
- Acerca una lámpara y evita tener una ventana detrás (contraluz).
- Con poca luz la cámara alarga la exposición y entrega menos cuadros por segundo, así que también bajan los FPS.
- Algunas clases son más difíciles para el modelo:
  - **Mochila:** se detecta mucho mejor **puesta en la espalda** y entera en el cuadro que apoyada en una mesa.
  - **Laptop:** se detecta por la pantalla y el teclado, no por la tapa.

**`Could not load the Qt platform plugin "xcb"`**
- Si el mensaje menciona `xcb-cursor`, falta el paquete del sistema: `sudo apt install libxcb-cursor0`.
- Si menciona `cv2/qt/plugins`, quedó instalado un OpenCV con GUI: vuelve a ejecutar `./setup.sh`.
- **Nunca** instales ni actualices `ultralytics` con `pip` por separado: reinstala `opencv-python`. Si lo hiciste, corre `./setup.sh` de nuevo.

**Menos de 15 FPS.**
- Revisa la sección 4: cargador conectado y turbo activo.
- La cámara integrada entrega como máximo unos 15–16 FPS a 1280×720. La cámara USB externa da 30 a esa resolución, y con ella la app llega a 19–22 FPS.

**Sin pantalla (por SSH).** `QT_QPA_PLATFORM=offscreen .venv/bin/python app.py --autoshot 8`.

## 8. Archivos

| Archivo | Contenido |
|---|---|
| `app.py` | Interfaz, bucle de video y dibujo |
| `detector.py` | Detección de objetos (YOLO) y de rostros (MediaPipe) |
| `scoring.py` | Antiparpadeo y puntaje del modo Universitario |
| `config.py` | Clases, etiquetas, puntos, umbrales y colores |
| `tests/test_scoring.py` | Pruebas del puntaje: `.venv/bin/python tests/test_scoring.py` |
| `tools/` | Scripts de verificación (cámaras, benchmark, detección sobre una imagen) |
| `capturas/` | Capturas de pantalla de la app |
