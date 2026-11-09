# Guion de demo y defensa — VisionAI

Para los integrantes del equipo. Aquí está qué decir, qué mostrar, en qué orden y cómo responder las preguntas del docente.
Reemplacen `[Integrante 1]`, `[Integrante 2]` y `[Integrante 3]` por sus nombres. Si son más, repartan los bloques.

**Equipo actual:** Windows, **AMD Ryzen 7 3700U** (4 núcleos/8 hilos), cámara integrada **Hy-FHD(B550)-Camera**, índice **1** mediante DirectShow. Usa `.\.venv\Scripts\python.exe app.py --camera 1`. Los índices pueden cambiar en otro equipo; usa el selector de la app. Se comprobó cargador conectado y plan de energía Equilibrado, sin cambiar ajustes globales.

**Preparación pendiente:** E5 y E6 siguen abiertas. La sesión de diez minutos terminó sin errores y se verificaron controles y poca luz. Faltan el resultado 60/60, pruebas físicas restantes y el video completo; además se comprobó una confusión de cuadernos con laptop en el propio modelo original (ver `VALIDACION_MODELO.md`).

---

## Datos clave (apréndanselos)

| Dato | Valor |
|---|---|
| Modelo de objetos | **YOLOv8n** (Ultralytics), preentrenado en **COCO-80**, OpenVINO FP32. Perfil `detail`: **480 px**, predeterminado; perfil `fast`: **320 px**, opcional y pendiente de validar con objetos reales |
| Modelo de rostros | **MediaPipe BlazeFace** (`blaze_face_short_range`) |
| Interfaz | PySide6 (Qt 6), dibujo con QPainter |
| Plan del proyecto | **Plan A** (solo clases COCO). YOLO-World se probó y se descartó por lento |
| **FPS Windows: línea base** | General **7.5** · Universitario **9.3** (2026-11-07, cámara 1, 1280×720). Son mediciones previas a la optimización; consulta el resultado actual en `PROGRESO.md` antes de la demo |
| Prueba breve Windows optimizada | Perfil opcional `fast` 320, captura real **640×480**: **17.90 FPS General / 19.01 Universitario**, corridas de 30/20 s (2026-11-08). La estabilidad de diez minutos y objetos reales siguen pendientes; `detail` 480 permanece predeterminado |
| FPS Linux: referencia histórica | Con USB externa: General **18.9** · Universitario **21.5** (2026-10-25). Con integrada: General 15.4–15.6 · Universitario 15.9–16.7. Cargador, turbo activo y 1280×720; no representan esta laptop Windows |
| Detección por frame: Linux histórico | General (objetos + personas + rostros): **38 ms** (~26 FPS) · Universitario: **32 ms** (~31 FPS) |
| Límite de FPS: Linux histórico | La integrada entregaba 15–16 cuadros por segundo a 1280×720. Con USB (30 cuadros por segundo), la detección y el dibujo fijaban el techo. El cuello de botella Windows se mide por separado |
| Puntos del modo Universitario | Mochila +10 · Libro / Cuaderno +20 · Laptop +25 · Celular +5 → **máximo 60** |
| Insignia "NIVEL UNIVERSITARIO" | Con **50 puntos o más** |
| Ronda del modo Universitario | **1 minuto**. Arranca con el primer objeto; cada objeto queda **guardado** aunque se retire. Termina antes si se juntan los 4. El resultado dura **5 s** y luego vuelve a 0 |
| Antiparpadeo | Un objeto se guarda tras **0.3 s** estable. El tracker mantiene su presencia hasta **0.7 s** después de dejar de verse; el puntaje guardado dura hasta el fin de la ronda |

**Regla de oro:** usa cargador, buena luz y comprueba los FPS en el equipo de la demo. El ajuste `/sys/.../no_turbo` y la caída a unos 10 FPS con batería se observaron en Linux; no son instrucciones ni mediciones Windows.

Para comparar perfiles en Windows, cierra la app entre corridas y usa la misma escena, luz y modo:

```powershell
.\.venv\Scripts\python.exe app.py --camera 1 --quality detail --resolution 640x480 --autoshot 12
.\.venv\Scripts\python.exe app.py --camera 1 --quality fast --resolution 640x480 --autoshot 12
```

El perfil rápido conserva YOLOv8n, sus clases, BlazeFace, controles y rondas; **no garantiza la misma precisión**. También hay que probar mochila, libro/cuaderno, laptop y celular, en particular objetos pequeños o lejanos. No comparar solo el FPS ni asumir que una ventana fluida implica más detecciones correctas.

