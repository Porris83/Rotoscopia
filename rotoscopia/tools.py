from PySide6 import QtCore, QtGui, QtWidgets
from .settings import BUCKET_TOLERANCE, ALPHA_PASS

class BaseTool:
    name = "base"
    requires_snapshot = True  # usado por canvas para decidir si toma undo al presionar

    def __init__(self, canvas):
        self.canvas = canvas

    # Helpers comunes
    def _overlay_point(self, event):
        try:
            p = event.position().toPoint()
        except AttributeError:
            p = event.pos()
        return self.canvas.mapToOverlay(p)

    def _get_active_layer_pixmap(self):
        """Get the pixmap of the active layer for drawing operations."""
        if not self.canvas.window_ref:
            return self.canvas.overlay
        
        active_layer = self.canvas.window_ref.get_active_layer()
        if active_layer:
            return active_layer.pixmap
        
        # Fallback to canvas overlay if no active layer
        return self.canvas.overlay

    def _update_after_draw(self):
        """Update display after drawing operation."""
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'compose_layers'):
            self.canvas.window_ref.compose_layers()
        else:
            self.canvas.update_display()

    # Nuevas firmas solicitadas
    def on_mouse_press(self, event):
        pass

    def on_mouse_move(self, event):
        pass

    def on_mouse_release(self, event):
        pass

