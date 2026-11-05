# Guion de demo y defensa — VisionAI

Para los integrantes del equipo. Aquí está qué decir, qué mostrar, en qué orden y cómo responder las preguntas del docente.
Reemplacen `[Integrante 1]`, `[Integrante 2]` y `[Integrante 3]` por sus nombres. Si son más, repartan los bloques.

---

## Datos clave (apréndanselos)

| Dato | Valor |
|---|---|
| Modelo de objetos | **YOLOv8n** (Ultralytics), preentrenado en **COCO-80**, acelerado con **OpenVINO**, entrada de **480 px** |
| Modelo de rostros | **MediaPipe BlazeFace** (`blaze_face_short_range`) |
| Interfaz | PySide6 (Qt 6), dibujo con QPainter |
| Plan del proyecto | **Plan A** (solo clases COCO). YOLO-World se probó y se descartó por lento |
| **FPS reales de la app** | **Con la cámara USB externa: General 18.9 · Universitario 21.5** (2026-10-25). Con la integrada: General 15.4–15.6 · Universitario 15.9–16.7. Siempre con la laptop enchufada, turbo de CPU activo y 1280×720 |
| Tiempo de detección por frame | General (objetos + personas + rostros): **38 ms** (~26 FPS) · Universitario: **32 ms** (~31 FPS) |
| Límite real de FPS | Con la integrada, la **cámara** (15–16 cuadros por segundo a 1280×720). Con la USB externa (30 cuadros por segundo), el límite pasa a ser la **detección y el dibujo** |
| Puntos del modo Universitario | Mochila +10 · Libro / Cuaderno +20 · Laptop +25 · Celular +5 → **máximo 60** |
| Insignia "NIVEL UNIVERSITARIO" | Con **50 puntos o más** |
| Ronda del modo Universitario | **1 minuto**. Arranca con el primer objeto; cada objeto queda **guardado** aunque se retire. Termina antes si se juntan los 4. El resultado dura **5 s** y luego vuelve a 0 |
| Antiparpadeo | Un objeto se guarda tras **0.3 s** visible. En el panel, sigue "en pantalla" hasta **0.7 s** después de dejar de verse |

**Regla de oro:** la laptop va **siempre enchufada** y con el **turbo activo** (ver el checklist, sección 4). En batería la app baja a unos 10 FPS.

---

## 1. Pitch de 5 minutos para la feria (público mixto)

Objetivo: que cualquier persona entienda qué hace y lo vea funcionar. Nada de jerga: "la cámara reconoce objetos", no "inferencia".
Arranquen con la app abierta en modo **General**, las estadísticas reiniciadas (`R`) y los objetos escondidos fuera del cuadro.

| Tiempo | Qué pasa | Qué se dice (sugerido) |
|---|---|---|
| **0:00–0:45** — Qué es | Una persona frente a la cámara. Se ven sus cajas de Persona y Rostro. | "Esto es VisionAI. Es una aplicación que mira por la cámara y reconoce en tiempo real lo que tiene delante: personas, caras y objetos. Cada cosa que reconoce la encierra en un recuadro, le pone su nombre y qué tan segura está, en porcentaje." |
| **0:45–2:00** — Modo General | Mostrar el celular y un libro. Apagar y prender **Rostros** con su casilla. Señalar el panel de la derecha. | "Fíjense en el número: 94 % quiere decir que está muy segura de que eso es una persona. Azul son personas, rosa son caras y verde son objetos. Puedo apagar lo que no quiero ver, por ejemplo las caras. A la derecha va la cuenta: cuántos cuadros por segundo procesa (unos 15, como un video) y cuántas veces apareció cada cosa." |
| **2:00–4:15** — Modo Universitario | Pulsar `M`: el reloj marca 1:00 y espera. Mostrar los objetos **uno a uno** (o de a dos), en este orden: mochila puesta → libro → laptop → celular. Cuando se enciende su chip, el objeto ya se puede bajar. | "Ahora un juego: ¿estás listo para la universidad? Tengo un minuto para mostrar todo lo que llevo. Arranco en cero: 'Aún no estás listo'. Con la mochila, +10: acceso al campus, y el reloj empieza a correr. Con un libro, +20; ya lo puedo bajar, los puntos quedan guardados. Con la laptop, +25... y al pasar los 50 puntos, ¡NIVEL UNIVERSITARIO! Con el celular junto los cuatro: ¡completo!, y me dice cuánto tardé." |
| **4:15–5:00** — Cierre | Apenas salga **¡COMPLETO!** con la insignia (se ve 5 s), pulsar `Espacio` para capturar. | "Todo esto corre en una laptop normal, sin tarjeta gráfica, usando una red neuronal llamada YOLO. Y si quieren, les sacamos una foto con su puntaje." |

