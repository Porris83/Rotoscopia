## 🚀 Actualización del `MANUAL_USUARIO.md` (v0.3.0)

Aquí tienes el texto actualizado. Lo que hice fue:
1.  **Herramientas:** Agregué la nueva "Pluma (Curva)" en la sección de herramientas.
2.  **Exportación:** Reemplacé la sección de "Guardado y Exportación" con la información de los **nuevos diálogos**, explicando el "Exportar Frame" y "Exportar Animación" que hicimos.
3.  **Atajos:** Agregué el atajo de la Pluma (que le asigné a la `P` por "Pluma" o "Pen").

### 📋 Tareas para vos:

1.  Abre tu archivo `MANUAL_USUARIO.md`.
2.  **Copia y pega** el contenido de abajo, reemplazando **todo** el texto del manual viejo.

---
(Inicio del nuevo manual)

# Manual de Usuario - Rotoscopia (v0.3.0)

## ¿Qué es Rotoscopia?

Rotoscopia es una herramienta de edición para crear animaciones cuadro a cuadro a partir de videos. Te permite dibujar encima de cada frame de un video para crear siluetas, limpiar animaciones o extraer elementos para pixel art.

---

## Interfaz de Usuario

### Panel Principal
- **Área de dibujo central**: Donde aparece el video y realizas tus dibujos
- **Barra superior**: Navegación de frames (<<, >>, Copiar frame anterior, contador)
- **Panel izquierdo**: Herramientas de dibujo
- **Panel derecho**: Capas y controles de visualización

### Menú Archivo
- **Importar**: Cargar video (MP4, MOV, AVI, MKV)
- **Exportar Frame Actual...**: Guardar el frame actual como PNG con opciones avanzadas (nuevo en v0.3.0)
- **Exportar Animación...**: Exportar la animación completa como Secuencia PNG o Video MP4 (nuevo en v0.3.0)
- **Guardar**: Guardar proyecto completo (`Ctrl+Shift+S`)
- **Cargar**: Abrir proyecto existente
- **Cerrar**: Cerrar proyecto actual
- **Help**: Ayuda (este manual)

---

## Herramientas de Dibujo

### Pincel (B)
**Descripción**: Herramienta principal para dibujar
- Tamaño ajustable con el slider "Grosor"
- Múltiples colores en la paleta
- Botón "+" para colores personalizados
- **Modos** (cuando pincel activo):
  - **Modo 1** (Tecla `1`): Normal
  - **Modo 2** (Tecla `2`): Semitransparente
  - **Modo 3** (Tecla `3`): Texturizado

### 🧽 Borrador (E)
**Descripción**: Elimina trazos y vuelve áreas transparentes
- Mismo tamaño que el pincel
- **Modos** (cuando borrador activo):
  - **Modo 1** (`Ctrl+1`): Borrado suave
  - **Modo 2** (`Ctrl+2`): Borrado medio
  - **Modo 3** (`Ctrl+3`): Borrado completo

### 📏 Línea (Shift+L)
**Descripción**: Dibuja líneas rectas
- Clic y arrastra para definir inicio y fin
- Previsualización en tiempo real
- Usa el color y grosor del pincel activo

### 🔥 Lazo (L)
**Descripción**: Herramienta de selección y transformación
- Selecciona áreas irregulares
- **Transformaciones disponibles**:
  - **Rotar 90°** (`]` horario, `[` antihorario)
  - **Espejar** (`F` horizontal, `Shift+F` vertical)
  - **Rotación fina** (`Ctrl+Flechas` pasos pequeños, `Ctrl+Shift+Flechas` pasos grandes)
- **Operaciones**:
  - **Copiar** (`Ctrl+C`)
  - **Pegar** (`Ctrl+V`)
  - **Invertir selección** (`Ctrl+Shift+I`)
  - **Seleccionar todo** (`Ctrl+A`)

### ✋ Mano (H)
**Descripción**: Navega por la imagen sin dibujar
- Arrastra para mover la vista
- Útil cuando estás con zoom

### 🪣 Balde (G)
**Descripción**: Rellena áreas con color
- Clic en un área para rellenarla
- Respeta bordes del mismo color

### ⬛ Rectángulo (R)
**Descripción**: Dibuja rectángulos y cuadrados
- Arrastra para definir el área
- Mantén Shift para cuadrados perfectos

### ⭕ Elipse (C)
**Descripción**: Dibuja círculos y elipses
- Arrastra para definir el área
- Mantén Shift para círculos perfectos

### 🖊️ Pluma (P) - ¡Nuevo en v0.3.0!
**Descripción**: Dibuja curvas Bézier precisas
- **Flujo "Clic-Clic-Curvar"**:
    1.  **Clic 1:** Fija el punto de inicio.
    2.  **Clic 2:** Fija el punto final.
    3.  **Mover ratón:** Ajusta la curva.
    4.  **Clic 3:** ¡Plasma la curva!