class BrushTool(BaseTool):
    name = "brush"
    def __init__(self, canvas):
        super().__init__(canvas)
        self.mode = 0  # 0 hard round, 1 soft round, 2 square
        self.last_point = None
        self._mask_cache = {}

    def _make_mask(self, size: int):
        key = (self.mode, size)
        if key in self._mask_cache:
            return self._mask_cache[key]
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pm)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor(0, 0, 0, 255)
        if self.mode == 0:  # hard round
            painter.setBrush(color); painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(0, 0, size, size)
        elif self.mode == 1:  # soft round
            # radial gradient
            grad = QtGui.QRadialGradient(QtCore.QPointF(size/2, size/2), size/2)
            inner = QtGui.QColor(0, 0, 0, 255)
            outer = QtGui.QColor(0, 0, 0, 0)
            grad.setColorAt(0.0, inner)
            grad.setColorAt(1.0, outer)
            painter.setBrush(QtGui.QBrush(grad)); painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(0, 0, size, size)
        else:  # square hard
            painter.setBrush(color); painter.setPen(QtCore.Qt.NoPen)
            painter.drawRect(0, 0, size, size)
        painter.end()
        self._mask_cache[key] = pm
        return pm

    def set_mode(self, mode: int):
        self.mode = max(0, min(2, mode))

    def on_mouse_press(self, event):
        self.last_point = self._overlay_point(event)

    def on_mouse_move(self, event):
        target_pixmap = self._get_active_layer_pixmap()
        if target_pixmap is None:
            return
        pt = self._overlay_point(event)
        if self.last_point is None:
            self.last_point = pt
        # Hard round fallback uses line for speed
        if self.mode == 0:
            painter = QtGui.QPainter(target_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, pt)
            painter.end()
        else:
            # stamp interpolation
            size = max(1, int(self.canvas.pen_width))
            mask = self._make_mask(size)
            dx = pt.x() - self.last_point.x(); dy = pt.y() - self.last_point.y()
            dist = max(abs(dx), abs(dy))
            steps = max(1, dist)
            painter = QtGui.QPainter(target_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            for i in range(steps + 1):
                t = i / steps
                x = int(self.last_point.x() + dx * t - size/2)
                y = int(self.last_point.y() + dy * t - size/2)
                # tint mask with pen color
                tinted = QtGui.QPixmap(mask)
                tp = QtGui.QPainter(tinted)
                tp.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
                tp.fillRect(tinted.rect(), self.canvas.pen_color)
                tp.end()
                painter.drawPixmap(x, y, tinted)
            painter.end()
        self.last_point = pt
        self._update_after_draw()

    def on_mouse_release(self, event):
        self.last_point = None

class EraserTool(BaseTool):
    name = "eraser"
    def __init__(self, canvas):
        super().__init__(canvas)
        self.mode = 0  # 0 hard round, 1 soft round, 2 square
        self.last_point = None
        self._mask_cache = {}

    def _make_mask(self, size: int):
        key = (self.mode, size)
        if key in self._mask_cache:
            return self._mask_cache[key]
        pm = QtGui.QPixmap(size, size); pm.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pm); painter.setRenderHint(QtGui.QPainter.Antialiasing)
        if self.mode == 0:  # hard round
            painter.setBrush(QtGui.QColor(255, 255, 255, 255)); painter.setPen(QtCore.Qt.NoPen); painter.drawEllipse(0, 0, size, size)
        elif self.mode == 1:  # soft round
            grad = QtGui.QRadialGradient(QtCore.QPointF(size/2, size/2), size/2)
            grad.setColorAt(0.0, QtGui.QColor(255, 255, 255, 255))
            grad.setColorAt(1.0, QtGui.QColor(255, 255, 255, 0))
            painter.setBrush(QtGui.QBrush(grad)); painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(0, 0, size, size)
        else:  # square
            painter.setBrush(QtGui.QColor(255, 255, 255, 255)); painter.setPen(QtCore.Qt.NoPen); painter.drawRect(0, 0, size, size)
        painter.end()
        self._mask_cache[key] = pm
        return pm

    def set_mode(self, mode: int):
        self.mode = max(0, min(2, mode))

    def on_mouse_press(self, event):
        self.last_point = self._overlay_point(event)

    def on_mouse_move(self, event):
        target_pixmap = self._get_active_layer_pixmap()
        if target_pixmap is None:
            return
        pt = self._overlay_point(event)
        if self.last_point is None:
            self.last_point = pt
        if self.mode == 0:
            painter = QtGui.QPainter(target_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            pen = QtGui.QPen(QtGui.QColor(0,0,0,0), self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.last_point, pt)
            painter.end()
        else:
            size = max(1, int(self.canvas.pen_width))
            mask = self._make_mask(size)
            dx = pt.x() - self.last_point.x(); dy = pt.y() - self.last_point.y()
            dist = max(abs(dx), abs(dy))
            steps = max(1, dist)
            painter = QtGui.QPainter(target_pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            for i in range(steps + 1):
                t = i / steps
                x = int(self.last_point.x() + dx * t - size/2)
                y = int(self.last_point.y() + dy * t - size/2)
                painter.drawPixmap(x, y, mask)
            painter.end()
        self.last_point = pt
        self._update_after_draw()

    def on_mouse_release(self, event):
        self.last_point = None

class LineTool(BaseTool):
    name = "line"

    def __init__(self, canvas):
        super().__init__(canvas)
        self._start = None
        self._base = None

    def on_mouse_press(self, event):
        self._start = self._overlay_point(event)
        target_pixmap = self._get_active_layer_pixmap()
        self._base = QtGui.QPixmap(target_pixmap) if target_pixmap else None

    def on_mouse_move(self, event):
        if self._start is None or self._base is None:
            return
            
        target_pixmap = self._get_active_layer_pixmap()
        if target_pixmap is None:
            return
            
        pt = self._overlay_point(event)
        temp = QtGui.QPixmap(self._base)
        painter = QtGui.QPainter(temp)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self._start, pt)
        painter.end()
        
        # Update the active layer with preview
        if self.canvas.window_ref:
            active_layer = self.canvas.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap = temp
        else:
            self.canvas.overlay = temp
            
        self._update_after_draw()

    def on_mouse_release(self, event):
        if self._start is None or self._base is None:
            self._start = None; self._base = None; return
            
        pt = self._overlay_point(event)
        painter = QtGui.QPainter(self._base)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self._start, pt)
        painter.end()
        
        # Update the active layer with final result
        if self.canvas.window_ref:
            active_layer = self.canvas.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap = self._base
        else:
            self.canvas.overlay = self._base
            
        self._update_after_draw()
        self._start = None; self._base = None

