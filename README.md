# Rotoscopia v0.3.2

Herramienta profesional de rotoscopia frame-por-frame con detección automática de bordes.

---

## Nuevas Características - v0.3.2

### Auto-Calco - Detección Automática de Bordes

Sistema de detección de bordes que utiliza algoritmos de visión por computadora (OpenCV Canny Edge Detection) para acelerar el proceso de rotoscopia.

**Características:**
- **Captura de Viewport**: Procesa exactamente el área visible en pantalla
- **Preview en Tiempo Real**: Visualiza los bordes detectados mientras ajustas parámetros
- **Diales de Control (1-11)**:
  - **DETALLE**: Ajusta la sensibilidad de detección
  - **LIMPIEZA**: Elimina ruido y componentes pequeños
- **Integración con Pincel**: Respeta el color y grosor del pincel activo
- **Atajo de Teclado**: `Ctrl+Shift+A`

**Flujo de Trabajo:**
1. Posiciona el viewport en el área deseada (zoom/scroll)
2. Presiona `Ctrl+Shift+A` o botón CAPTURAR
3. Ajusta diales DETALLE y LIMPIEZA
4. Presiona `Enter` o botón PLASMAR para transferir a la capa activa

**Tecnología Implementada:**
- Filtrado bilateral para preservar bordes
- Canny edge detection con umbrales adaptativos
- Eliminación de componentes pequeños mediante morfología
- Dilatación para ajuste de grosor
- Mapeo preciso de coordenadas con zoom/scroll

### Refactorización de Arquitectura

**Mejoras en el código:**
- Todas las herramientas consolidadas en `tools.py`
- Estructura modular preparada para empaquetado
- Imports optimizados sin dependencias externas

**Validaciones de seguridad agregadas:**
- Verificación de límites de ROI
- Checks de existencia de frames y ventanas
- Clamp de coordenadas para prevenir crashes
- Validación de áreas no vacías

### Correcciones de Bugs

✔️ Captura de viewport corregida con scroll y zoom
✔️ `mapToOverlay()` usa dimensiones correctas del frame
✔️ Orden de canales RGB corregido
✔️ Warning de jerarquía de widgets eliminado

---

## Implementación Técnica

### Nuevas Clases (en `tools.py`)

**`AutoCalcoEngine`**
- Motor de procesamiento con OpenCV
- Método `detect_edges_roi()` para procesamiento de región de interés
- Método `_remove_small_components()` para limpieza morfológica

**`AutoCalcoTool`**
- Lógica de captura y preview
- Método `activate()` para captura con scroll bars
- Método `update_preview()` con validaciones
- Método `commit_to_layer()` para plasmar resultado

**`AutoCalcoDock`**
- Panel de control con diales analógicos
- Validación anti wrap-around en diales
- Botones CAPTURAR y PLASMAR con códigos de color

### Modificaciones en Archivos Existentes

**`canvas.py`:**
- Import de AutoCalcoTool y AutoCalcoDock
- Método `activar_auto_calco()` para activación
- Atajo `Ctrl+Shift+A` registrado
- Renderizado de preview en `paintEvent()`
- Mejora de `mapToOverlay()` con dimensiones correctas

**`tools.py`:**
- Imports de cv2 y numpy agregados
- Aproximadamente 250 líneas nuevas con Auto-Calco completo

---

## Preparación para Distribución

### Nuevos Archivos

- **`build.py`**: Script automático de empaquetado con PyInstaller
- **`BUILD_INSTRUCTIONS.md`**: Guía de empaquetado para colaboradores
- **`requirements.txt`**: Dependencias del proyecto

### Empaquetado

```bash
python build.py
```

Genera `dist/Rotoscopia.exe` listo para distribución.

---

## Resumen de la Versión

La v0.3.2 incluye:

1. **Auto-Calco**: Detección automática de bordes para acelerar rotoscopia
2. **Arquitectura Modular**: Código limpio y extensible
3. **Validaciones Robustas**: Error handling y prevención de crashes
4. **Empaquetado Automático**: Scripts listos para distribución

---

## Herramientas Disponibles

- **Pincel**: Dibujo a mano alzada con 3 modos
- **Borrador**: Eliminación de trazos con 3 modos
- **Línea**: Líneas rectas entre dos puntos
- **Pluma**: Curvas Bézier suaves
- **Línea Dinámica**: Polilíneas editables
- **Elipse**: Círculos y óvalos
- **Rectángulo**: Figuras rectangulares
- **Balde**: Relleno de áreas cerradas
- **Lazo**: Selección y transformación de áreas
- **Mano**: Navegación del canvas
- **Auto-Calco**: Detección automática de bordes

---

## Requisitos del Sistema

- **Python**: 3.8+
- **Sistema Operativo**: Windows (principal), Linux, macOS
- **Dependencias**:
  - PySide6 >= 6.5.0
  - opencv-python >= 4.8.0
  - numpy >= 1.24.0
  - Pillow >= 10.0.0

---

## Documentación

- **Manual de Usuario**: Ver `MANUAL_USUARIO.md` para guía completa de uso
- **Instrucciones de Build**: Ver `BUILD_INSTRUCTIONS.md` para empaquetado

---

## Instalación para Usuarios

Descarga `Rotoscopia.exe` desde la sección Releases y ejecútalo. No requiere instalación adicional.

## Instalación para Desarrollo

```bash
# Clonar repositorio
git clone https://github.com/Porris83/Rotoscopia.git
cd Rotoscopia

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python rotoscopia/main.py
```

---

**Rotoscopia v0.3.2** - Enero 2026
