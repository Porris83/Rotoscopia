"""UI principal (canvas y ventana) con soporte de Onion Skin.

Punto de entrada de ejecución en ``rotoscopia.main`` (no usar if __name__ == '__main__').
"""

from __future__ import annotations

import cv2
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
from .project import ProjectManager
from .tools import BrushTool, EraserTool, LineTool, HandTool, LassoTool, BucketTool, RectangleTool, EllipseTool


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
        if self.overlay is None:
            return point
        bw = self.overlay.width(); bh = self.overlay.height()
        disp_w = int(bw * self.scale_factor); disp_h = int(bh * self.scale_factor)
        offset_x = (self.width() - disp_w) / 2.0; offset_y = (self.height() - disp_h) / 2.0
        x = (point.x() - offset_x) / self.scale_factor
        y = (point.y() - offset_y) / self.scale_factor
        x = max(0, min(bw - 1, int(round(x)))); y = max(0, min(bh - 1, int(round(y))))
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
        # Cancelar selección Lasso con Esc
        if event.key() == QtCore.Qt.Key_Escape:
            from .tools import LassoTool
            if isinstance(self.tool, LassoTool):
                self.tool.cancel_selection(); return
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
        painter.end()


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
        self.project_path = None
        self.project_name = None
        self.zoom_min = DEFAULT_ZOOM_MIN
        self.zoom_max = DEFAULT_ZOOM_MAX
        self.show_background = True
        self.project_mgr = ProjectManager(self)
        
        self.frame_layers: dict[int, list[Layer]] = {}  # frame_idx -> list of layers
        self.current_layer_idx = 0  # index of active layer in current frame
        
        # Keep old overlay system for backward compatibility during transition
        self.overlays = {}
        
        self._init_ui()
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

        self._create_layer_dock()

        # Toolbar Archivo
        tb_file = QtWidgets.QToolBar('Archivo')
        act_open = QtGui.QAction('Abrir', self); act_open.triggered.connect(self.open_video)
        act_save_png = QtGui.QAction('Guardar PNG', self); act_save_png.triggered.connect(self.save_current_overlay)
        act_save_proj = QtGui.QAction('Guardar Proy', self); act_save_proj.triggered.connect(self.save_project_dialog)
        act_load_proj = QtGui.QAction('Cargar Proy', self); act_load_proj.triggered.connect(self.load_project_dialog)
        tb_file.addActions([act_open, act_save_png, act_save_proj, act_load_proj])
        self.addToolBar(tb_file)

        # Toolbar Frames
        tb_frames = QtWidgets.QToolBar('Frames')
        act_prev = QtGui.QAction('<<', self); act_prev.triggered.connect(self.prev_frame)
        act_next = QtGui.QAction('>>', self); act_next.triggered.connect(self.next_frame)
        act_copy = QtGui.QAction('Copiar', self); act_copy.triggered.connect(self.copy_previous_overlay)
        tb_frames.addActions([act_prev, act_next, act_copy])
        self.frame_label = QtWidgets.QLabel('Frame: 0 / 0')
        frame_label_act = QtWidgets.QWidgetAction(self); frame_label_act.setDefaultWidget(self.frame_label)
        tb_frames.addAction(frame_label_act)
        self.addToolBar(tb_frames)

        # Toolbar Herramientas (con Mano)
        tb_tools = QtWidgets.QToolBar('Herramientas')
        self.tool_group = QtGui.QActionGroup(self); self.tool_group.setExclusive(True)
        self.action_brush = QtGui.QAction('Pincel', self, checkable=True)
        self.action_eraser = QtGui.QAction('Borrar', self, checkable=True)
        self.action_line = QtGui.QAction('Línea', self, checkable=True)
        self.action_lasso = QtGui.QAction('Lazo', self, checkable=True)
        self.action_hand = QtGui.QAction('Mano', self, checkable=True)
        self.action_bucket = QtGui.QAction('Balde', self, checkable=True)
        self.action_rectangle = QtGui.QAction('Rect', self, checkable=True)
        self.action_ellipse = QtGui.QAction('Elipse', self, checkable=True)
        for act, name in [
            (self.action_brush, 'brush'),
            (self.action_eraser, 'eraser'),
            (self.action_line, 'line'),
            (self.action_lasso, 'lasso'),
            (self.action_hand, 'hand'),
            (self.action_bucket, 'bucket'),
            (self.action_rectangle, 'rectangle'),
            (self.action_ellipse, 'ellipse'),
        ]:
            self.tool_group.addAction(act)
            act.triggered.connect(lambda checked, n=name: checked and self.set_tool(n))
            tb_tools.addAction(act)
        self.addToolBar(tb_tools)

        tb_layers = QtWidgets.QToolBar('Capas')
        act_add_layer = QtGui.QAction('+ Capa', self); act_add_layer.triggered.connect(self.add_layer_ui)
        act_delete_layer = QtGui.QAction('- Capa', self); act_delete_layer.triggered.connect(self.delete_current_layer)
        act_duplicate_layer = QtGui.QAction('Duplicar', self); act_duplicate_layer.triggered.connect(self.duplicate_current_layer)
        tb_layers.addActions([act_add_layer, act_delete_layer, act_duplicate_layer])
        self.addToolBar(tb_layers)

        # Toolbar Vista
        tb_view = QtWidgets.QToolBar('Vista')
        self.action_bg_toggle = QtGui.QAction('Fondo', self, checkable=True)
        self.action_bg_toggle.setChecked(True)
        self.action_bg_toggle.toggled.connect(self.set_bg_visible)
        act_bg_reset = QtGui.QAction('Reset BG', self)
        act_bg_reset.triggered.connect(lambda: (self.opacity_slider.setValue(int(DEFAULT_BG_OPACITY * 100)), self.set_bg_visible(True)))
        self.action_onion = QtGui.QAction('Onion', self, checkable=True)
        tb_view.addAction(self.action_bg_toggle)
        tb_view.addAction(act_bg_reset)
        tb_view.addAction(self.action_onion)
        # Sliders vista
        bg_label = QtWidgets.QLabel('BG Opacity')
        bg_label_act = QtWidgets.QWidgetAction(self); bg_label_act.setDefaultWidget(bg_label); tb_view.addAction(bg_label_act)
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(DEFAULT_BG_OPACITY * 100))
        self.opacity_slider.setFixedWidth(90)
        self.opacity_slider.valueChanged.connect(self.refresh_view)
        opacity_act = QtWidgets.QWidgetAction(self); opacity_act.setDefaultWidget(self.opacity_slider); tb_view.addAction(opacity_act)
        onion_label = QtWidgets.QLabel('Onion Opacity')
        onion_label_act = QtWidgets.QWidgetAction(self); onion_label_act.setDefaultWidget(onion_label); tb_view.addAction(onion_label_act)
        self.onion_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.onion_opacity_slider.setRange(0, 100)
        self.onion_opacity_slider.setValue(int(DEFAULT_ONION_OPACITY * 100))
        self.onion_opacity_slider.setFixedWidth(90)
        onion_act = QtWidgets.QWidgetAction(self); onion_act.setDefaultWidget(self.onion_opacity_slider); tb_view.addAction(onion_act)
        self.action_onion.toggled.connect(self.canvas.set_onion_enabled)
        self.onion_opacity_slider.valueChanged.connect(lambda v: self.canvas.set_onion_opacity(v / 100.0))
        self.action_onion.toggled.connect(self.onion_opacity_slider.setEnabled)
        self.onion_opacity_slider.setEnabled(self.action_onion.isChecked())
        self.addToolBar(tb_view)

        # Toolbar Dibujo (pincel + colores)
        tb_draw = QtWidgets.QToolBar('Dibujo')
        self.brush_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.brush_slider.setRange(1, MAX_BRUSH_SIZE)
        self.brush_slider.setValue(DEFAULT_BRUSH_SIZE)
        self.brush_slider.setFixedWidth(110)
        self.brush_slider.valueChanged.connect(self.apply_brush_changes)
        brush_act = QtWidgets.QWidgetAction(self); brush_act.setDefaultWidget(self.brush_slider); tb_draw.addAction(brush_act)
        for col in PALETTE_COLORS:
            btn = QtWidgets.QToolButton(); btn.setFixedSize(20, 20)
            btn.setStyleSheet(f'background:{col}; border:1px solid #444;')
            btn.clicked.connect(lambda _c=False, c=col: self.set_brush_color(c))
            color_act = QtWidgets.QWidgetAction(self); color_act.setDefaultWidget(btn); tb_draw.addAction(color_act)
        custom_btn = QtWidgets.QToolButton(); custom_btn.setText('+'); custom_btn.setFixedSize(24, 24)
        custom_btn.clicked.connect(self.pick_custom_color)
        custom_act = QtWidgets.QWidgetAction(self); custom_act.setDefaultWidget(custom_btn); tb_draw.addAction(custom_act)
        self.addToolBar(tb_draw)

        # Shortcuts y overlays
        self.overlays = {}
        # Navegación frames
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['next_frame']), self, activated=self.next_frame)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['prev_frame']), self, activated=self.prev_frame)
        if 'copy_prev_frame' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['copy_prev_frame']), self, activated=self.copy_previous_overlay)
        # Guardado / exportación
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['save_overlay']), self, activated=self.save_current_overlay)
        if 'save_project' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['save_project']), self, activated=self.save_project_dialog)
        if 'export_animation' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['export_animation']), self, activated=lambda: self.project_mgr.export_animation(self.frames))
        # Undo / Redo
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['undo']), self, activated=self.undo)
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['redo']), self, activated=self.redo)
        # Herramientas (selección directa)
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
        # Operaciones de selección (solo si Lasso activo)
        if 'copy_selection' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['copy_selection']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.copy_selection())
        if 'paste_selection' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['paste_selection']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.paste_selection())
        if 'invert_selection' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['invert_selection']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.invert_selection())
        if 'select_all' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['select_all']), self, activated=lambda: isinstance(self.canvas.tool, LassoTool) and self.canvas.tool.select_all())
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['hand_tool']), self, activated=lambda: self.action_hand.trigger())
        # Onion
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['toggle_onion']), self, activated=lambda: self.action_onion.setChecked(not self.action_onion.isChecked()))
        # Fondo
        if 'toggle_background' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['toggle_background']), self, activated=lambda: self.action_bg_toggle.setChecked(not self.action_bg_toggle.isChecked()))
        # Zoom
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['zoom_in']), self, activated=lambda: self.change_zoom(1.15))
        QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['zoom_out']), self, activated=lambda: self.change_zoom(1 / 1.15))
        if 'reset_zoom' in SHORTCUTS:
            QtGui.QShortcut(QtGui.QKeySequence(SHORTCUTS['reset_zoom']), self, activated=lambda: (setattr(self.canvas, 'scale_factor', 1.0), self.refresh_view()))

        # Modos de pincel (1/2/3) y borrador (Ctrl+1/2/3) sin interferir con otros
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
        # Filtro corregido (tenía corchete) y ampliado a mayúsculas
        filter_str = 'Videos (*.mp4 *.MP4 *.mov *.MOV *.avi *.AVI *.mkv *.MKV);;Todos (*.*)'
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Seleccionar video', '', filter_str)
        if not path:
            return
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self, 'Error', f'No se pudo abrir el video:\n{path}')
            return
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self, 'Video', f'El video no contiene frames o no se pudieron leer.\nRuta: {path}')
            return
        self.frames = frames; self.video_path = path; self.current_frame_idx = 0
        self.overlays.clear(); self.frame_layers.clear(); self.current_layer_idx = 0
        self.undo_stacks.clear(); self.redo_stacks.clear(); self.dirty_frames.clear(); self.canvas.clear_onion_cache()
        h, w = self.frames[0].shape[:2]; self.canvas.set_size(w, h)
        self.ensure_frame_has_layers(0, w, h)
        self.refresh_view()
        from pathlib import Path as _P
        self.statusBar().showMessage(f'Video cargado: {_P(path).name}', 4000)

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
        if not self.frames:
            return
        self.store_current_overlay(); idx = self.current_frame_idx
        
        if idx in self.frame_layers:
            composed = self.compose_layers_for_frame(idx)
            if not composed.isNull():
                self.project_mgr.save_frame(idx, composed)
                self.canvas.clear_onion_cache()
                return
        
        # Fallback to old overlay system
        overlay_pix = self.overlays.get(idx)
        if overlay_pix is None:
            QtWidgets.QMessageBox.information(self, 'Info', 'Overlay vacío: nada para guardar.')
            return
        self.project_mgr.save_frame(idx, overlay_pix)
        self.canvas.clear_onion_cache()

    def mark_dirty_current(self):
        self.dirty_frames.add(self.current_frame_idx)

    def maybe_autosave_current(self):
        if self.project_path and self.current_frame_idx in self.dirty_frames:
            if self.current_frame_idx in self.frame_layers:
                self.project_mgr.save_frame_layers(self.current_frame_idx)
            else:
                self.project_mgr.save_project_overlay(self.current_frame_idx)
            self.dirty_frames.discard(self.current_frame_idx)
            self.project_mgr.write_meta()

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
    def push_undo_snapshot(self):
        active_layer = self.get_active_layer()
        if active_layer is None or active_layer.pixmap.isNull():
            return
        if self.canvas.tool and hasattr(self.canvas.tool, 'requires_snapshot') and not self.canvas.tool.requires_snapshot:
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
            self.statusBar().showMessage(f'Proyecto guardado: {self.project_path.name}', 4000)

    def load_project_dialog(self):
        self.project_mgr.load_project_dialog()
        if self.project_name:
            self.statusBar().showMessage(f'Proyecto cargado: {self.project_name}', 4000)
