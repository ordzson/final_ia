# PROGRESO — VisionAI

Bitácora compartida entre instancias. Actualízala al terminar cada etapa. Usa fechas absolutas (AAAA-MM-DD).
Estados posibles: `pendiente` | `en curso` | `hecha` | `bloqueada`.

## Estado

| Etapa | Descripción | Estado | Fecha | Notas |
|---|---|---|---|---|
| E0 | Entorno, modelos y decisión Plan A/B | hecha | 2026-10-20 | Plan A, IMGSZ 480, cámara 0. Requiere turbo de CPU activo (ver Decisiones). |
| E1 | `detector.py` | hecha | 2026-10-20 | `detect()` en cámara: 38 ms modo General, 32 ms modo Uni (con turbo). |
| E2 | `scoring.py` y tests | hecha | 2026-10-20 | Tests OK, sin imports prohibidos. |
| E3 | `app.py`: ventana y modo General | hecha | 2026-10-20 | Autoshot 15.3 FPS (techo de la cámara a 720p). Cambio de cámara sin probar (solo hay una): va al checklist E5. |
| E4 | Modo Universitario | hecha | 2026-10-20 | **Con desviación aprobada:** el PNG con ≥ 55 y badge no se capturó (la mochila solo se detecta puesta). 15.8 FPS en Uni con cargador. **En batería, `detect()` tarda el doble (~10 FPS).** |
| E5 | Pulido, robustez y README | en curso | 2026-10-21 | Código, README y FPS con cargador hechos (ver Mediciones finales); falta el checklist [USUARIO]. |
| E6 | Guion de demo y defensa | en curso | 2026-10-21 | `GUION_DEMO.md` escrito con los FPS de E5 y Plan A. Faltan el video de respaldo [USUARIO] y cerrar E5. |

## Decisiones de Etapa 0

- Plan elegido (A/B) y justificación: **Plan A**. YOLOv8s-World v2 (vocabulario propio) sí se generó y exportó, pero en OpenVINO promedia **283 ms** (3.5 FPS) con turbo activo, más de 5× el límite de 55 ms. Se descarta solo por velocidad, sin necesidad de la prueba en vivo.
- Textos de vocabulario finales (solo Plan B): no aplica (se probó el VOCAB por defecto: "spiral notebook", "pen", etc.).
- `MODEL_PATH`: `models/yolov8n_openvino_model` (exportado con imgsz=480)
- `IMGSZ`: **480**. A 640, OpenVINO daba 52.5 ms (> 50); a 480 da 26–28 ms.
- Índice de la cámara integrada / la externa: integrada = **0** (1280×720 MJPG, imagen verificada con Read) / externa = **2** ("USB Camera", verificada el 2026-10-25 en E5); `CAMERA_INDEX_DEFAULT = 2` desde E5 (antes 0)
- Versiones: Python 3.12.3, torch 2.14.1+cpu, ultralytics 8.4.183, openvino 2026.4.1, mediapipe 1.1.1, PySide6 6.12.0, opencv-contrib-python-headless 5.0.0 (OpenCV **5**, no 4.x; ojo con cambios de API)
- Benchmark en ms promedio (FPS equivalentes), 100 frames reales de la cámara 0 a 1280×720, **con turbo activo**:
  - yolov8n .pt: 44.5 ms (22.5) a 640 · 31.1 ms (32.1) a 480
  - yolov8n OpenVINO: 52.5 ms (19.1) a 640 · **26.4–27.7 ms (36–38) a 480**
  - rostros MediaPipe: 3.5–3.9 ms (~270)
  - world_custom OpenVINO (Plan B): 283.0 ms (3.5) a 640
  - Con turbo apagado (estado en que estaba el equipo): yolov8n .pt 131.5 ms, OpenVINO 640 149.5 ms, world 448 ms, MediaPipe 7.2 ms.
