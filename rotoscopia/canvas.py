"""UI principal (canvas y ventana) con soporte de Onion Skin.

Punto de entrada de ejecución en ``rotoscopia.main`` (no usar if __name__ == '__main__').
"""

from __future__ import annotations

import cv2
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets

from .settings import (
    DEFAULT_ONION_OPACITY,
    DEFAULT_ZOOM_MIN,
    DEFAULT_ZOOM_MAX,
    MAX_HISTORY,
    DEFAULT_BRUSH_SIZE,
    DEFAULT_BRUSH_COLOR,
    MAX_BRUSH_SIZE,
    PALETTE_COLORS,
    SHORTCUTS,
    DEFAULT_BG_OPACITY,
)
from .utils import cvimg_to_qimage
from .project import ProjectManager, EXPORT_BG_TRANSPARENT, EXPORT_BG_VIDEO, EXPORT_BG_CROMA
from .tools import (
    BrushTool, EraserTool, LineTool, HandTool, LassoTool, BucketTool, 
    RectangleTool, EllipseTool, PlumaTool, DynamicLineTool,
    AutoCalcoTool, AutoCalcoDock
)


class Layer:
    """Represents a single drawing layer with properties."""
    
    def __init__(self, name: str = "Layer", width: int = 640, height: int = 480):
        self.name = name
        self.pixmap = QtGui.QPixmap(width, height)
        self.pixmap.fill(QtCore.Qt.transparent)
        self.visible = True
        self.opacity = 1.0  # 0.0 to 1.0
        
    def copy(self) -> 'Layer':
        """Create a deep copy of this layer."""
        new_layer = Layer(self.name + " Copy", self.pixmap.width(), self.pixmap.height())
        new_layer.pixmap = QtGui.QPixmap(self.pixmap)
        new_layer.visible = self.visible
        new_layer.opacity = self.opacity
        return new_layer


