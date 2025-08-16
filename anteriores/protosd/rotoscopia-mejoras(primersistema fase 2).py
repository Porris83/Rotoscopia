import sys
import os
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)


def cvimg_to_qimage(cv_img):
    """Convert BGR/uint8 image (OpenCV) to QImage"""
    if cv_img is None:
        return None
    h, w = cv_img.shape[:2]
    if cv_img.ndim == 2:
        fmt = QtGui.QImage.Format_Grayscale8
        qimg = QtGui.QImage(cv_img.data, w, h, cv_img.strides[0], fmt)
        return qimg.copy()
    if cv_img.shape[2] == 3:
        cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        qimg = QtGui.QImage(cv_img_rgb.data, w, h, cv_img_rgb.strides[0], QtGui.QImage.Format_RGB888)
        return qimg.copy()
    if cv_img.shape[2] == 4:
        cv_img_rgba = cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA)
        qimg = QtGui.QImage(cv_img_rgba.data, w, h, cv_img_rgba.strides[0], QtGui.QImage.Format_RGBA8888)
        return qimg.copy()
    return None


class DrawingCanvas(QtWidgets.QLabel):
    """Canvas de dibujo con soporte de modos (draw/erase), zoom y señales de stroke."""

    strokeStarted = QtCore.Signal()
    strokeEnded = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pen_width = 3
        self.pen_color = QtGui.QColor(0, 0, 0, 255)
        self._drawing = False
        self.last_point = None
        self.overlay = None
        self.mode = "draw"  # draw | erase
        self.current_background = None
        self.current_opacity = 0.5
        self.scale_factor = 1.0  # zoom factor
        self._panning = False
        self._pan_last = None
        self._base_size = None  # tamaño de la composición sin escalar

    def set_size(self, w, h):
        if self.overlay is None or self.overlay.size() != QtCore.QSize(w, h):
            pix = QtGui.QPixmap(w, h)
            pix.fill(QtCore.Qt.transparent)
            self.overlay = pix
            self.setPixmap(QtGui.QPixmap(w, h))

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.overlay is not None:
            self._drawing = True
            self.strokeStarted.emit()
            try:
                self.last_point = self.mapToOverlay(event.position().toPoint())
            except AttributeError:
                self.last_point = self.mapToOverlay(event.pos())
        elif event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._panning = True
            self._pan_last = event.globalPosition().toPoint() if hasattr(event,'globalPosition') else event.globalPos()

    def mouseMoveEvent(self, event):
        if self._panning:
            parent = self.parent()
            scroll_area = None
            while parent and not isinstance(parent, QtWidgets.QScrollArea):
                parent = parent.parent()
            if isinstance(parent, QtWidgets.QScrollArea) and self._pan_last is not None:
                current = event.globalPosition().toPoint() if hasattr(event,'globalPosition') else event.globalPos()
                dx = current.x() - self._pan_last.x()
                dy = current.y() - self._pan_last.y()
                parent.horizontalScrollBar().setValue(parent.horizontalScrollBar().value() - dx)
                parent.verticalScrollBar().setValue(parent.verticalScrollBar().value() - dy)
                self._pan_last = current
            return
        if self._drawing and self.overlay is not None:
            try:
                p = self.mapToOverlay(event.position().toPoint())
            except AttributeError:
                p = self.mapToOverlay(event.pos())
            painter = QtGui.QPainter(self.overlay)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            if self.mode == 'erase':
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                pen = QtGui.QPen(QtGui.QColor(0,0,0,0), self.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            else:
                pen = QtGui.QPen(self.pen_color, self.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setPen(pen)
            if self.last_point is not None:
                painter.drawLine(self.last_point, p)
            painter.end()
            self.last_point = p
            self.update_display()

    def mapToOverlay(self, point: QtCore.QPoint) -> QtCore.QPoint:
        """Mapea coords del widget a la capa considerando zoom y centrado."""
        if self.overlay is None:
            return point
        bw = self.overlay.width(); bh = self.overlay.height()
        disp_w = int(bw * self.scale_factor)
        disp_h = int(bh * self.scale_factor)
        offset_x = (self.width() - disp_w) / 2.0
        offset_y = (self.height() - disp_h) / 2.0
        x = (point.x() - offset_x) / self.scale_factor
        y = (point.y() - offset_y) / self.scale_factor
        x = max(0, min(bw - 1, int(round(x))))
        y = max(0, min(bh - 1, int(round(y))))
        return QtCore.QPoint(x, y)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drawing = False
            self.strokeEnded.emit()
        elif event.button() in (QtCore.Qt.MiddleButton, QtCore.Qt.RightButton):
            self._panning = False
            self._pan_last = None

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
                p.drawPixmap(0, 0, self.overlay)
                p.end()
                self.setPixmap(comp)
            return
        comp = QtGui.QPixmap(bg.size())
        comp.fill(QtCore.Qt.transparent)
        p = QtGui.QPainter(comp)
        p.setOpacity(op)
        p.drawPixmap(0, 0, bg)
        p.setOpacity(1.0)
        if self.overlay is not None:
            p.drawPixmap(0, 0, self.overlay)
        p.end()
        self._base_size = comp.size()
        if abs(self.scale_factor - 1.0) > 1e-3:
            scaled = comp.scaled(int(comp.width()*self.scale_factor), int(comp.height()*self.scale_factor), QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            self.setPixmap(scaled)
            self.resize(scaled.size())
        else:
            self.setPixmap(comp)

    def get_overlay_image(self):
        if self.overlay is None:
            return None
        return self.overlay.toImage()

    def set_overlay_from_image(self, qimg):
        if qimg is None:
            return
        pix = QtGui.QPixmap.fromImage(qimg)
        self.overlay = pix
        self.update_display()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rotoscopia MVP - Fase 2")
        self.resize(1100, 750)

        # Core state
        self.frames = []  # list of numpy BGR frames
        self.current_frame_idx = 0
        self.video_path = None

        # Phase 2 state
        self.onion_enabled = False
        self.onion_opacity = 0.3
        self.undo_stacks = {}   # frame -> list[pixmap]
        self.redo_stacks = {}
        self.max_history = 20
        self.dirty_frames = set()
        self.project_path = None
        self.project_name = None
        self.zoom_min = 0.25
        self.zoom_max = 6.0

        # UI Controls
        open_btn = QtWidgets.QPushButton("Abrir video")
        open_btn.clicked.connect(self.open_video)
        self.prev_btn = QtWidgets.QPushButton("<<")
        self.prev_btn.clicked.connect(self.prev_frame)
        self.next_btn = QtWidgets.QPushButton(">>")
        self.next_btn.clicked.connect(self.next_frame)
        self.copy_prev_btn = QtWidgets.QPushButton("Copiar anterior")
        self.copy_prev_btn.clicked.connect(self.copy_previous_overlay)
        self.save_btn = QtWidgets.QPushButton("Guardar PNG")
        self.save_btn.clicked.connect(self.save_current_overlay)
        self.clear_btn = QtWidgets.QPushButton("Limpiar")
        self.clear_btn.clicked.connect(self.clear_current_overlay)
        self.eraser_btn = QtWidgets.QPushButton("Borrar")
        self.eraser_btn.setCheckable(True)
        self.eraser_btn.toggled.connect(self.toggle_eraser)

        self.onion_checkbox = QtWidgets.QCheckBox("Onion")
        self.onion_checkbox.stateChanged.connect(self.toggle_onion)
        self.onion_opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.onion_opacity_slider.setRange(0,100)
        self.onion_opacity_slider.setValue(int(self.onion_opacity*100))
        self.onion_opacity_slider.setFixedWidth(80)
        self.onion_opacity_slider.valueChanged.connect(self.change_onion_opacity)

        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0,100)
        self.opacity_slider.setValue(50)
        self.opacity_slider.valueChanged.connect(self.refresh_view)

        self.brush_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.brush_slider.setRange(1,12)
        self.brush_slider.setValue(3)
        self.brush_slider.setFixedWidth(100)
        self.brush_slider.valueChanged.connect(self.apply_brush_changes)

        palette_colors = ["#000000", "#FFFFFF", "#FF0000", "#0066FF", "#00AA00"]
        self.color_layout = QtWidgets.QHBoxLayout()
        for col in palette_colors:
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(20,20)
            btn.setStyleSheet(f"background:{col}; border:1px solid #444;")
            btn.clicked.connect(lambda checked=False, c=col: self.set_brush_color(c))
            self.color_layout.addWidget(btn)
        self.custom_color_btn = QtWidgets.QPushButton("+")
        self.custom_color_btn.setFixedSize(24,24)
        self.custom_color_btn.clicked.connect(self.pick_custom_color)
        self.color_layout.addWidget(self.custom_color_btn)
        self.project_btn = QtWidgets.QPushButton("Guardar Proyecto")
        self.project_btn.clicked.connect(self.save_project_dialog)
        self.load_project_btn = QtWidgets.QPushButton("Cargar Proyecto")
        self.load_project_btn.clicked.connect(self.load_project_dialog)

        self.frame_label = QtWidgets.QLabel("Frame: 0 / 0")

        top_layout = QtWidgets.QHBoxLayout()
        for w in [open_btn, self.prev_btn, self.next_btn, self.copy_prev_btn, self.clear_btn, self.eraser_btn, self.save_btn, self.project_btn, self.load_project_btn]:
            top_layout.addWidget(w)
        top_layout.addWidget(QtWidgets.QLabel("Fondo"))
        top_layout.addWidget(self.opacity_slider)
        top_layout.addWidget(self.onion_checkbox)
        top_layout.addWidget(self.onion_opacity_slider)
        top_layout.addWidget(QtWidgets.QLabel("Brush"))
        top_layout.addWidget(self.brush_slider)
        top_layout.addLayout(self.color_layout)
        top_layout.addWidget(self.frame_label)

        container = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(container)
        main_layout.addLayout(top_layout)

        self.canvas = DrawingCanvas()
        self.canvas.setAlignment(QtCore.Qt.AlignCenter)
        self.canvas.setMinimumSize(640,480)
        self.canvas.setStyleSheet("border:1px solid #444; background:white;")

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.canvas)
        main_layout.addWidget(scroll)
        self.setCentralWidget(container)

        self.overlays = {}

        # Shortcuts
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Right), self, activated=self.next_frame)
        QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Left), self, activated=self.prev_frame)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+S"), self, activated=self.save_current_overlay)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Z"), self, activated=self.undo)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Y"), self, activated=self.redo)
        QtGui.QShortcut(QtGui.QKeySequence("E"), self, activated=lambda: self.eraser_btn.setChecked(not self.eraser_btn.isChecked()))
        QtGui.QShortcut(QtGui.QKeySequence("O"), self, activated=lambda: self.onion_checkbox.setChecked(not self.onion_checkbox.isChecked()))
        QtGui.QShortcut(QtGui.QKeySequence("+"), self, activated=lambda: self.change_zoom(1.15))
        QtGui.QShortcut(QtGui.QKeySequence("-"), self, activated=lambda: self.change_zoom(1/1.15))

        self.canvas.installEventFilter(self)
        self.canvas.strokeStarted.connect(self.push_undo_snapshot)
        self.canvas.strokeEnded.connect(self.mark_dirty_current)

    # --------------- Core operations ---------------
    def open_video(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleccionar video", "", "Videos (*.mp4 *.mov *.avi *.mkv)")
        if not path:
            return
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self, "Error", "No se pudo abrir el video.")
            return
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self, "Video", "El video no contiene frames.")
            return
        self.frames = frames
        self.video_path = path
        self.current_frame_idx = 0
        self.overlays.clear()
        self.undo_stacks.clear()
        self.redo_stacks.clear()
        self.dirty_frames.clear()
        # init overlay size
        h, w = self.frames[0].shape[:2]
        self.canvas.set_size(w, h)
        self.refresh_view()

    def refresh_view(self):
        if not self.frames:
            return
        idx = self.current_frame_idx
        frame = self.frames[idx]
        qimg = cvimg_to_qimage(frame)
        if qimg is None:
            return
        bg_pix = QtGui.QPixmap.fromImage(qimg)
        if self.onion_enabled and idx > 0:
            prev_q = cvimg_to_qimage(self.frames[idx-1])
            if prev_q:
                prev_pix = QtGui.QPixmap.fromImage(prev_q)
                comp = QtGui.QPixmap(prev_pix.size())
                comp.fill(QtCore.Qt.transparent)
                p = QtGui.QPainter(comp)
                p.setOpacity(self.onion_opacity)
                p.drawPixmap(0,0,prev_pix)
                p.setOpacity(1.0)
                p.drawPixmap(0,0,bg_pix)
                p.end()
                bg_pix = comp
        self.canvas.set_size(bg_pix.width(), bg_pix.height())
        if idx in self.overlays and self.overlays[idx] is not None:
            self.canvas.overlay = self.overlays[idx]
        else:
            if self.canvas.overlay is None or self.canvas.overlay.size() != bg_pix.size():
                self.canvas.set_size(bg_pix.width(), bg_pix.height())
            self.overlays[idx] = self.canvas.overlay
        opacity = self.opacity_slider.value()/100.0
        self.canvas.update_display(background_pixmap=bg_pix, opacity=opacity)
        self.frame_label.setText(f"Frame: {idx+1} / {len(self.frames)}")

    def store_current_overlay(self):
        if self.canvas.overlay is not None:
            self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)

    def next_frame(self):
        if not self.frames:
            return
        self.maybe_autosave_current()
        self.store_current_overlay()
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            if self.current_frame_idx in self.overlays:
                self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.refresh_view()

    def prev_frame(self):
        if not self.frames:
            return
        self.maybe_autosave_current()
        self.store_current_overlay()
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            if self.current_frame_idx in self.overlays:
                self.canvas.overlay = self.overlays[self.current_frame_idx]
            self.refresh_view()

    def copy_previous_overlay(self):
        if self.current_frame_idx == 0:
            QtWidgets.QMessageBox.information(self, "Info", "No hay frame anterior para copiar.")
            return
        prev_idx = self.current_frame_idx - 1
        if prev_idx in self.overlays and self.overlays[prev_idx] is not None:
            self.canvas.overlay = QtGui.QPixmap(self.overlays[prev_idx])
            self.overlays[self.current_frame_idx] = QtGui.QPixmap(self.canvas.overlay)
            self.refresh_view()
        else:
            QtWidgets.QMessageBox.information(self, "Info", "No hay overlay en el frame anterior.")

    def clear_current_overlay(self):
        self.push_undo_snapshot()
        self.canvas.clear_overlay()
        if self.current_frame_idx in self.overlays:
            del self.overlays[self.current_frame_idx]
        self.mark_dirty_current()

    def save_current_overlay(self):
        if not self.frames:
            return
        self.store_current_overlay()
        idx = self.current_frame_idx
        overlay_pix = self.overlays.get(idx)
        if overlay_pix is None:
            QtWidgets.QMessageBox.information(self, "Info", "Overlay vacío: nada para guardar.")
            return
        try:
            qimg = overlay_pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
            w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
            try:
                byte_count = qimg.sizeInBytes()
            except AttributeError:
                byte_count = qimg.byteCount()
            arr = np.frombuffer(ptr, np.uint8, count=byte_count).reshape((h, w, 4)).copy()
            pil = Image.fromarray(arr, mode="RGBA")
            out_path = EXPORT_DIR / f"frame_{idx:05d}.png"
            pil.save(str(out_path))
            QtWidgets.QMessageBox.information(self, "Guardado", f"Guardado {out_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error al guardar: {e}")

    # --------------- Phase 2 helpers ---------------
    def toggle_eraser(self, checked: bool):
        self.canvas.mode = 'erase' if checked else 'draw'
        self.eraser_btn.setStyleSheet('background:#ffc9c9;' if checked else '')

    def toggle_onion(self):
        self.onion_enabled = self.onion_checkbox.isChecked()
        self.refresh_view()

    def change_onion_opacity(self):
        self.onion_opacity = self.onion_opacity_slider.value()/100.0
        if self.onion_enabled:
            self.refresh_view()

    def apply_brush_changes(self):
        self.canvas.pen_width = self.brush_slider.value()

    def set_brush_color(self, hex_color: str):
        col = QtGui.QColor(hex_color)
        col.setAlpha(255)
        self.canvas.pen_color = col

    def pick_custom_color(self):
        col = QtWidgets.QColorDialog.getColor(self.canvas.pen_color, self, "Seleccionar color")
        if col.isValid():
            self.canvas.pen_color = col

    # Undo / Redo
    def push_undo_snapshot(self):
        if self.canvas.overlay is None:
            return
        stack = self.undo_stacks.setdefault(self.current_frame_idx, [])
        if len(stack) >= self.max_history:
            stack.pop(0)
        stack.append(QtGui.QPixmap(self.canvas.overlay))
        self.redo_stacks.setdefault(self.current_frame_idx, []).clear()

    def undo(self):
        stack = self.undo_stacks.get(self.current_frame_idx, [])
        if not stack:
            return
        current = QtGui.QPixmap(self.canvas.overlay) if self.canvas.overlay else None
        prev = stack.pop()
        rstack = self.redo_stacks.setdefault(self.current_frame_idx, [])
        if current is not None:
            rstack.append(current)
        self.canvas.overlay = QtGui.QPixmap(prev)
        self.refresh_view()

    def redo(self):
        rstack = self.redo_stacks.get(self.current_frame_idx, [])
        if not rstack:
            return
        current = QtGui.QPixmap(self.canvas.overlay) if self.canvas.overlay else None
        nxt = rstack.pop()
        stack = self.undo_stacks.setdefault(self.current_frame_idx, [])
        if current is not None:
            stack.append(current)
        self.canvas.overlay = QtGui.QPixmap(nxt)
        self.refresh_view()

    def mark_dirty_current(self):
        self.dirty_frames.add(self.current_frame_idx)

    def maybe_autosave_current(self):
        if self.project_path and self.current_frame_idx in self.dirty_frames:
            self.save_overlay_to_project(self.current_frame_idx)
            self.dirty_frames.discard(self.current_frame_idx)
            self.write_project_meta()

    # Zoom
    def change_zoom(self, factor):
        new_scale = self.canvas.scale_factor * factor
        new_scale = max(self.zoom_min, min(self.zoom_max, new_scale))
        if abs(new_scale - self.canvas.scale_factor) < 1e-3:
            return
        self.canvas.scale_factor = new_scale
        self.refresh_view()

    def eventFilter(self, obj, event):
        if obj is self.canvas and event.type() == QtCore.QEvent.Wheel:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1/1.15
            self.change_zoom(factor)
            return True
        return super().eventFilter(obj, event)

    # Project persistence
    def save_project_dialog(self):
        if not self.frames:
            QtWidgets.QMessageBox.information(self, "Info", "Carga un video antes de guardar un proyecto.")
            return
        name, ok = QtWidgets.QInputDialog.getText(self, "Nombre del Proyecto", "Nombre:")
        if not ok or not name.strip():
            return
        self.project_name = name.strip()
        self.project_path = PROJECTS_DIR / self.project_name
        (self.project_path / 'frames').mkdir(parents=True, exist_ok=True)
        for idx, pix in self.overlays.items():
            if pix is not None:
                self.save_overlay_to_project(idx)
        self.write_project_meta()
        QtWidgets.QMessageBox.information(self, "Proyecto", f"Proyecto guardado en {self.project_path}")

    def save_overlay_to_project(self, idx):
        pix = self.overlays.get(idx)
        if pix is None:
            return
        qimg = pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
        w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
        try:
            bc = qimg.sizeInBytes()
        except AttributeError:
            bc = qimg.byteCount()
        arr = np.frombuffer(ptr, np.uint8, count=bc).reshape((h, w, 4)).copy()
        pil = Image.fromarray(arr, mode='RGBA')
        out_dir = self.project_path / 'frames'
        out_dir.mkdir(exist_ok=True, parents=True)
        out_path = out_dir / f"frame_{idx:05d}.png"
        pil.save(str(out_path))

    def write_project_meta(self):
        if not self.project_path:
            return
        meta = {
            "version": 1,
            "video_path": self.video_path,
            "frame_width": self.frames[0].shape[1] if self.frames else None,
            "frame_height": self.frames[0].shape[0] if self.frames else None,
            "frame_count": len(self.frames),
            "fps": 12,
            "frames_with_overlay": sorted([i for i,o in self.overlays.items() if o is not None]),
            "settings": {
                "brush_color": self.canvas.pen_color.name(QtGui.QColor.HexArgb),
                "brush_size": self.canvas.pen_width
            }
        }
        tmp_path = self.project_path / 'meta.tmp'
        final_path = self.project_path / 'meta.json'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, final_path)

    def load_project_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleccionar meta.json", str(PROJECTS_DIR), "meta.json (meta.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo leer meta.json: {e}")
            return
        video_path = meta.get('video_path')
        if not video_path or not os.path.exists(video_path):
            QtWidgets.QMessageBox.warning(self, "Proyecto", "Video original no encontrado. Selecciona manualmente.")
            video_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Video del proyecto", "", "Videos (*.mp4 *.mov *.avi *.mkv)")
            if not video_path:
                return
        # Cargar video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self, "Error", "No se pudo abrir el video del proyecto.")
            return
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self, "Proyecto", "El video no contiene frames.")
            return
        self.frames = frames
        self.video_path = video_path
        self.current_frame_idx = 0
        self.overlays.clear()
        self.undo_stacks.clear()
        self.redo_stacks.clear()
        self.dirty_frames.clear()
        self.project_path = Path(path).parent
        self.project_name = self.project_path.name
        # Cargar overlays
        frames_with_overlay = meta.get('frames_with_overlay', [])
        frames_dir = self.project_path / 'frames'
        for idx in frames_with_overlay:
            overlay_file = frames_dir / f"frame_{idx:05d}.png"
            if overlay_file.exists():
                qimg = QtGui.QImage(str(overlay_file))
                if not qimg.isNull():
                    self.overlays[idx] = QtGui.QPixmap.fromImage(qimg)
        # Restaurar ajustes
        settings = meta.get('settings', {})
        brush_size = settings.get('brush_size')
        if isinstance(brush_size, int):
            self.brush_slider.setValue(max(1, min(12, brush_size)))
            self.canvas.pen_width = self.brush_slider.value()
        brush_color = settings.get('brush_color')
        if brush_color:
            col = QtGui.QColor(brush_color)
            if col.isValid():
                self.canvas.pen_color = col
        # Init canvas size
        h, w = self.frames[0].shape[:2]
        self.canvas.set_size(w, h)
        self.refresh_view()
        QtWidgets.QMessageBox.information(self, "Proyecto", f"Proyecto cargado: {self.project_name}")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