**Si la mochila no se enciende en 3 s:** no insistan; sigan con el libro. **Libro + laptop + celular suman 50**, justo lo que pide la insignia. La mochila se puede sumar al final, antes de que se acabe el minuto, para llegar a 60.

**Cómo mostrar cada objeto para que se detecte:**
- **Mochila:** **puesta en la espalda**, de espaldas o de 3/4 a la cámara y entera en el cuadro. Apoyada en la mesa casi no se detecta: el modelo aprendió con fotos de gente que la lleva puesta.
- **Laptop:** con la **pantalla encendida y el teclado hacia la cámara**. Si se ve solo la tapa, no se detecta. Tiene que ser una segunda laptop, no la que corre la app.
- **Libro o cuaderno:** abierto o de frente, a 50–80 cm. El modelo lo detecta con la clase libro y en pantalla sale "Libro / Cuaderno" (ver la pregunta 5).
- **Celular:** en la mano, con la pantalla o el dorso hacia la cámara.

---

## 2. Demo de 15 minutos ante el docente

Ensáyenla en **13 minutos** para tener margen. Cada bloque apunta a un criterio de la rúbrica.

| Tiempo | Quién | Bloque | Qué se muestra o se dice | Rúbrica |
|---|---|---|---|---|
| **0:00–1:30** | [Integrante 1] | Presentación | El problema y la solución en una frase. Arquitectura: cámara → espejo → YOLOv8n (objetos y personas) + BlazeFace (rostros) → antiparpadeo y puntaje → dibujo con QPainter → interfaz Qt. | Demo (10) |
| **1:30–4:30** | [Integrante 2] | Modo General en vivo | Persona, rostro, celular, libro y laptop con caja, etiqueta en español y %. Apagar y prender **Objetos**, **Personas** y **Rostros**. Subir la confianza a 70 % (salen menos cajas) y bajarla a 20 % (salen más). Panel: FPS, tiempo, "En pantalla" y "Apariciones". **Capturar** con `Espacio` y abrir el PNG de `capturas/`. | Integración del modelo (30) · Interfaz (30) |
| **4:30–8:00** | [Integrante 3] | Modo Universitario | Pulsar `M`: las casillas quedan deshabilitadas porque este modo solo busca objetos universitarios. El reloj marca 1:00 y arranca con el primer objeto. Mostrar los objetos uno a uno: "+X pts" flotante, barra animada, nivel, chips. Retirar un objeto: su caja y "En pantalla" se actualizan al instante, pero el puntaje se mantiene porque ya quedó guardado (explicar por qué, ver "Otras preguntas posibles"). Llegar a la insignia y a **¡COMPLETO!**; a los 5 s todo vuelve a 0. Señalar "Tiempo de la ronda" y "Mejor puntaje de la sesión" en el panel. | Modo universitario (30) |
| **8:00–9:30** | [Integrante 2] | Robustez | **Poca luz:** tapar casi toda la lente con la mano 2 s → franja amarilla y "Luz: Baja" en el panel. **Objeto parcial:** sacar media laptop del cuadro; debería seguir detectada. **Quitar y poner rápido:** el puntaje no parpadea (antiparpadeo). **Desconectar la cámara USB:** sale el aviso, la app no se cierra y al reconectarla el video vuelve solo. *(Estos cuatro puntos se prueban en el checklist final del proyecto. Ensáyenlos antes y saquen del guion el que no salga bien.)* | Extra feria |
| **9:30–12:30** | [Integrante 1] | Cómo funciona | Por qué YOLOv8n (pregunta 1), cómo funciona por dentro (pregunta 2), OpenVINO y FPS reales (preguntas 3 y 8), rostros (pregunta 4), Plan A (pregunta 5), antiparpadeo (pregunta 6). Si piden código: `detector.py` (detección), `scoring.py` (puntaje), `config.py` (clases y puntos). | Justificación del modelo |
| **12:30–15:00** | Todos | Preguntas | Limitaciones (pregunta 7) y las que haga el docente. | — |

