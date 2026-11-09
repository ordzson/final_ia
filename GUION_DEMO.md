# Guion de demo y defensa — VisionAI

Para los integrantes del equipo. Aquí está qué decir, qué mostrar, en qué orden y cómo responder las preguntas del docente.
Reemplacen `[Integrante 1]`, `[Integrante 2]` y `[Integrante 3]` por sus nombres. Si son más, repartan los bloques.

**Equipo actual:** Windows, **AMD Ryzen 7 3700U** (4 núcleos/8 hilos), cámara integrada **Hy-FHD(B550)-Camera**, índice **1** mediante DirectShow. Usa `.\.venv\Scripts\python.exe app.py --camera 1`. Los índices pueden cambiar en otro equipo; usa el selector de la app. Se comprobó cargador conectado y plan de energía Equilibrado, sin cambiar ajustes globales.

**Prioridad actual:** distinguir mejor cuaderno y laptop, aunque bajen los FPS. Windows inicia con **YOLO26s a 640**, perfil `accurate`. La app da alrededor de **3–4 FPS** en este equipo: **no cumple los ≥15 FPS de la rúbrica**. El usuario aceptó esta prioridad; E5 y E6 siguen abiertas por ese requisito y por las pruebas físicas y el respaldo pendientes. La sesión anterior de diez minutos corresponde al perfil rápido, no acredita estabilidad prolongada del modelo nuevo. Ver [VALIDACION_MODELO.md](VALIDACION_MODELO.md).

---

## Datos clave (apréndanselos)

| Dato | Valor |
|---|---|
| Modelo de objetos actual | **YOLOv8n COCO** a 480 en el perfil predeterminado `detail`, más **YOLOv8n de útiles** a 640, ambos OpenVINO FP32 |
| Otros perfiles COCO | `fast`: YOLOv8n a 320; `accurate`: YOLO26s a 640 |
| Modelo de rostros | **MediaPipe BlazeFace** (`blaze_face_short_range`) |
| Interfaz | PySide6 (Qt 6), dibujo QPainter/RGB32; YOLO y rostros en un `QThread`, captura/controles/puntaje en GUI |
| Clases adicionales | Lápiz, cuaderno y lapicero, ajustadas con School supplies y detector_de_utiles |
| **FPS Windows: línea base** | General **7.5** · Universitario **9.3** (2026-11-07, cámara 1, 1280×720). Son mediciones previas a la optimización; consulta el resultado actual en `PROGRESO.md` antes de la demo |
| FPS Windows actual: `accurate` | Alrededor de **3–4 FPS**. Corrida Universitario de 20 s: **3.45 FPS**, 62 resultados en **17.9937 s** útiles, sin error. Una corrida de 25 s empezó en General, pero el usuario pasó a Uni: no es una medida exclusiva de General |
| FPS Windows: historial `fast` | **17.90 FPS General / 19.01 Universitario** en corridas breves; sesión anterior de 600 s: **17.71 FPS** en Uni, con caída a unos 5 al grabar. Son cifras de YOLOv8n 320, no de `accurate` |
| FPS Linux: referencia histórica | Con USB externa: General **18.9** · Universitario **21.5** (2026-10-25). Con integrada: General 15.4–15.6 · Universitario 15.9–16.7. Cargador, turbo activo y 1280×720; no representan esta laptop Windows |
| Detección por frame: Linux histórico | General (objetos + personas + rostros): **38 ms** (~26 FPS) · Universitario: **32 ms** (~31 FPS) |
| Límite de FPS: Linux histórico | La integrada entregaba 15–16 cuadros por segundo a 1280×720. Con USB (30 cuadros por segundo), la detección y el dibujo fijaban el techo. El cuello de botella Windows se mide por separado |
| Puntos del modo Universitario | Mochila +10 · Cuaderno +15 · Libro +20 · Laptop +25 · Lapicero +5 → **máximo 75** |
| Insignia "NIVEL UNIVERSITARIO" | Con **50 puntos o más** |
| Puntaje en vivo | El puntaje suma los tipos visibles y disminuye al retirarlos. `--uni-round` activa el juego acumulativo de 60 s |
| Antiparpadeo | Un objeto suma tras **0.3 s** de presencia estable y deja de sumar tras **0.7 s** sin detección |