---

## 1. Pitch de 5 minutos para la feria (público mixto)

Objetivo: que cualquier persona entienda qué hace y lo vea funcionar. Nada de jerga: "la cámara reconoce objetos", no "inferencia".
Arranquen con la app abierta en modo **General**, las estadísticas reiniciadas (`R`) y los objetos escondidos fuera del cuadro.

| Tiempo | Qué pasa | Qué se dice (sugerido) |
|---|---|---|
| **0:00–0:45** — Qué es | Una persona frente a la cámara. Se ven sus cajas de Persona y Rostro. | "Esto es VisionAI. Es una aplicación que mira por la cámara y reconoce en tiempo real lo que tiene delante: personas, caras y objetos. Cada cosa que reconoce la encierra en un recuadro, le pone su nombre y qué tan segura está, en porcentaje." |
| **0:45–2:00** — Modo General | Mostrar el celular y un libro. Apagar y prender **Rostros** con su casilla. Señalar el panel de la derecha. | "Fíjense en el número: 94 % indica la confianza del modelo. Azul son personas, rosa son caras y verde son objetos. Puedo apagar lo que no quiero ver, por ejemplo las caras. A la derecha se ven los cuadros por segundo que está procesando ahora y cuántas veces apareció cada clase." |
| **2:00–4:15** — Modo Universitario | Pulsar `M`: el reloj marca 1:00 y espera. Mostrar los objetos **uno a uno** (o de a dos), en este orden: mochila puesta → libro → laptop → celular. Cuando se enciende su chip, el objeto ya se puede bajar. | "Ahora un juego: ¿estás listo para la universidad? Tengo un minuto para mostrar todo lo que llevo. Arranco en cero: 'Aún no estás listo'. Con la mochila, +10: acceso al campus, y el reloj empieza a correr. Con un libro, +20; ya lo puedo bajar, los puntos quedan guardados. Con la laptop, +25... y al pasar los 50 puntos, ¡NIVEL UNIVERSITARIO! Con el celular junto los cuatro: ¡completo!, y me dice cuánto tardé." |
| **4:15–5:00** — Cierre | Apenas salga **¡COMPLETO!** con la insignia (se ve 5 s), pulsar `Espacio` para capturar. | "Todo esto corre en la CPU de una laptop, usando una red neuronal llamada YOLO. Y si quieren, les sacamos una foto con su puntaje." |

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
| **8:00–9:30** | [Integrante 2] | Robustez | **Poca luz:** tapar casi toda la lente con la mano 2 s y comprobar franja amarilla y "Luz: Baja". **Objeto parcial:** probar una laptop parcialmente fuera del cuadro. **Quitar y poner rápido:** comprobar el filtro de presencia y que la ronda no duplica puntos. **USB, si se dispone de una:** desconectar y reconectar; comprobar aviso y recuperación. La integrada no se desenchufa. *(Pruebas físicas pendientes: ensayarlas antes y mostrar únicamente resultados comprobados.)* | Extra feria |
| **9:30–12:30** | [Integrante 1] | Cómo funciona | Por qué YOLOv8n (pregunta 1), cómo funciona por dentro (pregunta 2), OpenVINO y FPS reales (preguntas 3 y 8), rostros (pregunta 4), Plan A (pregunta 5), antiparpadeo (pregunta 6). Si piden código: `detector.py` (detección), `scoring.py` (puntaje), `config.py` (clases y puntos). | Justificación del modelo |
| **12:30–15:00** | Todos | Preguntas | Limitaciones (pregunta 7) y las que haga el docente. | — |

**Si algo falla en vivo:**
- **No hay video en Windows:** prueben `--camera 1`, cierren otras apps que usen la cámara y revisen permisos de cámara para aplicaciones de escritorio. Si cambió el índice, usen el selector. Los índices Linux históricos eran integrada 0 y USB 2.
- **FPS bajo 15:** conecten el cargador, mejoren la luz y consulten la configuración y medición actuales de `PROGRESO.md`. El comando de turbo Linux no se aplica a Windows.
- **Un objeto no se detecta:** acérquenlo a 50–80 cm, mejoren la luz y gírenlo (laptop con la pantalla, mochila puesta). Último recurso: bajar el slider de confianza a 25–30 %.
- **La app se cuelga:** `Ctrl+Q` y vuelvan a abrirla (tarda unos segundos en cargar los modelos). Si no se recupera, pongan el **video de respaldo**.