- Resultado de la prueba en vivo (por clase): no se hizo. El Plan B quedó descartado por velocidad (paso 10, primer criterio), así que la comparación en vivo con objetos ya no decidía nada. Las detecciones reales se verifican en E1 (persona y rostro) y E4 (objetos del modo universitario).
- Ajustes necesarios:
  - No hizo falta el pop de `QT_QPA_PLATFORM_PLUGIN_PATH`: `import cv2` + PySide6 abren ventana sin errores.
  - **CRÍTICO PARA FPS: turbo de CPU.** El equipo tenía `intel_pstate/no_turbo=1` y `platform_profile=low-power` aun enchufado (los núcleos P topados a 1.3 GHz). `sudo tlp start` no lo cambió. Se arregló a mano (temporal, se pierde al reiniciar):
    `echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo` y `echo performance | sudo tee /sys/firmware/acpi/platform_profile`.
    Se debe repetir antes de cada medición de FPS (E3–E5) y el día de la demo, con la laptop enchufada. Comprobar con `cat /sys/devices/system/cpu/intel_pstate/no_turbo` (debe dar 0). E5 y E6 deben incluirlo en README y GUION_DEMO.
  - Ultralytics no instaló CLIP solo ("AutoUpdate skipped (offline)", su chequeo de red falla en este equipo). Se instaló a mano con `pip install git+https://github.com/ultralytics/CLIP.git` (misma fuente prevista). No afecta al Plan A.

## Mediciones finales (E5)

- FPS en modo General: **15.6 / 15.4** (`app.py --autoshot 8`, dos corridas, usuario frente a la cámara con celular; `tools/out/e5_fps_general_1.png`)
- FPS en modo Universitario: **15.9 / 16.7** (`app.py --mode uni --autoshot 8`, dos corridas, con mochila en mano; `tools/out/e5_fps_uni_2.png`)
- Condiciones: 2026-10-21, cargador conectado, `no_turbo=0`, `platform_profile=performance`, EPP `balance_performance`, cámara integrada 0 a 1280×720, buena luz.
- Medidas de FPS aplicadas: ninguna nueva (los dos modos ≥ 15). `IMGSZ = 480` ya venía de E0. El techo sigue siendo la cámara integrada (~15–16 FPS a 720p), no la inferencia. Margen pequeño: con poca luz o en batería baja de 15.
- **Con la cámara USB externa (índice 2), 2026-10-25:** General **18.9** (`app.py --camera 2 --autoshot 8`, `tools/out/e5_ext_general.png`), Universitario **21.5** (`--mode uni`, `e5_ext_uni.png`), arranque sin `--camera` **20.3** (`e5_ext_frio.png`). Mismas condiciones de energía (cargador, `no_turbo=0`, `performance`, EPP `balance_performance`). La externa entrega 30 FPS a 1280×720 MJPG (19.6 a 1080p, 30 a 800×600 y 640×480), así que el techo pasa a ser la detección y el dibujo.
- Resultado del checklist final:
  - [x] Arranque en frío con la cámara externa: `app.py` sin argumentos abre "Cámara 2 (1280×720)", 20.3 FPS, Persona 95 % y Rostro 96 % (`tools/out/e5_ext_frio.png`).
  - [ ] Corrida larga: **parcial.** El 2026-10-25 corrió 3 min 10 s (el usuario pidió cerrarla para cambiar el modo Universitario). RSS estable: 774 MB a los 30 s y 776 MB al final (máx. 778); CPU ~580 %; sin errores en `tools/out/e5_largo_app.log`. Falta repetirla 10 min con el modo de rondas.
  - [ ] Resto del checklist: pendiente (interruptores, poca luz real, objeto parcial, quitar y poner, desconectar y reconectar el USB, badge capturado en vivo).

## Bitácora

<!-- Una sección por etapa: "### E<N> — AAAA-MM-DD", con lo hecho, las desviaciones del plan y los problemas abiertos. -->

### E0 — 2026-10-20

**Hecho:** `requirements.txt`, `setup.sh` (idempotente, corrido 2 veces sin error), `requirements.lock.txt`, `config.py` (Plan A), `tools/cam_check.py`, `tools/bench.py`, `tools/live_check.py`, `tools/make_world.py`. Modelos en `models/`: `yolov8n.pt`, `yolov8n_openvino_model/` (imgsz 480), `blaze_face_short_range.tflite`. También quedaron los archivos del Plan B (`yolov8s-worldv2.pt`, `world_custom.pt`, `world_custom_openvino_model/`, `weights/clip`; ~440 MB): no los usa nada y se pueden borrar.