class HandTool(BaseTool):
    name = "hand"
    requires_snapshot = False  # No modifica el lienzo

    def __init__(self, canvas):
        super().__init__(canvas)
        self.dragging = False
        self.last_pos = None
        self.original_cursor = None

    def activate(self):
        """Cambiar cursor a mano abierta al activar."""
        self.original_cursor = self.canvas.cursor()
        self.canvas.setCursor(QtCore.Qt.OpenHandCursor)

    def deactivate(self):
        """Restaurar cursor original al desactivar."""
        if self.original_cursor is not None:
            self.canvas.setCursor(self.original_cursor)
        self.dragging = False
        self.last_pos = None

    def on_mouse_press(self, event):
        """Iniciar pan con botón izquierdo."""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            if hasattr(event, 'globalPosition'):
                self.last_pos = event.globalPosition().toPoint()
            else:
                self.last_pos = event.globalPos()
            self.canvas.setCursor(QtCore.Qt.ClosedHandCursor)

    def on_mouse_move(self, event):
        """Realizar pan mientras se arrastra."""
        if not self.dragging or self.last_pos is None:
            return

        parent = self.canvas.parent()
        while parent and not isinstance(parent, QtWidgets.QScrollArea):
            parent = parent.parent()
        
        if not isinstance(parent, QtWidgets.QScrollArea):
            return

        if hasattr(event, 'globalPosition'):
            current_pos = event.globalPosition().toPoint()
        else:
            current_pos = event.globalPos()

        # Calculate delta movement
        dx = current_pos.x() - self.last_pos.x()
        dy = current_pos.y() - self.last_pos.y()

        h_bar = parent.horizontalScrollBar()
        v_bar = parent.verticalScrollBar()
        
        new_h = h_bar.value() - dx
        new_v = v_bar.value() - dy
        
        h_bar.setValue(new_h)
        v_bar.setValue(new_v)

        # Update last position
        self.last_pos = current_pos

    def on_mouse_release(self, event):
        """Finalizar pan."""
        if event.button() == QtCore.Qt.LeftButton and self.dragging:
            self.dragging = False
            self.last_pos = None
            self.canvas.setCursor(QtCore.Qt.OpenHandCursor)