**Si algo falla en vivo:**
- **No hay video:** elijan otra cámara en el selector. La integrada es la 0; la USB suele ser la 2.
- **FPS bajo 15:** revisen que el cargador esté conectado y el turbo activo.
- **Un objeto no se detecta:** acérquenlo a 50–80 cm, mejoren la luz y gírenlo (laptop con la pantalla, mochila puesta). Último recurso: bajar el slider de confianza a 25–30 %.
- **La app se cuelga:** `Ctrl+Q` y vuelvan a abrirla (tarda unos segundos en cargar los modelos). Si no se recupera, pongan el **video de respaldo**.

---

## 3. Preguntas y respuestas de defensa

### 1. ¿Por qué YOLOv8n y no SSD o MediaPipe?

Porque es el más preciso de los tres y aun así cumple los 15 FPS en nuestra CPU.

| Modelo | Precisión en COCO (mAP50-95) | Comentario |
|---|---|---|
| **YOLOv8n** | **37.3** | 3.2 M de parámetros, 8.7 GFLOPs. La "n" es *nano*, la versión más pequeña de la familia (n, s, m, l, x). |
| MediaPipe Object Detector (EfficientDet-Lite0) | 25.7 | Muy bueno para móviles. MediaPipe es excelente en rostros y manos, pero su detector general es menos preciso. |
| SSD MobileNet v2 | ~20–22 | Rápido en móviles, pero unos 15 puntos menos que YOLOv8n. |

- Las cifras son oficiales: Ultralytics para YOLOv8n (COCO val2017, entrada de 640), la documentación de TensorFlow Lite para EfficientDet-Lite0 y el *model zoo* de TensorFlow para SSD.
- En nuestro equipo, YOLOv8n tarda **26–28 ms por imagen** con OpenVINO, así que sobra margen para 15 FPS. No hacía falta sacrificar precisión con un modelo más débil.
- Si preguntan por qué no una versión más grande: YOLOv8s tiene más del triple de cálculo (28.6 GFLOPs frente a 8.7). No la medimos, pero el margen que nos queda no alcanza para eso. YOLOv8s-World, de ese tamaño, sí la medimos: 283 ms.
- **Matiz honesto:** el 37.3 se mide con imágenes de 640 px. Nosotros usamos **480 px** para ir el doble de rápido (52.5 ms → 27 ms), y eso baja un poco la precisión, sobre todo con objetos pequeños o lejanos.

### 2. ¿Cómo funciona YOLO por dentro?

"YOLO" significa *You Only Look Once*: mira la imagen **una sola vez** y en esa pasada predice todas las cajas y sus clases. Es un detector **de una etapa** (no propone regiones primero para clasificarlas después) y **sin anchors**: predice directamente el centro del objeto y la distancia a cada borde, en lugar de ajustar cajas de tamaño predefinido.

Paso a paso, con nuestros números:

1. **Letterbox:** la imagen de la cámara (1280×720) se reduce a 480 px manteniendo la proporción y se rellena con gris lo que sobra.
2. **Backbone (CSPDarknet con bloques C2f):** red convolucional que extrae características: bordes, texturas, partes de objetos.
3. **Neck (PAN-FPN):** mezcla las características de 3 escalas, para detectar a la vez objetos grandes y pequeños.
4. **Head desacoplado:** en cada celda de las 3 escalas predice por separado la caja (con DFL, que estima cada borde como una distribución de probabilidad) y el puntaje de cada una de las 80 clases.
   - Con strides 8, 16 y 32 sobre 480 px salen 60×60 + 30×30 + 15×15 = **4725 candidatos** (a 640 serían 8400).
5. **Filtro por confianza:** se descartan los candidatos por debajo del umbral del slider (35 % por defecto).
6. **NMS (*non-maximum suppression*):** si dos cajas de la misma clase se solapan más de un 70 % (IoU 0.7), queda solo la de mayor confianza.

Después, nuestro código pasa las cajas a coordenadas del frame, se queda con las clases que nos interesan, traduce la etiqueta al español y la dibuja.

**Qué es el % que se ve:** es la confianza del modelo en que la caja contiene esa clase. No es la exactitud del sistema. Un 90 % no significa que acierte 9 de cada 10 veces.

### 3. ¿Qué es OpenVINO y por qué se usa?

OpenVINO es un kit de Intel que convierte el modelo a su propio formato (archivos `.xml` y `.bin`) y lo optimiza para procesadores Intel: fusiona capas y aprovecha las instrucciones vectoriales de la CPU. Nuestro equipo tiene un Intel Core i5-1235U y no tiene GPU NVIDIA, así que no hay CUDA: todo corre en la CPU.