**Criterios de aceptación:**
- [x] `./setup.sh` termina con código 0. Verificación del paso 4: `5.0.0 8.4.183 1.1.1 2026.4.1 6.12.0` y `qt+cv2 ok`. `pip list | grep -i opencv` → solo `opencv-contrib-python-headless 5.0.0.93`.
- [x] Existen `models/yolov8n_openvino_model/` (con `metadata.yaml`) y `models/blaze_face_short_range.tflite`.
- [x] Cámara 0 entrega imagen real (`tools/out/cam_0.jpg`, revisada con Read).
- [x] Benchmark anotado. yolov8n OpenVINO a 480: 26.4–27.7 ms (≤ 66 ms).
- [x] Decisión A/B anotada: Plan A (world_custom = 283 ms).
- [x] `import config` funciona y tiene una sola variante (`grep -c "Plan B:" config.py` → 0).

**Desviaciones del plan:**
- `IMGSZ = 480` (no 640), como prevé el paso 7.
- CLIP instalado a mano desde GitHub (Ultralytics se creyó offline). Queda en `requirements.lock.txt`; no se agregó a `requirements.txt` porque el Plan A no lo usa.
- No se hizo la prueba en vivo con objetos (ver Decisiones).

**Problemas abiertos (para E3/E5):**
1. **Turbo de CPU** (ver Decisiones → Ajustes). Sin turbo, OpenVINO a 640 da ~150 ms y la app no llega a 15 FPS. El ajuste se pierde al reiniciar.
2. **Techo de FPS de la cámara integrada.** Con exposición automática y luz de interior entrega solo ~15.3 FPS a 1280×720, 16.7 a 960×540 y 18.7 a 640×480 (en oscuridad, unos 10). El FPS de la app nunca superará lo que da la cámara: en E3, medir con buena luz o con la cámara externa. Si el autoshot da < 15 por culpa de la cámara (no de la inferencia), anotarlo así. La medida 2 de E5 (960×540) ayuda un poco.
3. No forzar la exposición manual con `CAP_PROP_AUTO_EXPOSURE=1`: dejó la imagen negra y el ajuste persiste en la cámara. Se restauró con `CAP_PROP_AUTO_EXPOSURE=3`.
4. OpenCV instalado es la **5.0** (no 4.x). Las APIs usadas en el plan (`VideoCapture`, `cvtColor`, `flip`, `resize`) funcionan igual.
5. Cámara externa sin probar: correr `tools/cam_check.py` cuando esté conectada y anotar el índice.

### E2 — 2026-10-20

**Hecho:** `scoring.py` (`PresenceTracker`, `UniState`, `UniScorer`, según el contrato de PLAN.md §5 y su algoritmo exacto) y `tests/test_scoring.py` (7 casos obligatorios, tiempos simulados en pasos de 0.05 s, verificación en 0.25/0.35 s).

**Criterios de aceptación:**
- [x] `.venv/bin/python tests/test_scoring.py` → `OK` (código 0).
- [x] `grep -E "import (cv2|PySide6|ultralytics)|from (PySide6|ultralytics|detector)" scoring.py` → sin salida (código 1). `scoring.py` solo importa `dataclasses` y `config`.

**Detalles de implementación (para E4):**
- `UniScorer` filtra las claves a los UNI_ITEMS disponibles antes de pasarlas al tracker, así que se le puede pasar `{d.key for d in dets}` sin filtrar.
- `level_text`: si dos ítems presentes empatan en puntos, gana el primero en el orden de UNI_ITEMS (en Plan A no hay empates).
- `UniScorer.reset()` reinicia el tracker; tras el reset un objeto necesita otra vez 0.3 s estable para contar.
- `PresenceTracker()` sin argumentos usa `config.PRESENCE_ENTER_S` / `PRESENCE_HOLD_S`; E3 puede usarlo tal cual como `stats_tracker`.

**Desviaciones del plan:** ninguna.
**Problemas abiertos:** ninguno.

### E1 — 2026-10-20

**Hecho:** `detector.py` (`Det`, `Detector` según el contrato de PLAN §5) y `tools/detect_image.py`. Imagen de prueba en `tools/out/bus.jpg`.