- **Cancelar**: Presiona `Esc` antes del Clic 3 para cancelar el trazo.
- Usa el color y grosor del pincel activo.

---

## 🎬 Navegación de Frames

### Controles Básicos
- **Frame Anterior**: `←` (Flecha izquierda) o botón `<<`
- **Frame Siguiente**: `→` (Flecha derecha) o botón `>>`
- **Copiar Frame Anterior**: `Ctrl+D` o botón "Copiar frame anterior"

### Contador de Frames
- Muestra "Frame: X / Total" en la barra superior
- Te indica tu posición actual en el video

---

## 📚 Sistema de Capas

### Panel de Capas (Derecha)
- **Lista de capas**: Muestra todas las capas del frame actual
- **Botones de control**:
  - **+**: Crear nueva capa
  - **-**: Eliminar capa seleccionada
  - **⧉**: Duplicar capa
  - **Renombrar**: Renombrar capa

### Propiedades de Capa
- **Visible**: Checkbox para mostrar/ocultar capa
- **Opacidad**: Slider para transparencia (0-100%)

---

## Controles de Visualización (Grupo "Vista")

### 🎭 Fondo
- **Checkbox "Fondo"**: Muestra/oculta el video de fondo
- **Botón "Reset"**: Restaura opacidad predeterminada y activa fondo
- **Slider "Opacidad Fondo"**: Controla transparencia del video (0-100%)
- **Atajo**: `Ctrl+B` para alternar fondo

### 🧅 Onion Skin
- **Checkbox "Onion"**: Activa/desactiva vista de frames adyacentes
- **Botón "Toggle Onion"**: Alterna rápidamente el onion skin
- **Slider "Opacidad Onion"**: Controla transparencia de frames anteriores/siguientes
- **Atajo**: `O` para alternar onion skin
- **Colores**: Frame anterior (azul), frame siguiente (rojo)

---

## 🔍 Zoom y Navegación

### Controles de Zoom
- **Acercar**: `Ctrl++` o rueda del ratón hacia arriba
- **Alejar**: `Ctrl+-` o rueda del ratón hacia abajo  
- **Reset Zoom**: `Ctrl+0` vuelve al 100%
- **Zoom anclado**: El zoom se centra donde está el cursor

### Navegación (Pan)
- **Herramienta Mano** (`H`): Arrastra para mover la vista
- **Botón medio del ratón**: También funciona para arrastrar

---

## Guardado y Exportación (Mejorado en v0.3.0)

### Guardar Trabajo
- **Guardar Proyecto**: `Ctrl+Shift+S` - Guarda todo el proyecto (archivos de capas, metadata, etc.).
- **Cargar Proyecto**: Desde menú Archivo.

### Exportar Frame Actual...
- **Ubicación**: Menú `Archivo -> Exportar Frame Actual...`
- Abre un diálogo para guardar **un solo PNG** con opciones avanzadas:
  - **Nombre de Archivo**: Puedes elegir el nombre y la ubicación.
  - **Fondo**: Elige entre `Transparente`, `Incluir fondo del video` o `Rellenar con Croma`.
  - **Capas**: Marca `[ ] Exportar capas por separado` para guardar cada capa en su propio archivo (ej: `nombre_Capa 1.png`).

### Exportar Animación...
- **Ubicación**: Menú `Archivo -> Exportar Animación...`
- Abre un diálogo para exportar el **proyecto completo**.
- **¡No congela la app!** La exportación se ejecuta en segundo plano.
- **Formato de Salida**:
  - `(•) Secuencia PNG`: Ideal para videojuegos. Guarda cada frame como un PNG (`frame_001.png`, `frame_002.png`, etc.).
  - `(•) Video MP4`: Para vistas rápidas o redes sociales.
- **Fondo**: Elige entre `Transparente` (solo para PNG), `Incluir fondo del video` o `Rellenar con Croma`.

---

## Atajos de Teclado Completos

### 🎬 Navegación
| Acción | Atajo |
|--------|-------|
| Frame siguiente | `→` |
| Frame anterior | `←` |
| Copiar frame anterior | `Ctrl+D` |

### Herramientas
| Herramienta | Atajo |
|-------------|-------|
| Pincel | `B` |
| Borrador | `E` |
| Línea | `Shift+L` |
| Lazo | `L` |
| Mano | `H` |
| Balde | `G` |
| Rectángulo | `R` |
| Elipse | `C` |
| **Pluma (Curva)** | `P` |

