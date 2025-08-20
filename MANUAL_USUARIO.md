# Manual de Usuario - Rotoscopia

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
- **Exportar Frame (PNG)**: Guardar frame actual como imagen
- **Guardar**: Guardar proyecto completo
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

## Guardado y Exportación

### Guardar Trabajo
- **Guardar Frame**: `Ctrl+S` - Exporta frame actual como PNG
- **Guardar Proyecto**: `Ctrl+Shift+S` - Guarda todo el proyecto
- **Cargar Proyecto**: Desde menú Archivo

### Exportar Animación
- **Exportar Animación**: `Ctrl+E`
- Opciones disponibles:
  - Video MP4
  - Secuencia de imágenes PNG
- Incluye todas las capas visibles y el fondo

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
| Guardar frame PNG | `Ctrl+S` |
| Guardar proyecto | `Ctrl+Shift+S` |
| Exportar animación | `Ctrl+E` |

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
1. **Seleccionar herramienta** (generalmente Pincel `B`)
2. **Ajustar grosor y color** en el panel izquierdo
3. **Crear capas adicionales** si necesitas separar elementos
4. **Dibujar** sobre el frame actual

### 3. Navegación
1. **Avanzar al siguiente frame** (`→`)
2. **Copiar frame anterior** (`Ctrl+D`) si necesitas continuidad
3. **Repetir proceso** de dibujo

### 4. Finalización
1. **Guardar proyecto** regularmente (`Ctrl+Shift+S`)
2. **Exportar frames individuales** (`Ctrl+S`) si necesitas
3. **Exportar animación completa** (`Ctrl+E`) al terminar

---

## Consejos y Trucos

### Dibujo Eficiente
- Usa **capas separadas** para diferentes elementos (personaje, fondo, efectos)
- El **Onion Skin** te ayuda a mantener consistencia entre frames
- **Copia frames anteriores** (`Ctrl+D`) para acelerar animaciones con poco cambio

### 🔍 Navegación
- Usa **zoom** (`Ctrl++/Ctrl+-`) para detalles finos
- La **herramienta Mano** (`H`) es esencial cuando trabajas con zoom
- El **botón medio del ratón** también sirve para pan

### Organización
- **Guarda el proyecto frecuentemente** (`Ctrl+Shift+S`)
- **Nombra las capas** descriptivamente (personaje, fondo, sombra, etc.)
- Usa la **opacidad de capas** para efectos sutiles

### ⚡ Atajos Esenciales
- `B` para pincel, `E` para borrador - los más usados
- `←/→` para navegación rápida entre frames
- `Ctrl+Z/Ctrl+Shift+Z` para deshacer/rehacer
- `O` para toggle rápido de onion skin

---

## 🐛 Solución de Problemas

### El video no se carga
- Verifica que el formato sea compatible (MP4, MOV, AVI, MKV)
- Asegúrate de que el archivo no esté corrupto

### La aplicación va lenta
- Reduce la opacidad del onion skin
- Trabaja con menos capas cuando sea posible
- Cierra otros programas pesados

### No puedo ver mis trazos
- Verifica que la capa esté visible (checkbox "Visible")
- Revisa la opacidad de la capa
- Asegúrate de estar en la capa correcta

### Los atajos no funcionan
- Verifica que el cursor esté sobre el área de dibujo
- Algunos atajos requieren que una herramienta específica esté activa

---

## 📞 Soporte

Para reportar errores o sugerir mejoras, consulta la documentación del proyecto o contacta al desarrollador.

---

*Manual de Usuario v0.1.0 - Rotoscopia 2025*