---

## 3. Preguntas y respuestas de defensa

### 1. ¿Por qué YOLOv8n y no SSD o MediaPipe?

Porque ofrece la mayor precisión publicada de estos tres modelos y una versión pequeña para CPU. Se eligió con pruebas Linux que superaban 15 FPS; en Windows el cumplimiento se acredita con sus propias mediciones actuales.

| Modelo | Precisión en COCO (mAP50-95) | Comentario |
|---|---|---|
| **YOLOv8n** | **37.3** | 3.2 M de parámetros, 8.7 GFLOPs. La "n" es *nano*, la versión más pequeña de la familia (n, s, m, l, x). |
| MediaPipe Object Detector (EfficientDet-Lite0) | 25.7 | Muy bueno para móviles. MediaPipe es excelente en rostros y manos, pero su detector general es menos preciso. |
| SSD MobileNet v2 | ~20–22 | Rápido en móviles, pero unos 15 puntos menos que YOLOv8n. |

- Las cifras son oficiales: Ultralytics para YOLOv8n (COCO val2017, entrada de 640), la documentación de TensorFlow Lite para EfficientDet-Lite0 y el *model zoo* de TensorFlow para SSD.
- En el equipo Linux original, YOLOv8n tardó **26–28 ms por imagen** con OpenVINO. Es el benchmark que justificó la elección; no es el tiempo de inferencia de esta laptop Windows.
- Si preguntan por qué no una versión más grande: YOLOv8s tiene más del triple de cálculo (28.6 GFLOPs frente a 8.7). No la medimos, pero el margen que nos queda no alcanza para eso. YOLOv8s-World, de ese tamaño, sí la medimos: 283 ms.
- **Matiz honesto:** el 37.3 se mide con imágenes de 640 px. Los perfiles usan **480 o 320 px**; no se ha medido su mAP. En el benchmark Linux bajar de 640 a 480 pasó de 52.5 ms a unos 27 ms. Reducir la entrada puede perder objetos pequeños o lejanos; los FPS Windows se miden por separado.

### 2. ¿Cómo funciona YOLO por dentro?

"YOLO" significa *You Only Look Once*: mira la imagen **una sola vez** y en esa pasada predice todas las cajas y sus clases. Es un detector **de una etapa** (no propone regiones primero para clasificarlas después) y **sin anchors**: predice directamente el centro del objeto y la distancia a cada borde, en lugar de ajustar cajas de tamaño predefinido.

Paso a paso, con nuestros números:

1. **Letterbox:** la imagen de la cámara (640×480 por defecto en Windows) se adapta a la entrada de 480 en `detail` o 320 en `fast`, manteniendo la proporción y rellenando con gris.
2. **Backbone (CSPDarknet con bloques C2f):** red convolucional que extrae características: bordes, texturas, partes de objetos.
3. **Neck (PAN-FPN):** mezcla las características de 3 escalas, para detectar a la vez objetos grandes y pequeños.
4. **Head desacoplado:** en cada celda de las 3 escalas predice por separado la caja (con DFL, que estima cada borde como una distribución de probabilidad) y el puntaje de cada una de las 80 clases.
   - Con strides 8, 16 y 32: a **320 px** salen 40×40 + 20×20 + 10×10 = **2100 candidatos**; a **480 px**, 60×60 + 30×30 + 15×15 = **4725**; a **640 px**, **8400**.
5. **Filtro por confianza:** se descartan los candidatos por debajo del umbral del slider (35 % por defecto).
6. **NMS (*non-maximum suppression*):** si dos cajas de la misma clase se solapan más de un 70 % (IoU 0.7), queda solo la de mayor confianza.

Después, nuestro código pasa las cajas a coordenadas del frame, se queda con las clases que nos interesan, traduce la etiqueta al español y la dibuja.

**Qué es el % que se ve:** es la confianza del modelo en que la caja contiene esa clase. No es la exactitud del sistema. Un 90 % no significa que acierte 9 de cada 10 veces.

### 3. ¿Qué es OpenVINO y por qué se usa?

OpenVINO es un kit de Intel que convierte el modelo a su propio formato (archivos `.xml` y `.bin`) y lo optimiza para CPU, entre otros dispositivos. La aplicación ejecuta la inferencia en CPU. El equipo Linux usado para el benchmark tenía un Intel Core i5-1235U; no hay que atribuir ese procesador a la laptop Windows actual.

Medición histórica Linux de YOLOv8n (100 frames reales de la cámara, turbo activo):