### Modos de Herramientas
| Modo | Atajo |
|------|-------|
| Pincel modo 1 | `1` |
| Pincel modo 2 | `2` |
| Pincel modo 3 | `3` |
| Borrador modo 1 | `Ctrl+1` |
| Borrador modo 2 | `Ctrl+2` |
| Borrador modo 3 | `Ctrl+3` |

### Transformaciones (Lazo)
| Acción | Atajo |
|--------|-------|
| Rotar 90° horario | `]` |
| Rotar 90° antihorario | `[` |
| Espejar horizontal | `F` |
| Espejar vertical | `Shift+F` |
| Rotar fino antihorario | `Ctrl+←` |
| Rotar fino horario | `Ctrl+→` |
| Rotar amplio antihorario | `Ctrl+Shift+←` |
| Rotar amplio horario | `Ctrl+Shift+→` |

### Selección (Lazo)
| Acción | Atajo |
|--------|-------|
| Copiar selección | `Ctrl+C` |
| Pegar selección | `Ctrl+V` |
| Invertir selección | `Ctrl+Shift+I` |
| Seleccionar todo | `Ctrl+A` |

### Archivo
| Acción | Atajo |
|--------|-------|
| Guardar proyecto | `Ctrl+Shift+S` |
| (El resto de exportaciones ahora están en el menú) |

### Edición
| Acción | Atajo |
|--------|-------|
| Deshacer | `Ctrl+Z` |
| Rehacer | `Ctrl+Shift+Z` |

### Visualización
| Acción | Atajo |
|--------|-------|
| Toggle Onion Skin | `O` |
| Toggle fondo | `Ctrl+B` |

### 🔍 Zoom
| Acción | Atajo |
|--------|-------|
| Acercar | `Ctrl++` |
| Alejar | `Ctrl+-` |
| Reset zoom | `Ctrl+0` |

---

## 🎯 Flujo de Trabajo Recomendado

### 1. Preparación
1. **Importar video** desde menú Archivo > Importar
2. **Ajustar visualización**:
   - Activar Onion Skin (`O`) si necesitas ver frames adyacentes
   - Ajustar opacidad del fondo según necesites

### 2. Dibujo
1. **Seleccionar herramienta** (Pincel `B`, Pluma `P`, etc.)
2. **Ajustar grosor y color** en el panel izquierdo
3. **Crear capas adicionales** si necesitas separar elementos
4. **Dibujar** sobre el frame actual

### 3. Navegación
1. **Avanzar al siguiente frame** (`→`)
2. **Copiar frame anterior** (`Ctrl+D`) si necesitas continuidad
3. **Repetir proceso** de dibujo

### 4. Finalización
1. **Guardar proyecto** regularmente (`Ctrl+Shift+S`)
2. **Exportar frames individuales** (Menú `Archivo -> Exportar Frame Actual...`) si necesitas
3. **Exportar animación completa** (Menú `Archivo -> Exportar Animación...`) al terminar

---

## Consejos y Trucos

### Dibujo Eficiente
- Usa **capas separadas** para diferentes elementos (personaje, fondo, efectos)
- La **Pluma (`P`)** es ideal para líneas limpias y curvas suaves.
- El **Onion Skin** te ayuda a mantener consistencia entre frames

### 🔍 Navegación
- Usa **zoom** (`Ctrl++/Ctrl+-`) para detalles finos
- La **herramienta Mano** (`H`) es esencial cuando trabajas con zoom
- El **botón medio del ratón** también sirve para pan

### Organización
- **Guarda el proyecto frecuentemente** (`Ctrl+Shift+S`)
- **Nombra las capas** descriptivamente (personaje, fondo, sombra, etc.)
- Usa la **opacidad de capas** para efectos sútiles

### ⚡ Atajos Esenciales
- `B` para pincel, `E` para borrador, `P` para pluma
- `←/→` para navegación rápida entre frames
- `Ctrl+Z/Ctrl+Shift+Z` para deshacer/rehacer
- `O` para toggle rápido de onion skin

---

## 🐛 Solución de Problemas

### La aplicación se congela al exportar
- Este bug fue **solucionado en v0.3.0**. Si sigues experimentando esto, asegúrate de tener la última versión.

### El video no se carga
- Verifica que el formato sea compatible (MP4, MOV, AVI, MKV)
- Asegúrate de que el archivo no esté corrupto

### No puedo ver mis trazos
- Verifica que la capa esté visible (checkbox "Visible")
- Revisa la opacidad de la capa
- Asegúrate de estar en la capa correcta

### Los atajos no funcionan
- Verifica que el cursor esté sobre el área de dibujo
- Algunos atajos (`1`, `2`, `3`) requieren que el Pincel esté activo

---

## 📞 Soporte

Para reportar errores o sugerir mejoras, consulta la documentación del proyecto o contacta al desarrollador.

---

*Manual de Usuario v0.3.0 - Rotoscopia 2025*