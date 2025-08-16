Resumen de los artículos

Frames per Second (FPS)
Define cuántos cuadros se muestran por segundo. A 12 FPS necesitas 12 dibujos para un segundo de animación; a 30 FPS, tendrás una animación más fluida, aunque requerirá más trabajo. Puedes configurar el FPS al crear el proyecto o cambiarlo luego desde los ajustes del proyecto. El estándar de la industria es 12 FPS como punto de partida 
support.flipaclip.com
.

Adding Images to a Project
Permite importar imágenes al proyecto: dentro de cualquier fotograma, toca los tres puntos, selecciona "Add Image" (Agregar Imagen), elige la fuente (galería, archivos, etc.), y ajusta tamaño y posición 
support.flipaclip.com
.

Importing Videos
Puedes usar videos como referencia para trazar o animar encima. Desde cualquier fotograma, accedés a tres puntos → "Add Video", eligís el archivo, recortás si querés, y al importar, se agrega como una nueva capa 
support.flipaclip.com
.

Copying and Pasting Frames
Herramientas rápidas para acelerar el flujo de trabajo:

Presioná largo en un fotograma en el visor y copiás/pasteás antes o después con íconos flechados.

En "Frames Viewer", podés seleccionar múltiples ff. para copiar y pegarlos en bloque.

También podés copiar capas individuales o seleccionadas con la herramienta "lasso" 
support.flipaclip.com
.

The Ruler Tool
Ideal para dibujar líneas perfectas o formas (línea recta, círculo, rectángulo). También permite activar el modo espejo y bloquear la guía. Para usarlo: doble toque en el ícono del pincel → aparece menú secundario con el objeto “ruler”; seleccionás tipo de forma, posicionás y ajustás tamaño, ángulo y posición. Para salir, tocás de nuevo el ícono del regla 
support.flipaclip.com
.

Color Picker
Varias modalidades para elegir color:

Wheel: anillo de matiz con disco interior para saturación.

Classic: sliders de matiz, saturación y brillo.

Harmony: sugiere paletas de color armónicas.

Value: permite ingresar valores numéricos o hexadecimales precisos.

Swatch: podés crear paletas guardadas (hasta 6 colores). También incluye cuentagotas para seleccionar color desde el lienzo. 
support.flipaclip.com

FlipaClip Brushes & Brush Settings

Brush Types: incluye Pen, Sketch, Airbrush (y versión oscura), Crayon, Pencil, Highlighter, Pixel Brush, Ink Brush, Spray Brush, Stippling, Rough Pen, Calligraphy, Halftone, Hatch. Algunos requieren suscripción Plus o pueden desbloquearse temporalmente con anuncios 
support.flipaclip.com
.

Brush Settings: ajustá Stabilizer (suaviza trazos), Thickness, Opacity y Color. Se accede tocando el ícono de ajustes del pincel. También podés cambiar rápidamente grosor y opacidad directamente desde la barra de herramientas 
support.flipaclip.com
.

Lasso Tool
(En FlipaClip dentro de Copy/Paste): permite seleccionar libremente una zona del dibujo (recordá que trabaja por capa). Útil para copiar partes específicas del dibujo y luego pegarlas en otro lugar o fotograma 
support.flipaclip.com
Wikipedia
.

Blur Brush
Se accede desde los tres puntos del menú de herramientas. El efecto difumina solamente la capa activa, ideal para añadir profundidad. Podés ajustar tamaño y opacidad 
support.flipaclip.com
.

Smudge Brush
También disponible desde los tres puntos: permite difuminar o mezclar los trazos dentro de la capa activa, creando transiciones suaves o efectos de movimiento 
support.flipaclip.com
.

Cómo podés aprovechar esta info en tu app

Bases técnicas claras: la explicación de FPS, estabilizador, herramientas de selección, pinceles y otros pueden servir como referencia funcional y de UX.

Inspiración de UI/UX: podés ver cómo se organizan los ajustes (por ejemplo, cómo se accede al Brush Settings rápidamente).

Documentación estructurada: podés organizar tu app con secciones similares: básicos, herramientas, pintura avanzada, atajos, etc.

Optimización del flujo de trabajo: atajos útiles como copiar/paste rápido, uso de lasso, o elegir frames por bloque son ideas valiosas.

---------------------------------------------------------

Resumen de los artículos
1. Playback Preview – Slow or Skipping Frames

Cuando la vista previa de tu animación se ve lenta o directamente salta cuadros, puede deberse a la capacidad de tu dispositivo o al uso sincronizado del audio.
Causas comunes:

Animaciones largas que sobrepasan la memoria RAM usada para la caché.

Presencia de audio, lo que obliga a la app a priorizar la sincronización y sacrificar fluidez.
Soluciones recomendadas:

Reducí el tamaño del canvas.

Ocultá o eliminá capas innecesarias.

Silenciá temporalmente el audio durante la revisión.

Desactivá modos de mezcla (Blend Mode) y efectos glow mientras revisás. Todos estos cambios mejoran la velocidad de reproducción, pero recordá volver a activarlos antes de exportar. 
FlipaClip

2. Using the Paint Bucket on a Different Layer

La herramienta cubo de pintura no permite llenar en otra capa directamente, pero hay un truco muy útil:

Duplicate la capa del arte lineal.

Ocultá la capa duplicada (solo veas la inferior).

Usá el cubo de pintura en esa capa visible.

Zoom para limpiar bordes si fuese necesario.

Volvé a mostrar la capa superior.
Esto te da una capa con el color aplicado por separado y mantiene intacto el arte original. 
FlipaClip

3. Blurry Images with Lasso Tool