| Formato | Entrada 640 | Entrada 480 |
|---|---|---|
| PyTorch (`.pt`) | 44.5 ms (22 FPS) | 31.1 ms (32 FPS) |
| **OpenVINO** | 52.5 ms (19 FPS) | **26.4–27.7 ms (36–38 FPS)** |

- La combinación más rápida de aquel benchmark fue **OpenVINO a 480 px**: unos 4 ms menos por imagen que PyTorch (~13 %).
- A 640 px, OpenVINO no ganó en nuestra medición. Por eso bajamos a 480.
- **Seamos honestos si lo preguntan:** lo que más pesó en los FPS no fue OpenVINO solo, sino la entrada de 480 px y el **turbo de la CPU**. Con el turbo apagado, la misma detección tardaba unos 150 ms.

### 4. ¿Por qué MediaPipe para los rostros?

- **COCO no tiene la clase "rostro"**, así que YOLOv8n no puede detectarlos. Entrenar un modelo propio estaba fuera del alcance.
- BlazeFace ("BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs", Bazarevsky et al., Google, 2019) está pensado justo para esto: caras cercanas a una cámara frontal.
- En el benchmark Linux tardó **3.5–3.9 ms por frame** (unos 270 FPS de inferencia). Su coste Windows se mide en ese equipo.
- Usamos la variante *short range*, que funciona para caras a menos de unos 2 m. En una foto de calle con gente lejos no detecta caras, y es lo esperado.

### 5. ¿Por qué no se detectan cuadernos ni lapiceros?

- YOLOv8n viene entrenado con **COCO-80**, que tiene `book`, `laptop`, `backpack` y `cell phone`, pero **no tiene** "cuaderno" ni "lapicero".
- **Probamos una alternativa: YOLO-World** ("YOLO-World: Real-Time Open-Vocabulary Object Detection", Cheng et al., CVPR 2024).
  - Es un detector de vocabulario abierto: se le escriben las clases en texto ("spiral notebook", "pen"), las codifica con CLIP y las cruza con lo que ve.
  - En el equipo Linux lo generamos y exportamos a OpenVINO, pero tardó **283 ms por imagen (3.5 FPS)**. Incumplía el requisito de 15 FPS allí, así que lo descartamos.
- **Decisión (Plan A):**
  - El cuaderno se detecta con la clase **libro** de COCO; por eso la etiqueta dice "Libro / Cuaderno" y vale +20 (no los +15 del enunciado). En nuestras pruebas, un cuaderno de dibujo salió como libro con 41–74 %.
  - El lapicero se reemplazó por el **Celular** (+5, "Siempre conectado"). El enunciado cita el celular como clase válida.
  - Quedan **4 objetos mapeados**, que es el mínimo que pide el enunciado.
- **Trabajo futuro:** entrenar YOLOv8n con fotos propias de cuadernos y lapiceros (*fine-tuning*), o usar YOLO-World en un equipo con GPU.

### 6. ¿Qué hace el antiparpadeo?

- El detector a veces ve durante uno o dos frames un objeto que no está (falso positivo), o pierde uno que sí está. Como el modo Universitario guarda cada objeto, un falso positivo regalaría puntos.
- **Para entrar:** un objeto tiene que verse de forma estable **0.3 s** (unos 5 frames) antes de contar. Así no suma un falso positivo de un solo frame.
- **Para salir:** el tracker sigue considerando presente la clase hasta **0.7 s** después de dejar de verse. Ese margen evita que un hueco breve cuente como una aparición nueva. La lista de detecciones actuales y sus cajas pueden desaparecer antes; el puntaje de la ronda permanece porque el objeto ya se guardó.
- Cada clase suma **una sola vez**: dos libros siguen siendo +20.
- Lo comprobamos con 11 pruebas automáticas (`tests/test_scoring.py`). Por ejemplo: con 0.25 s visible todavía no cuenta y con 0.35 s ya cuenta; un hueco de 0.5 s lo mantiene y uno de 0.8 s lo quita. Las de la ronda comprueban que lo guardado se conserva al retirarlo, que lo que aparece después del minuto no suma y que con los 4 la ronda termina antes.
- Es lógica pura en `scoring.py`, separada de la interfaz y del modelo.

### 7. ¿Cuáles son las limitaciones?