class DrawingCanvas(QtWidgets.QLabel):
    strokeStarted = QtCore.Signal()
    strokeEnded = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        # Enable touch support
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.pen_width = DEFAULT_BRUSH_SIZE
        self.pen_color = QtGui.QColor(DEFAULT_BRUSH_COLOR); self.pen_color.setAlpha(255)
        self._drawing = False
        self.overlay: QtGui.QPixmap | None = None
        self.tool = None
        self.current_background: QtGui.QPixmap | None = None
        self.current_opacity = DEFAULT_BG_OPACITY
        self.scale_factor = 1.0
        self._panning = False
        self._pan_last = None
        # Onion Skin
        self.onion_enabled = False
        self.onion_opacity = DEFAULT_ONION_OPACITY
        self._onion_cache: dict[int, QtGui.QPixmap] = {}
        # Touch support for pinch zoom
        self._pinch_distance = 0.0
        self._is_pinching = False
        self._last_pinch_center = None  # For two-finger pan
        # Referencias externas
        self.project: ProjectManager | None = None
        self.window_ref = None  # MainWindow

    def set_size(self, w: int, h: int):
        if self.overlay is None or self.overlay.size() != QtCore.QSize(w, h):
            pix = QtGui.QPixmap(w, h); pix.fill(QtCore.Qt.transparent)
            self.overlay = pix
            self.setPixmap(QtGui.QPixmap(w, h))
        # Update all layers in current frame to match new size
        if self.window_ref and self.window_ref.current_frame_idx in self.window_ref.frame_layers:
            for layer in self.window_ref.frame_layers[self.window_ref.current_frame_idx]:
                if layer.pixmap.size() != QtCore.QSize(w, h):
                    old_pixmap = layer.pixmap
                    layer.pixmap = QtGui.QPixmap(w, h)
                    layer.pixmap.fill(QtCore.Qt.transparent)
                    # Copy old content if it exists
                    if not old_pixmap.isNull():
                        painter = QtGui.QPainter(layer.pixmap)
                        painter.drawPixmap(0, 0, old_pixmap)
                        painter.end()

    # ---------------- Tamaño / coordenadas ----------------
    def mapToOverlay(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """Mapea un punto del canvas a coordenadas de la imagen original (considerando zoom y offset)"""
        # Obtener dimensiones del frame actual
        if self.window_ref and self.window_ref.frames:
            frame = self.window_ref.frames[self.window_ref.current_frame_idx]
            bh, bw = frame.shape[:2]
        elif self.overlay is not None:
            bw = self.overlay.width()
            bh = self.overlay.height()
        else:
            return point
        
        # Calcular dimensiones escaladas y offset de centrado
        disp_w = int(bw * self.scale_factor)
        disp_h = int(bh * self.scale_factor)
        offset_x = (self.width() - disp_w) / 2.0
        offset_y = (self.height() - disp_h) / 2.0
        
        # Transformar coordenadas del canvas a coordenadas de la imagen
        x = (point.x() - offset_x) / self.scale_factor
        y = (point.y() - offset_y) / self.scale_factor
        
        # Clamp a los límites de la imagen
        x = max(0, min(bw - 1, int(round(x))))
        y = max(0, min(bh - 1, int(round(y))))
        
        return QtCore.QPoint(x, y)

    # ---------------- Eventos de ratón ----------------
    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # HandTool: manejar sin iniciar un trazo de dibujo
        from .tools import HandTool  # import local para evitar ciclos si se reordena
        if isinstance(self.tool, HandTool) and event.button() == QtCore.Qt.LeftButton:
            self.tool.on_mouse_press(event)
            return
        if event.button() == QtCore.Qt.LeftButton and self.overlay is not None:
            self._drawing = True; self.strokeStarted.emit()
            if self.tool:
                self.tool.on_mouse_press(event)
        elif event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._panning = True
            self._pan_last = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        from .tools import HandTool
        if isinstance(self.tool, HandTool):
            self.tool.on_mouse_move(event)
            return
        if self._panning:
            parent = self.parent()
            while parent and not isinstance(parent, QtWidgets.QScrollArea):
                parent = parent.parent()
            if isinstance(parent, QtWidgets.QScrollArea) and self._pan_last is not None:
                current = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
                dx = current.x() - self._pan_last.x(); dy = current.y() - self._pan_last.y()
                parent.horizontalScrollBar().setValue(parent.horizontalScrollBar().value() - dx)
                parent.verticalScrollBar().setValue(parent.verticalScrollBar().value() - dy)
                self._pan_last = current
            return
        if self._drawing and self.overlay is not None and self.tool:
            self.tool.on_mouse_move(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        from .tools import HandTool
        if isinstance(self.tool, HandTool) and event.button() == QtCore.Qt.LeftButton:
            self.tool.on_mouse_release(event)
            return
        if event.button() == QtCore.Qt.LeftButton:
            if self.tool:
                self.tool.on_mouse_release(event)
            self._drawing = False; self.strokeEnded.emit()
        elif event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._panning = False; self._pan_last = None

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        # 1. Importar TODAS las herramientas que pueden usar teclas
        #    (Ya debería estar así por el paso anterior)
        from .tools import LassoTool, PlumaTool, DynamicLineTool
        
        # 2. Delegar el evento a la herramienta activa si sabe manejarlo
        #    Revisamos si la herramienta actual (self.tool) tiene el método 'keyPressEvent'
        if hasattr(self.tool, 'keyPressEvent'):
            try:
                # Llamamos al método de la herramienta (ej: DynamicLineTool.keyPressEvent)
                # Ese método devuelve True si manejó la tecla (como hicimos en el Paso 3)
                was_handled = self.tool.keyPressEvent(event)
                
                if was_handled:
                    return  # La herramienta consumió la tecla (Enter/Esc), no hacer nada más.
            except Exception:
                # Proteger contra bugs en la propia herramienta
                pass
        
        # 3. Si la herramienta no tenía el método 'keyPressEvent',
        #    o si lo tenía pero no manejó esta tecla (devolvió False),
        #    dejar que el widget base maneje el evento (ej: para otros atajos).
        super().keyPressEvent(event)

    # ---------------- Overlay helpers ----------------
    def clear_overlay(self):
        if self.window_ref and self.overlay is not None:
            # Clear the active layer instead of just the overlay
            active_layer = self.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap.fill(QtCore.Qt.transparent)
                self.window_ref.compose_layers()
            else:
                self.overlay.fill(QtCore.Qt.transparent)
            self.update_display()

    def update_display(self, background_pixmap: QtGui.QPixmap | None = None, opacity: float = 0.5):
        if background_pixmap is not None:
            self.current_background = background_pixmap
            self.current_opacity = opacity
        base = self.current_background or self.overlay
        if base is not None:
            tw = int(base.width() * self.scale_factor); th = int(base.height() * self.scale_factor)
            self.resize(tw, th)
        self.update()

    # ---------------- Onion API ----------------
    def set_onion_enabled(self, enabled: bool):
        self.onion_enabled = enabled; self.update()

    def set_onion_opacity(self, value: float):
        self.onion_opacity = max(0.0, min(1.0, value))
        if self.onion_enabled:
            self.update()

    def clear_onion_cache(self):
        self._onion_cache.clear()

    def draw_onion_layer(self, painter: QtGui.QPainter, idx: int, is_prev: bool):
        """Dibuja el frame vecino tintado sólo sobre sus píxeles (no áreas transparentes)."""
        if not self.project or not self.window_ref:
            return
        if idx < 0 or idx >= len(self.window_ref.frames):
            return
        pm = self._onion_cache.get(idx)
        if pm is None:
            if idx in self.window_ref.frame_layers:
                pm = self.window_ref.compose_layers_for_frame(idx)
            else:
                ov_pix = self.window_ref.overlays.get(idx)
                if ov_pix is not None:
                    pm = ov_pix
                else:
                    loaded = self.project.load_frame(idx)
                    if loaded is None:
                        return
                    pm = loaded
            self._onion_cache[idx] = pm
        if pm.isNull():
            return
        base_w = pm.width(); base_h = pm.height()
        disp_w = int(base_w * self.scale_factor); disp_h = int(base_h * self.scale_factor)
        if abs(self.scale_factor - 1.0) > 1e-3:
            pm_draw = pm.scaled(disp_w, disp_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
        else:
            pm_draw = pm
        offset_x = (self.width() - disp_w) / 2.0; offset_y = (self.height() - disp_h) / 2.0
        alpha = int(self.onion_opacity * 255)
        color = QtGui.QColor(80, 160, 255, alpha) if is_prev else QtGui.QColor(255, 120, 120, alpha)
        tinted = QtGui.QPixmap(pm_draw.size())
        tinted.fill(QtCore.Qt.transparent)
        tp = QtGui.QPainter(tinted)
        tp.drawPixmap(0, 0, pm_draw)
        tp.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        tp.fillRect(tinted.rect(), color)
        tp.end()
        painter.drawPixmap(int(offset_x), int(offset_y), tinted)

    # ---------------- Paint ----------------
    def paintEvent(self, event: QtGui.QPaintEvent):  # noqa: D401
        painter = QtGui.QPainter(self); painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        base = self.current_background; ov = self.overlay
        if base is not None:
            bw = base.width(); bh = base.height()
        elif ov is not None:
            bw = ov.width(); bh = ov.height()
        else:
            bw = self.width(); bh = self.height()
        disp_w = int(bw * self.scale_factor); disp_h = int(bh * self.scale_factor)
        offset_x = (self.width() - disp_w) / 2.0; offset_y = (self.height() - disp_h) / 2.0
        # Fondo
        if base is not None:
            base_draw = base.scaled(disp_w, disp_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation) if abs(self.scale_factor - 1.0) > 1e-3 else base
            painter.save(); painter.setOpacity(self.current_opacity); painter.drawPixmap(int(offset_x), int(offset_y), base_draw); painter.restore()
        # Onion
        if self.onion_enabled and self.window_ref is not None:
            cf = self.window_ref.current_frame_idx
            if cf - 1 >= 0:
                self.draw_onion_layer(painter, cf - 1, True)
            if cf + 1 < len(self.window_ref.frames):
                self.draw_onion_layer(painter, cf + 1, False)
        # Overlay actual
        if ov is not None and not ov.isNull():
            ov_draw = ov.scaled(disp_w, disp_h, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation) if abs(self.scale_factor - 1.0) > 1e-3 else ov
            painter.drawPixmap(int(offset_x), int(offset_y), ov_draw)
        
        # Preview de Auto Calco (si está activo)
        if self.window_ref and hasattr(self.window_ref, 'auto_calco_tool'):
            auto_calco = self.window_ref.auto_calco_tool
            if auto_calco.preview_pixmap is not None and not auto_calco.preview_pixmap.isNull():
                # Obtener posición original de la captura
                p = auto_calco.roi_rect.topLeft()
                
                # Escalar el preview_pixmap según el zoom actual
                preview_w = int(auto_calco.preview_pixmap.width() * self.scale_factor)
                preview_h = int(auto_calco.preview_pixmap.height() * self.scale_factor)
                scaled_preview = auto_calco.preview_pixmap.scaled(
                    preview_w, preview_h,
                    QtCore.Qt.IgnoreAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
                
                # Calcular posición en pantalla
                screen_x = int(offset_x + p.x() * self.scale_factor)
                screen_y = int(offset_y + p.y() * self.scale_factor)
                
                # Dibujar el preview
                painter.drawPixmap(screen_x, screen_y, scaled_preview)
        
        # Dibujo de selección (Lasso) si activo
        from .tools import LassoTool
        if isinstance(self.tool, LassoTool):
            # Crear painter sobre coordenadas overlay escaladas
            painter.save()
            painter.translate(offset_x, offset_y)
            painter.scale(self.scale_factor, self.scale_factor)
            try:
                self.tool.draw_selection(painter)
            except Exception:
                pass
            painter.restore()
        # Previsualización de Pluma
        from .tools import PlumaTool, DynamicLineTool
        if isinstance(self.tool, PlumaTool):
            painter.save()
            painter.translate(offset_x, offset_y)
            painter.scale(self.scale_factor, self.scale_factor)
            try:
                self.tool.draw_preview(painter)
            except Exception:
                pass  # Evitar que un error de preview rompa el render
            painter.restore()
        # Previsualización de Línea Dinámica
        if isinstance(self.tool, DynamicLineTool):
            painter.save()
            painter.translate(offset_x, offset_y)
            painter.scale(self.scale_factor, self.scale_factor)
            try:
                self.tool.draw_preview(painter)
            except Exception:
                pass  # Evitar que un error de preview rompa el render
            painter.restore()
        painter.end()

    # ---------------- Touch support ----------------
    def touchEvent(self, event):
        """Convert touch events to mouse events for drawing support, with pinch zoom."""
        if not event.touchPoints():
            return False
        
        touch_points = event.touchPoints()
        
        # Handle two-finger pinch zoom
        if len(touch_points) >= 2:
            self._handle_pinch_zoom(event, touch_points)
            return True
        
        # Handle single finger drawing (only if not currently pinching)
        if len(touch_points) == 1 and not self._is_pinching:
            self._handle_single_touch_drawing(event, touch_points[0])
            return True
        
        # Accept the event to prevent further processing
        event.accept()
        return True
    
    def _handle_pinch_zoom(self, event, touch_points):
        """Handle two-finger pinch zoom gesture and two-finger pan."""
        if len(touch_points) < 2:
            return
            
        # Calculate distance between the two fingers
        point1 = touch_points[0].position()
        point2 = touch_points[1].position()
        current_distance = ((point1.x() - point2.x()) ** 2 + (point1.y() - point2.y()) ** 2) ** 0.5
        
        # Calculate center point between fingers
        center_x = (point1.x() + point2.x()) / 2
        center_y = (point1.y() + point2.y()) / 2
        current_center = QtCore.QPoint(int(center_x), int(center_y))
        
        if event.type() == QtCore.QEvent.TouchBegin:
            self._pinch_distance = current_distance
            self._last_pinch_center = current_center
            self._is_pinching = True
            
        elif event.type() == QtCore.QEvent.TouchUpdate and self._is_pinching:
            if self._pinch_distance > 0 and self._last_pinch_center is not None:
                # Calculate distance ratio for zoom detection
                distance_ratio = current_distance / self._pinch_distance
                distance_change = abs(distance_ratio - 1.0)
                
                # Calculate center movement for pan detection
                center_delta_x = current_center.x() - self._last_pinch_center.x()
                center_delta_y = current_center.y() - self._last_pinch_center.y()
                center_movement = (center_delta_x ** 2 + center_delta_y ** 2) ** 0.5
                
                # Prioritize zoom if distance change is significant
                if distance_change > 0.05:  # 5% threshold for zoom
                    zoom_factor = distance_ratio
                    
                    # Limit zoom factor to reasonable values
                    zoom_factor = max(0.5, min(2.0, zoom_factor))
                    
                    # Apply zoom through window reference
                    if self.window_ref:
                        self.window_ref.zoom_with_anchor(zoom_factor, current_center)
                    
                    # Update stored distance
                    self._pinch_distance = current_distance
                
                # Apply pan if center moved significantly and no major zoom
                elif center_movement > 5:  # 5 pixel threshold for pan
                    self._apply_two_finger_pan(center_delta_x, center_delta_y)
                
                # Update stored center position
                self._last_pinch_center = current_center
                    
        elif event.type() == QtCore.QEvent.TouchEnd:
            self._is_pinching = False
            self._pinch_distance = 0.0
            self._last_pinch_center = None
        
        event.accept()
    
    def _apply_two_finger_pan(self, delta_x, delta_y):
        """Apply two-finger pan movement to the canvas."""
        # Find the scroll area parent (same logic as mouse pan)
        parent = self.parent()
        while parent and not isinstance(parent, QtWidgets.QScrollArea):
            parent = parent.parent()
            
        if isinstance(parent, QtWidgets.QScrollArea):
            # Apply the pan movement (invert delta like mouse pan does)
            h_scrollbar = parent.horizontalScrollBar()
            v_scrollbar = parent.verticalScrollBar()
            
            h_scrollbar.setValue(h_scrollbar.value() - delta_x)
            v_scrollbar.setValue(v_scrollbar.value() - delta_y)
    
    def _handle_single_touch_drawing(self, event, touch_point):
        """Handle single finger touch for drawing."""
        pos = touch_point.position().toPoint()
        
        # Create corresponding mouse event
        mouse_event = None
        
        if event.type() == QtCore.QEvent.TouchBegin:
            mouse_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonPress,
                touch_point.position(),
                touch_point.globalPosition(),
                QtCore.Qt.LeftButton,
                QtCore.Qt.LeftButton,
                QtCore.Qt.NoModifier
            )
            self.mousePressEvent(mouse_event)
            
        elif event.type() == QtCore.QEvent.TouchUpdate:
            mouse_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseMove,
                touch_point.position(),
                touch_point.globalPosition(),
                QtCore.Qt.LeftButton,
                QtCore.Qt.LeftButton,
                QtCore.Qt.NoModifier
            )
            self.mouseMoveEvent(mouse_event)
            
        elif event.type() == QtCore.QEvent.TouchEnd:
            mouse_event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseButtonRelease,
                touch_point.position(),
                touch_point.globalPosition(),
                QtCore.Qt.LeftButton,
                QtCore.Qt.LeftButton,
                QtCore.Qt.NoModifier
            )
            self.mouseReleaseEvent(mouse_event)
        
        event.accept()

    def event(self, event):
        """Override event handler to intercept touch events."""
        if event.type() in (QtCore.QEvent.TouchBegin, QtCore.QEvent.TouchUpdate, QtCore.QEvent.TouchEnd):
            return self.touchEvent(event)
        return super().event(event)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Rotoscopia MVP - Modular')
        self.resize(1100, 750)
        # Estado
        self.frames: list = []
        self.current_frame_idx = 0
        self.video_path: str | None = None
        self.undo_stacks: dict[int, list[QtGui.QPixmap]] = {}
        self.redo_stacks: dict[int, list[QtGui.QPixmap]] = {}
        self.max_history = MAX_HISTORY
        self.dirty_frames: set[int] = set()
        self.is_dirty = False  # Track unsaved changes
        self.project_path = None
        self.project_name = None
        self.fps_original = None  # Original video FPS
        self.fps_target = None   # Target FPS for subsampling
        self.zoom_min = DEFAULT_ZOOM_MIN
        self.zoom_max = DEFAULT_ZOOM_MAX
        self.show_background = True
        self.project_mgr = ProjectManager(self)
        self.project = self.project_mgr  # Alias for specification compliance
        self.thread_pool = QtCore.QThreadPool()
        
        self.frame_layers: dict[int, list[Layer]] = {}  # frame_idx -> list of layers
        self.current_layer_idx = 0  # index of active layer in current frame
        
        # Keep old overlay system for backward compatibility during transition
        self.overlays = {}
        
        self._init_ui()
        
        # Inicializar Auto Calco (después de que canvas esté listo)
        self.auto_calco_tool = AutoCalcoTool(self.canvas)
        self.auto_calco_dock = AutoCalcoDock(self, self.auto_calco_tool)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.auto_calco_dock)
        
        self.set_tool('brush')
        if not self.statusBar():
            self.setStatusBar(QtWidgets.QStatusBar())
        self.statusBar().showMessage('Listo')

    # ---------------- UI ----------------
    def _init_ui(self):
        # Contenedor central y scroll
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        self.canvas = DrawingCanvas()
        # Ensure the canvas can receive keyboard focus so tools get key events (Esc, etc.)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setAlignment(QtCore.Qt.AlignCenter)
        self.canvas.setMinimumSize(640, 480)
        self.canvas.setStyleSheet('border:1px solid #444; background:white;')
        self.canvas.project = self.project_mgr
        self.canvas.window_ref = self
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setAlignment(QtCore.Qt.AlignCenter)
        scroll.setWidget(self.canvas)
        vbox.addWidget(scroll)
        self.setCentralWidget(container)

        # Menú Archivo reorganizado
        menubar = self.menuBar() if hasattr(self, 'menuBar') else None
        if menubar is None:
            menubar = QtWidgets.QMenuBar(self)
            self.setMenuBar(menubar)
        # Elimina menú Archivo previo si se había creado ya (evitar duplicados al reinicializar)
        for m in menubar.findChildren(QtWidgets.QMenu):
            if m.title() == 'Archivo':
                menubar.removeAction(m.menuAction())
        menu_archivo = menubar.addMenu('Archivo')
        # Acciones solicitadas (orden): Importar, Exportar Frame (PNG), Guardar, Cargar, Cerrar, Help
        self.action_import = QtGui.QAction('Importar', self)
        self.action_import.triggered.connect(self.open_video)
        self.action_export_frame = QtGui.QAction('Exportar Frame (PNG)', self)
        self.action_export_frame.triggered.connect(self.save_current_overlay)
        self.action_export_animation = QtGui.QAction('Exportar Animación...', self)
        self.action_export_animation.triggered.connect(self.show_export_animation_dialog)
        self.action_save_project_menu = QtGui.QAction('Guardar', self)
        self.action_save_project_menu.triggered.connect(self.save_project_dialog)
        self.action_load_project_menu = QtGui.QAction('Cargar', self)
        self.action_load_project_menu.triggered.connect(self.load_project_dialog)
        self.action_close_project_menu = QtGui.QAction('Cerrar', self)
        self.action_close_project_menu.triggered.connect(self.close_project)
        self.action_help = QtGui.QAction('Help', self)
        self.action_help.triggered.connect(self.show_help_manual)
        for a in [
            self.action_import,
            self.action_export_frame,
            self.action_export_animation,
            self.action_save_project_menu,
            self.action_load_project_menu,
            self.action_close_project_menu,
            self.action_help
        ]:
            menu_archivo.addAction(a)

        # Toolbar Frames
        tb_frames = QtWidgets.QToolBar('Frames')
        act_prev = QtGui.QAction('<<', self); act_prev.triggered.connect(self.prev_frame)
        act_next = QtGui.QAction('>>', self); act_next.triggered.connect(self.next_frame)
        act_copy = QtGui.QAction('Copiar frame anterior', self); act_copy.triggered.connect(self.copy_previous_overlay)
        tb_frames.addActions([act_prev, act_next, act_copy])
        self.frame_label = QtWidgets.QLabel('Frame: 0 / 0')
        frame_label_act = QtWidgets.QWidgetAction(self); frame_label_act.setDefaultWidget(self.frame_label)
        tb_frames.addAction(frame_label_act)
        self.addToolBar(tb_frames)

        # Dock Herramientas (reemplaza toolbar vertical para ser como panel de capas)
        self.tool_group = QtGui.QActionGroup(self); self.tool_group.setExclusive(True)
        self.action_brush = QtGui.QAction('Pincel', self, checkable=True)
        self.action_eraser = QtGui.QAction('Borrar', self, checkable=True)
        self.action_line = QtGui.QAction('Línea', self, checkable=True)
        self.action_lasso = QtGui.QAction('Lazo', self, checkable=True)
        self.action_hand = QtGui.QAction('Mano', self, checkable=True)
        self.action_bucket = QtGui.QAction('Balde', self, checkable=True)
        self.action_rectangle = QtGui.QAction('Rect', self, checkable=True)
        self.action_ellipse = QtGui.QAction('Elipse', self, checkable=True)
        self.action_pluma = QtGui.QAction('Pluma', self, checkable=True)
        self.action_dynamic_line = QtGui.QAction('Línea Dinámica', self, checkable=True)
        tools_dock = QtWidgets.QDockWidget('Herramientas', self)
        tools_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        tools_widget = QtWidgets.QWidget(); tools_layout = QtWidgets.QVBoxLayout(tools_widget); tools_layout.setContentsMargins(4,4,4,4)
        for act, name in [
            (self.action_brush, 'brush'),
            (self.action_eraser, 'eraser'),
            (self.action_line, 'line'),
            (self.action_lasso, 'lasso'),
            (self.action_hand, 'hand'),
            (self.action_bucket, 'bucket'),
            (self.action_rectangle, 'rectangle'),
            (self.action_ellipse, 'ellipse'),
            (self.action_pluma, 'pluma'),
            (self.action_dynamic_line, 'dynamic_line'),
        ]:
            self.tool_group.addAction(act)
            act.triggered.connect(lambda checked, n=name: checked and self.set_tool(n))
            btn = QtWidgets.QToolButton()
            btn.setDefaultAction(act)  # mantiene texto, checkable y sincroniza estados
            tools_layout.addWidget(btn)
        tools_layout.addStretch(1)
        tools_dock.setWidget(tools_widget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, tools_dock)

        # (Reubicado) Controles de vista que se añadirán al panel de capas
        self.action_bg_toggle = QtGui.QAction('Fondo', self, checkable=True)
        self.action_bg_toggle.setChecked(True)
        self.action_bg_toggle.toggled.connect(self.set_bg_visible)
        self.action_onion = QtGui.QAction('Onion', self, checkable=True)
        # Sliders
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(DEFAULT_BG_OPACITY * 100))
        self.opacity_slider.setFixedWidth(120)
        self.opacity_slider.valueChanged.connect(self.refresh_view)
        self.onion_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.onion_opacity_slider.setRange(0, 100)
        self.onion_opacity_slider.setValue(int(DEFAULT_ONION_OPACITY * 100))
        self.onion_opacity_slider.setFixedWidth(120)
        self.action_onion.toggled.connect(self.canvas.set_onion_enabled)
        self.onion_opacity_slider.valueChanged.connect(lambda v: self.canvas.set_onion_opacity(v / 100.0))
        self.action_onion.toggled.connect(self.onion_opacity_slider.setEnabled)
        self.onion_opacity_slider.setEnabled(self.action_onion.isChecked())

        # Create layer dock after view controls are defined
        self._create_layer_dock()

        # (Reubicado) Controles de dibujo: slider de pincel y colores ahora irán en el dock de herramientas
        self.brush_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.brush_slider.setRange(1, MAX_BRUSH_SIZE)
        self.brush_slider.setValue(DEFAULT_BRUSH_SIZE)
        self.brush_slider.setFixedWidth(120)
        self.brush_slider.valueChanged.connect(self.apply_brush_changes)
        try:
            for dw in self.findChildren(QtWidgets.QDockWidget):
                if dw.windowTitle() == 'Herramientas':
                    tools_widget = dw.widget()
                    if tools_widget:
                        lay = tools_widget.layout()
                        if lay:
                            lay.addWidget(QtWidgets.QLabel('Grosor'))
                            lay.addWidget(self.brush_slider)
                            palette_row = QtWidgets.QHBoxLayout()
                            for col in PALETTE_COLORS:
                                btn = QtWidgets.QToolButton(); btn.setFixedSize(20, 20)
                                btn.setStyleSheet(f'background:{col}; border:1px solid #444;')
                                btn.clicked.connect(lambda _c=False, c=col: self.set_brush_color(c))
                                palette_row.addWidget(btn)
                            custom_btn = QtWidgets.QToolButton(); custom_btn.setText('+'); custom_btn.setFixedSize(24, 24)
                            custom_btn.clicked.connect(self.pick_custom_color)
                            palette_row.addWidget(custom_btn)
                            container_palette = QtWidgets.QWidget(); container_palette.setLayout(palette_row)
                            lay.addWidget(QtWidgets.QLabel('Color'))
                            lay.addWidget(container_palette)
        except Exception:
            pass

        # Shortcuts y overlays
        self.overlays = {}
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['next_frame']), self, activated=self.next_frame)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['prev_frame']), self, activated=self.prev_frame)
        if 'copy_prev_frame' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['copy_prev_frame']), self, activated=self.copy_previous_overlay)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['save_overlay']), self, activated=self.save_current_overlay)
        if 'save_project' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['save_project']), self, activated=self.save_project_dialog)
        if 'export_animation' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['export_animation']), self, activated=lambda: self.project_mgr.export_animation(self.frames))
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['undo']), self, activated=self.undo)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['redo']), self, activated=self.redo)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['brush_tool']), self, activated=lambda: self.action_brush.trigger())
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['eraser_tool']), self, activated=lambda: self.action_eraser.trigger())
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['line_tool']), self, activated=lambda: self.action_line.trigger())
        if 'lasso_tool' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_tool']), self, activated=lambda: self.action_lasso.trigger())
        if 'bucket_tool' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['bucket_tool']), self, activated=lambda: self.action_bucket.trigger())
        if 'rectangle_tool' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['rectangle_tool']), self, activated=lambda: self.action_rectangle.trigger())
        if 'ellipse_tool' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['ellipse_tool']), self, activated=lambda: self.action_ellipse.trigger())
        if 'copy_selection' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['copy_selection']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.copy_selection())
        if 'paste_selection' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['paste_selection']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.paste_selection())
        if 'invert_selection' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['invert_selection']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.invert_selection())
        if 'select_all' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['select_all']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.select_all())
        if 'lasso_rotate_cw' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_rotate_cw']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.rotate_90(True))
        if 'lasso_rotate_ccw' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_rotate_ccw']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.rotate_90(False))
        if 'lasso_flip_horizontal' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_flip_horizontal']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.flip(True))
        if 'lasso_flip_vertical' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_flip_vertical']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.flip(False))
        if 'lasso_rotate_small_ccw' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_rotate_small_ccw']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.rotate_angle(-5))
        if 'lasso_rotate_small_cw' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_rotate_small_cw']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.rotate_angle(5))
        if 'lasso_rotate_big_ccw' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_rotate_big_ccw']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.rotate_angle(-15))
        if 'lasso_rotate_big_cw' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['lasso_rotate_big_cw']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.rotate_angle(15))
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['hand_tool']), self, activated=lambda: self.action_hand.trigger())
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['toggle_onion']), self, activated=lambda: self.action_onion.setChecked(not self.action_onion.isChecked()))
        if 'toggle_background' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['toggle_background']), self, activated=lambda: self.action_bg_toggle.setChecked(not self.action_bg_toggle.isChecked()))
        
        # Atajo para Auto-Calco (Ctrl+Shift+A)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+A'), self, activated=self.activar_auto_calco)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['zoom_in']), self, activated=lambda: self.change_zoom(1.15))
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['zoom_out']), self, activated=lambda: self.change_zoom(1 / 1.15))
        if 'reset_zoom' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['reset_zoom']), self, activated=lambda: (setattr(self.canvas, 'scale_factor', 1.0), self.refresh_view()))

        from .tools import BrushTool, EraserTool
        if 'brush_mode_1' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['brush_mode_1']), self, activated=lambda: isinstance(self.canvas.tool, BrushTool) and self._set_brush_mode(0))
        if 'brush_mode_2' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['brush_mode_2']), self, activated=lambda: isinstance(self.canvas.tool, BrushTool) and self._set_brush_mode(1))
        if 'brush_mode_3' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['brush_mode_3']), self, activated=lambda: isinstance(self.canvas.tool, BrushTool) and self._set_brush_mode(2))
        if 'eraser_mode_1' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['eraser_mode_1']), self, activated=lambda: isinstance(self.canvas.tool, EraserTool) and self._set_eraser_mode(0))
        if 'eraser_mode_2' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['eraser_mode_2']), self, activated=lambda: isinstance(self.canvas.tool, EraserTool) and self._set_eraser_mode(1))
        if 'eraser_mode_3' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['eraser_mode_3']), self, activated=lambda: isinstance(self.canvas.tool, EraserTool) and self._set_eraser_mode(2))

        # Hooks canvas
        self.canvas.installEventFilter(self)
        self.canvas.strokeStarted.connect(self.push_undo_snapshot)
        self.canvas.strokeEnded.connect(self.mark_dirty_current)
        self.action_brush.setChecked(True)

    def _create_layer_dock(self):
        """Create the layer management dock widget."""
        self.layer_dock = QtWidgets.QDockWidget('Capas', self)
        self.layer_dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        
        # Layer dock content
        layer_widget = QtWidgets.QWidget()
        layer_layout = QtWidgets.QVBoxLayout(layer_widget)
        
        # Layer list
        self.layer_list = QtWidgets.QListWidget()
        self.layer_list.setMaximumHeight(200)
        self.layer_list.itemClicked.connect(self.on_layer_selected)
        layer_layout.addWidget(QtWidgets.QLabel('Capas:'))
        layer_layout.addWidget(self.layer_list)
        
        # Layer controls
        controls_layout = QtWidgets.QHBoxLayout()
        self.btn_add_layer = QtWidgets.QPushButton('+')
        self.btn_add_layer.setFixedSize(30, 30)
        self.btn_add_layer.clicked.connect(self.add_layer_ui)
        self.btn_delete_layer = QtWidgets.QPushButton('-')
        self.btn_delete_layer.setFixedSize(30, 30)
        self.btn_delete_layer.clicked.connect(self.delete_current_layer)
        self.btn_duplicate_layer = QtWidgets.QPushButton('⧉')
        self.btn_duplicate_layer.setFixedSize(30, 30)
        self.btn_duplicate_layer.clicked.connect(self.duplicate_current_layer)
        self.btn_rename_layer = QtWidgets.QPushButton('✏')
        self.btn_rename_layer.setFixedSize(30, 30)
        self.btn_rename_layer.clicked.connect(self.rename_current_layer)
        
        controls_layout.addWidget(self.btn_add_layer)
        controls_layout.addWidget(self.btn_delete_layer)
        controls_layout.addWidget(self.btn_duplicate_layer)
        controls_layout.addWidget(self.btn_rename_layer)
        controls_layout.addStretch()
        layer_layout.addLayout(controls_layout)
        
        # Layer properties
        props_group = QtWidgets.QGroupBox('Propiedades de Capa')
        props_layout = QtWidgets.QVBoxLayout(props_group)
        
        # Visibility checkbox
        self.layer_visible_cb = QtWidgets.QCheckBox('Visible')
        self.layer_visible_cb.setChecked(True)
        self.layer_visible_cb.toggled.connect(self.on_layer_visibility_changed)
        props_layout.addWidget(self.layer_visible_cb)
        
        # Opacity slider
        opacity_layout = QtWidgets.QHBoxLayout()
        opacity_layout.addWidget(QtWidgets.QLabel('Opacidad:'))
        self.layer_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.layer_opacity_slider.setRange(0, 100)
        self.layer_opacity_slider.setValue(100)
        self.layer_opacity_slider.valueChanged.connect(self.on_layer_opacity_changed)
        self.layer_opacity_label = QtWidgets.QLabel('100%')
        self.layer_opacity_label.setFixedWidth(35)
        opacity_layout.addWidget(self.layer_opacity_slider)
        opacity_layout.addWidget(self.layer_opacity_label)
        props_layout.addLayout(opacity_layout)
        
        layer_layout.addWidget(props_group)
        
        # Vista controls group
        view_group = QtWidgets.QGroupBox('Vista')
        view_layout = QtWidgets.QVBoxLayout(view_group)
        
        # Background controls
        bg_row = QtWidgets.QHBoxLayout()
        bg_cb = QtWidgets.QCheckBox('Fondo visible')
        bg_cb.setChecked(self.action_bg_toggle.isChecked())
        # Sincronización bidireccional
        bg_cb.toggled.connect(self.action_bg_toggle.setChecked)
        self.action_bg_toggle.toggled.connect(bg_cb.setChecked)
        bg_row.addWidget(bg_cb)
        
        # Reset background button
        self.toggle_background_btn = QtWidgets.QPushButton('Reset Fondo')
        self.toggle_background_btn.clicked.connect(lambda: (self.opacity_slider.setValue(int(DEFAULT_BG_OPACITY * 100)), self.set_bg_visible(True)))
        bg_row.addWidget(self.toggle_background_btn)
        bg_row.addStretch()
        view_layout.addLayout(bg_row)
        
        # Background opacity slider
        bg_op_row = QtWidgets.QHBoxLayout()
        bg_op_row.addWidget(QtWidgets.QLabel('Opacidad Fondo:'))
        self.bg_opacity_slider = self.opacity_slider  # Referencia para el nombre solicitado
        bg_op_row.addWidget(self.bg_opacity_slider)
        view_layout.addLayout(bg_op_row)
        
        # Onion controls
        onion_row = QtWidgets.QHBoxLayout()
        onion_cb = QtWidgets.QCheckBox('Onion')
        onion_cb.setChecked(self.action_onion.isChecked())
        # Sincronización bidireccional
        onion_cb.toggled.connect(self.action_onion.setChecked)
        self.action_onion.toggled.connect(onion_cb.setChecked)
        onion_row.addWidget(onion_cb)
        
        # Toggle onion button (si se necesita en el futuro)
        self.toggle_onion_btn = QtWidgets.QPushButton('Toggle Onion')
        self.toggle_onion_btn.clicked.connect(lambda: self.action_onion.setChecked(not self.action_onion.isChecked()))
        onion_row.addWidget(self.toggle_onion_btn)
        onion_row.addStretch()
        view_layout.addLayout(onion_row)
        
        # Onion opacity slider
        onion_op_row = QtWidgets.QHBoxLayout()
        onion_op_row.addWidget(QtWidgets.QLabel('Opacidad Onion:'))
        onion_op_row.addWidget(self.onion_opacity_slider)
        view_layout.addLayout(onion_op_row)
        
        layer_layout.addWidget(view_group)
        layer_layout.addStretch()
        
        self.layer_dock.setWidget(layer_widget)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.layer_dock)

    def update_layer_list(self):
        """Update the layer list widget to show current frame layers."""
        self.layer_list.clear()
        if self.current_frame_idx not in self.frame_layers:
            return
        
        layers = self.frame_layers[self.current_frame_idx]
        for i, layer in enumerate(reversed(layers)):  # Show top layer first
            item = QtWidgets.QListWidgetItem(layer.name)
            item.setData(QtCore.Qt.UserRole, len(layers) - 1 - i)  # Store actual index
            
            # Visual indicators
            if not layer.visible:
                item.setForeground(QtGui.QColor(128, 128, 128))  # Gray out invisible layers
            if len(layers) - 1 - i == self.current_layer_idx:
                item.setBackground(QtGui.QColor(100, 150, 255, 100))  # Highlight active layer
            
            self.layer_list.addItem(item)
        
        # Update layer properties controls
        active_layer = self.get_active_layer()
        if active_layer:
            self.layer_visible_cb.setChecked(active_layer.visible)
            self.layer_opacity_slider.setValue(int(active_layer.opacity * 100))
            self.layer_opacity_label.setText(f'{int(active_layer.opacity * 100)}%')

    def on_layer_selected(self, item):
        """Handle layer selection in the list."""
        layer_idx = item.data(QtCore.Qt.UserRole)
        if layer_idx is not None:
            self.current_layer_idx = layer_idx
            self.update_layer_list()
            self.statusBar().showMessage(f'Capa activa: {item.text()}')

    def on_layer_visibility_changed(self, visible):
        """Handle layer visibility toggle."""
        active_layer = self.get_active_layer()
        if active_layer:
            active_layer.visible = visible
            self.compose_layers()
            self.update_layer_list()

    def on_layer_opacity_changed(self, value):
        """Handle layer opacity change."""
        active_layer = self.get_active_layer()
        if active_layer:
            active_layer.opacity = value / 100.0
            self.layer_opacity_label.setText(f'{value}%')
            self.compose_layers()

    def add_layer_ui(self):
        """Add a new layer with UI feedback."""
        if not self.frames:
            QtWidgets.QMessageBox.information(self, 'Info', 'Carga un video primero.')
            return
        
        name, ok = QtWidgets.QInputDialog.getText(self, 'Nueva Capa', 'Nombre de la capa:', text=f'Layer {len(self.frame_layers.get(self.current_frame_idx, [])) + 1}')
        if ok and name.strip():
            self.add_layer(name.strip())
            self.update_layer_list()
            self.statusBar().showMessage(f'Capa agregada: {name.strip()}')

    def delete_current_layer(self):
        """Delete the currently active layer."""
        if self.current_frame_idx not in self.frame_layers:
            return
        
        layers = self.frame_layers[self.current_frame_idx]
        if len(layers) <= 1:
            QtWidgets.QMessageBox.information(self, 'Info', 'No se puede eliminar la última capa.')
            return
        
        if 0 <= self.current_layer_idx < len(layers):
            layer_name = layers[self.current_layer_idx].name
            reply = QtWidgets.QMessageBox.question(self, 'Eliminar Capa', f'¿Eliminar la capa "{layer_name}"?')
            if reply == QtWidgets.QMessageBox.Yes:
                layers.pop(self.current_layer_idx)
                if self.current_layer_idx >= len(layers):
                    self.current_layer_idx = len(layers) - 1
                self.compose_layers()
                self.update_layer_list()
                self.statusBar().showMessage(f'Capa eliminada: {layer_name}')

    def duplicate_current_layer(self):
        """Duplicate the currently active layer."""
        active_layer = self.get_active_layer()
        if not active_layer:
            return
        
        new_layer = active_layer.copy()
        new_layer.name = f'{active_layer.name} Copy'
        
        layers = self.frame_layers[self.current_frame_idx]
        layers.insert(self.current_layer_idx + 1, new_layer)
        self.current_layer_idx += 1
        self.compose_layers()
        self.update_layer_list()
        self.statusBar().showMessage(f'Capa duplicada: {new_layer.name}')

    def rename_current_layer(self):
        """Rename the currently selected layer."""
        if self.current_frame_idx not in self.frame_layers:
            return
            
        layers = self.frame_layers[self.current_frame_idx]
        if not layers or self.current_layer_idx < 0 or self.current_layer_idx >= len(layers):
            return
            
        current_layer = layers[self.current_layer_idx]
        
        # Show input dialog
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, 'Renombrar Capa', 
            'Nuevo nombre:', 
            text=current_layer.name
        )
        
        if ok and new_name.strip():
            current_layer.name = new_name.strip()
            self.update_layer_list()
            self.mark_dirty_current()
            self.statusBar().showMessage(f'Capa renombrada: {current_layer.name}')

    # ---------------- Core ops ----------------
    # Modified open_video to work with layers
    def open_video(self):
        # 1. Check if project is loaded and ask for confirmation
        if self.project is not None and (self.frames or self.is_dirty):
            if not self.ask_to_save_and_close():
                return  # User cancelled, abort operation
            
            # Reset canvas and clear project state
            self.frames.clear()
            self.overlays.clear()
            self.frame_layers.clear()
            self.undo_stacks.clear()
            self.redo_stacks.clear()
            self.dirty_frames.clear()
            self.is_dirty = False
            self.current_frame_idx = 0
            self.current_layer_idx = 0
            self.project_path = None
            self.project_name = None
            self.fps_original = None
            self.fps_target = None
            self.canvas.overlay = None
            self.canvas.current_background = None
            try:
                self.canvas.clear_onion_cache()
            except Exception:
                pass
            # Note: Don't set self.project = None as we still need the ProjectManager
            
        # Select video file
        filter_str = 'Videos/Imagenes (*.mp4 *.MP4 *.mov *.MOV *.avi *.AVI *.mkv *.MKV *.png *.PNG *.jpg *.JPG *.jpeg *.JPEG *.bmp *.BMP);;Todos (*.*)'
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Seleccionar recurso', '', filter_str)
        if not path:
            return
        # Detect if image (omit FPS dialog)
        ext = Path(path).suffix.lower()
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp'}
        if ext in image_exts:
            target_fps = 1
        else:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                QtWidgets.QMessageBox.critical(self, 'Error', f'No se pudo abrir el video:\n{path}')
                return
            fps_original = cap.get(cv2.CAP_PROP_FPS) or 12.0
            cap.release()
            if fps_original <= 0:
                fps_original = 12.0
            target_fps, ok = QtWidgets.QInputDialog.getInt(
                self,
                "Frames por segundo",
                "¿Cuántos FPS querés cargar del video?",
                12,
                1,
                int(max(1, round(fps_original)))
            )
            if not ok:
                return
        # 3. Load resource with target FPS using ProjectManager
        if self.project is None:  # puede haber quedado en None tras cerrar
            self.project = self.project_mgr
        if not self.project.load_video(path, target_fps):
            return  # Loading failed

    def get_active_layer(self) -> Layer | None:
        """Get the currently active layer for drawing."""
        if self.current_frame_idx not in self.frame_layers:
            return None
        layers = self.frame_layers[self.current_frame_idx]
        if 0 <= self.current_layer_idx < len(layers):
            return layers[self.current_layer_idx]
        return None
    
    def ensure_frame_has_layers(self, frame_idx: int, width: int = 640, height: int = 480):
        """Ensure a frame has at least one layer."""
        if frame_idx not in self.frame_layers:
            self.frame_layers[frame_idx] = [Layer("Layer 1", width, height)]
    
    def add_layer(self, name: str = None) -> Layer:
        """Add a new layer to the current frame."""
        if not self.frames:
            return None
        
        if name is None:
            layer_count = len(self.frame_layers.get(self.current_frame_idx, []))
            name = f"Layer {layer_count + 1}"
        
        h, w = self.frames[self.current_frame_idx].shape[:2]
        new_layer = Layer(name, w, h)
        
        if self.current_frame_idx not in self.frame_layers:
            self.frame_layers[self.current_frame_idx] = []
        
        self.frame_layers[self.current_frame_idx].append(new_layer)
        self.current_layer_idx = len(self.frame_layers[self.current_frame_idx]) - 1
        self.compose_layers()
        return new_layer
    
    def compose_layers(self):
        """Compose all visible layers in current frame into the canvas overlay."""
        if not self.frames or self.current_frame_idx not in self.frame_layers:
            return
        
        layers = self.frame_layers[self.current_frame_idx]
        if not layers:
            return
        
        # Create composed pixmap
        h, w = self.frames[self.current_frame_idx].shape[:2]
        composed = QtGui.QPixmap(w, h)
        composed.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(composed)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for layer in layers:
            if layer.visible and not layer.pixmap.isNull():
                painter.setOpacity(layer.opacity)
                painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        
        self.canvas.overlay = composed
        self.canvas.update_display()
    
    def compose_layers_for_frame(self, frame_idx: int) -> QtGui.QPixmap:
        """Compose layers for a specific frame (used for onion skinning)."""
        if frame_idx not in self.frame_layers or not self.frames:
            return QtGui.QPixmap()
        
        layers = self.frame_layers[frame_idx]
        if not layers:
            return QtGui.QPixmap()
        
        h, w = self.frames[frame_idx].shape[:2]
        composed = QtGui.QPixmap(w, h)
        composed.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(composed)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        for layer in layers:
            if layer.visible and not layer.pixmap.isNull():
                painter.setOpacity(layer.opacity)
                painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        
        return composed

    def refresh_view(self):
        if not self.frames:
            return
        idx = self.current_frame_idx; frame = self.frames[idx]
        qimg = cvimg_to_qimage(frame)
        if qimg is None:
            return
        bg_pix = QtGui.QPixmap.fromImage(qimg)
        self.canvas.set_size(bg_pix.width(), bg_pix.height())
        
        # Ensure frame has layers
        self.ensure_frame_has_layers(idx, bg_pix.width(), bg_pix.height())
        
        if idx in self.frame_layers:
            self.compose_layers()
        elif idx in self.overlays and self.overlays[idx] is not None:
            self.canvas.overlay = self.overlays[idx]
        else:
            blank = QtGui.QPixmap(bg_pix.size()); blank.fill(QtCore.Qt.transparent); self.canvas.overlay = blank
        
        opacity = self.opacity_slider.value() / 100.0 if self.show_background else 0.0
        self.canvas.update_display(background_pixmap=bg_pix, opacity=opacity)
        self.frame_label.setText(f'Frame: {idx + 1} / {len(self.frames)}')
        
        self.update_layer_list()

    def store_current_overlay(self):
        if self.canvas.overlay is not None:
            # Store in both systems during transition
            self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)
            # Layers are already stored in frame_layers, no need to duplicate

    def next_frame(self):
        if not self.frames:
            return
        self.maybe_autosave_current(); self.store_current_overlay()
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            h, w = self.frames[self.current_frame_idx].shape[:2]
            self.ensure_frame_has_layers(self.current_frame_idx, w, h)
            
            # Reset layer index if it's out of bounds for new frame
            if self.current_frame_idx in self.frame_layers:
                max_layer_idx = len(self.frame_layers[self.current_frame_idx]) - 1
                if self.current_layer_idx > max_layer_idx:
                    self.current_layer_idx = max_layer_idx
            
            # Fallback to old overlay system if no layers
            if self.current_frame_idx in self.overlays:
                self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.canvas.clear_onion_cache(); self.refresh_view(); self.statusBar().showMessage(f'Frame: {self.current_frame_idx + 1}')

    def prev_frame(self):
        if not self.frames:
            return
        self.maybe_autosave_current(); self.store_current_overlay()
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            h, w = self.frames[self.current_frame_idx].shape[:2]
            self.ensure_frame_has_layers(self.current_frame_idx, w, h)
            
            # Reset layer index if it's out of bounds for new frame
            if self.current_frame_idx in self.frame_layers:
                max_layer_idx = len(self.frame_layers[self.current_frame_idx]) - 1
                if self.current_layer_idx > max_layer_idx:
                    self.current_layer_idx = max_layer_idx
            
            # Fallback to old overlay system if no layers
            if self.current_frame_idx in self.overlays:
                self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.canvas.clear_onion_cache(); self.refresh_view(); self.statusBar().showMessage(f'Frame: {self.current_frame_idx + 1}')

    def activar_auto_calco(self):
        """Activa la herramienta Auto-Calco, muestra el dock y captura el viewport."""
        # Mostrar el panel Marshall
        self.auto_calco_dock.show()
        
        # Activar la herramienta (captura ROI del viewport visible)
        self.auto_calco_tool.activate()
        
        # Dar foco al canvas para que los atajos de teclado funcionen (Enter para plasmar)
        self.canvas.setFocus()
        
        # Actualizar estado visual
        self.statusBar().showMessage('Auto-Calco activado. Ajusta los parámetros y presiona Enter para plasmar.')

    def copy_previous_overlay(self):
        if self.current_frame_idx == 0:
            QtWidgets.QMessageBox.information(self, 'Info', 'No hay frame anterior para copiar.')
            return
        prev_idx = self.current_frame_idx - 1
        
        if prev_idx in self.frame_layers:
            prev_layers = self.frame_layers[prev_idx]
            if prev_layers:
                self.frame_layers[self.current_frame_idx] = [layer.copy() for layer in prev_layers]
                self.current_layer_idx = min(self.current_layer_idx, len(self.frame_layers[self.current_frame_idx]) - 1)
                self.compose_layers()
                self.update_layer_list()
                self.statusBar().showMessage(f'Copiadas {len(prev_layers)} capas del frame anterior')
                return
        
        # Fallback to old overlay system
        if prev_idx in self.overlays and self.overlays[prev_idx] is not None:
            self.canvas.overlay = QtGui.QPixmap(self.overlays[prev_idx]); self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)
            self.canvas.clear_onion_cache(); self.refresh_view()
        else:
            QtWidgets.QMessageBox.information(self, 'Info', 'No hay overlay en el frame anterior.')

    def clear_current_overlay(self):
        active_layer = self.get_active_layer()
        if active_layer:
            self.push_undo_snapshot()
            active_layer.pixmap.fill(QtCore.Qt.transparent)
            self.compose_layers()
            self.mark_dirty_current()
        else:
            # Fallback to old system
            self.push_undo_snapshot(); self.canvas.clear_overlay()
            if self.current_frame_idx in self.overlays:
                del self.overlays[self.current_frame_idx]
            self.mark_dirty_current()

    def save_current_overlay(self):
        """Exporta el frame actual con opciones avanzadas usando ExportFrameDialog."""
        if not self.frames:
            QtWidgets.QMessageBox.information(self, 'Info', 'No hay frames cargados.')
            return
        
        idx = self.current_frame_idx
        default_name = f"frame_{idx:05d}.png"
        
        # Mostrar diálogo de exportación
        dialog = ExportFrameDialog(default_name, self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return
        
        options = dialog.get_export_options()
        filename = options['filename']
        
        if not filename:
            return
        
        # Asegurar extensión .png
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        try:
            # Obtener el pixmap compuesto
            if idx in self.frame_layers:
                layers = self.frame_layers[idx]
            else:
                layers = []
            
            # Exportar capas por separado si está habilitado
            if options['separate_layers'] and layers:
                base_path = Path(filename)
                stem = base_path.stem
                parent = base_path.parent
                
                for i, layer in enumerate(layers):
                    if not layer.visible:
                        continue
                    layer_filename = parent / f"{stem}_layer_{i:02d}_{layer.name}.png"
                    self._export_single_layer(layer.pixmap, str(layer_filename), options, idx)
                
                QtWidgets.QMessageBox.information(
                    self, 'Exportación Completa',
                    f'Se exportaron {len([l for l in layers if l.visible])} capas.'
                )
            else:
                # Exportar composición única
                if idx in self.frame_layers:
                    composed = self.compose_layers_for_frame(idx)
                else:
                    composed = self.overlays.get(idx)
                
                if composed is None or composed.isNull():
                    QtWidgets.QMessageBox.information(self, 'Info', 'Overlay vacío: nada para guardar.')
                    return
                
                self._export_single_layer(composed, filename, options, idx)
                QtWidgets.QMessageBox.information(self, 'Exportación Completa', f'Frame guardado en:\n{filename}')
            
            self.canvas.clear_onion_cache()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Error al exportar frame:\n{str(e)}')
    
    def _export_single_layer(self, pixmap: QtGui.QPixmap, filename: str, options: dict, frame_idx: int):
        """Exporta un solo pixmap con las opciones especificadas."""
        from PIL import Image
        import numpy as np
        
        # Determinar el fondo
        if options['include_background'] and frame_idx < len(self.frames):
            # Componer con el fondo del video
            bg_frame = self.frames[frame_idx]
            h, w = bg_frame.shape[:2]
            
            # Crear imagen de salida
            final_pixmap = QtGui.QPixmap(w, h)
            painter = QtGui.QPainter(final_pixmap)
            
            # Dibujar fondo
            bg_qimg = cvimg_to_qimage(bg_frame)
            painter.drawImage(0, 0, bg_qimg)
            
            # Dibujar overlay
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            # Guardar
            final_pixmap.save(filename, 'PNG')
            
        elif options['use_chroma']:
            # Rellenar con verde croma
            w, h = pixmap.width(), pixmap.height()
            final_pixmap = QtGui.QPixmap(w, h)
            final_pixmap.fill(QtGui.QColor(0, 255, 0))  # Verde croma
            
            painter = QtGui.QPainter(final_pixmap)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            final_pixmap.save(filename, 'PNG')
            
        else:
            # Transparente (por defecto)
            pixmap.save(filename, 'PNG')

    def show_export_animation_dialog(self):
        """Muestra el diálogo de exportación de animación."""
        target_fps = getattr(self, 'fps_target', 12)
        dialog = ExportAnimationDialog(default_fps=target_fps, parent=self)
        
        if dialog.exec():
            if not self.frames:
                QtWidgets.QMessageBox.warning(self, 'Error', 'No hay frames cargados para exportar.')
                return
                
            opts = dialog.get_export_options()
            path = opts['path']
            if not path:
                QtWidgets.QMessageBox.warning(self, 'Error', 'No se seleccionó una ruta de salida.')
                return
            
            # ¡Crear el Worker!
            worker = ExportWorker(
                self.project_mgr,
                self.frames,
                path,
                opts['fps'],
                opts['background_mode']
            )
            
            # Conectar las señales del worker a la UI
            worker.signals.finished.connect(self.on_export_finished)
            worker.signals.error.connect(self.on_export_error)
            # (Podríamos conectar 'progress' a un QProgressBar en el futuro)
            
            # Iniciar el worker en el hilo separado
            self.thread_pool.start(worker)
            
            # Informar al usuario
            self.statusBar().showMessage(f'Exportando animación a {path} en segundo plano...')

    def mark_dirty_current(self):
        self.dirty_frames.add(self.current_frame_idx)
        self.is_dirty = True  # Mark that there are unsaved changes

    def ask_to_save_and_close(self):
        """
        Ask user to save unsaved changes before closing/opening new project.
        Returns True if operation can continue, False if cancelled.
        """
        if not self.is_dirty:
            return True
        
        # Create message box with three options
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle('Cambios sin guardar')
        box.setText('Hay cambios sin guardar. ¿Desea guardarlos?')
        box.setIcon(QtWidgets.QMessageBox.Question)
        
        # Add custom buttons
        save_btn = box.addButton('Guardar', QtWidgets.QMessageBox.AcceptRole)
        discard_btn = box.addButton('No guardar', QtWidgets.QMessageBox.DestructiveRole)
        cancel_btn = box.addButton('Cancelar', QtWidgets.QMessageBox.RejectRole)
        
        # Show dialog and get result
        box.exec()
        clicked_button = box.clickedButton()
        
        if clicked_button == save_btn:
            # Save and continue
            if hasattr(self, 'project_mgr') and self.project_mgr:
                self.project_mgr.save_project_overlay()
                self.is_dirty = False  # Mark as saved
            return True
        elif clicked_button == discard_btn:
            # Don't save, but continue
            self.is_dirty = False  # Reset dirty flag
            return True
        else:  # Cancel button or dialog closed
            return False

    def maybe_autosave_current(self):
        if self.project_path and self.current_frame_idx in self.dirty_frames:
            if self.current_frame_idx in self.frame_layers:
                self.project_mgr.save_frame_layers(self.current_frame_idx)
            else:
                self.project_mgr.save_project_overlay(self.current_frame_idx)
            self.dirty_frames.discard(self.current_frame_idx)
            self.project_mgr.write_meta()
            # Reset global dirty flag if no more dirty frames
            if not self.dirty_frames:
                self.is_dirty = False

    # ---------------- Herramientas / ajustes ----------------
    def set_tool(self, name: str):
        mapping = {
            'brush': BrushTool,
            'eraser': EraserTool,
            'line': LineTool,
            'lasso': LassoTool,
            'hand': HandTool,
            'bucket': BucketTool,
            'rectangle': RectangleTool,
            'ellipse': EllipseTool,
            'pluma': PlumaTool,
            'dynamic_line': DynamicLineTool,
        }
        # Desactivar herramienta anterior si tiene hook
        if self.canvas.tool and hasattr(self.canvas.tool, 'deactivate'):
            self.canvas.tool.deactivate()
        cls = mapping.get(name, BrushTool)
        self.canvas.tool = cls(self.canvas)
        if hasattr(self.canvas.tool, 'activate'):
            self.canvas.tool.activate()
        if hasattr(self, 'action_brush'):
            self.action_brush.setChecked(name == 'brush')
            self.action_eraser.setChecked(name == 'eraser')
            self.action_line.setChecked(name == 'line')
            if hasattr(self, 'action_lasso'):
                self.action_lasso.setChecked(name == 'lasso')
            if hasattr(self, 'action_hand'):
                self.action_hand.setChecked(name == 'hand')
            if hasattr(self, 'action_bucket'):
                self.action_bucket.setChecked(name == 'bucket')
            if hasattr(self, 'action_rectangle'):
                self.action_rectangle.setChecked(name == 'rectangle')
            if hasattr(self, 'action_ellipse'):
                self.action_ellipse.setChecked(name == 'ellipse')
            if hasattr(self, 'action_pluma'):
                self.action_pluma.setChecked(name == 'pluma')
            if hasattr(self, 'action_dynamic_line'):
                self.action_dynamic_line.setChecked(name == 'dynamic_line')
        self.statusBar().showMessage(f'Herramienta: {name}')

    def _set_brush_mode(self, mode: int):
        if isinstance(self.canvas.tool, BrushTool):
            self.canvas.tool.set_mode(mode)
            self.statusBar().showMessage(f'Pincel modo: {mode+1}')

    def _set_eraser_mode(self, mode: int):
        if isinstance(self.canvas.tool, EraserTool):
            self.canvas.tool.set_mode(mode)
            self.statusBar().showMessage(f'Borrador modo: {mode+1}')

    def set_bg_visible(self, visible: bool):
        self.show_background = visible; self.refresh_view()

    def apply_brush_changes(self):
        self.canvas.pen_width = self.brush_slider.value()

    def set_brush_color(self, hex_color: str):
        col = QtGui.QColor(hex_color); col.setAlpha(255); self.canvas.pen_color = col

    def pick_custom_color(self):
        col = QtWidgets.QColorDialog.getColor(self.canvas.pen_color, self, 'Seleccionar color')
        if col.isValid():
            self.canvas.pen_color = col

    # ---------------- Undo / Redo ----------------
    def push_undo_snapshot(self, force: bool = False):
        active_layer = self.get_active_layer()
        if active_layer is None or active_layer.pixmap.isNull():
            return
        # Respect the force flag: only skip snapshot if not forced and the current tool opts out
        if not force and self.canvas.tool and hasattr(self.canvas.tool, 'requires_snapshot') and not self.canvas.tool.requires_snapshot:
            return
        stack = self.undo_stacks.setdefault(self.current_frame_idx, [])
        if len(stack) >= self.max_history:
            stack.pop(0)
        stack.append(QtGui.QPixmap(active_layer.pixmap))
        self.redo_stacks.setdefault(self.current_frame_idx, []).clear()

    def undo(self):
        stack = self.undo_stacks.get(self.current_frame_idx, [])
        if not stack:
            return
        active_layer = self.get_active_layer()
        if not active_layer:
            return
        current = QtGui.QPixmap(active_layer.pixmap) if not active_layer.pixmap.isNull() else None
        prev = stack.pop(); rstack = self.redo_stacks.setdefault(self.current_frame_idx, [])
        if current is not None:
            rstack.append(current)
        active_layer.pixmap = QtGui.QPixmap(prev)
        self.compose_layers()

    def redo(self):
        rstack = self.redo_stacks.get(self.current_frame_idx, [])
        if not rstack:
            return
        active_layer = self.get_active_layer()
        if not active_layer:
            return
        current = QtGui.QPixmap(active_layer.pixmap) if not active_layer.pixmap.isNull() else None
        nxt = rstack.pop(); stack = self.undo_stacks.setdefault(self.current_frame_idx, [])
        if current is not None:
            stack.append(current)
        active_layer.pixmap = QtGui.QPixmap(nxt)
        self.compose_layers()

    # ---------------- Zoom ----------------
    def change_zoom(self, factor: float):
        # Find the scroll area to get viewport center
        scroll = self.canvas.parent()
        while scroll and not isinstance(scroll, QtWidgets.QScrollArea):
            scroll = scroll.parent()
        
        if isinstance(scroll, QtWidgets.QScrollArea):
            # Get viewport center as anchor point
            viewport = scroll.viewport()
            center_x = viewport.width() // 2
            center_y = viewport.height() // 2
            center_pos = QtCore.QPoint(center_x, center_y)
            
            # Use zoom_with_anchor to maintain center
            self.zoom_with_anchor(factor, center_pos)
        else:
            # Fallback to simple zoom if no scroll area found
            new_scale = self.canvas.scale_factor * factor
            new_scale = max(self.zoom_min, min(self.zoom_max, new_scale))
            if abs(new_scale - self.canvas.scale_factor) < 1e-3:
                return
            self.canvas.scale_factor = new_scale
            self.refresh_view()

    def zoom_with_anchor(self, factor: float, cursor_pos: QtCore.QPoint):
        old_scale = self.canvas.scale_factor
        new_scale = old_scale * factor
        new_scale = max(self.zoom_min, min(self.zoom_max, new_scale))
        if abs(new_scale - old_scale) < 1e-3:
            return

        # Convertir posición del cursor a coords de overlay (para futura extensión)
        overlay_pos = self.canvas.mapToOverlay(cursor_pos)
        _ = overlay_pos  # evitar warning si no se usa todavía

        # Localizar scroll area
        scroll = self.canvas.parent()
        while scroll and not isinstance(scroll, QtWidgets.QScrollArea):
            scroll = scroll.parent()
        if not isinstance(scroll, QtWidgets.QScrollArea):
            self.canvas.scale_factor = new_scale
            self.refresh_view()
            return

        hbar = scroll.horizontalScrollBar()
        vbar = scroll.verticalScrollBar()

        old_h = hbar.value()
        old_v = vbar.value()

        # Aplicar escala y refrescar (redimensiona canvas)
        self.canvas.scale_factor = new_scale
        self.refresh_view()

        scale_ratio = new_scale / old_scale
        new_h = int((old_h + cursor_pos.x()) * scale_ratio - cursor_pos.x())
        new_v = int((old_v + cursor_pos.y()) * scale_ratio - cursor_pos.y())

        hbar.setValue(max(hbar.minimum(), min(hbar.maximum(), new_h)))
        vbar.setValue(max(vbar.minimum(), min(vbar.maximum(), new_v)))

    def eventFilter(self, obj, event):
        if obj is self.canvas and event.type() == QtCore.QEvent.Wheel:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            # Posición del cursor relativa al canvas (contenido actual escalado)
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            self.zoom_with_anchor(factor, pos)
            return True
        return super().eventFilter(obj, event)

    # ---------------- Proyecto ----------------
    def save_project_dialog(self):
        self.project_mgr.save_project_dialog()
        if self.project_path:
            self.is_dirty = False  # Reset dirty flag after successful save
            self.statusBar().showMessage(f'Proyecto guardado: {self.project_path.name}', 4000)

    def load_project_dialog(self):
        # Check for unsaved changes before loading project
        if not self.ask_to_save_and_close():
            return  # User cancelled, don't proceed
            
        self.project_mgr.load_project_dialog()
        if self.project_name:
            self.is_dirty = False  # Reset dirty flag after loading project
            self.statusBar().showMessage(f'Proyecto cargado: {self.project_name}', 4000)

    def close_project(self):
        """Close current project, asking to save if there are unsaved changes."""
        # Ask for confirmation if there are unsaved changes
        if not self.ask_to_save_and_close():
            return  # User cancelled, don't proceed
            
        # Reset all project state
        self.frames.clear()
        self.overlays.clear()
        self.frame_layers.clear()
        self.undo_stacks.clear()
        self.redo_stacks.clear()
        self.dirty_frames.clear()
        self.is_dirty = False
        self.current_frame_idx = 0
        self.current_layer_idx = 0
        self.project_path = None
        self.project_name = None
        self.fps_original = None
        self.fps_target = None
        
        # Clear canvas and UI
        self.canvas.overlay = None
        self.canvas.current_background = None
        try:
            self.canvas.clear_onion_cache()
            self.layer_list.clear()
        except Exception:
            pass
            
        # Reset UI elements
        self.frame_label.setText('Frame: 0 / 0')
        self.setWindowTitle('Rotoscopia MVP - Modular')
        # Sliders / toggles / zoom
        try:
            self.brush_slider.setValue(DEFAULT_BRUSH_SIZE)
            self.opacity_slider.setValue(int(DEFAULT_BG_OPACITY * 100))
            self.onion_opacity_slider.setValue(int(DEFAULT_ONION_OPACITY * 100))
            if hasattr(self, 'action_onion'):
                self.action_onion.setChecked(False)
            if hasattr(self, 'action_bg_toggle'):
                self.action_bg_toggle.setChecked(True)
            self.canvas.scale_factor = 1.0
        except Exception:
            pass
        # Pintar canvas vacío
        blank = QtGui.QPixmap(640, 480)
        blank.fill(QtCore.Qt.lightGray)
        self.canvas.setPixmap(blank)
        
        # Set project to None (ready for new video)
        self.project = None
        
        self.statusBar().showMessage('Proyecto cerrado', 3000)
    
    def on_export_finished(self, message):
        """Se llama cuando el worker de exportación termina con éxito."""
        self.statusBar().showMessage('¡Exportación completada!', 5000)
        QtWidgets.QMessageBox.information(self, 'Exportación Completa', message)
    
    def on_export_error(self, error_message):
        """Se llama cuando el worker de exportación falla."""
        self.statusBar().showMessage('Error durante la exportación.', 5000)
        QtWidgets.QMessageBox.critical(self, 'Error de Exportación', error_message)

    def show_help_manual(self):
        """Muestra el manual de usuario en una ventana de diálogo."""
        try:
            # Intentar abrir el manual de usuario
            manual_path = Path(__file__).parent.parent / "MANUAL_USUARIO.md"
            
            if manual_path.exists():
                with open(manual_path, 'r', encoding='utf-8') as f:
                    manual_content = f.read()
                
                # Crear ventana de diálogo para mostrar el manual
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle('Manual de Usuario - Rotoscopia')
                dialog.setModal(True)
                dialog.resize(800, 600)
                
                layout = QtWidgets.QVBoxLayout(dialog)
                
                # Área de texto para el contenido del manual
                text_area = QtWidgets.QTextEdit()
                text_area.setReadOnly(True)
                text_area.setPlainText(manual_content)
                text_area.setFont(QtGui.QFont("Consolas", 9))
                
                layout.addWidget(text_area)
                
                # Botones
                button_layout = QtWidgets.QHBoxLayout()
                
                # Botón para abrir archivo externo
                open_file_btn = QtWidgets.QPushButton('Abrir en Editor')
                open_file_btn.clicked.connect(lambda: self.open_external_file(manual_path))
                button_layout.addWidget(open_file_btn)
                
                button_layout.addStretch()
                
                close_btn = QtWidgets.QPushButton('Cerrar')
                close_btn.clicked.connect(dialog.accept)
                button_layout.addWidget(close_btn)
                
                layout.addLayout(button_layout)
                
                dialog.exec()
            else:
                # Manual no encontrado, mostrar información básica
                QtWidgets.QMessageBox.information(
                    self, 
                    'Manual de Usuario', 
                    '📖 Manual de Usuario - Rotoscopia\n\n'
                    '⌨️ Atajos Principales:\n'
                    '• B - Pincel\n'
                    '• E - Borrador\n'
                    '• L - Lazo\n'
                    '• H - Mano\n'
                    '• ←/→ - Navegar frames\n'
                    '• Ctrl+D - Copiar frame anterior\n'
                    '• Ctrl+S - Guardar frame\n'
                    '• Ctrl+Shift+S - Guardar proyecto\n'
                    '• O - Toggle Onion Skin\n'
                    '• Ctrl+B - Toggle fondo\n\n'
                    '📄 Para el manual completo, consulta MANUAL_USUARIO.md'
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                'Error',
                f'No se pudo abrir el manual: {str(e)}\n\n'
                'Consulta MANUAL_USUARIO.md en la carpeta del proyecto.'
            )

    def open_external_file(self, file_path):
        """Abre un archivo en el editor predeterminado del sistema."""
        try:
            import subprocess
            import sys
            
            if sys.platform.startswith('win'):
                subprocess.run(['notepad.exe', str(file_path)], check=False)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', str(file_path)], check=False)
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path)], check=False)
        except Exception:
            QtWidgets.QMessageBox.information(
                self,
                'Información',
                f'Manual ubicado en:\n{file_path}\n\nÁbrelo manualmente con tu editor preferido.'
            )