Al usar la herramienta lazo, puede notarse que las imágenes seleccionadas o pegadas se vuelven borrosas. Esto es normal al trabajar con imágenes ráster (bitmap). Los problemas surgen al rotar o escalar copias de una imagen, perdiendo datos de píxeles cada vez.
Cómo evitarlo:

Siempre copiá desde la fuente original, no de la versión modificada.

Usá un canvas más grande para que la pérdida de calidad sea menos perceptible. 
FlipaClip

4. Using the Threshold Setting

Este ajuste ayuda a controlar la extensión del relleno del cubo de pintura, evitando que queden espacios blancos cerca del contorno.
Cómo usarlo:

Aparecía como un porcentaje debajo del selector de color del cubo.

Presioná el ícono de porcentaje y ajustalo hacia arriba o abajo para regular cuánto se expande el relleno. Aumentalo si observás espacios blancos cerca del borde. 
FlipaClip

5. Deleted and Merged Layers

Tené mucho cuidado al borrar o fusionar capas: estas acciones no se pueden deshacer una vez confirmadas.
Consejo crucial: realizá copias de seguridad de tus proyectos regularmente, especialmente antes de fusionar o eliminar capas finales. 
FlipaClip

Cómo podés aprovechar estos consejos en tu app

Rendimiento y fluidez: implementá opciones para ocultar capas o disminuir el canvas durante la vista previa, y restaurarlas antes de exportar.

Interacción entre capas y herramientas: replicá la técnica del “paint bucket en capa oculta” para mantener arte vectorizado separado del color.

Herramientas robustas de selección: agregá advertencias o reconstrucción de calidad cuando el usuario escale o rote imágenes ráster.

Ajustes precisos: incorporá un control de umbral (threshold) similar para ajustar la tolerancia del rellenado.

Seguridad de edición: sugerí al usuario guardar automáticamente versiones antes de acciones irreversibles en capas.

--------------------------------------------------------------

Resumen de Advanced Options de FlipaClip
1. Layers

Cómo gestionar capas: agregar, renombrar, seleccionar, reordenar, duplicar, bloquear, ocultar, ajustar opacidad y eliminar.

Límite de capas:

Gratis: hasta 3 capas.

Mediante anuncios: hasta 10 capas.

Premium: hasta 10 capas automáticamente.

Merging (fusión) solo disponible para usuarios premium; no se puede deshacer una vez realizado.

Nota: eliminar una capa la borra de todos los fotogramas y también es irreversible. 
FlipaClip

2. Onion Skinning

Técnica que permite ver fotogramas anteriores y posteriores en semitransparencia, facilitando animaciones más fluidas.

Ajustes disponibles:

Modo coloreado (rojo para previos, verde para siguientes).

Looping para animaciones cíclicas.

Control del número de frames visibles antes y después.

Ajuste de transparencia.

Skipping (omitir frames) para animaciones de alta resolución. 
FlipaClip

3. Voice Maker

Funcionalidad avanzada incluida en FlipaClip Plus que permite generar voces para personajes directamente dentro de la app. 
FlipaClip
+1

4. Removing the Watermark

Otra función premium (Plus): permite quitar la marca de agua (logo) de FlipaClip en las exportaciones del video. 
FlipaClip
+1

5. Rotoscoping with FlipaClip

Funcionalidad avanzada que permite trazar una imagen o video cuadro por cuadro para crear animaciones realistas (rotoscopia). 
FlipaClip

6. Using the Stabilizer

Estabilizador que suaviza los trazos al dibujar, configurable según la intensidad deseada. Disponible para todos los pinceles desde el menú de ajustes del pincel. 
FlipaClip

7. Glow Feature

Efecto de brillo que se puede aplicar a capas mediante el panel de configuración de capas. Ajustable con opciones para brillo y contorno. 
FlipaClip

8. Time-Lapse Feature

Permite generar automáticamente un video acelerado (time-lapse) de una animación, útil para mostrar el proceso de creación. 
FlipaClip

9. Slice with Magic Cut

Herramienta que corta partes específicas de imágenes o animaciones automáticamente, acelerando la edición o recorte. 
FlipaClip

10. The Grid

Opción para mostrar una cuadrícula guía mientras dibujás.

Ajustes disponibles: opacidad, distancia entre líneas verticales y horizontales.

No aparece en el producto final exportado.

Compatible con pixel snapping cuando está activado el efecto de píxel. 
FlipaClip

11. Blending Mode

Permite cambiar el modo de fusión de una capa (como multiply, overlay, etc.) para lograr efectos visuales complejos. Accesible desde la configuración de la capa. 
FlipaClip

12. Are there any keyboard shortcuts available for FlipaClip?

Atajos disponibles:

← / →: avanzar o retroceder fotogramas.

↑ / ↓: cambiar capa activa.

Space: reproducir vista previa.

O: activar/desactivar onion skin.

E: herramienta borrador.

B: pincel anterior. 
FlipaClip

Tablas comparativas para tu app
Funcionalidad	Utilidad principal
Capas (Layers)	Organización, control y composición visual
Onion Skinning	Precisión en animación cuadro a cuadro
Estabilizador	Trazos suaves, apoya precisión digital
Glow / Blending Mode	Efectos visuales creativos y llamativos
Grid & Pixel Snap	Diseño simétrico y trabajo pixel-perfect
Time-Lapse / Rotoscoping	Contenido dinámico y técnicas de animación avanzada
Voice Maker, Magic Cut, Watermark	Funciones premium que enriquecen experiencia y branding
Atajos de teclado	Fluidez y eficiencia en flujo de trabajo