**Criterios de aceptación:**
- [x] `tools/detect_image.py --image tools/out/bus.jpg` → 3 `person` con conf 0.90, 0.84 y 0.82 (imagen revisada con Read).
- [x] **[USUARIO]** `--camera 0` con el usuario frente a la cámara → `person` 0.87 y `face` 0.95. `detect_result.jpg` revisado con Read: cajas correctas.
- [x] `detect(frame, 0.35, set())` → `[]` sin llamar a YOLO (verificado con un espía sobre `model.predict`). Lo mismo con `{"rostros"}` solo, con `{"personas"}` + `only_keys=UNI_ITEMS` (intersección vacía), y con frames `None` o `0×0`.
- [x] `detect(frame, 0.05, {"objetos"}, only_keys=set(UNI_ITEMS))` pide a YOLO `classes=[24, 63, 67, 73]` (backpack, laptop, cell phone, book) y solo devuelve esas claves. Se comprobó en `bus.jpg` y en 55 frames de cámara. Ninguna de las dos fuentes tenía objetos universitarios, así que la detección real de esos objetos se verifica en E4.
- [x] Todas las `Det.label` salen de `LABELS_ES` o `FACE_LABEL`. Las cajas son `int` de Python dentro del frame, y `conf` es `float`.

**Mediciones** (55 frames reales de la cámara 0 a 1280×720, con turbo, sin contar el calentamiento): `detect()` tarda **38.4 ms (26 FPS)** en modo General (objetos + personas + rostros) y **31.8 ms (31.5 FPS)** en modo Uni (`{"objetos"}` + `only_keys`). Solo inferencia: el FPS de la app también depende de la cámara (ver el problema abierto 2 de E0).

**Desviaciones y decisiones:**
- Los rostros también se filtran con el `conf` de la interfaz, además de `FACE_MIN_CONF` (umbral efectivo = máx. de ambos). Así el slider de E3 afecta a todos los grupos.
- Las cajas que quedan sin área al recortarlas al frame (p. ej., un rostro casi fuera de cuadro) se descartan.
- `Detector.__init__` hace una inferencia de calentamiento con un frame negro (OpenVINO compila el modelo en la primera llamada), así que el primer frame de la app no se congela. Ultralytics carga el modelo dos veces al iniciar (`model.names` y luego `predict`): solo afecta al arranque.
- En `bus.jpg` no sale ningún rostro: `blaze_face_short_range` está pensado para caras a menos de unos 2 m y allí son muy pequeñas. Es lo esperado.

### E3 — 2026-10-20

**Hecho:** `app.py` con ventana, modo General, panel lateral, Capturar, Reiniciar, atajos, argumentos `--camera/--mode/--autoshot` y mensaje sin cámara. El archivo lo escribió una instancia anterior que no dejó bitácora. Esta sesión corrió los criterios y la cerró junto con E4.

**Criterios de aceptación:**
- [x] `app.py --autoshot 8` → `AUTOSHOT fps=15.3 frames=99`, código 0 (turbo activo, usuario frente a la cámara).
- [x] `tools/out/e3_autoshot_general.png` revisado con Read: video, caja "Persona 94%", panel con FPS 15.0, tiempo, modo, "En pantalla" y "Apariciones", todos los controles.
- [x] **[USUARIO]** Prueba manual confirmada por el usuario: cada interruptor oculta y muestra su grupo, el slider cambia las detecciones, Capturar crea el PNG, Reiniciar pone todo en cero y los atajos funcionan. **Excepción:** el cambio de cámara no se pudo probar porque solo está conectada la integrada y el selector solo lista "Cámara 0". Se prueba en el checklist de E5 con la cámara externa.
- [x] `app.py --camera 1 --autoshot 5` (índice de metadatos) → muestra "Cámara no disponible — conecta una cámara o elige otra en el selector" y sale con código 0 (`tools/out/e3_autoshot_nocam.png`). La desconexión física (15 lecturas fallidas) queda para el checklist de E5.

**Corrección hecha durante E4 que afecta a E3:** el botón del modo activo va en negrita (QSS `:checked`) y su texto se cortaba ("Universitaric"). Ahora los dos botones tienen un ancho mínimo calculado con la fuente en negrita.