class LassoTool(BaseTool):
    name = "lasso"
    requires_snapshot = False  # no snapshot hasta mover/aplicar

    def __init__(self, canvas):
        super().__init__(canvas)
        self.points = []  # puntos libres
        self.path = None  # QPainterPath cerrado
        self.preview_pixmap = None  # contenido seleccionado
        self.copied_pixmap = None   # buffer de copia
        self.dragging_selection = False
        self.last_move_pos = None
        self.offset = QtCore.QPoint(0, 0)

    def activate(self):
        self.canvas.setCursor(QtCore.Qt.CrossCursor)

    def deactivate(self):
        self.canvas.setCursor(QtCore.Qt.ArrowCursor)
        self.points.clear()
        self.path = None
        self.preview_pixmap = None
        self.copied_pixmap = None
        self.dragging_selection = False
        self.last_move_pos = None
        self.offset = QtCore.QPoint(0, 0)
        self.canvas.update()

    def on_mouse_press(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            pos = self._overlay_point(event)
            # Detectar click dentro de la selección teniendo en cuenta el offset visual
            if self.path:
                local_pos = pos
                # Si hay offset (preview antes de commit) ajustar para probar containment
                if not self.offset.isNull():
                    local_pos = pos - self.offset
                if self.path.contains(local_pos):
                    self.dragging_selection = True
                    self.last_move_pos = pos
                    return
            # Fallback legacy (sin offset)
            if self.path and self.path.contains(pos):
                self.dragging_selection = True
                self.last_move_pos = pos
                return
            self.points = [pos]
            self.path = None
            self.preview_pixmap = None
            self.dragging_selection = False
            self.offset = QtCore.QPoint(0, 0)
            self.canvas.update()

    def on_mouse_move(self, event):
        pos = self._overlay_point(event)
        if self.dragging_selection and self.preview_pixmap is not None and self.last_move_pos is not None:
            delta = pos - self.last_move_pos
            self.offset += delta
            self.last_move_pos = pos
            self.canvas.update(); return
        if event.buttons() & QtCore.Qt.LeftButton and self.points:
            if (pos - self.points[-1]).manhattanLength() > 1:
                self.points.append(pos); self.canvas.update()

    def on_mouse_release(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.dragging_selection:
                self.apply_move()
                self.dragging_selection = False
                self.last_move_pos = None
                self.offset = QtCore.QPoint(0, 0)
                return
            # Caso: offset cambió pero flag no se activó (click falló dentro por offset)
            if self.preview_pixmap and self.path and not self.offset.isNull():
                self.apply_move()
                return
            if len(self.points) > 2:
                self.path = QtGui.QPainterPath(); self.path.moveTo(self.points[0])
                for p in self.points[1:]:
                    self.path.lineTo(p)
                self.path.closeSubpath()
                self.extract_selection_pixmap()
            else:
                self.points.clear(); self.path = None; self.preview_pixmap = None
            self.canvas.update()

    def extract_selection_pixmap(self):
        target_pixmap = self._get_active_layer_pixmap()
        if not target_pixmap or target_pixmap.isNull() or not self.path:
            return
        rect = self.path.boundingRect().toRect().adjusted(-1, -1, 1, 1)
        rect = rect.intersected(QtCore.QRect(0, 0, target_pixmap.width(), target_pixmap.height()))
        if rect.isEmpty():
            return
        self.preview_pixmap = QtGui.QPixmap(rect.width(), rect.height())
        self.preview_pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self.preview_pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(-rect.topLeft())
        painter.setClipPath(self.path)
        painter.drawPixmap(0, 0, target_pixmap)
        painter.end()

    def apply_move(self):
        """Commit (pegar) el contenido en la capa activa en la nueva posición.

        Pasos:
        1. Limpiar el área original (limitado al path original).
        2. Desactivar clipping para que el drawPixmap no quede recortado.
        3. Dibujar el preview_pixmap completo en (boundingRect.topLeft + offset).
        4. Trasladar el path para reflejar la nueva posición y resetear offset.
        """
        if not self.preview_pixmap or not self.path:
            return
        target_pixmap = self._get_active_layer_pixmap()
        if not target_pixmap:
            return

        # (Opcional) snapshot para undo antes de modificar si disponible
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'push_undo_snapshot'):
            self.canvas.window_ref.push_undo_snapshot()

        orig_rect = self.path.boundingRect()
        painter = QtGui.QPainter(target_pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Limpiar sólo dentro del path original
        painter.setClipPath(self.path)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
        painter.fillRect(orig_rect, QtCore.Qt.transparent)
        # Desactivar clipping antes de dibujar en nueva posición para no recortar la silueta movida
        painter.setClipping(False)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        new_top_left = orig_rect.topLeft().toPoint() + self.offset
        painter.drawPixmap(new_top_left, self.preview_pixmap)
        painter.end()

        # Actualizar path a la nueva ubicación (lógica de selección persistente)
        if not self.offset.isNull():
            self.path.translate(self.offset)
        self.offset = QtCore.QPoint(0, 0)

        # Refrescar composición/visibilidad
        self._update_after_draw()

    def copy_selection(self):
        if self.preview_pixmap is None and self.path:
            self.extract_selection_pixmap()
        self.copied_pixmap = self.preview_pixmap and QtGui.QPixmap(self.preview_pixmap)
        if self.copied_pixmap:
            QtWidgets.QApplication.clipboard().setPixmap(self.copied_pixmap)

    def paste_selection(self):
        clip = QtWidgets.QApplication.clipboard(); pm = clip.pixmap()
        if pm.isNull():
            if self.copied_pixmap is None:
                return
            pm = self.copied_pixmap
        self.preview_pixmap = QtGui.QPixmap(pm)
        self.path = QtGui.QPainterPath(); self.path.addRect(0, 0, self.preview_pixmap.width(), self.preview_pixmap.height())
        self.points = []
        self.offset = QtCore.QPoint(10, 10)  # offset visual
        self.canvas.update()

    def invert_selection(self):
        target_pixmap = self._get_active_layer_pixmap()
        if not target_pixmap or target_pixmap.isNull():
            return
        rect = QtCore.QRectF(0, 0, target_pixmap.width(), target_pixmap.height())
        whole = QtGui.QPainterPath(); whole.addRect(rect)
        self.path = whole.subtracted(self.path) if self.path else whole
        self.extract_selection_pixmap(); self.canvas.update()

    def select_all(self):
        target_pixmap = self._get_active_layer_pixmap()
        if not target_pixmap or target_pixmap.isNull():
            return
        self.path = QtGui.QPainterPath(); self.path.addRect(0, 0, target_pixmap.width(), target_pixmap.height())
        self.points = []
        self.extract_selection_pixmap(); self.canvas.update()

    def draw_selection(self, painter: QtGui.QPainter):
        if self.path:
            pen = QtGui.QPen(QtGui.QColor(0, 170, 255, 220), 1, QtCore.Qt.DashLine)
            painter.setPen(pen); painter.setBrush(QtCore.Qt.NoBrush); painter.drawPath(self.path)
        elif self.points:
            pen = QtGui.QPen(QtGui.QColor(0, 170, 255, 180), 1, QtCore.Qt.DotLine)
            painter.setPen(pen)
            for i in range(1, len(self.points)):
                painter.drawLine(self.points[i-1], self.points[i])
        if self.preview_pixmap and self.path and not self.offset.isNull():
            rect = self.path.boundingRect().toRect(); new_pos = rect.topLeft() + self.offset
            painter.setOpacity(0.6); painter.drawPixmap(new_pos, self.preview_pixmap); painter.setOpacity(1.0)

    def apply_action(self, pixmap: QtGui.QPixmap):  # placeholder
        pass


class BucketTool(BaseTool):
    name = "bucket"
    tolerance = BUCKET_TOLERANCE  # configurable vía settings

    def on_mouse_press(self, event):
        pt = self._overlay_point(event)
        x = int(pt.x()); y = int(pt.y())
        target_pixmap = self._get_active_layer_pixmap()
        if not target_pixmap or target_pixmap.isNull():
            return
        if x < 0 or y < 0 or x >= target_pixmap.width() or y >= target_pixmap.height():
            return
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'push_undo_snapshot'):
            self.canvas.window_ref.push_undo_snapshot()
        self.apply_fill(target_pixmap, QtCore.QPoint(x, y), self.canvas.pen_color)
        self._update_after_draw()

    def apply_fill(self, pixmap: QtGui.QPixmap, start_point: QtCore.QPoint, new_color: QtGui.QColor):
        """Flood fill con soporte de límites anti-alias (alpha) y similitud RGB.

        - Si el pixel seed es transparente (alpha == 0): solo rellena píxeles con alpha <= ALPHA_PASS.
        - Si es opaco: rellena por similitud de color (suma de diferencias RGB <= 3 * tolerance), ignorando alpha.
        - Acceso directo BGRA.
        """
        if pixmap.isNull():
            return
        img = pixmap.toImage().convertToFormat(QtGui.QImage.Format_ARGB32)
        w = img.width(); h = img.height()
        x0 = start_point.x(); y0 = start_point.y()
        if x0 < 0 or y0 < 0 or x0 >= w or y0 >= h:
            return
        stride = img.bytesPerLine()
        ptr = img.bits()
        # PySide6 puede devolver un sip.voidptr (requiere setsize) o directamente un memoryview.
        if hasattr(ptr, 'setsize'):
            try:
                # sizeInBytes() en versiones nuevas; fallback a height*stride
                size = getattr(img, 'sizeInBytes', None)
                if callable(size):
                    ptr.setsize(size())
                else:
                    ptr.setsize(img.height() * stride)
            except Exception:
                pass
        buf = ptr if isinstance(ptr, memoryview) else memoryview(ptr)

        def get_pixel(x, y):
            base = y * stride + x * 4
            b = buf[base + 0]; g = buf[base + 1]; r = buf[base + 2]; a = buf[base + 3]
            return r, g, b, a

        def set_pixel(x, y, c: QtGui.QColor):
            base = y * stride + x * 4
            buf[base + 0] = c.blue()
            buf[base + 1] = c.green()
            buf[base + 2] = c.red()
            buf[base + 3] = 255  # forzamos opaco al rellenar

        sr, sg, sb, sa = get_pixel(x0, y0)
        nr, ng, nb = new_color.red(), new_color.green(), new_color.blue()
        # Evitar trabajo si ya coincide en región opaca
        if sa > 0 and (sr, sg, sb) == (nr, ng, nb):
            return

        tol = self.tolerance
        color_threshold = 3 * tol

        visited = bytearray(w * h)
        stack = [(x0, y0)]
        visited[y0 * w + x0] = 1

        seed_transparent = (sa == 0)

        while stack:
            x, y = stack.pop()
            r, g, b, a = get_pixel(x, y)
            if seed_transparent:
                # Solo rellenar “vacío” (alpha muy baja) para no cruzar strokes anti-aliased
                if a > ALPHA_PASS:
                    continue
            else:
                diff = abs(r - sr) + abs(g - sg) + abs(b - sb)
                if diff > color_threshold:
                    continue
            # Pintar
            set_pixel(x, y, new_color)
            # Vecinos 4-dir
            for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                if 0 <= nx < w and 0 <= ny < h:
                    nidx = ny * w + nx
                    if not visited[nidx]:
                        visited[nidx] = 1
                        stack.append((nx, ny))

        # Actualizar el pixmap directamente desde la QImage para asegurar refresco correcto
        pixmap.convertFromImage(img)


class RectangleTool(BaseTool):
    name = "rectangle"

    def __init__(self, canvas):
        super().__init__(canvas)
        self.start = None
        self.base = None
        self.preview = None

    def on_mouse_press(self, event):
        self.start = self._overlay_point(event)
        target = self._get_active_layer_pixmap()
        self.base = QtGui.QPixmap(target) if target else None

    def on_mouse_move(self, event):
        if self.start is None or self.base is None:
            return
        target = self._get_active_layer_pixmap()
        if target is None:
            return
        pt = self._overlay_point(event)
        rect = QtCore.QRect(self.start, pt).normalized()
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            size = min(rect.width(), rect.height())
            rect.setWidth(size); rect.setHeight(size)
        temp = QtGui.QPixmap(self.base)
        p = QtGui.QPainter(temp); p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.SquareCap, QtCore.Qt.RoundJoin)
        p.setPen(pen)
        if event.modifiers() & QtCore.Qt.AltModifier:
            # Relleno puntual con Alt
            brush = QtGui.QBrush(self.canvas.pen_color)
            p.fillRect(rect, brush)
        p.drawRect(rect)
        p.end()
        # Update preview into active layer
        if self.canvas.window_ref:
            active_layer = self.canvas.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap = temp
        else:
            self.canvas.overlay = temp
        self._update_after_draw()

    def on_mouse_release(self, event):
        if self.start is None or self.base is None:
            self.start = None; self.base = None; return
        pt = self._overlay_point(event)
        rect = QtCore.QRect(self.start, pt).normalized()
        if rect.width() < 1 or rect.height() < 1:
            self.start = None; self.base = None; return
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            size = min(rect.width(), rect.height())
            rect.setWidth(size); rect.setHeight(size)
        # Snapshot undo
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'push_undo_snapshot'):
            self.canvas.window_ref.push_undo_snapshot()
        target = self._get_active_layer_pixmap()
        if target is None:
            self.start = None; self.base = None; return
        painter = QtGui.QPainter(target); painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.SquareCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        if event.modifiers() & QtCore.Qt.AltModifier:
            painter.fillRect(rect, QtGui.QBrush(self.canvas.pen_color))
        painter.drawRect(rect); painter.end()
        self._update_after_draw()
        self.start = None; self.base = None