Medición de YOLOv8n (100 frames reales de la cámara, turbo activo):

| Formato | Entrada 640 | Entrada 480 |
|---|---|---|
| PyTorch (`.pt`) | 44.5 ms (22 FPS) | 31.1 ms (32 FPS) |
| **OpenVINO** | 52.5 ms (19 FPS) | **26.4–27.7 ms (36–38 FPS)** |

- La combinación más rápida es **OpenVINO a 480 px**: unos 4 ms menos por imagen que PyTorch (~13 %).
- A 640 px, OpenVINO no ganó en nuestra medición. Por eso bajamos a 480.
- **Seamos honestos si lo preguntan:** lo que más pesó en los FPS no fue OpenVINO solo, sino la entrada de 480 px y el **turbo de la CPU**. Con el turbo apagado, la misma detección tardaba unos 150 ms.

### 4. ¿Por qué MediaPipe para los rostros?

- **COCO no tiene la clase "rostro"**, así que YOLOv8n no puede detectarlos. Entrenar un modelo propio estaba fuera del alcance.
- BlazeFace ("BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs", Bazarevsky et al., Google, 2019) está pensado justo para esto: caras cercanas a una cámara frontal.
- Es muy rápido: **3.5–3.9 ms por frame** en nuestra CPU (unos 270 FPS). Sumarlo casi no cuesta.
- Usamos la variante *short range*, que funciona para caras a menos de unos 2 m. En una foto de calle con gente lejos no detecta caras, y es lo esperado.

### 5. ¿Por qué no se detectan cuadernos ni lapiceros?

- YOLOv8n viene entrenado con **COCO-80**, que tiene `book`, `laptop`, `backpack` y `cell phone`, pero **no tiene** "cuaderno" ni "lapicero".
- **Probamos una alternativa: YOLO-World** ("YOLO-World: Real-Time Open-Vocabulary Object Detection", Cheng et al., CVPR 2024).
  - Es un detector de vocabulario abierto: se le escriben las clases en texto ("spiral notebook", "pen"), las codifica con CLIP y las cruza con lo que ve.
  - Lo generamos y exportamos a OpenVINO, pero tardó **283 ms por imagen (3.5 FPS)**. Incumplía el requisito de 15 FPS, así que lo descartamos.
- **Decisión (Plan A):**
  - El cuaderno se detecta con la clase **libro** de COCO; por eso la etiqueta dice "Libro / Cuaderno" y vale +20 (no los +15 del enunciado). En nuestras pruebas, un cuaderno de dibujo salió como libro con 41–74 %.
  - El lapicero se reemplazó por el **Celular** (+5, "Siempre conectado"). El enunciado cita el celular como clase válida.
  - Quedan **4 objetos mapeados**, que es el mínimo que pide el enunciado.
- **Trabajo futuro:** entrenar YOLOv8n con fotos propias de cuadernos y lapiceros (*fine-tuning*), o usar YOLO-World en un equipo con GPU.

### 6. ¿Qué hace el antiparpadeo?

- El detector a veces ve durante uno o dos frames un objeto que no está (falso positivo), o pierde uno que sí está. Como el modo Universitario guarda cada objeto, un falso positivo regalaría puntos.
- **Para entrar:** un objeto tiene que verse de forma estable **0.3 s** (unos 5 frames) antes de contar. Así no suma un falso positivo de un solo frame.
- **Para salir:** sigue contando como presente hasta **0.7 s** después de dejar de verse. En el modo Universitario ya no resta puntos (el objeto quedó guardado), pero en el panel evita que un hueco breve cuente como una aparición nueva. También ayuda con objetos parciales o tapados a ratos.
- Cada clase suma **una sola vez**: dos libros siguen siendo +20.
- Lo comprobamos con 11 pruebas automáticas (`tests/test_scoring.py`). Por ejemplo: con 0.25 s visible todavía no cuenta y con 0.35 s ya cuenta; un hueco de 0.5 s lo mantiene y uno de 0.8 s lo quita. Las de la ronda comprueban que lo guardado se conserva al retirarlo, que lo que aparece después del minuto no suma y que con los 4 la ronda termina antes.
- Es lógica pura en `scoring.py`, separada de la interfaz y del modelo.

### 7. ¿Cuáles son las limitaciones?