**Regla de oro:** usa cargador, buena luz y comprueba los FPS en el equipo de la demo. El ajuste `/sys/.../no_turbo` y la caída a unos 10 FPS con batería se observaron en Linux; no son instrucciones ni mediciones Windows.

Para elegir un perfil en Windows, cierra la app entre corridas:

```powershell
.\.venv\Scripts\python.exe app.py --camera 1 --quality accurate --resolution 640x480
.\.venv\Scripts\python.exe app.py --camera 1 --quality detail --resolution 640x480 --autoshot 12
.\.venv\Scripts\python.exe app.py --camera 1 --quality fast --resolution 640x480 --autoshot 12
```

Los tres perfiles conservan las clases de la app, BlazeFace, controles y rondas, pero cambian el detector y sus resultados. `accurate` mejoró esta confusión cuaderno/laptop y el F1 de la muestra pública; también añadió falsos positivos y sigue fallando con páginas abiertas. `fast` reduce cálculo, con mayor riesgo de omitir objetos pequeños o lejanos. Las funciones disponibles no garantizan la misma precisión.

---

## 1. Pitch de 5 minutos para la feria (público mixto)

Objetivo: que cualquier persona entienda qué hace y lo vea funcionar. Nada de jerga: "la cámara reconoce objetos", no "inferencia".
Arranquen con la app abierta en modo **General**, las estadísticas reiniciadas (`R`) y los objetos escondidos fuera del cuadro.

| Tiempo | Qué pasa | Qué se dice (sugerido) |
|---|---|---|
| **0:00–0:45** — Qué es | Una persona frente a la cámara. Se ven sus cajas de Persona y Rostro. | "Esto es VisionAI. Es una aplicación que mira por la cámara y reconoce en tiempo real lo que tiene delante: personas, caras y objetos. Cada cosa que reconoce la encierra en un recuadro, le pone su nombre y qué tan segura está, en porcentaje." |
| **0:45–2:00** — Modo General | Mostrar el celular y un libro. Apagar y prender **Rostros** con su casilla. Señalar el panel de la derecha. | "Fíjense en el número: 94 % indica la confianza del modelo. Azul son personas, rosa son caras y verde son objetos. Puedo apagar lo que no quiero ver, por ejemplo las caras. A la derecha se ven los cuadros por segundo que está procesando ahora y cuántas veces apareció cada clase." |
| **2:00–4:15** — Modo Universitario | Pulsar `M`. Mostrar laptop, libro y cuaderno separados en el cuadro. Mostrar también mochila y lapicero. Retirar un objeto y señalar el cambio de puntaje. | "Cada tipo de objeto que ven suma una vez. Una laptop vale 25 y un cuaderno vale 15. Con 50 puntos aparece Nivel Universitario. Al retirar un objeto, el puntaje baja." |
| **4:15–5:00** — Cierre | Pulsar `Espacio` con la insignia visible para capturar. | "YOLO encuentra los objetos en cada imagen y muestra una caja con su confianza. Podemos guardar la imagen con su puntaje." |

**Libro, laptop y cuaderno suman 60 puntos** cuando los tres permanecen visibles y se detectan.

**Cómo mostrar cada objeto para que se detecte:**
- **Mochila:** ensayar puesta en la espalda, de espaldas o de 3/4 y entera en cuadro. Esa postura ayudó en las pruebas anteriores; comprobarla con `accurate` y la mochila de la demo.
- **Laptop:** ensayar con pantalla y teclado hacia la cámara, y comprobar también la tapa cerrada y su presencia junto al cuaderno. Usar una segunda laptop; no asumir que todas las vistas se reconocen.
- **Libro y cuaderno:** ensayar ambos juntos, con el cuaderno abierto y cerrado. Son clases distintas y suman puntos por separado.
- **Lapicero:** ensayar cerca de la cámara y mostrarlo separado de un lápiz para comprobar las dos etiquetas en General.
- **Celular:** en la mano, con la pantalla o el dorso hacia la cámara.

---

## 2. Demo de 15 minutos ante el docente

Ensáyenla en **13 minutos** para tener margen. Cada bloque apunta a un criterio de la rúbrica.

