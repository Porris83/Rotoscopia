# Manual de Usuario - Rotoscopia v0.3.2

Guía completa para usar todas las características de Rotoscopia, la herramienta profesional de rotoscopia frame-por-frame.

---

## Tabla de Contenidos

1. [Primeros Pasos](#primeros-pasos)
2. [Interfaz Principal](#interfaz-principal)
3. [Herramientas de Dibujo](#herramientas-de-dibujo)
4. [Auto-Calco con IA](#auto-calco-con-ia)
5. [Sistema de Capas](#sistema-de-capas)
6. [Navegación y Visualización](#navegación-y-visualización)
7. [Exportación](#exportación)
8. [Atajos de Teclado](#atajos-de-teclado)
9. [Consejos y Trucos](#consejos-y-trucos)

---

## Primeros Pasos

### Instalación
1. Descarga `Rotoscopia.exe`
2. Ejecuta el archivo (no requiere instalación)
3. ¡Listo para usar!

### Cargar un Video o Imagen
1. **Menú Archivo → Abrir Video** (o `Ctrl+O`)
2. Selecciona tu archivo:
   - Videos: `.mp4`, `.avi`, `.mov`, `.mkv`
   - Imágenes: `.png`, `.jpg`, `.jpeg`, `.bmp`
3. La aplicación cargará todos los frames en memoria

---

## Interfaz Principal

### Componentes

```
┌─────────────────────────────────────────────────────────────┐
│ [Archivo]                                          [Capas]  │
├─────────────────────────────────────────────────────────────┤
│ [Herramientas: ✏️ 🗑️ 📏 ⭕ ▭ ⬜ 🖊️ 📐 ✋ 🪣]                  │
├──────────────────────┬──────────────────────────────────────┤
│                      │  🎸 AUTO-CALCO                       │
│                      │  ┌─────────────────────────────┐    │
│                      │  │ 📷 CAPTURAR                 │    │
│   CANVAS             │  ├─────────────────────────────┤    │
│   (Área de dibujo)   │  │ ⚙️ DETALLE    ⚙️ LIMPIEZA  │    │
│                      │  │    [dial]        [dial]     │    │
│                      │  │      ⚡                      │    │
│                      │  │   PLASMAR                   │    │
│                      │  └─────────────────────────────┘    │
├──────────────────────┴──────────────────────────────────────┤
│ << Frame 1/120 >>  [▶️] [Onion] [Fondo] [Zoom: 100%]       │
└─────────────────────────────────────────────────────────────┘
```

---

## Herramientas de Dibujo

### Pincel (Brush)
**Atajo:** `B`

Herramienta básica de dibujo a mano alzada.

**Uso:**
1. Selecciona el pincel
2. Ajusta el grosor con el slider
3. Elige color en la paleta
4. Dibuja con clic izquierdo sostenido

**Modos del pincel** (`1`, `2`, `3`):
- **Modo 1**: Trazo normal
- **Modo 2**: Trazo suave
- **Modo 3**: Trazo con presión

---

### Borrador (Eraser)
**Atajo:** `E`

Borra partes del dibujo.

**Uso:**
1. Selecciona el borrador
2. Ajusta el grosor
3. Borra con clic izquierdo sostenido

**Modos del borrador** (`Shift+1`, `Shift+2`, `Shift+3`):
- **Modo 1**: Borrado normal
- **Modo 2**: Borrado suave
- **Modo 3**: Borrado fuerte

---

### Línea Recta (Line)
**Atajo:** `L`

Dibuja líneas rectas entre dos puntos.

**Uso:**
1. Clic en el punto inicial
2. Mueve el mouse (preview en rojo punteado)
3. Clic en el punto final para plasmar

**Cancelar:** `Esc`

---

### Pluma (Curva Bézier)
**Atajo:** `P`

Crea curvas suaves y precisas.

**Uso:**
1. **Clic 1**: Punto inicial (A)
2. **Clic 2**: Punto final (B)
3. **Mover mouse**: Ajusta la curva
4. **Clic 3**: Plasma la curva

**Cancelar:** `Esc`

---

### Línea Dinámica (Polilínea)
**Atajo:** `Shift+L`

Crea líneas de múltiples segmentos editables.

**Uso:**
1. **Clic**: Agrega un punto
2. **Clic en punto existente + arrastrar**: Mueve el punto
3. Vista previa en rojo punteado
4. **Enter**: Plasma la línea
5. **Esc**: Cancela

**Puntos:**
- Azul: Puntos normales
- Rojo: Punto seleccionado

---

### Elipse
Dibuja círculos y óvalos.

**Uso:**
1. Clic y arrastra para definir el rectángulo contenedor
2. Suelta para plasmar

---

### Rectángulo
Dibuja rectángulos.

**Uso:**
1. Clic en una esquina
2. Arrastra a la esquina opuesta
3. Suelta para plasmar

---

### Mano (Hand/Pan)
**Atajo:** `H` o **Botón medio del mouse**

Mueve el canvas cuando hay zoom.

**Uso:**
1. Selecciona la mano O mantén botón medio/derecho
2. Arrastra para mover el canvas

---

### Balde (Fill)
Rellena áreas cerradas con color.

**Uso:**
1. Selecciona el balde
2. Ajusta tolerancia si es necesario
3. Clic en el área a rellenar

---

### Lazo (Lasso)
**Atajo:** `Ctrl+L`

Selecciona áreas para transformar.

**Uso:**
1. Dibuja un contorno alrededor del área
2. Cierra el trazo
3. Transforma la selección:
   - **Arrastrar**: Mover
   - **Rueda**: Rotar
   - **Ctrl+C/V**: Copiar/Pegar
   - **Ctrl+I**: Invertir selección
   - **Ctrl+A**: Seleccionar todo

**Rotación:**
- `Ctrl+]` / `Ctrl+[`: Rotar 90° (horario/antihorario)
- `Alt+]` / `Alt+[`: Rotar 15° (horario/antihorario)
- `,` / `.`: Rotar 5° (horario/antihorario)

**Voltear:**
- `Ctrl+Shift+H`: Voltear horizontal
- `Ctrl+Shift+V`: Voltear vertical

---

## Auto-Calco

Detecta automáticamente los bordes de tu video usando algoritmos de visión por computadora (Canny Edge Detection).

### Activación
- **Atajo:** `Ctrl+Shift+A`
- **Botón:** 📷 CAPTURAR en el dock Auto-Calco

### Flujo de Trabajo

#### 1. Posicionar el Viewport
- Usa **zoom** (`+`/`-` o rueda del mouse) para acercarte al área de interés
- Usa **scroll** o **pan** (botón medio) para centrar el área
- Solo se procesará lo que veas en pantalla

#### 2. Capturar
- Presiona `Ctrl+Shift+A` o el botón **📷 CAPTURAR**
- El sistema capturará exactamente el área visible
- Aparecerá un preview en rojo sobre el canvas

#### 3. Ajustar Parámetros

**🎚️ Dial DETALLE (1-11):**
- **1-3**: Muy selectivo, solo bordes fuertes
- **4-7**: Equilibrado (recomendado)
- **8-11**: Máximo detalle, detecta todo

**🎚️ Dial LIMPIEZA (1-11):**
- **1-3**: Sin filtrar, mantiene todo el ruido
- **4-7**: Equilibrado, elimina ruido moderado
- **8-11**: Ultra limpio, solo líneas principales

**Los diales se actualizan en tiempo real** - verás el preview cambiar mientras ajustas.

#### 4. Plasmar
- Cuando estés satisfecho con el resultado:
  - Presiona **Enter** O
  - Click en el botón **⚡ PLASMAR**
- Las líneas se transferirán a la capa activa con el color y grosor del pincel actual

### Consejos para Auto-Calco

**Mejores Resultados:**
- Trabaja en secciones pequeñas (zoom in)
- Buena iluminación en el video original
- Bordes contrastados
- Ajusta DETALLE primero, luego LIMPIEZA

**Evitar:**
- Capturar el frame completo (muy lento y ruidoso)
- Usar en áreas con textura uniforme
- DETALLE en 11 + LIMPIEZA en 1 (genera ruido excesivo)

### Tecnología

El Auto-Calco usa:
- **Filtrado Bilateral**: Preserva bordes mientras suaviza superficies
- **Canny Edge Detection**: Algoritmo de detección de bordes de OpenCV
- **Morfología**: Elimina componentes pequeños y conecta líneas
- **Dilatación**: Ajusta el grosor según tu pincel

---

## Sistema de Capas

### Panel de Capas

Ubicado en el dock derecho, muestra todas las capas del frame actual.

**Controles por capa:**
- **Visibilidad**: Click para ocultar/mostrar
- **Opacidad**: Slider para ajustar transparencia (0-100%)
- **Nombre**: Doble-click para renombrar
- **Eliminar**: Botón para borrar la capa

### Gestión de Capas

**Crear capa nueva:**
- Botón **+ Nueva Capa** en el panel

**Seleccionar capa activa:**
- Click en la capa en el panel
- La capa activa se resalta

**Reordenar capas:**
- Arrastra y suelta en el panel
- Las capas superiores se dibujan encima

**Combinar capas:**
- Selecciona varias capas
- Click derecho → Combinar

### Capa Activa

Solo la capa activa recibe el dibujo. Está resaltada en el panel de capas.

**Cambiar capa activa:**
- Click en otra capa en el panel
- `Ctrl+Up/Down` (siguiente/anterior)

---

## Navegación y Visualización

### Navegación entre Frames

**Botones:**
- **<<** Anterior
- **>>** Siguiente

**Atajos:**
- `Left` / `Right`: Frame anterior/siguiente
- `Home` / `End`: Primer/último frame
- `PageUp` / `PageDown`: Saltar 10 frames

### Onion Skin (Papel Cebolla)

Muestra el frame anterior con transparencia para referencia.

**Activar/Desactivar:**
- Botón **[Onion]** en la barra inferior
- Atajo: `O`

**Ajustar opacidad:**
- Slider en configuración
- Valor recomendado: 30-50%

### Fondo del Video

**Mostrar/Ocultar:**
- Botón **[Fondo]** en la barra inferior
- Atajo: `Ctrl+B`

**Ajustar opacidad del fondo:**
- Slider en la barra de herramientas
- 0% = invisible, 100% = opaco

### Zoom

**Acercar/Alejar:**
- `+` / `-`: Zoom in/out
- **Rueda del mouse**: Zoom continuo
- `Ctrl+0`: Resetear zoom a 100%

**Límites:**
- Mínimo: 10%
- Máximo: 800%

---

## Exportación

### Exportar Frame Actual

**Menú Archivo → Exportar Frame** o `Ctrl+S`

**Opciones:**
1. **Nombre de archivo**: Personaliza el nombre (default: `frame_00001.png`)
2. **Modo de fondo**:
   - Transparente (recomendado para PNG)
   - Incluir fondo del video
   - Rellenar con Croma (verde)
3. **Exportar capas por separado**: Genera un PNG por cada capa visible

**Resultado:** Archivo PNG en la carpeta que elijas

---

### Exportar Animación

**Menú Archivo → Exportar Animación** o `Ctrl+Shift+E`

#### Opciones

**Formato:**
- **Secuencia PNG**: Un archivo `.png` por frame
- **Video MP4**: Un solo archivo `.mp4`

**Modo de fondo:**
- Transparente (solo PNG)
- Incluir fondo del video
- Rellenar con Croma (solo PNG)

**FPS** (solo MP4):
- Valor recomendado: 12-30 fps
- Predeterminado: 12 fps

#### Proceso de Exportación

1. Se abre el diálogo de opciones
2. Seleccionas formato y opciones
3. Eliges carpeta de destino
4. Click en **OK**
5. **La exportación se ejecuta en segundo plano**
   - Puedes seguir trabajando
   - Se muestra progreso en la barra de estado
6. Notificación al completar

**Resultado:**
- **PNG**: Carpeta con archivos numerados (`frame_00001.png`, etc.)
- **MP4**: Un solo archivo de video

---

## Atajos de Teclado

### General
| Atajo | Acción |
|-------|--------|
| `Ctrl+O` | Abrir video |
| `Ctrl+S` | Exportar frame actual |
| `Ctrl+Shift+E` | Exportar animación |
| `Ctrl+Z` | Deshacer |
| `Ctrl+Y` | Rehacer |
| `Ctrl+Q` | Salir |

### Herramientas
| Atajo | Herramienta |
|-------|-------------|
| `B` | Pincel |
| `E` | Borrador |
| `L` | Línea |
| `P` | Pluma |
| `Shift+L` | Línea Dinámica |
| `H` | Mano (Pan) |
| `Ctrl+L` | Lazo |
| `Ctrl+Shift+A` | **Auto-Calco** |

### Navegación
| Atajo | Acción |
|-------|--------|
| `Left` / `Right` | Frame anterior/siguiente |
| `Home` / `End` | Primer/último frame |
| `Ctrl+D` | Copiar frame anterior |

### Visualización
| Atajo | Acción |
|-------|--------|
| `O` | Toggle Onion Skin |
| `Ctrl+B` | Toggle Fondo |
| `+` / `-` | Zoom in/out |
| `Ctrl+0` | Reset zoom |

### Auto-Calco
| Atajo | Acción |
|-------|--------|
| `Ctrl+Shift+A` | Activar y capturar |
| `Enter` | Plasmar resultado |

### Lazo (Selección)
| Atajo | Acción |
|-------|--------|
| `Ctrl+C` | Copiar selección |
| `Ctrl+V` | Pegar selección |
| `Ctrl+I` | Invertir selección |
| `Ctrl+A` | Seleccionar todo |
| `Ctrl+]` / `Ctrl+[` | Rotar 90° |
| `Alt+]` / `Alt+[` | Rotar 15° |
| `,` / `.` | Rotar 5° |
| `Ctrl+Shift+H` | Voltear horizontal |
| `Ctrl+Shift+V` | Voltear vertical |

---

## Consejos y Trucos

### Workflow Eficiente

1. **Carga el video**
2. **Ajusta el fondo** (opacidad ~50% para ver tu dibujo)
3. **Activa Onion Skin** para referencia
4. **Frame por frame:**
   - Usa **Auto-Calco** para bordes principales
   - Refina con **Pincel** o **Pluma**
   - Usa **Línea Dinámica** para estructuras rectas
5. **Exporta** cuando termines

### Auto-Calco Avanzado

**Estrategia de capas:**
1. Capa 1: Auto-Calco con DETALLE bajo (líneas principales)
2. Capa 2: Auto-Calco con DETALLE alto (detalles finos)
3. Combina ajustando opacidad

**Secciones:**
- Procesa cabeza, torso, brazos, piernas por separado
- Usa zoom para trabajar en detalle
- Combina todo al final

### Optimización de Rendimiento

**Videos largos:**
- Trabaja por secuencias (carga solo los frames necesarios)
- Exporta en bloques

**Archivos pesados:**
- Reduce resolución del video antes de cargar
- Usa formato MP4 en vez de PNG sequence para export final

### Atajos Personales

Los usuarios avanzados pueden editar `settings.py` para personalizar atajos.

---

## Solución de Problemas

### La aplicación se congela

**Causas:**
- Video muy largo/pesado
- Exportación MP4 muy grande

**Solución:**
- Reduce la duración del video
- Exporta en formato PNG en vez de MP4
- Aumenta RAM disponible

### Auto-Calco no funciona

**Verifica:**
1. ¿Hay un frame cargado?
2. ¿El área tiene contraste?
3. ¿Los diales están en rango razonable (4-7)?

**Prueba:**
- Ajusta DETALLE a 6
- Ajusta LIMPIEZA a 3
- Captura un área pequeña primero

### Los colores no coinciden

- Auto-Calco usa el color del pincel actual
- Cambia el color ANTES de plasmar
- El grosor también se respeta

### No puedo hacer zoom

- Verifica que el canvas tenga foco (click en él)
- Prueba con `+`/`-` en vez de rueda del mouse

---

## Soporte

**Versión:** 0.3.2

**Requisitos:**
- Windows 10/11 (recomendado)
- 4GB RAM mínimo
- OpenGL 2.0+

**Reportar bugs:**
- GitHub Issues (si aplicable)
- Email del desarrollador
- Incluye: versión, OS, pasos para reproducir

---

**¡Gracias por usar Rotoscopia!**

*Manual actualizado para v0.3.2 - Enero 2026*