- **Clases de COCO:** no hay cuaderno ni lapicero (pregunta 5).
- **Mochila:** es la clase más difícil. Apoyada en la mesa da 10–36 % de confianza (bajo el umbral). Puesta y vista de espaldas da 52–68 %. Con contraluz baja más.
- **Laptop:** se detecta por la pantalla y el teclado, no por la tapa.
- **FPS con margen corto en la integrada:** 15.4–16.7, porque esa cámara entrega solo 15–16 cuadros por segundo a 720p. Con la USB externa la app da 19–22 FPS. En batería la app baja a ~10 FPS, y con poca luz la cámara alarga la exposición y entrega ~11 FPS.
- **Distancia:** a 480 px, los objetos pequeños o lejanos se pierden antes. Los rostros, a más de ~2 m.
- **No distingue instancias:** cuenta clases, no objetos individuales. Tampoco hace seguimiento (*tracking*) de cada objeto.
- **Depende de la luz:** por eso la app avisa cuando la imagen está oscura.

### 8. ¿Cuántos FPS da y cómo se midieron?

- **Resultado con la cámara USB externa:** General **18.9 FPS** y Universitario **21.5 FPS** (2026-10-25, laptop enchufada, turbo activo, 1280×720).
- **Con la cámara integrada:** General 15.4–15.6 FPS y Universitario 15.9–16.7 FPS (2026-10-21, dos corridas por modo, buena luz).
- **Cómo se midieron:** con `app.py --autoshot 8`, que corre la app 8 s y divide los frames procesados después de los 2 primeros segundos entre su tiempo. El FPS del panel es una media móvil sobre el tiempo entre frames.
- **Por qué no más:** la detección sola daría ~26 FPS en General y ~31 en Universitario (38 y 32 ms). La cámara integrada no entrega más de 15–16 cuadros por segundo a 720p; la USB externa da 30, y entonces el tope lo ponen la detección y el dibujo de la interfaz (19–22 FPS).
- El modo Universitario es algo más rápido porque no busca personas ni rostros.

### Otras preguntas posibles

- **¿Por qué el video sale en espejo?** Porque así lo esperamos todos, como en un espejo o una videollamada. Se voltea **antes** de detectar, para que las cajas coincidan con la imagen.
- **¿Por qué dibujan con QPainter y no con OpenCV?** `cv2.putText` no soporta tildes ni la ñ ("Aún", "Cámara"). QPainter sí, además de antialiasing y transparencias para el HUD.
- **¿Por qué 480 px y no 640?** A 640, OpenVINO tardaba 52.5 ms; a 480, 27 ms. Ganamos el doble de velocidad a cambio de algo de precisión en objetos pequeños.
- **¿Entrenaron el modelo?** No. Usamos los pesos oficiales preentrenados en COCO. El trabajo del equipo fue elegir y optimizar el modelo, integrar los dos detectores, el antiparpadeo, el puntaje y la interfaz.
- **¿Por qué el puntaje no baja al retirar un objeto?** Por diseño: es una ronda de 1 minuto y el progreso se guarda, para no obligar a sostener todos los objetos a la vez frente a la cámara. Lo que sí cambia en tiempo real al retirarlo es su caja, la lista "En pantalla" del panel y el reloj. Al terminar la ronda el puntaje vuelve a 0.
- **¿Qué pasa si se desconecta la cámara?** La app no se cierra: muestra un aviso, intenta reabrirla cada 2 s y el video vuelve solo.

---

## 4. Checklist del día de la demo

### La noche anterior

- [ ] Laptop cargada al 100 %. El **cargador** va en la mochila.
- [ ] **Video de respaldo** grabado, revisado completo y copiado al escritorio, a una memoria USB y a la nube.
- [ ] Kit de objetos:
  - [ ] **Mochila.** Mejor de color claro o con detalles (bolsillos, tirantes). Las lisas y oscuras cuestan más.
  - [ ] Libro y cuaderno.
  - [ ] **Segunda laptop** (no la que corre la app), cargada.
  - [ ] Celular.
- [ ] Cámara USB externa y su cable.
- [ ] **Lámpara o aro de luz**, y una extensión eléctrica.

### Al llegar (30 min antes)

- [ ] **Enchufar la laptop.** Nunca en batería.
- [ ] **Activar el turbo de la CPU.** Se pierde al reiniciar, así que hay que hacerlo siempre:
  ```bash
  echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
  echo performance | sudo tee /sys/firmware/acpi/platform_profile
  cat /sys/devices/system/cpu/intel_pstate/no_turbo   # debe dar 0
  ```