class ExportFrameDialog(QtWidgets.QDialog):
    """Diálogo para exportar el frame actual con opciones avanzadas."""
    
    def __init__(self, default_filename: str, parent=None):
        super().__init__(parent)
        self.default_filename = default_filename
        self.setWindowTitle('Exportar Frame Actual')
        layout = QtWidgets.QVBoxLayout(self)
        
        # Grupo para el nombre de archivo
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(QtWidgets.QLabel('Guardar como:'))
        self.filename_edit = QtWidgets.QLineEdit(self.default_filename)
        name_layout.addWidget(self.filename_edit)
        self.browse_btn = QtWidgets.QPushButton('...')
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self.browse_file)
        name_layout.addWidget(self.browse_btn)
        layout.addLayout(name_layout)
        
        # Grupo de opciones de fondo
        bg_group = QtWidgets.QGroupBox('Opciones de Fondo')
        bg_layout = QtWidgets.QVBoxLayout(bg_group)
        self.radio_transparent = QtWidgets.QRadioButton('Transparente')
        self.radio_include_bg = QtWidgets.QRadioButton('Incluir fondo del video')
        self.radio_croma = QtWidgets.QRadioButton('Rellenar con Croma (verde)')
        self.radio_transparent.setChecked(True)
        bg_layout.addWidget(self.radio_transparent)
        bg_layout.addWidget(self.radio_include_bg)
        bg_layout.addWidget(self.radio_croma)
        layout.addWidget(bg_group)
        
        # Checkbox de capas
        self.check_separate_layers = QtWidgets.QCheckBox('Exportar capas por separado')
        layout.addWidget(self.check_separate_layers)
        
        # Botones OK/Cancelar
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    
    def browse_file(self):
        """Abre un diálogo para seleccionar la ubicación del archivo."""
        from .settings import EXPORTS_DIR
        
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            'Guardar Frame Como',
            str(EXPORTS_DIR / self.default_filename),
            'Imágenes PNG (*.png);;Todos los archivos (*.*)'
        )
        
        if file_path:
            self.filename_edit.setText(file_path)
    
    def get_export_options(self):
        """Retorna un diccionario con las opciones seleccionadas."""
        return {
            'filename': self.filename_edit.text(),
            'transparent': self.radio_transparent.isChecked(),
            'include_background': self.radio_include_bg.isChecked(),
            'use_chroma': self.radio_croma.isChecked(),
            'separate_layers': self.check_separate_layers.isChecked()
        }