- **Clases de COCO:** no hay cuaderno ni lapicero (pregunta 5).
- **Mochila:** es la clase más difícil. Apoyada en la mesa da 10–36 % de confianza (bajo el umbral). Puesta y vista de espaldas da 52–68 %. Con contraluz baja más.
- **Laptop:** se detecta por la pantalla y el teclado, no por la tapa.
- **Rendimiento dependiente del equipo:** la línea base Windows fue 7.5 FPS General y 9.3 Universitario; consulta los resultados posteriores de `PROGRESO.md`. Históricamente Linux daba 15.4–16.7 con integrada y 19–22 con USB; en batería bajaba a unos 10. Esos valores no se trasladan a Windows.
- **Distancia y tamaño de entrada:** los objetos pequeños o lejanos pueden perderse al reducir la entrada; el riesgo aumenta en `fast` 320 frente a `detail` 480. BlazeFace conserva su modelo; los rostros a más de unos 2 m siguen siendo una limitación.
- **No distingue instancias:** cuenta clases, no objetos individuales. Tampoco hace seguimiento (*tracking*) de cada objeto.
- **Depende de la luz:** por eso la app avisa cuando la imagen está oscura.

### 8. ¿Cuántos FPS da y cómo se midieron?

- **Windows actual, línea base previa a optimización:** General **7.5 FPS** y Universitario **9.3 FPS** (2026-11-07, cámara integrada 1, DirectShow, 1280×720). Consultar la medición final en `PROGRESO.md` antes de citar cifras de la demo.
- **Diagnóstico Windows posterior:** la captura sola a 1280×720 entrega unos **10 FPS**, aunque el driver acepte pedir 30. A 640×480 entrega unos **30 FPS**, pero con el modelo 480 la app midió General **7.52** y Universitario **8.25**. Con los ajustes de CPU y `QThread`, el perfil opcional 320 midió después **17.90/19.01 FPS** en corridas de 30/20 s. Un primer ensayo asíncrono había dado 6.54/15.68: consultar la sesión larga y los objetos reales antes de citar cifras estables para la demo.
- **Referencia histórica Linux con USB:** General **18.9 FPS** y Universitario **21.5 FPS** (2026-10-25, cargador, turbo activo, 1280×720).
- **Referencia histórica Linux con integrada:** General 15.4–15.6 FPS y Universitario 15.9–16.7 FPS (2026-10-21, dos corridas por modo, buena luz).
- **Cómo se midieron:** con `app.py --autoshot 8`, que corre la app 8 s y divide los frames procesados después de los 2 primeros segundos entre su tiempo. El FPS del panel es una media móvil sobre el tiempo entre frames.
- **Qué limita los FPS:** en Linux la integrada limitaba a 15–16 y con USB el coste de detección y dibujo limitaba a 19–22. El diagnóstico Windows debe separar captura, inferencia y dibujo antes de atribuirle el mismo cuello de botella.
- El modo Universitario es algo más rápido porque no busca personas ni rostros.

### Otras preguntas posibles

- **¿Por qué el video sale en espejo?** Porque así lo esperamos todos, como en un espejo o una videollamada. Se voltea **antes** de detectar, para que las cajas coincidan con la imagen.
- **¿Por qué dibujan con QPainter y no con OpenCV?** `cv2.putText` no soporta tildes ni la ñ ("Aún", "Cámara"). QPainter sí, además de antialiasing y transparencias para el HUD.
- **¿Por qué 480 o 320 px y no 640?** E0 eligió 480 por el benchmark Linux. En Windows hay un perfil opcional 320 para reducir cálculo con los mismos pesos y clases. El perfil 480 permanece disponible; elegir 320 exige comprobar FPS y detección de objetos reales, porque puede perder objetos pequeños o lejanos.
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

### Al llegar (30 min antes, Windows)

- [ ] **Enchufar la laptop.** Nunca en batería.
- [ ] Revisar el modo de energía Windows y cerrar aplicaciones que compitan por la CPU o la cámara.
- [ ] Abrir la app con la **cámara integrada**:
  ```powershell
  .\.venv\Scripts\python.exe app.py --camera 1
  ```
  Índice **1**, DirectShow, verificado en esta laptop. Si se usa otra cámara o cambia el índice, elegirla en el selector. `tools/cam_check.py` es una herramienta Linux y no se usa para este diagnóstico Windows.
- [ ] Ubicar la cámara con un **fondo despejado** y **sin ventana detrás** (el contraluz arruina la detección).
- [ ] **Sacar del cuadro** las mochilas, libros, laptops y celulares que no sean del kit: en modo Universitario, cualquier objeto del fondo suma puntos.
- [ ] Encender la lámpara de frente a quien muestra los objetos.
- [ ] Cerrar el navegador y otras apps pesadas: le quitan CPU a la detección.

