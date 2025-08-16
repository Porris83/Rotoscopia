import os, cv2
from PySide6 import QtCore, QtGui, QtWidgets
from pathlib import Path
try:
    from .settings import DEFAULT_ONION_OPACITY, DEFAULT_ZOOM_MIN, DEFAULT_ZOOM_MAX, MAX_HISTORY, EXPORT_DIR, PROJECTS_DIR
    from .utils import cvimg_to_qimage
    from .project import ProjectManager
except ImportError:
    from settings import DEFAULT_ONION_OPACITY, DEFAULT_ZOOM_MIN, DEFAULT_ZOOM_MAX, MAX_HISTORY, EXPORT_DIR, PROJECTS_DIR
    from utils import cvimg_to_qimage
    from project import ProjectManager

class DrawingCanvas(QtWidgets.QLabel):
    strokeStarted = QtCore.Signal()
    strokeEnded = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pen_width = 3
        self.pen_color = QtGui.QColor(0,0,0,255)
        self._drawing = False
        self.last_point = None
        self.overlay = None
        # herramienta actual (instancia de BaseTool)
        self.tool = None
        self.current_background = None
        self.current_opacity = 0.5
        self.scale_factor = 1.0
        self._panning = False
        self._pan_last = None
        self._base_size = None
        # compat restos anteriores (ya manejado por LineTool ahora, pero se conservan si alguna parte externa los usa)
        self.line_start = None
        self._line_base = None

    def set_size(self, w, h):
        if self.overlay is None or self.overlay.size() != QtCore.QSize(w,h):
            pix = QtGui.QPixmap(w,h)
            pix.fill(QtCore.Qt.transparent)
            self.overlay = pix
            self.setPixmap(QtGui.QPixmap(w,h))

    def mapToOverlay(self, point: QtCore.QPoint) -> QtCore.QPoint:
        if self.overlay is None:
            return point
        bw = self.overlay.width(); bh = self.overlay.height()
        disp_w = int(bw * self.scale_factor)
        disp_h = int(bh * self.scale_factor)
        offset_x = (self.width() - disp_w)/2.0
        offset_y = (self.height() - disp_h)/2.0
        x = (point.x() - offset_x) / self.scale_factor
        y = (point.y() - offset_y) / self.scale_factor
        x = max(0, min(bw-1, int(round(x))))
        y = max(0, min(bh-1, int(round(y))))
        return QtCore.QPoint(x,y)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.overlay is not None:
            self._drawing = True
            # emitir strokeStarted y permitir a MainWindow enganchar undo
            self.strokeStarted.emit()
            if self.tool:
                # si la herramienta requiere snapshot ya se habrá tomado en slot conectado
                self.tool.on_mouse_press(event)
        elif event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._panning = True
            self._pan_last = event.globalPosition().toPoint() if hasattr(event,'globalPosition') else event.globalPos()

    def mouseMoveEvent(self, event):
        if self._panning:
            parent = self.parent()
            while parent and not isinstance(parent, QtWidgets.QScrollArea):
                parent = parent.parent()
            if isinstance(parent, QtWidgets.QScrollArea) and self._pan_last is not None:
                current = event.globalPosition().toPoint() if hasattr(event,'globalPosition') else event.globalPos()
                dx = current.x() - self._pan_last.x(); dy = current.y() - self._pan_last.y()
                parent.horizontalScrollBar().setValue(parent.horizontalScrollBar().value() - dx)
                parent.verticalScrollBar().setValue(parent.verticalScrollBar().value() - dy)
                self._pan_last = current
            return
        if self._drawing and self.overlay is not None and self.tool:
            self.tool.on_mouse_move(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.tool:
                self.tool.on_mouse_release(event)
            self._drawing = False
            self.strokeEnded.emit()
        elif event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._panning = False; self._pan_last = None

    def clear_overlay(self):
        if self.overlay is not None:
            self.overlay.fill(QtCore.Qt.transparent)
            self.update_display()

    def update_display(self, background_pixmap=None, opacity=0.5):
        if background_pixmap is not None:
            self.current_background = background_pixmap
            self.current_opacity = opacity
        bg = background_pixmap or self.current_background
        op = opacity if background_pixmap is not None else self.current_opacity
        if bg is None:
            if self.overlay is not None:
                comp = QtGui.QPixmap(self.overlay.size())
                comp.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter(comp)
                p.drawPixmap(0,0,self.overlay)
                p.end()
                self.setPixmap(comp)
            return
        comp = QtGui.QPixmap(bg.size())
        comp.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(comp)
        p.setOpacity(op)
        p.drawPixmap(0,0,bg)
        p.setOpacity(1.0)
        if self.overlay is not None:
            p.drawPixmap(0,0,self.overlay)
        p.end()
        self._base_size = comp.size()
        if abs(self.scale_factor - 1.0) > 1e-3:
            scaled = comp.scaled(int(comp.width()*self.scale_factor), int(comp.height()*self.scale_factor), QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            self.setPixmap(scaled)
            self.resize(scaled.size())
        else:
            self.setPixmap(comp)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Rotoscopia MVP - Modular')
        self.resize(1100, 750)
        # core state
        self.frames = []
        self.current_frame_idx = 0
        self.video_path = None
        self.onion_enabled = False
        self.onion_opacity = DEFAULT_ONION_OPACITY
        self.undo_stacks = {}
        self.redo_stacks = {}
        self.max_history = MAX_HISTORY
        self.dirty_frames = set()
        self.project_path = None
        self.project_name = None
        self.zoom_min = DEFAULT_ZOOM_MIN
        self.zoom_max = DEFAULT_ZOOM_MAX
        self.show_background = True
        # project manager
        self.project_mgr = ProjectManager(self)
        # build UI
        self._init_ui()
        # initial tool
        self.set_tool('brush')

    def _init_ui(self):
        open_btn = QtWidgets.QPushButton('Abrir video'); open_btn.clicked.connect(self.open_video)
        self.prev_btn = QtWidgets.QPushButton('<<'); self.prev_btn.clicked.connect(self.prev_frame)
        self.next_btn = QtWidgets.QPushButton('>>'); self.next_btn.clicked.connect(self.next_frame)
        self.copy_prev_btn = QtWidgets.QPushButton('Copiar anterior'); self.copy_prev_btn.clicked.connect(self.copy_previous_overlay)
        self.save_btn = QtWidgets.QPushButton('Guardar PNG'); self.save_btn.clicked.connect(self.save_current_overlay)
        self.clear_btn = QtWidgets.QPushButton('Limpiar'); self.clear_btn.clicked.connect(self.clear_current_overlay)
        self.brush_btn = QtWidgets.QPushButton('Pincel'); self.brush_btn.setCheckable(True); self.brush_btn.setChecked(True); self.brush_btn.toggled.connect(lambda ch: ch and self.set_tool('brush'))
        self.eraser_btn = QtWidgets.QPushButton('Borrar'); self.eraser_btn.setCheckable(True); self.eraser_btn.toggled.connect(lambda ch: ch and self.set_tool('eraser'))
        self.line_btn = QtWidgets.QPushButton('Línea'); self.line_btn.setCheckable(True); self.line_btn.toggled.connect(lambda ch: ch and self.set_tool('line'))
        grp = QtWidgets.QButtonGroup(self)
        for b in [self.brush_btn, self.eraser_btn, self.line_btn]:
            grp.addButton(b)
        grp.setExclusive(True)
        self.onion_checkbox = QtWidgets.QCheckBox('Onion'); self.onion_checkbox.stateChanged.connect(self.toggle_onion)
        self.onion_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.onion_opacity_slider.setRange(0, 100); self.onion_opacity_slider.setValue(int(self.onion_opacity * 100)); self.onion_opacity_slider.setFixedWidth(80); self.onion_opacity_slider.valueChanged.connect(self.change_onion_opacity)
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.opacity_slider.setRange(0, 100); self.opacity_slider.setValue(50); self.opacity_slider.valueChanged.connect(self.refresh_view)
        self.bg_check = QtWidgets.QCheckBox('Fondo'); self.bg_check.setChecked(True); self.bg_check.stateChanged.connect(self.toggle_background)
        self.bg_reset_btn = QtWidgets.QPushButton('Reset BG'); self.bg_reset_btn.setFixedWidth(70); self.bg_reset_btn.clicked.connect(lambda: (self.opacity_slider.setValue(50), self.set_bg_visible(True)))
        self.brush_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.brush_slider.setRange(1, 12); self.brush_slider.setValue(3); self.brush_slider.setFixedWidth(100); self.brush_slider.valueChanged.connect(self.apply_brush_changes)
        palette_colors = ['#000000', '#FFFFFF', '#FF0000', '#0066FF', '#00AA00']
        self.color_layout = QtWidgets.QHBoxLayout()
        for col in palette_colors:
            btn = QtWidgets.QPushButton(); btn.setFixedSize(20, 20); btn.setStyleSheet(f'background:{col}; border:1px solid #444;'); btn.clicked.connect(lambda checked=False, c=col: self.set_brush_color(c)); self.color_layout.addWidget(btn)
        self.custom_color_btn = QtWidgets.QPushButton('+'); self.custom_color_btn.setFixedSize(24, 24); self.custom_color_btn.clicked.connect(self.pick_custom_color); self.color_layout.addWidget(self.custom_color_btn)
        self.project_btn = QtWidgets.QPushButton('Guardar Proyecto'); self.project_btn.clicked.connect(self.project_mgr.save_project_dialog)
        self.load_project_btn = QtWidgets.QPushButton('Cargar Proyecto'); self.load_project_btn.clicked.connect(self.project_mgr.load_project_dialog)
        self.frame_label = QtWidgets.QLabel('Frame: 0 / 0')
        top_layout = QtWidgets.QHBoxLayout()
        for w in [open_btn, self.prev_btn, self.next_btn, self.copy_prev_btn, self.clear_btn, self.brush_btn, self.eraser_btn, self.line_btn, self.save_btn, self.project_btn, self.load_project_btn]:
            top_layout.addWidget(w)
        top_layout.addWidget(self.bg_check)
        top_layout.addWidget(self.opacity_slider)
        top_layout.addWidget(self.bg_reset_btn)
        top_layout.addWidget(self.onion_checkbox)
        top_layout.addWidget(self.onion_opacity_slider)
        top_layout.addWidget(QtWidgets.QLabel('Brush'))
        top_layout.addWidget(self.brush_slider)
        top_layout.addLayout(self.color_layout)
        top_layout.addWidget(self.frame_label)
        container = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(container)
        main_layout.addLayout(top_layout)
        self.canvas = DrawingCanvas(); self.canvas.setAlignment(QtCore.Qt.AlignCenter); self.canvas.setMinimumSize(640, 480); self.canvas.setStyleSheet('border:1px solid #444; background:white;')
        scroll = QtWidgets.QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(self.canvas); main_layout.addWidget(scroll); self.setCentralWidget(container)
        self.overlays = {}
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Right), self, activated=self.next_frame)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Left), self, activated=self.prev_frame)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+S'), self, activated=self.save_current_overlay)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Z'), self, activated=self.undo)
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Y'), self, activated=self.redo)
        QtGui.QShortcut(QtGui.QKeySequence('E'), self, activated=lambda: self.eraser_btn.setChecked(not self.eraser_btn.isChecked()))
        QtGui.QShortcut(QtGui.QKeySequence('O'), self, activated=lambda: self.onion_checkbox.setChecked(not self.onion_checkbox.isChecked()))
        QtGui.QShortcut(QtGui.QKeySequence('+'), self, activated=lambda: self.change_zoom(1.15))
        QtGui.QShortcut(QtGui.QKeySequence('-'), self, activated=lambda: self.change_zoom(1 / 1.15))
        self.canvas.installEventFilter(self)
        self.canvas.strokeStarted.connect(self.push_undo_snapshot)
        self.canvas.strokeEnded.connect(self.mark_dirty_current)

    # --- core operations (simplified from original) ---
    def open_video(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Seleccionar video', '', 'Videos (*.mp4 *.mov *.avi *.mkv)')
        if not path: return
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self,'Error','No se pudo abrir el video.'); return
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret: break
            frames.append(frame)
        cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self,'Video','El video no contiene frames.'); return
        self.frames = frames; self.video_path = path; self.current_frame_idx = 0
        self.overlays.clear(); self.undo_stacks.clear(); self.redo_stacks.clear(); self.dirty_frames.clear()
        h,w = self.frames[0].shape[:2]; self.canvas.set_size(w,h); self.refresh_view()

    def refresh_view(self):
        if not self.frames: return
        idx = self.current_frame_idx; frame = self.frames[idx]
        qimg = cvimg_to_qimage(frame)
        if qimg is None: return
        bg_pix = QtGui.QPixmap.fromImage(qimg)
        if self.onion_enabled and idx > 0:
            prev_q = cvimg_to_qimage(self.frames[idx-1])
            if prev_q:
                prev_pix = QtGui.QPixmap.fromImage(prev_q)
                comp = QtGui.QPixmap(prev_pix.size()); comp.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter(comp); p.setOpacity(self.onion_opacity); p.drawPixmap(0,0,prev_pix)
                if self.onion_opacity>0: p.setOpacity(self.onion_opacity*0.6); p.fillRect(comp.rect(), QtGui.QColor(180,0,255,60))
                p.setOpacity(1.0); p.drawPixmap(0,0,bg_pix); p.end(); bg_pix = comp
        self.canvas.set_size(bg_pix.width(), bg_pix.height())
        if idx in self.overlays and self.overlays[idx] is not None:
            self.canvas.overlay = self.overlays[idx]
        else:
            blank = QtGui.QPixmap(bg_pix.size()); blank.fill(QtCore.Qt.transparent); self.canvas.overlay = blank; self.overlays[idx] = self.canvas.overlay
        opacity = self.opacity_slider.value()/100.0 if self.show_background else 0.0
        self.canvas.update_display(background_pixmap=bg_pix, opacity=opacity)
        self.frame_label.setText(f'Frame: {idx+1} / {len(self.frames)}')

    def store_current_overlay(self):
        if self.canvas.overlay is not None:
            self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)

    def next_frame(self):
        if not self.frames: return
        self.maybe_autosave_current(); self.store_current_overlay()
        if self.current_frame_idx < len(self.frames)-1:
            self.current_frame_idx += 1
            if self.current_frame_idx in self.overlays: self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.refresh_view()

    def prev_frame(self):
        if not self.frames: return
        self.maybe_autosave_current(); self.store_current_overlay()
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            if self.current_frame_idx in self.overlays: self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.refresh_view()

    def copy_previous_overlay(self):
        if self.current_frame_idx == 0:
            QtWidgets.QMessageBox.information(self,'Info','No hay frame anterior para copiar.'); return
        prev_idx = self.current_frame_idx - 1
        if prev_idx in self.overlays and self.overlays[prev_idx] is not None:
            self.canvas.overlay = QtGui.QPixmap(self.overlays[prev_idx]); self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay); self.refresh_view()
        else:
            QtWidgets.QMessageBox.information(self,'Info','No hay overlay en el frame anterior.')

    def clear_current_overlay(self):
        self.push_undo_snapshot(); self.canvas.clear_overlay()
        if self.current_frame_idx in self.overlays: del self.overlays[self.current_frame_idx]
        self.mark_dirty_current()

    def save_current_overlay(self):
        if not self.frames: return
        self.store_current_overlay(); idx = self.current_frame_idx; overlay_pix = self.overlays.get(idx)
        if overlay_pix is None:
            QtWidgets.QMessageBox.information(self,'Info','Overlay vacío: nada para guardar.'); return
        try:
            qimg = overlay_pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
            w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
            try: byte_count = qimg.sizeInBytes()
            except AttributeError: byte_count = qimg.byteCount()
            import numpy as np; from PIL import Image
            arr = np.frombuffer(ptr, np.uint8, count=byte_count).reshape((h,w,4)).copy()
            pil = Image.fromarray(arr, mode='RGBA'); out_path = EXPORT_DIR / f'frame_{idx:05d}.png'; pil.save(str(out_path))
            QtWidgets.QMessageBox.information(self,'Guardado', f'Guardado {out_path}')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,'Error', f'Error al guardar: {e}')

    # helpers
    def set_tool(self, name:str):
        # carga perezosa de clases de herramienta
        try:
            from .tools import BrushTool, EraserTool, LineTool
        except ImportError:
            from tools import BrushTool, EraserTool, LineTool
        mapping = {
            'brush': BrushTool,
            'eraser': EraserTool,
            'line': LineTool,
        }
        cls = mapping.get(name, BrushTool)
        self.canvas.tool = cls(self.canvas)
        self.brush_btn.setStyleSheet('background:#d0ffd0;' if name=='brush' else '')
        self.eraser_btn.setStyleSheet('background:#ffc9c9;' if name=='eraser' else '')
        self.line_btn.setStyleSheet('background:#c9e1ff;' if name=='line' else '')

    def toggle_background(self): self.set_bg_visible(self.bg_check.isChecked())
    def set_bg_visible(self, visible:bool):
        self.show_background = visible
        if self.bg_check.isChecked() != visible: self.bg_check.setChecked(visible)
        self.refresh_view()
    def toggle_onion(self): self.onion_enabled = self.onion_checkbox.isChecked(); self.refresh_view()
    def change_onion_opacity(self): self.onion_opacity = self.onion_opacity_slider.value()/100.0; self.refresh_view() if self.onion_enabled else None
    def apply_brush_changes(self): self.canvas.pen_width = self.brush_slider.value()
    def set_brush_color(self, hex_color:str): col = QtGui.QColor(hex_color); col.setAlpha(255); self.canvas.pen_color = col
    def pick_custom_color(self):
        col = QtWidgets.QColorDialog.getColor(self.canvas.pen_color, self,'Seleccionar color')
        if col.isValid(): self.canvas.pen_color = col

    # undo/redo
    def push_undo_snapshot(self):
        if self.canvas.overlay is None: return
        # sólo snapshot si la herramienta lo requiere (por ejemplo, líneas o acciones complejas)
        if self.canvas.tool and hasattr(self.canvas.tool, 'requires_snapshot') and not self.canvas.tool.requires_snapshot:
            return
        stack = self.undo_stacks.setdefault(self.current_frame_idx, [])
        if len(stack) >= self.max_history: stack.pop(0)
        stack.append(QtGui.QPixmap(self.canvas.overlay))
        self.redo_stacks.setdefault(self.current_frame_idx, []).clear()
    def undo(self):
        stack = self.undo_stacks.get(self.current_frame_idx, [])
        if not stack: return
        current = QtGui.QPixmap(self.canvas.overlay) if self.canvas.overlay else None
        prev = stack.pop(); rstack = self.redo_stacks.setdefault(self.current_frame_idx, [])
        if current is not None: rstack.append(current)
        self.canvas.overlay = QtGui.QPixmap(prev); self.refresh_view()
    def redo(self):
        rstack = self.redo_stacks.get(self.current_frame_idx, [])
        if not rstack: return
        current = QtGui.QPixmap(self.canvas.overlay) if self.canvas.overlay else None
        nxt = rstack.pop(); stack = self.undo_stacks.setdefault(self.current_frame_idx, [])
        if current is not None: stack.append(current)
        self.canvas.overlay = QtGui.QPixmap(nxt); self.refresh_view()
    def mark_dirty_current(self): self.dirty_frames.add(self.current_frame_idx)
    def maybe_autosave_current(self):
        if self.project_path and self.current_frame_idx in self.dirty_frames:
            # delegar a project manager
            self.project_mgr.save_overlay(self.current_frame_idx)
            self.dirty_frames.discard(self.current_frame_idx)
            self.project_mgr.write_meta()

    # zoom
    def change_zoom(self, factor):
        new_scale = self.canvas.scale_factor * factor; new_scale = max(self.zoom_min, min(self.zoom_max, new_scale))
        if abs(new_scale - self.canvas.scale_factor) < 1e-3: return
        self.canvas.scale_factor = new_scale; self.refresh_view()
    def eventFilter(self, obj, event):
        if obj is self.canvas and event.type() == QtCore.QEvent.Wheel:
            delta = event.angleDelta().y(); factor = 1.15 if delta>0 else 1/1.15; self.change_zoom(factor); return True
        return super().eventFilter(obj, event)

    # project wrappers
    def save_project_dialog(self): self.project_mgr.save_project_dialog()
    def load_project_dialog(self): self.project_mgr.load_project_dialog()

if __name__ == '__main__':
    # debug run standalone
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show(); sys.exit(app.exec())