**Problemas abiertos (para E5):**
- El FPS de la app lo limita la cámara integrada, no la inferencia: ~15.3 a 1280×720 con buena luz y **10.7** en una escena oscura (exposición automática; medido en E4). Con poca luz la app queda bajo 15 FPS. La medida 2 de E5 (captura a 960×540) o la cámara externa deberían ayudar.

### E4 — 2026-10-20

**Hecho:** modo "Listo para la Universidad" en `app.py`:
- Al entrar: `uni_scorer.reset()`, checkboxes deshabilitados con el tooltip "Solo en modo General", detección `{"objetos"}` con `only_keys=UNI_ITEMS`.
- Cajas doradas con píldora "Laptop +25 · 87%".
- HUD superior: puntaje, "de 60 pts", barra animada (`disp += (score - disp) * 0.15`, azul bajo 50 y dorada desde 50), nivel y chips por ítem.
- Badge "NIVEL UNIVERSITARIO" con opacidad pulsante.
- "+X pts" flotantes de 1 s.
- Panel con puntaje actual, mejor puntaje e ítems presentes con su título.
- `--mode uni` funciona.

**Criterios de aceptación:**
- [x] `tests/test_scoring.py` → `OK`.
- [x] **[USUARIO]** Sin objetos: `app.py --mode uni --autoshot 8` → `fps=15.4`. El PNG (`tools/out/e4_autoshot_vacio.png`) muestra `0`, "de 60 pts", "Aún no estás listo...", los 4 chips apagados y los checkboxes atenuados.
- [ ] **[USUARIO]** Con mochila, libro y laptop: **no se logró el PNG con ≥ 55 y badge.** El usuario aprobó cerrar con desviación. Evidencia:
  - En vivo **sí se llegó a 55**: "Mejor puntaje de la sesión 55" en el intento 2, cuando los tres coincidieron unos instantes.
  - Mejor PNG: **45 pts**, "Listo para el aula", chips Libro y Laptop encendidos, Laptop 50 % y Libro 41 % (intento 5). En otro intento, Laptop al 82 %.
  - Mochila detectada en el PNG final con cargador: Mochila 54 % → 10 pts, "Acceso a campus" (`tools/out/e4_final_uni.png`).
  - El badge, los chips encendidos y los "+X pts" se verificaron con una simulación offline sobre `bus.jpg` (Det falsos: 55 pts, badge, 3 flotantes, vuelta a 0 en 0.7 s al quitarlos).
  - **Pendiente para el checklist de E5:** repetir `--mode uni --autoshot` con mochila **puesta** + laptop + libro.
- [x] **[USUARIO]** En vivo (lo confirmó el usuario y se vio en las capturas): el puntaje sube en < 1 s y aparece "+20 pts", baja en < 1.5 s, la barra se anima suave y no hay parpadeo.

**Mediciones finales con cargador** (turbo on, `platform_profile=performance`, EPP `balance_performance`): General **15.9 FPS**, Uni **15.8 FPS** (`tools/out/e4_final_general.png`, `e4_final_uni.png`).

**Hallazgos importantes (para E5 y E6):**
1. **Batería = la mitad de FPS.** Sin cargador, el EPP pasa a `balance_power`, la CPU baja a ~600 MHz y `detect()` (General) sube de 38 a **82 ms** → la app da ~10 FPS. Los intentos de 10–12 FPS de esta etapa se midieron en batería. Con cargador, `read()` tarda ~10 ms y la cámara vuelve a ser el techo (~15–16 FPS a 720p). **README y GUION: la laptop SIEMPRE enchufada**, además del ajuste de turbo de E0.
2. **Mochila: clase débil en YOLOv8n/COCO.** Prueba de 40 s solo con la mochila (azul marino lisa), confianza máxima por segundo:
   - Sobre la mesa: 0.10–0.36. Casi nunca pasa el umbral de 0.35.
   - En la mano: 0.32–0.47, a ratos.
   - **Puesta y vista de espaldas o 3/4: 0.52–0.68.**
   - Puesta pero muy cerca de la cámara (cortada): 0.
   
   En COCO las mochilas aparecen casi siempre puestas en personas. **Para la demo: llevar la mochila puesta y entera en cuadro.** Si se puede, usar una más clara o con más detalle (bolsillos, tirantes marcados). La de color verde o turquesa del cuarto del usuario no se probó. Con contraluz (ventana detrás) baja todavía más.