### 10 minutos antes

- [ ] Abrir la app: `.\.venv\Scripts\python.exe app.py --camera 1`.
- [ ] Probar los dos modos: los FPS del panel deben ser **≥ 15**.
- [ ] Anotar el perfil (`detail` o `fast`) y resolución efectiva de la corrida. Si se usa `fast`, verificar antes los cuatro objetos reales y sus limitaciones de distancia.
- [ ] Probar cada objeto del kit en modo Universitario y llegar a la insignia una vez.
- [ ] Volver a modo General y pulsar **`R`** para que las estadísticas arranquen en cero.
- [ ] Dejar el video de respaldo abierto en el reproductor, en pausa, en otra ventana.

### Cierre del proyecto: evidencia que sigue pendiente

- [x] Sesión continua de diez minutos: 10,513 resultados, sin errores registrados; pico RSS 649.36 MiB. Ver límites de FPS durante grabación en PROGRESO.
- [x] Interruptores, slider, captura, reinicio y poca luz confirmados por el usuario; confianza, reinicios y luz registrados también por el observador.
- [ ] Objeto parcial y quitar/poner objetos rápido; anotar el resultado efectivo.
- [ ] Mostrar los cuatro objetos hasta el badge y **¡COMPLETO!**, retirar objetos sin perder puntos, comprobar fin por tiempo y reinicio de ronda.
- [ ] Desconectar y reconectar una USB si está disponible; si solo hay integrada, registrar que esa prueba física no se hizo.
- [ ] Grabar y revisar el video de respaldo; anotar archivo, duración y fecha en `PROGRESO.md`.

El registro Linux del ajuste de turbo y la cámara USB 2 se conserva en README/PROGRESO como referencia histórica. E5/E6 solo se cierran cuando sus criterios están respaldados por evidencia.

---

## 5. Cómo grabar el video de respaldo [USUARIO]

Este video lo graba el equipo; no lo graba el agente. Sirve para mostrar el proyecto si falla la cámara o el equipo el día de la demo.

**Antes de grabar:** laptop enchufada, app Windows con cámara 1, buena luz, fondo despejado y el kit de objetos a mano. Revisar los FPS mientras se graba.

### Qué grabar (2 a 3 minutos)

| Tiempo | Contenido |
|---|---|
| 0:00–0:15 | La ventana de VisionAI abierta en modo General, con una persona en cuadro. |
| 0:15–1:15 | Modo General: persona, rostro, celular, libro y laptop con sus cajas. Apagar y prender cada casilla. Mover el slider de confianza. Capturar con `Espacio`. |
| 1:15–2:30 | Modo Universitario (`M`): con el reloj corriendo, los objetos entran uno a uno hasta la insignia NIVEL UNIVERSITARIO y luego hasta 60 (**¡COMPLETO!**). Esperar los 5 s del resultado para que se vea la vuelta a 0. |
| 2:30–3:00 | Plano del panel lateral: FPS, mejor puntaje y apariciones. |

### Windows: Xbox Game Bar

1. Abran VisionAI y dejen su ventana activa. Pulsen `Win+G` para comprobar que Game Bar está disponible.
2. Pulsen `Win+Alt+R` para iniciar la grabación; repitan el atajo al terminar el guion. `Win+Alt+M` activa o desactiva el micrófono.
3. Busquen el archivo **MP4** en **Vídeos → Capturas** y revisen que se ven la ventana, las etiquetas y el puntaje.

Estos atajos y la ubicación están documentados por [Microsoft Support](https://support.microsoft.com/es-es/accessibility/windows/use-a-screen-reader-to-record-your-screen-with-xbox-game-bar). Se verificó una grabación reproducible de **25.989 s** en esta laptop; el usuario confirmó que grabar reduce el rendimiento. Ese clip corto todavía no cubre el respaldo completo de 2–3 minutos.

Si no se puede grabar esa ventana o los FPS caen al grabar, filmen la pantalla con un celular. SimpleScreenRecorder era el grabador del equipo Linux histórico; no se presupone instalado en Windows.

### Después de grabar

- [ ] Vean el video completo una vez: que se lean las etiquetas, los % y el puntaje.
- [ ] Cópienlo a una memoria USB y a la nube.
- [ ] Anoten en `PROGRESO.md` (E6): nombre del archivo, duración y fecha.