class EllipseTool(BaseTool):
    name = "ellipse"

    def __init__(self, canvas):
        super().__init__(canvas)
        self.start = None
        self.base = None

    def on_mouse_press(self, event):
        self.start = self._overlay_point(event)
        target = self._get_active_layer_pixmap()
        self.base = QtGui.QPixmap(target) if target else None

    def on_mouse_move(self, event):
        if self.start is None or self.base is None:
            return
        target = self._get_active_layer_pixmap()
        if target is None:
            return
        pt = self._overlay_point(event)
        rect = QtCore.QRect(self.start, pt).normalized()
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            size = min(rect.width(), rect.height())
            rect.setWidth(size); rect.setHeight(size)
        temp = QtGui.QPixmap(self.base)
        p = QtGui.QPainter(temp); p.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        p.setPen(pen)
        if event.modifiers() & QtCore.Qt.AltModifier:
            p.setBrush(QtGui.QBrush(self.canvas.pen_color))
        else:
            p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(rect)
        p.end()
        if self.canvas.window_ref:
            active_layer = self.canvas.window_ref.get_active_layer()
            if active_layer:
                active_layer.pixmap = temp
        else:
            self.canvas.overlay = temp
        self._update_after_draw()

    def on_mouse_release(self, event):
        if self.start is None or self.base is None:
            self.start = None; self.base = None; return
        pt = self._overlay_point(event)
        rect = QtCore.QRect(self.start, pt).normalized()
        if rect.width() < 1 or rect.height() < 1:
            self.start = None; self.base = None; return
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            size = min(rect.width(), rect.height())
            rect.setWidth(size); rect.setHeight(size)
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'push_undo_snapshot'):
            self.canvas.window_ref.push_undo_snapshot()
        target = self._get_active_layer_pixmap()
        if target is None:
            self.start = None; self.base = None; return
        painter = QtGui.QPainter(target); painter.setRenderHint(QtGui.QPainter.Antialiasing)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setPen(pen)
        if event.modifiers() & QtCore.Qt.AltModifier:
            painter.setBrush(QtGui.QBrush(self.canvas.pen_color))
        else:
            painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawEllipse(rect); painter.end()
        self._update_after_draw()
        self.start = None; self.base = None