| Tiempo | Quién | Bloque | Qué se muestra o se dice | Rúbrica |
|---|---|---|---|---|
| **0:00–1:30** | [Integrante 1] | Presentación | El problema y la solución en una frase. Arquitectura: captura y espejo en GUI → YOLO26s + BlazeFace en worker → resultado vigente → antiparpadeo, puntaje y QPainter en GUI. Se priorizó distinguir cuaderno/laptop y se declara el coste actual de 3–4 FPS. | Demo (10) |
| **1:30–4:30** | [Integrante 2] | Modo General en vivo | Persona, rostro, celular, libro y laptop con caja, etiqueta en español y %. Apagar y prender **Objetos**, **Personas** y **Rostros**. Subir la confianza a 70 % (salen menos cajas) y bajarla a 20 % (salen más). Panel: FPS, tiempo, "En pantalla" y "Apariciones". **Capturar** con `Espacio` y abrir el PNG de `capturas/`. | Integración del modelo (30) · Interfaz (30) |
| **4:30–8:00** | [Integrante 3] | Modo Universitario | Pulsar `M`. Mostrar al menos cuatro tipos, señalar las cajas, los puntos flotantes, los chips y el nivel. Retirar uno y mostrar la reducción del puntaje. Volver a mostrarlo para recuperar la insignia. | Modo universitario (30) |
| **8:00–9:30** | [Integrante 2] | Robustez | **Poca luz:** tapar casi toda la lente con la mano 2 s y comprobar franja amarilla y "Luz: Baja". **Objeto parcial:** probar una laptop parcialmente fuera del cuadro. **Quitar y poner rápido:** comprobar el filtro de presencia y que la ronda no duplica puntos. **USB, si se dispone de una:** desconectar y reconectar; comprobar aviso y recuperación. La integrada no se desenchufa. *(Pruebas físicas pendientes: ensayarlas antes y mostrar únicamente resultados comprobados.)* | Extra feria |
| **9:30–12:30** | [Integrante 1] | Cómo funciona | Por qué YOLO26s (pregunta 1), flujo de detección (pregunta 2), OpenVINO y FPS reales (preguntas 3 y 8), rostros (pregunta 4), cuadernos y dataset (pregunta 5), antiparpadeo (pregunta 6). Si piden código: `detector.py`, `scoring.py`, `config.py` y evaluación con cajas en `tools/evaluate_detection.py`. | Justificación del modelo |
| **12:30–15:00** | Todos | Preguntas | Limitaciones (pregunta 7) y las que haga el docente. | — |

**Si algo falla en vivo:**
- **No hay video en Windows:** prueben `--camera 1`, cierren otras apps que usen la cámara y revisen permisos de cámara para aplicaciones de escritorio. Si cambió el índice, usen el selector. Los índices Linux históricos eran integrada 0 y USB 2.
- **FPS bajo 15:** con `accurate` es una limitación conocida: alrededor de 3–4. No prometer que una lámpara o el cargador la resuelven. Se puede elegir `fast` si se acepta su menor reconocimiento; dejar registrado el perfil usado. El comando de turbo Linux no se aplica a Windows.
- **Un objeto no se detecta:** acérquenlo a 50–80 cm, mejoren la luz y gírenlo (laptop con la pantalla, mochila puesta). Último recurso: bajar el slider de confianza a 25–30 %.
- **La app se cuelga:** `Ctrl+Q` y vuelvan a abrirla (tarda unos segundos en cargar los modelos). Si no se recupera, pongan el **video de respaldo**.

---

## 3. Preguntas y respuestas de defensa

### 1. ¿Por qué usamos ahora YOLO26s?

El perfil `detail` usa YOLOv8n COCO a 480 y un segundo YOLOv8n ajustado a 640 para lápiz, cuaderno y lapicero. Ambos usan OpenVINO FP32. En el Ryzen 5 3600, la app procesó 17.48 FPS en General y 18.72 FPS en Universitario con imágenes reproducidas. El equipo debe medir la cámara que usará en la demo.

En **45 imágenes reservadas de COCO val2017**, con confianza 0.35 y matching de la misma clase a IoU ≥0.5:

| Resultado | `fast` YOLOv8n 320 | `accurate` YOLO26s 640 |
|---|---:|---:|
| Laptops correctas / 23 | 12 | **16** |
| Falsos positivos laptop | 5 | **4** |
| Libros correctos / 43 | 0 | **12** |
| Falsos positivos libro | 0 | **2** |
| F1 macro de 13 clases | 39.3 % | **61.4 %** |
| Falsos positivos totales | **20** | 44 |