class ExportAnimationDialog(QtWidgets.QDialog):
    """Diálogo para exportar la animación completa como secuencia de imágenes."""
    
    def __init__(self, default_fps: int = 12, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Exportar Animación')
        layout = QtWidgets.QVBoxLayout(self)

        # 1. Grupo de Formato
        format_group = QtWidgets.QGroupBox('Formato de Salida')
        format_layout = QtWidgets.QVBoxLayout(format_group)
        self.radio_png = QtWidgets.QRadioButton('Secuencia PNG (para videojuegos / post-producción)')
        self.radio_mp4 = QtWidgets.QRadioButton('Video MP4 (para redes / vista rápida)')
        self.radio_png.setChecked(True)
        format_layout.addWidget(self.radio_png)
        format_layout.addWidget(self.radio_mp4)
        layout.addWidget(format_group)
        
        # 2. Grupo de Fondo
        bg_group = QtWidgets.QGroupBox('Opciones de Fondo')
        bg_layout = QtWidgets.QVBoxLayout(bg_group)
        self.radio_transparent = QtWidgets.QRadioButton('Transparente (Recomendado)')
        self.radio_include_bg = QtWidgets.QRadioButton('Incluir fondo del video')
        self.radio_croma = QtWidgets.QRadioButton('Rellenar con Croma (verde)')
        self.radio_transparent.setChecked(True)
        bg_layout.addWidget(self.radio_transparent)
        bg_layout.addWidget(self.radio_include_bg)
        bg_layout.addWidget(self.radio_croma)
        layout.addWidget(bg_group)
        
        # 3. Grupo de Ubicación
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(QtWidgets.QLabel('Guardar en:'))
        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setPlaceholderText('Selecciona una carpeta o archivo...')
        path_layout.addWidget(self.path_edit)
        self.browse_btn = QtWidgets.QPushButton('Elegir Carpeta...')
        self.browse_btn.clicked.connect(self.browse_output)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)
        
        # 4. Grupo de FPS (para MP4)
        self.fps_widget = QtWidgets.QWidget()  # Usamos un widget para ocultar/mostrar todo junto
        fps_layout = QtWidgets.QHBoxLayout(self.fps_widget)
        fps_layout.setContentsMargins(0, 0, 0, 0)
        self.fps_label = QtWidgets.QLabel('FPS (Velocidad):')
        fps_layout.addWidget(self.fps_label)
        self.fps_spin = QtWidgets.QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(default_fps)
        fps_layout.addWidget(self.fps_spin)
        fps_layout.addStretch()
        layout.addWidget(self.fps_widget)
        
        # Conectar radios para UI dinámica
        self.radio_png.toggled.connect(self.update_ui_mode)
        self.radio_transparent.toggled.connect(self.update_ui_mode)
        self.update_ui_mode()  # Llamar una vez para el estado inicial

        # Botones OK/Cancelar
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
    
    def update_ui_mode(self):
        """Lógica para mostrar/ocultar opciones según el formato seleccionado."""
        is_png = self.radio_png.isChecked()
        is_transparent = self.radio_transparent.isChecked()

        # Ocultar FPS si es PNG
        self.fps_widget.setVisible(not is_png)

        # Cambiar texto del botón
        self.browse_btn.setText('Elegir Carpeta...' if is_png else 'Guardar Como...')

        # Deshabilitar "Transparente" si es MP4 (MP4 no soporta transparencia)
        self.radio_transparent.setEnabled(is_png)
        if not is_png and is_transparent:
            # Si estaba en transparente y cambian a MP4, forzar "Incluir fondo"
            self.radio_include_bg.setChecked(True)
    
    def browse_output(self):
        """Abre diálogo para seleccionar carpeta (PNG) o archivo (MP4)."""
        is_png = self.radio_png.isChecked()
        if is_png:
            # Pedir una CARPETA
            path = QtWidgets.QFileDialog.getExistingDirectory(
                self, 'Seleccionar Carpeta de Exportación', self.path_edit.text()
            )
        else:
            # Pedir un ARCHIVO .mp4
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Guardar Video MP4', self.path_edit.text(), 'Video MP4 (*.mp4)'
            )
        
        if path:
            self.path_edit.setText(path)
    
    def get_export_options(self):
        """Retorna las opciones de exportación seleccionadas por el usuario."""
        options = {}
        options['is_png'] = self.radio_png.isChecked()
        options['path'] = self.path_edit.text()
        options['fps'] = self.fps_spin.value()
        
        if self.radio_transparent.isChecked():
            options['background_mode'] = EXPORT_BG_TRANSPARENT
        elif self.radio_croma.isChecked():
            options['background_mode'] = EXPORT_BG_CROMA
        else:  # self.radio_include_bg.isChecked()
            options['background_mode'] = EXPORT_BG_VIDEO
            
        return options