3. La laptop se detecta por la **pantalla y el teclado**. Vista desde atrás (la tapa) no se detecta.
4. El cuaderno de dibujo "Drawing Pad A4" se detecta como Libro (41–74 %), como prevé el Plan A.

**Cambios fuera del alcance literal de E4 (pequeños, de corrección):**
- Paleta del grupo Disabled atenuada (`#4a4f6e`): sin ella, los checkboxes deshabilitados se veían iguales a los activos.
- Ancho mínimo de los botones de modo, calculado en negrita (afectaba a E3).
- La píldora de las cajas nunca sube por encima del HUD (`draw_box(..., top=HUD_H*s)`), porque si no el HUD la tapaba.
- Los "+X pts" arrancan sobre la píldora de la caja y, si la caja toca el HUD, justo debajo de él.
- Marca blanca en la barra en la posición de la meta (50/60), para que el público vea cuánto falta para el badge.

**Problemas abiertos:** cambio de cámara y autoshot completo de E4 → checklist de E5.

### E5 — 2026-10-21 (en curso)

**Hecho (sin usuario):**
- **Poca luz:** brillo medio de una miniatura gris 64×36 por frame. Si queda bajo `LOW_LIGHT_MEAN` más de 1 s, se dibuja una franja inferior amarilla ("Poca luz: la detección puede fallar. Acerca una lámpara.") y el panel muestra "Luz: OK / Baja". Verificado con una cámara falsa (`bus.jpg` al 25 % de brillo) en los dos modos: `tools/out/e5_fake_dark_general.png` y `e5_fake_dark_uni.png`.
- **QSS:** fuente del sistema a 11 pt, títulos del panel a 9 pt en `muted`, valores a 14 pt en negrita, hover y pressed en botones, hover en combo y checkboxes, slider con `accent`, tooltip oscuro.
- **Robustez de cámara (no estaba en el plan; es para el ítem del checklist "desconectar y reconectar"):**
  - Sin cámara, se reintenta abrir la elegida cada 2 s y el video vuelve solo ("Cámara N reconectada").
  - El selector vuelve a buscar cámaras cada vez que se abre, así aparecen las conectadas en caliente. La cámara en uso se salta en esa búsqueda.
  - El selector usa la señal `activated` (solo la emite el usuario).
  - Se silenciaron los avisos `WARN` de V4L2 en cada reintento (`cv2.utils.logging`).
  - Verificado con una cámara falsa que falla tras 60 frames: aviso, 2 reintentos fallidos y reconexión (`tools/out/e5_fake_reconnect.png`). `--camera 1` → aviso, código 0 y sin spam en la terminal (`e5_nocam.png`).
- **`README.md`** escrito.
- `tests/test_scoring.py` → `OK`.

**Criterio "siguiendo el README desde cero se llega a la app abierta": cumplido.**
- Prueba en una copia limpia: solo código, sin `.venv` ni `models/`, en una ruta con espacio.
- Se siguieron al pie de la letra las secciones 2 y 3:
  - `./setup.sh` → 46 s (con caché de pip).
  - Descarga de `yolov8n.pt` desde GitHub y export a OpenVINO 480.
  - `curl` del modelo de rostros.
  - `pip list` → solo `opencv-contrib-python-headless`.
  - Tests → `OK`.
- Después, `app.py --autoshot 6` desde la copia → `fps=16.5`, código 0, ventana con Persona y Rostro (`tools/out/e5_readme_copia.png`). La copia se borró después.

### E6 — 2026-10-21 (en curso)

Se empezó con E5 todavía `en curso` (falta su checklist [USUARIO]), como permite el plan ("el guion puede empezarse antes"). Los FPS ya estaban medidos con cargador en E5.

**Hecho:** `GUION_DEMO.md` con las 5 secciones del plan:
1. Pitch de 5 min.
2. Demo de 15 min por bloques, con `[Integrante N]` y el criterio de la rúbrica de cada bloque.
3. Preguntas y respuestas de defensa (las 7 del plan, una de FPS y otras posibles).
4. Checklist del día de la demo.
5. Instrucciones del video de respaldo.

