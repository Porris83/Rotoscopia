### 📋 README.md (Actualizado para v0.3.1)

(Copia y pega esto en tu archivo `README.md` principal)

# Rotoscopia v0.3.1 - Herramientas de Precisión

Esta versión añade la **Línea Dinámica** (polilínea) a las herramientas de precisión y mantiene el robusto sistema de exportación introducido en la v0.3.0.

## 🆕 Nuevas Características

### 🖊️ Nueva Herramienta: Pluma (Curva)
Se añade la **Herramienta Pluma** a la barra de herramientas. Esta herramienta permite crear curvas suaves y precisas, ideales para rotoscopia de alta fidelidad.

- **Flujo de trabajo "Clic-Clic-Curvar"**:
    1.  **Clic 1:** Fija el punto de inicio (Punto A).
    2.  **Clic 2:** Fija el punto final (Punto B).
    3.  **Mover ratón:** Ajusta la tensión de la curva (Punto de Control).
    4.  **Clic 3:** ¡Plasma la curva Bézier!
- **Cancelación con `Esc`**: Puedes cancelar un trazo en curso antes del Clic 3.
- **Integración total**: Funciona con el sistema de Undo/Redo (`Ctrl+Z`).

### 📏 Nueva Herramienta: Línea Dinámica (v0.3.1)
Se añade la **Herramienta Línea Dinámica** a la barra de herramientas. Es ideal para crear trazos rectos de múltiples puntos (polilíneas) de forma editable.

- **Flujo de trabajo "Clic y Editar"**:
    1.  **Clic:** Añade un punto nuevo.
    2.  **Arrastrar:** Mueve un punto existente (los puntos se muestran en azul/rojo).
    3.  La vista previa se muestra como una línea roja punteada.
- **Plasmar con `Enter`**: Presiona `Enter` para dibujar la línea de forma permanente en la capa.
- **Cancelación con `Esc`**: Presiona `Esc` para borrar la línea actual que estás editando.
- **Integración total**: Funciona con el grosor del pincel y el sistema de Undo/Redo (`Ctrl+Z`).

### 🚀 Sistema de Exportación Avanzado (de v0.3.0)
Se ha rediseñado todo el flujo de exportación para ser más potente, flexible y estable, solucionando los principales cuellos de botella del diagnóstico de rendimiento.

#### 1. Exportación en Segundo Plano (Sin Congelamiento)
- **¡No más congelamiento!** Las exportaciones de animación (PNG o MP4) ahora se ejecutan en un **hilo trabajador** (`ExportWorker`) separado.
- Puedes **seguir trabajando** en la aplicación mientras se exporta tu video en segundo plano.
- Una **notificación emergente** te avisa cuando la exportación ha finalizado con éxito o si ha ocurrido un error.

#### 2. Nuevo Diálogo: "Exportar Frame Actual"
Un nuevo diálogo (`ExportFrameDialog`) reemplaza el guardado simple, ofreciendo control total:
- **Nombre de archivo personalizado**: Sugiere un nombre por defecto (ej: `frame_001.png`) pero te permite cambiarlo.
- **Modos de Fondo**:
    - `(•) Transparente`
    - `(•) Incluir fondo del video`
    - `(•) Rellenar con Croma (verde)`
- **Exportar Capas por Separado**: Un checkbox (`[ ] Exportar capas por separado`) que guarda cada capa en un archivo PNG individual (ej: `mi_frame_Capa 1.png`).

#### 3. Nuevo Diálogo: "Exportar Animación"
Un nuevo diálogo (`ExportAnimationDialog`) te da control total sobre la exportación de la secuencia completa:
- **Formato de Salida**:
    - `(•) Secuencia PNG` (Ideal para videojuegos y post-producción).
    - `(•) Video MP4` (Para vistas rápidas o redes sociales).
- **Modos de Fondo**:
    - `(•) Transparente` (Recomendado para PNG).
    - `(•) Incluir fondo del video`.
    - `(•) Rellenar con Croma (verde)` (El fondo verde se añade automáticamente).
- **UI Inteligente**: Las opciones se adaptan (ej: "Transparente" se deshabilita para MP4, y el FPS se oculta para PNG).

### 🐛 Arreglo de Bugs Críticos (de v0.3.0)
- **Arreglado (BUG 1):** Las exportaciones de animación ya no **congelan la aplicación**.
- **Arreglado (BUG 2):** La exportación de **Secuencia PNG** ahora genera archivos con **fondo transparente real** en lugar de un fondo negro.
- **Arreglado (BUG 3):** Corregido el `TypeError` que causaba un **crash** al usar "Exportar capas por separado".

## 🔧 Implementación Técnica
- **`tools.py`**: Añadidas las nuevas clases `PlumaTool` y `DynamicLineTool`.
- **`canvas.py`**: Añadidas las clases `ExportFrameDialog`, `ExportAnimationDialog`, `ExportSignals` y `ExportWorker`. Integrado `QThreadPool` para la exportación en segundo plano. Refactorizado `keyPressEvent` para delegación genérica.
- **`project.py`**: Refactorizada la función `export_animation` para soportar modos de fondo (Transparente, Video, Croma) y arreglar el bug de transparencia en PNG.

## 🏆 Resumen de la Versión
La v0.3.1 continúa la transformación de Rotoscopia a una herramienta profesional estable. La adición de la **Pluma** y la **Línea Dinámica** permite un control de dibujo de precisión inigualable, mientras que el sistema de exportación en segundo plano soluciona el mayor problema de rendimiento, haciendo que la aplicación sea fluida y confiable de principio a fin.

---