La mejora incluye un coste: más falsos positivos globales y unos 3–4 FPS en esta CPU. No mejoró todas las clases ni cumple el requisito de 15 FPS. Las 45 imágenes son una muestra pequeña reservada, no el test oficial COCO ni una medida de mAP. La elección y las predicciones completas están en [VALIDACION_MODELO.md](VALIDACION_MODELO.md).

**Historia:** YOLOv8n fue la elección inicial en el equipo Linux y permanece disponible en `detail`/`fast`. Sus cifras publicadas y sus benchmarks anteriores no describen YOLO26s. MediaPipe se conserva para rostros, una tarea distinta de la detección de objetos COCO.

### 2. ¿Cómo funciona YOLO por dentro?

"YOLO" significa *You Only Look Once*. La red procesa la imagen y produce predicciones de cajas y clases. En la defensa describimos el flujo del modelo actual; los bloques concretos cambian entre familias de YOLO.

Paso a paso, con nuestros números:

1. **Letterbox:** la imagen de la cámara, 640×480 por defecto en Windows, se adapta a la entrada **640×640** de `accurate`, manteniendo la proporción y añadiendo relleno.
2. **Backbone:** extrae características visuales, desde bordes y texturas hasta partes de objetos.
3. **Combinación de escalas:** integra características de distintas resoluciones para objetos de varios tamaños.
4. **Cabeza de detección:** produce cajas y puntuaciones de clase según la arquitectura de YOLO26s.
5. **Postproceso compatible con el modelo:** se aplica el umbral de confianza y se obtienen las detecciones finales. El valor inicial visible es 35 %.

Después, nuestro código pasa las cajas a coordenadas del frame, se queda con las clases que nos interesan, traduce la etiqueta al español y la dibuja.

**Qué es el % que se ve:** es la confianza del modelo en que la caja contiene esa clase. No es la exactitud del sistema. Un 90 % no significa que acierte 9 de cada 10 veces.

### 3. ¿Qué es OpenVINO y por qué se usa?

OpenVINO es un kit de Intel que convierte el modelo a su propio formato (archivos `.xml` y `.bin`) y lo optimiza para CPU, entre otros dispositivos. La aplicación ejecuta la inferencia en CPU. El equipo Linux usado para el benchmark tenía un Intel Core i5-1235U; no hay que atribuir ese procesador a la laptop Windows actual.

Actualmente se exportó YOLO26s a **640 FP32**. En las 35 capturas propias, esa exportación conservó los conteos por vista del `.pt` de YOLO26s; no se asegura equivalencia numérica en toda imagen posible. Mantener OpenVINO no garantiza 15 FPS: el modelo actual da alrededor de 3–4 en esta CPU.

**Referencia histórica:** con YOLOv8n en Linux, OpenVINO a 480 midió 26.4–27.7 ms frente a 31.1 ms de PyTorch. A 640 OpenVINO fue más lento. Esa comparación explica la configuración anterior; no mide la aceleración de YOLO26s en Windows.

### 4. ¿Por qué MediaPipe para los rostros?

- **COCO no tiene la clase "rostro"**. Los detectores de objetos COCO usados aquí se complementan con BlazeFace para esa tarea.
- BlazeFace ("BlazeFace: Sub-millisecond Neural Face Detection on Mobile GPUs", Bazarevsky et al., Google, 2019) está pensado justo para esto: caras cercanas a una cámara frontal.
- En el benchmark Linux tardó **3.5–3.9 ms por frame** (unos 270 FPS de inferencia). Su coste Windows se mide en ese equipo.
- Usamos la variante *short range*, que funciona para caras a menos de unos 2 m. En una foto de calle con gente lejos no detecta caras, y es lo esperado.

### 5. ¿Ya distingue todos los cuadernos de las laptops? ¿Con qué datos se probó?

El perfil COCO detecta libros y laptops. El detector complementario se entrenó para lápices, cuadernos y lapiceros. Consulta [las pruebas del detector complementario](DATASET_RECONOCIMIENTO.md) y ensaya cuadernos y laptops reales juntos antes de la demo.

En las **mismas 35 capturas propias**, al umbral 0.35:

| Vista | `fast` anterior | `accurate` actual |
|---|---|---|
| Tapa cerrada, 4 fotos | 0 libro: 3 laptop y 1 omitida | **4 libro** |
| Tapa levantada, 8 fotos | 0 libro: 8 omitidas | **7 libro**, 1 laptop |
| Páginas visibles, 10 fotos | 0 libro: 4 laptop y 6 omitidas | **10 omitidas** |
| Celular, 13 fotos | **13 celular** | **13 celular** |