- [ ] Conectar la **cámara externa** y ver su índice:
  ```bash
  cd "/home/ordson/Documentos/Universidad/ia final"
  .venv/bin/python tools/cam_check.py      # guarda una foto por índice en tools/out/
  ```
  Índice de la cámara externa: **2** (verificado el 2026-10-25; la integrada es 0). La app abre la 2 por defecto.
- [ ] Ubicar la cámara con un **fondo despejado** y **sin ventana detrás** (el contraluz arruina la detección).
- [ ] **Sacar del cuadro** las mochilas, libros, laptops y celulares que no sean del kit: en modo Universitario, cualquier objeto del fondo suma puntos.
- [ ] Encender la lámpara de frente a quien muestra los objetos.
- [ ] Cerrar el navegador y otras apps pesadas: le quitan CPU a la detección.

### 10 minutos antes

- [ ] Abrir la app: `.venv/bin/python app.py` (abre la 2 sola; si la externa quedó con otro índice, `--camera N`).
- [ ] Probar los dos modos: los FPS del panel deben ser **≥ 15**.
- [ ] Probar cada objeto del kit en modo Universitario y llegar a la insignia una vez.
- [ ] Volver a modo General y pulsar **`R`** para que las estadísticas arranquen en cero.
- [ ] Dejar el video de respaldo abierto en el reproductor, en pausa, en otra ventana.

---

## 5. Cómo grabar el video de respaldo [USUARIO]

Este video lo graba el equipo; no lo graba el agente. Sirve para mostrar el proyecto si falla la cámara o el equipo el día de la demo.

**Antes de grabar:** laptop enchufada, turbo activo (sección 4), buena luz, fondo despejado y el kit de objetos a mano.

### Qué grabar (2 a 3 minutos)

| Tiempo | Contenido |
|---|---|
| 0:00–0:15 | La ventana de VisionAI abierta en modo General, con una persona en cuadro. |
| 0:15–1:15 | Modo General: persona, rostro, celular, libro y laptop con sus cajas. Apagar y prender cada casilla. Mover el slider de confianza. Capturar con `Espacio`. |
| 1:15–2:30 | Modo Universitario (`M`): con el reloj corriendo, los objetos entran uno a uno hasta la insignia NIVEL UNIVERSITARIO y luego hasta 60 (**¡COMPLETO!**). Esperar los 5 s del resultado para que se vea la vuelta a 0. |
| 2:30–3:00 | Plano del panel lateral: FPS, mejor puntaje y apariciones. |

### Con SimpleScreenRecorder (ya está instalado)

Este equipo usa Linux Mint con escritorio Cinnamon, que no trae grabador de pantalla propio. El atajo `Ctrl+Alt+Shift+R` de GNOME **no funciona** aquí. Usen SimpleScreenRecorder (los nombres de los botones pueden variar un poco según el idioma):

1. Abran la app VisionAI y déjenla en modo General.
2. Abran **SimpleScreenRecorder** desde el menú y pulsen **Continuar**.
3. **Entrada:**
   - Elijan **grabar un rectángulo fijo** y pulsen **seleccionar ventana**. Hagan clic sobre la ventana de VisionAI.
   - **Cuadros por segundo: 25.** La app va a ~15, así que más no aporta y cuesta CPU.
   - El audio es opcional. Si van a narrar, activen **grabar audio**.
4. **Salida:**
   - Contenedor **MP4**, códec **H.264**, preset **superfast**.
   - Archivo: `~/Vídeos/VisionAI_respaldo.mp4`.
5. Pulsen **Comenzar grabación** (o el atajo `Ctrl+R`, si está activado en esa pantalla), sigan el guion de arriba y pulsen **Guardar grabación** al terminar.

**Durante la grabación**, miren el FPS del panel: grabar también gasta CPU. Si baja de 15, bajen los cuadros por segundo del grabador a 15. Si aun así no alcanza, filmen la pantalla con un celular, que no le quita nada a la laptop.

**Alternativa:** OBS Studio (`sudo apt install obs-studio`). No está instalado.

### Después de grabar

- [ ] Vean el video completo una vez: que se lean las etiquetas, los % y el puntaje.
- [ ] Cópienlo a una memoria USB y a la nube.
- [ ] Anoten en `PROGRESO.md` (E6): nombre del archivo, duración y fecha.