**Criterios de aceptación:**
- [x] `GUION_DEMO.md` completo, con los FPS reales (General 15.4–15.6, Universitario 15.9–16.7) y el Plan A. Si el checklist de E5 cambia algún número (por ejemplo, con la cámara externa), hay que actualizar la tabla "Datos clave" y la pregunta 8.
- [ ] **[USUARIO]** Video de respaldo: pendiente. Al grabarlo, anotar aquí el archivo, la duración y la fecha.

**Números de §9 verificados en la web (2026-10-21):**
- YOLOv8n: 37.3 mAP50-95, 3.2 M parámetros y 8.7 GFLOPs (docs de Ultralytics, COCO val2017 a 640).
- EfficientDet-Lite0 (MediaPipe): 25.69 mAP en COCO val2017 (docs de TF Lite Model Maker). Se agregó al guion; §9 solo decía "menos preciso".
- SSD MobileNet v2: 22 mAP en COCO minival2014 y ~20.2 en val2017. Coincide con el "~20–22" de §9.

**Desviaciones del plan:**
- **Grabador de pantalla:** el equipo es Linux Mint 22.2 con Cinnamon 6.4.8, no GNOME. El atajo `Ctrl+Alt+Shift+R` del plan no existe aquí. El guion usa **SimpleScreenRecorder**, que ya está instalado (OBS no lo está).
- **OpenVINO:** §9 dice que OpenVINO "es lo que permite superar los 15 FPS", pero el benchmark de E0 no lo respalda. A 480 ahorra ~4 ms (27 frente a 31 ms de PyTorch) y a 640 fue más lento (52.5 frente a 44.5 ms). Lo que más pesó fue la entrada de 480 y el turbo de CPU. El guion lo explica con esos números para no afirmar algo que el docente pueda refutar.
- **Candidatos de YOLO:** el guion usa 4725 (entrada de 480: 60² + 30² + 15²) y menciona los 8400 de 640.
- **Orden del modo Universitario:** mochila → libro → laptop → celular. Como la mochila es poco fiable, el guion avisa que libro + laptop + celular suman 50 y alcanzan la insignia sin ella.

**Pendiente para cerrar E6:**
1. E5 en `hecha` (checklist final). En particular: el índice de la cámara externa (en el guion queda un espacio "____" para escribirlo) y los cuatro puntos del bloque "Robustez" de la demo de 15 min.
2. Video de respaldo grabado y anotado.

**Actualización 2026-10-25 (desde E5):** índice de la cámara externa (2) y FPS con ella escritos en la tabla "Datos clave", la limitación de FPS, la pregunta 8 y el checklist del día de la demo.

### E5 — 2026-10-25 (continuación: cámara externa)

**Hecho:**
- `tools/cam_check.py` con la cámara USB conectada: índices 0 (integrada) y **2** ("USB Camera") dan imagen; 1 y 3 son de metadatos. `tools/out/cam_2.jpg` revisada con Read.
- Modos de la externa (MJPG, 3 s por modo): 1920×1080 → 19.6 FPS · **1280×720 → 30.0** · pedido 960×540 → entrega 800×600 a 30.0 · 640×480 → 30.0.
- `CAMERA_INDEX_DEFAULT = 2` en `config.py`. Si la 2 no está, `_select_initial_camera` ya abre la primera disponible (sin cambios en `app.py`).
- README y GUION_DEMO actualizados con el índice y los FPS nuevos.

**Mediciones:** ver "Mediciones finales (E5)": General 18.9, Universitario 21.5, arranque en frío 20.3.

**Hallazgos con la cámara externa (sin corregir todavía):**
1. **Franja blanca arriba del video.** Las primeras filas de cada frame salen dañadas: brillo medio por fila 254.2, 251.0, 127.2, 12.3 y luego ~113 normal. Es de la cámara, no de la app. Se ve como una línea blanca fina sobre el video (`e5_ext_general.png`).
2. **Rostro falso.** "Rostro 51 %" sobre la mano con el celular, con la cara fuera del cuadro (`e5_ext_general.png`). El umbral efectivo de rostros es máx(slider 0.35, `FACE_MIN_CONF` 0.5). Los rostros reales dan 0.95–0.96.
3. La cámara quedó baja, apuntando al torso. Para la demo, ponerla a la altura de la cara.