Son fotos del **mismo cuaderno y del mismo celular**, varias parecidas. El 4/4 de tapa cerrada describe ese material; no garantiza reconocer otros cuadernos. Las páginas abiertas siguen siendo un fallo importante. Tampoco se renombraron predicciones `laptop` como `book` mediante reglas.

Además se usaron **90 imágenes COCO val2017 con cajas**: 45 para validación y 45 reservadas para prueba, disjuntas. Cada grupo cubre las 13 clases de la app y seis imágenes negativas. No se usaron para entrenar. Las 35 capturas propias tienen etiquetas por imagen, sin cajas: aún no son un dataset de entrenamiento YOLO.

Las 35 capturas y las imágenes COCO documentan la comparación anterior al entrenamiento de útiles.

### 6. ¿Qué hace el antiparpadeo?

- El detector a veces ve durante uno o dos frames un objeto que no está (falso positivo), o pierde uno que sí está. Como el modo Universitario guarda cada objeto, un falso positivo regalaría puntos.
- **Para entrar:** un objeto tiene que verse de forma estable **0.3 s** antes de contar. El número de frames depende de los FPS; no se trasladan los cinco frames aproximados del perfil rápido a la ejecución actual de 3–4 FPS.
- **Para salir:** el tracker conserva la presencia hasta **0.7 s** después de la última detección. El puntaje en vivo baja cuando vence ese margen.
- Cada clase suma **una sola vez**: dos libros siguen siendo +20.
- Las pruebas de `tests/test_scoring.py` comprueban los márgenes de entrada/salida, acumulación, plazos y reloj sin frames nuevos. Las pruebas Qt verifican controles y ejecución del worker con datos sintéticos. Los resultados de esas pruebas no sustituyen la detección de objetos reales.
- Es lógica pura en `scoring.py`, separada de la interfaz y del modelo.

### 7. ¿Cuáles son las limitaciones?

- **Clases de COCO:** no hay cuaderno ni lapicero (pregunta 5).
- **Cuaderno:** mejora con tapa cerrada o levantada en el objeto probado, pero se omitieron las diez fotos de páginas visibles. No generalizar las capturas repetidas a otros cuadernos.
- **Otras clases y falsos positivos:** en la prueba pública reservada aumentó el F1 macro, pero los falsos positivos totales subieron de 20 a 44. Algunas clases empeoraron; por ejemplo, teclado y celular públicos. El celular de las capturas propias sí mantuvo 13/13.
- **Mochila y laptop:** ensayar los objetos concretos y varias vistas. La recomendación de mochila puesta proviene de las pruebas anteriores de YOLOv8n; sus porcentajes no son mediciones del modelo actual.
- **Rendimiento actual:** `accurate` da alrededor de 3–4 FPS en este Windows. No cumple los ≥15 FPS de la rúbrica. Los FPS rápidos de YOLOv8n y las mediciones Linux son históricos.
- **Distancia y tamaño de entrada:** los objetos pequeños o lejanos pueden perderse al reducir la entrada; el riesgo aumenta en `fast` 320 frente a `detail` 480. BlazeFace conserva su modelo; los rostros a más de unos 2 m siguen siendo una limitación.
- **No distingue instancias:** cuenta clases, no objetos individuales. Tampoco hace seguimiento (*tracking*) de cada objeto.
- **Depende de la luz:** por eso la app avisa cuando la imagen está oscura.

### 8. ¿Cuántos FPS da y cómo se midieron?

- **Actual, `accurate` YOLO26s 640:** alrededor de **3–4 FPS**. En Universitario, una corrida de 20 s dio **3.44565 FPS**: **62 resultados nuevos en 17.9937 s útiles**, después del calentamiento, sin error.
- **Cuidado al atribuir modos:** la corrida de 25 s se inició en General, pero el usuario cambió a Universitario y se comprobó en su captura. Se describe como corrida con cambio de modo; no como una medición exclusiva de General.
- **Historial Windows, `fast` YOLOv8n 320:** 17.90 FPS General y 19.01 Universitario en corridas breves. La sesión de 600 s completó 10,513 resultados sin errores; en Uni midió 17.71 FPS y al grabar cayó a unos 5. Esa sesión pertenece al perfil anterior.
- **Captura física Windows:** unos 30 FPS a 640×480 y unos 10 a 1280×720. Son FPS de cámara; no son la velocidad de detección de YOLO26s.
- **Cómo se cuentan ahora:** `frame_processed` se emite por un resultado nuevo aceptado y dibujado. `--autoshot`, `tools/profile_app.py` y `tools/verify_live.py` usan ese evento, excluyendo el calentamiento. Los repintados y resultados descartados de controles anteriores no suman FPS. El panel muestra una media móvil.
- **Límite de la elección actual:** el usuario prioriza el reconocimiento cuaderno/laptop y acepta la menor velocidad. La rúbrica sigue exigiendo ≥15 FPS; esa parte y E5/E6 no se dan por cumplidas.