# 1. Objeto de Señales
# (QRunnable no es un QObject, así que necesita un objeto separado para emitir señales)
class ExportSignals(QtCore.QObject):
    progress = QtCore.Signal(int)      # Señal para el progreso (ej: porcentaje)
    finished = QtCore.Signal(str)      # Señal de éxito (con un mensaje)
    error = QtCore.Signal(str)         # Señal de error (con un mensaje)


# 2. El Hilo Trabajador (Worker)
class ExportWorker(QtCore.QRunnable):
    def __init__(self, project_mgr, frames, path, fps, background_mode):
        super().__init__()
        # Guardar todos los parámetros necesarios
        self.project_mgr = project_mgr
        self.frames = frames
        self.path = path
        self.fps = fps
        self.background_mode = background_mode
        self.signals = ExportSignals()  # Crear la instancia de señales

    @QtCore.Slot()  # Indica que esto es un "slot" para ser ejecutado por el hilo
    def run(self):
        try:
            # Importamos las constantes que 'export_animation' necesita
            from .project import EXPORT_BG_TRANSPARENT, EXPORT_BG_VIDEO, EXPORT_BG_CROMA
            
            # ¡Aquí llamamos a la función pesada que arreglamos!
            self.project_mgr.export_animation(
                self.frames,
                self.path,
                self.fps,
                self.background_mode
            )
            
            # Si todo sale bien, emitimos la señal de "finished"
            self.signals.finished.emit(f"¡Animación exportada con éxito en:\n{self.path}")
        except Exception as e:
            # Si algo falla, capturamos el error y emitimos la señal de "error"
            import traceback
            error_msg = f"Error al exportar: {e}\n\n{traceback.format_exc()}"
            self.signals.error.emit(error_msg)