**Arreglos aprobados por el usuario (2026-10-25):**
- **Franja blanca:** `app.py` descarta las primeras `CROP_TOP = 4` filas de cada frame, antes del espejo y de detectar. Con la integrada también se aplica (4 de 720 filas, sin efecto visible). Verificado en `tools/out/e5_fix_general.png`: el borde superior sale limpio.
- **Etiquetas que se tapaban:** `draw_box` recibe `taken`, la lista de píldoras ya dibujadas en el frame. Si la nueva choca con alguna, baja justo debajo de ella. Los dos modos dibujan de mayor a menor confianza. Verificado así:
  - Offline, con 4 Det falsos que se pisan sobre `bus.jpg`: Persona, Celular y "Libro / Cuaderno" quedan apiladas y legibles (`tools/out/e5_overlap_fake.png`).
  - En vivo: "Rostro 96 %" y "Persona 94 %" salen sin taparse (`e5_fix_general.png`).
- **Etiqueta "Libro / Cuaderno"** para `book` en `config.py` (COCO no tiene cuaderno). El chip "Libro / Cuaderno +20" entra en el HUD (`e5_fix_uni.png`). README y GUION actualizados.
- **No aplicado:** subir `FACE_MIN_CONF` (el usuario no lo eligió).
- `tests/test_scoring.py` → `OK`. FPS tras los cambios, con la cámara 2: General **18.0** y Universitario **20.1**.

### Cambio de alcance — 2026-10-25: modo Universitario por rondas (pedido por el usuario)

**Motivo:** juntar todos los objetos a la vez frente a la cámara era incómodo, y la mochila solo se detecta puesta.

**Nuevo comportamiento:**
- Ronda de `UNI_ROUND_S = 60` s. Arranca con el primer objeto que entra tras pasar al modo.
- Cada objeto se guarda al verse 0.3 s estable y **no se pierde al retirarlo**. Se pueden mostrar uno a uno o de a varios.
- Termina al acabarse el minuto o al juntar los 4.
- El resultado ("¡TIEMPO!" o "¡COMPLETO! en N s") se muestra `UNI_RESULT_S = 5` s. Luego el puntaje vuelve a 0 y espera otra ronda.
- Los objetos que siguen en cuadro no arrancan una ronda nueva solos (si no, con todo en cuadro las rondas se encadenarían).

**Cambios:**
- `config.py`: `UNI_ROUND_S` y `UNI_RESULT_S`.
- `scoring.py`: `UniScorer` con fases `waiting`, `running` y `result`. `UniState` suma `collected`, `phase`, `time_left` y `result_left`; `entered` pasa a significar "guardado en este frame". `PresenceTracker` no cambia.
- `tests/test_scoring.py`: 4 casos nuevos (acumular uno a uno, fin por tiempo, completo antes de tiempo, sin rondas encadenadas). Ajustado `test_reset`. Total: 11, `OK`.
- `app.py`:
  - Reloj a la derecha del HUD ("1:00 · Muestra un objeto" → "0:47 · restantes", rojo en los últimos 10 s).
  - Chips encendidos según lo guardado.
  - Tarjeta central con el resultado.
  - Panel con "Tiempo de la ronda" e "Ítems guardados" (antes "Ítems presentes").
- PLAN.md §5 y §6, README y GUION_DEMO actualizados. En el guion: pitch, bloque Universitario de la demo, video de respaldo, pregunta 6 y la pregunta nueva "¿Por qué el puntaje no baja al retirar un objeto?".

**Verificación:**
- Render offline con estados reales de `UniScorer` (espera, en curso con "+20 pts", reloj rojo a 0:08, fin por tiempo con 55 y badge, completo 60/60 "en 10 s"): todo correcto.
- En vivo: `app.py --mode uni --autoshot 8` → 22.8 FPS, código 0, sin trazas de error. Estado de espera visible (`tools/out/e5_ronda_uni.png`).
- **Falta probarlo en vivo con objetos [USUARIO].**

**Riesgo frente al enunciado:** el criterio 5.1 dice "actualiza el puntaje en tiempo real al mostrar y retirar objetos". Ahora retirar no baja el puntaje. Al retirar, sí cambian al instante la caja, "En pantalla" y el reloj. El guion tiene la respuesta preparada.
