import json, os
from pathlib import Path
from PySide6 import QtWidgets, QtGui
import numpy as np
from PIL import Image
import cv2
from .settings import PROJECTS_DIR
from .utils import cvimg_to_qimage, qpixmap_to_pil

class ProjectManager:
    def __init__(self, window):
        self.window = window  # referencia a MainWindow

    def save_project_dialog(self):
        if not self.window.frames:
            QtWidgets.QMessageBox.information(self.window, "Info", "Carga un video antes de guardar un proyecto.")
            return
        name, ok = QtWidgets.QInputDialog.getText(self.window, "Nombre del Proyecto", "Nombre:")
        if not ok or not name.strip():
            return
        self.window.project_name = name.strip()
        self.window.project_path = PROJECTS_DIR / self.window.project_name
        (self.window.project_path / 'frames').mkdir(parents=True, exist_ok=True)
        for idx, pix in self.window.overlays.items():
            if pix is not None:
                self.save_overlay(idx)
        self.write_meta()
        QtWidgets.QMessageBox.information(self.window, "Proyecto", f"Proyecto guardado en {self.window.project_path}")

    def save_overlay(self, idx):
        pix = self.window.overlays.get(idx)
        if pix is None:
            return
        pil = qpixmap_to_pil(pix)
        out_dir = self.window.project_path / 'frames'
        out_dir.mkdir(exist_ok=True, parents=True)
        out_path = out_dir / f"frame_{idx:05d}.png"
        pil.save(str(out_path))

    def write_meta(self):
        if not self.window.project_path:
            return
        meta = {
            "version": 1,
            "video_path": self.window.video_path,
            "frame_width": self.window.frames[0].shape[1] if self.window.frames else None,
            "frame_height": self.window.frames[0].shape[0] if self.window.frames else None,
            "frame_count": len(self.window.frames),
            "fps": 12,
            "frames_with_overlay": sorted([i for i,o in self.window.overlays.items() if o is not None]),
            "settings": {
                "brush_color": self.window.canvas.pen_color.name(QtGui.QColor.HexArgb),
                "brush_size": self.window.canvas.pen_width
            }
        }
        tmp_path = self.window.project_path / 'meta.tmp'
        final_path = self.window.project_path / 'meta.json'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, final_path)

    def load_project_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Seleccionar meta.json", str(PROJECTS_DIR), "meta.json (meta.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self.window, "Error", f"No se pudo leer meta.json: {e}")
            return
        video_path = meta.get('video_path')
        if not video_path or not os.path.exists(video_path):
            QtWidgets.QMessageBox.warning(self.window, "Proyecto", "Video original no encontrado. Selecciona manualmente.")
            video_path, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Video del proyecto", "", "Videos (*.mp4 *.mov *.avi *.mkv)")
            if not video_path:
                return
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            QtWidgets.QMessageBox.critical(self.window, "Error", "No se pudo abrir el video del proyecto.")
            return
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if not frames:
            QtWidgets.QMessageBox.warning(self.window, "Proyecto", "El video no contiene frames.")
            return
        self.window.frames = frames
        self.window.video_path = video_path
        self.window.current_frame_idx = 0
        self.window.overlays.clear()
        self.window.undo_stacks.clear()
        self.window.redo_stacks.clear()
        self.window.dirty_frames.clear()
        self.window.project_path = Path(path).parent
        self.window.project_name = self.window.project_path.name
        frames_with_overlay = meta.get('frames_with_overlay', [])
        frames_dir = self.window.project_path / 'frames'
        for idx in frames_with_overlay:
            overlay_file = frames_dir / f"frame_{idx:05d}.png"
            if overlay_file.exists():
                qimg = QtGui.QImage(str(overlay_file))
                if not qimg.isNull():
                    self.window.overlays[idx] = QtGui.QPixmap.fromImage(qimg)
        settings = meta.get('settings', {})
        brush_size = settings.get('brush_size')
        if isinstance(brush_size, int):
            self.window.brush_slider.setValue(max(1, min(12, brush_size)))
            self.window.canvas.pen_width = self.window.brush_slider.value()
        brush_color = settings.get('brush_color')
        if brush_color:
            col = QtGui.QColor(brush_color)
            if col.isValid():
                self.window.canvas.pen_color = col
        h, w = self.window.frames[0].shape[:2]
        self.window.canvas.set_size(w, h)
        self.window.refresh_view()
        QtWidgets.QMessageBox.information(self.window, "Proyecto", f"Proyecto cargado: {self.window.project_name}")