### Otras preguntas posibles

- **¿Por qué el video sale en espejo?** Porque así lo esperamos todos, como en un espejo o una videollamada. Se voltea **antes** de detectar, para que las cajas coincidan con la imagen.
- **¿Por qué dibujan con QPainter y no con OpenCV?** `cv2.putText` no soporta tildes ni la ñ ("Aún", "Cámara"). QPainter sí, además de antialiasing y transparencias para el HUD.
- **¿Por qué usar ahora 640?** Se eligió YOLO26s 640 por los resultados propios y públicos de reconocimiento. El efecto mezcla cambio de modelo y tamaño de entrada; no se atribuye la mejora solo a la resolución. `detail` 480 y `fast` 320 conservan YOLOv8n como alternativas.
- **¿Entrenaron el modelo?** No. Usamos los pesos oficiales preentrenados en COCO. El trabajo del equipo fue elegir y optimizar el modelo, integrar los dos detectores, el antiparpadeo, el puntaje y la interfaz.
- **¿Por qué tarda un momento en bajar el puntaje?** El filtro conserva la presencia hasta 0.7 s para tolerar omisiones de algunos fotogramas.
- **¿Qué pasa si se desconecta la cámara?** La app no se cierra: muestra un aviso, intenta reabrirla cada 2 s y el video vuelve solo.
- **¿Por qué un hilo de inferencia?** YOLO y rostros trabajan en un `QThread`; cámara, widgets y puntaje permanecen en GUI. Solo hay una inferencia en curso. Cambiar controles invalida resultados anteriores, evitando aplicar cajas o puntos de otra configuración.

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
- [ ] Probar los dos modos y anotar sus FPS efectivos. Con `accurate` se esperan unos 3–4 en este equipo: declarar que no cumple el mínimo de 15 de la rúbrica.
- [ ] Anotar perfil (`accurate`, `detail` o `fast`), modelo y resolución efectiva. Ensayar los objetos de la demo con ese perfil; no trasladar resultados entre perfiles.
- [ ] Probar cada objeto del kit en modo Universitario y llegar a la insignia una vez.
- [ ] Volver a modo General y pulsar **`R`** para que las estadísticas arranquen en cero.
- [ ] Dejar el video de respaldo abierto en el reproductor, en pausa, en otra ventana.

### Cierre del proyecto: evidencia que sigue pendiente

- [x] **Histórico, perfil `fast`:** sesión continua de diez minutos, 10,513 resultados, sin errores; pico RSS 649.36 MiB. No corresponde a YOLO26s.
- [ ] Sesión prolongada equivalente con el perfil actual `accurate`; las corridas breves no la sustituyen.
- [x] Interruptores, slider, captura, reinicio y poca luz confirmados por el usuario; confianza, reinicios y luz registrados también por el observador.
- [ ] Objeto parcial y quitar/poner objetos rápido; anotar el resultado efectivo.
- [ ] Mostrar al menos cuatro tipos, alcanzar la insignia y comprobar que baja el puntaje al retirar un objeto.
- [ ] Desconectar y reconectar una USB si está disponible; si solo hay integrada, registrar que esa prueba física no se hizo.
- [ ] Grabar y revisar el video de respaldo; anotar archivo, duración y fecha en `PROGRESO.md`.
- [ ] Criterio ≥15 FPS: sigue incumplido con `accurate`; registrar la prioridad de reconocimiento aceptada sin marcar ese criterio como logrado.

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
| 1:15–2:30 | Modo Universitario (`M`). Mostrar al menos cuatro tipos, señalar la insignia y retirar un objeto para grabar el cambio de puntaje. |
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
