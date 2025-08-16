# -*- coding: utf-8 -*-
import sys
import cv2
import numpy as np
from pathlib import Path
#from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

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
    """A QLabel that supports freehand drawing on a transparent QPixmap overlay."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.pen_width = 3
        self.pen_color = QtGui.QColor(0, 0, 0, 255)
        self.mode = "draw"  # or 'erase'
        self._drawing = False
        self.last_point = None
        self.overlay = None

    def set_size(self, w, h):
        if self.overlay is None or self.overlay.size() != QtCore.QSize(w, h):
            self.overlay = QtGui.QPixmap(w, h)
            self.overlay.fill(QtCore.Qt.transparent)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.overlay is not None:
            self._drawing = True
            self.last_point = event.position()

    def mouseMoveEvent(self, event):
        if self._drawing and self.overlay is not None:
            painter = QtGui.QPainter(self.overlay)
            if self.mode == "draw":
                painter.setPen(QtGui.QPen(self.pen_color, self.pen_width))
            else:  # erase
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
                painter.setPen(QtGui.QPen(QtCore.Qt.transparent, self.pen_width))
            
            if self.last_point:
                painter.drawLine(self.last_point, event.position())
            self.last_point = event.position()
            painter.end()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drawing = False

    def clear_overlay(self):
        if self.overlay:
            self.overlay.fill(QtCore.Qt.transparent)
            self.update()

    def update_display(self, background_pixmap=None, opacity=0.5):
        """Compose background and overlay into the label's visible pixmap."""
        if background_pixmap is None:
            self.setPixmap(self.overlay)
            return
        
        composed = QtGui.QPixmap(background_pixmap.size())
        composed.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(composed)
        painter.setOpacity(opacity)
        painter.drawPixmap(0, 0, background_pixmap)
        painter.setOpacity(1.0)
        if self.overlay:
            painter.drawPixmap(0, 0, self.overlay)
        painter.end()
        
        self.setPixmap(composed)

    def get_overlay_image(self):
        """Return the overlay as QImage for saving."""
        if self.overlay:
            return self.overlay.toImage()
        return None

    def set_overlay_from_image(self, qimg):
        """Load overlay from QImage (for copying previous frame)."""
        if qimg:
            self.overlay = QtGui.QPixmap.fromImage(qimg)
            self.update()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rotoscopia MVP")
        self.resize(1200, 800)
        
        self.frames = []
        self.overlays = {}  # Store overlays per frame
        self.current_frame_idx = 0
        self.background_opacity = 0.5
        
        # UI setup
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Top controls
        top_layout = QtWidgets.QHBoxLayout()
        
        self.btn_open = QtWidgets.QPushButton("Abrir Video")
        self.btn_prev = QtWidgets.QPushButton("< Anterior")
        self.btn_next = QtWidgets.QPushButton("Siguiente >")
        self.btn_copy_prev = QtWidgets.QPushButton("Copiar Anterior")
        self.btn_clear = QtWidgets.QPushButton("Limpiar")
        self.btn_save = QtWidgets.QPushButton("Guardar Frame")
        
        # Opacity control
        self.opacity_label = QtWidgets.QLabel("Opacidad fondo:")
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(50)
        
        top_layout.addWidget(self.btn_open)
        top_layout.addWidget(self.btn_prev)
        top_layout.addWidget(self.btn_next)
        top_layout.addWidget(self.btn_copy_prev)
        top_layout.addWidget(self.btn_clear)
        top_layout.addWidget(self.btn_save)
        top_layout.addStretch()
        top_layout.addWidget(self.opacity_label)
        top_layout.addWidget(self.opacity_slider)
        
        # Canvas
        self.canvas = DrawingCanvas()
        self.canvas.setMinimumSize(640, 480)
        self.canvas.setStyleSheet("border: 1px solid black; background-color: white;")
        
        # Status
        self.status_label = QtWidgets.QLabel("Frame: 0/0")
        
        layout.addLayout(top_layout)
        layout.addWidget(self.canvas)
        layout.addWidget(self.status_label)
        
        # Connect signals
        self.btn_open.clicked.connect(self.open_video)
        self.btn_prev.clicked.connect(self.prev_frame)
        self.btn_next.clicked.connect(self.next_frame)
        self.btn_copy_prev.clicked.connect(self.copy_previous_overlay)
        self.btn_clear.clicked.connect(self.canvas.clear_overlay)
        self.btn_save.clicked.connect(self.save_current_overlay)
        self.opacity_slider.valueChanged.connect(self.update_opacity)

    def open_video(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Abrir video", "", "Videos (*.mp4 *.mov *.avi *.mkv)"
        )
        if path:
            self.load_frames(path)
            self.refresh_view()

    def load_frames(self, path):
        """Load all frames from video into memory."""
        cap = cv2.VideoCapture(path)
        self.frames = []
        self.overlays = {}
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            self.frames.append(frame)
        
        cap.release()
        self.current_frame_idx = 0
        print(f"Loaded {len(self.frames)} frames")

    def refresh_view(self):
        """Update canvas with current frame and overlay."""
        if not self.frames:
            return
        
        # Store current overlay
        self.store_current_overlay()
        
        # Get current frame
        frame = self.frames[self.current_frame_idx]
        h, w = frame.shape[:2]
        
        # Set canvas size and convert frame to QPixmap
        self.canvas.set_size(w, h)
        qimg = cvimg_to_qimage(frame)
        bg_pixmap = QtGui.QPixmap.fromImage(qimg)
        
        # Load overlay for this frame if exists
        if self.current_frame_idx in self.overlays:
            self.canvas.set_overlay_from_image(self.overlays[self.current_frame_idx])
        else:
            self.canvas.clear_overlay()
        
        # Update display
        self.canvas.update_display(bg_pixmap, self.background_opacity)
        self.status_label.setText(f"Frame: {self.current_frame_idx + 1}/{len(self.frames)}")

    def next_frame(self):
        if self.current_frame_idx < len(self.frames) - 1:
            self.current_frame_idx += 1
            self.refresh_view()

    def prev_frame(self):
        if self.current_frame_idx > 0:
            self.current_frame_idx -= 1
            self.refresh_view()

    def store_current_overlay(self):
        """Store current overlay in memory."""
        overlay_img = self.canvas.get_overlay_image()
        if overlay_img:
            self.overlays[self.current_frame_idx] = overlay_img

    def copy_previous_overlay(self):
        """Copy overlay from previous frame."""
        if self.current_frame_idx > 0:
            prev_idx = self.current_frame_idx - 1
            if prev_idx in self.overlays:
                self.canvas.set_overlay_from_image(self.overlays[prev_idx])
                self.canvas.update()

    def update_opacity(self, value):
        """Update background opacity."""
        self.background_opacity = value / 100.0
        self.refresh_view()

    def save_current_overlay(self):
        """Save current overlay as PNG."""
        self.store_current_overlay()
        overlay_img = self.canvas.get_overlay_image()
        
        if overlay_img:
            filename = f"frame_{self.current_frame_idx:04d}.png"
            filepath = EXPORT_DIR / filename
            overlay_img.save(str(filepath))
            QtWidgets.QMessageBox.information(self, "Guardado", f"Guardado: {filename}")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "No hay dibujo para guardar")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
