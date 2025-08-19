from PySide6 import QtCore, QtGui, QtWidgets
from .settings import BUCKET_TOLERANCE, ALPHA_PASS


class BaseTool:
    name = "base"
    requires_snapshot = True  # por defecto capturar estado para undo

    def __init__(self, canvas):
        self.canvas = canvas

    # Punto en coordenadas de overlay/layer
    def _overlay_point(self, event) -> QtCore.QPoint:
        if hasattr(event, 'position'):
            p = event.position().toPoint()
        else:
            p = event.pos()
        return self.canvas.mapToOverlay(p)

    def _get_active_layer_pixmap(self) -> QtGui.QPixmap | None:
        if self.canvas.window_ref:
            layer = self.canvas.window_ref.get_active_layer()
            if layer:
                return layer.pixmap
        return self.canvas.overlay  # fallback

    def _update_after_draw(self):
        if self.canvas.window_ref:
            self.canvas.window_ref.compose_layers()
        else:
            self.canvas.update()

# --- LassoTool (top-level) ---
class LassoTool(BaseTool):
    name = "lasso"
    requires_snapshot = False

    def __init__(self, canvas):
        super().__init__(canvas)
        self.points: list[QtCore.QPointF] = []
        self.path: QtGui.QPainterPath | None = None
        self.selection_pixmap: QtGui.QPixmap | None = None
        self.selection_rect: QtCore.QRectF = QtCore.QRectF()
        self.selection_offset: QtCore.QPointF = QtCore.QPointF(0, 0)
        self.selection_anchor: QtCore.QPointF = QtCore.QPointF(0, 0)
        self.selection_transform: QtGui.QTransform = QtGui.QTransform()
        self.copied_pixmap: QtGui.QPixmap | None = None
        self.dragging_selection = False
        self.last_move_pos: QtCore.QPoint | None = None
        self.in_transform = False

    def activate(self):
        self.canvas.setCursor(QtCore.Qt.CrossCursor)

    def deactivate(self):
        self.canvas.setCursor(QtCore.Qt.ArrowCursor)
        self.cancel_selection()

    def _init_selection_state(self, pm: QtGui.QPixmap, top_left: QtCore.QPoint):
        self.selection_pixmap = pm
        self.selection_rect = QtCore.QRectF(top_left, QtCore.QSizeF(pm.width(), pm.height()))
        self.selection_offset = QtCore.QPointF(0, 0)
        self.selection_anchor = QtCore.QPointF(pm.width() / 2.0, pm.height() / 2.0)
        self.selection_transform = QtGui.QTransform()
        self.in_transform = False

    def on_mouse_press(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        pos = self._overlay_point(event)
        if self.path:
            local = pos - self.selection_offset if not self.selection_offset.isNull() else pos
            if self.path.contains(local):
                self.dragging_selection = True
                self.last_move_pos = pos
                return
        self.points = [pos]
        self.path = None
        self.selection_pixmap = None
        self.selection_rect = QtCore.QRectF()
        self.selection_offset = QtCore.QPointF(0, 0)
        self.selection_transform = QtGui.QTransform()
        self.in_transform = False
        self.canvas.update()

    def on_mouse_move(self, event):
        pos = self._overlay_point(event)
        if self.dragging_selection and self.selection_pixmap is not None and self.last_move_pos is not None:
            delta = pos - self.last_move_pos
            self.selection_offset += QtCore.QPointF(delta)
            self.last_move_pos = pos
            self.canvas.update()
            return
        if (event.buttons() & QtCore.Qt.LeftButton) and self.points:
            if (pos - self.points[-1]).manhattanLength() > 1:
                self.points.append(pos)
                self.canvas.update()

    def on_mouse_release(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self.dragging_selection:
            self.apply_move()
            self.dragging_selection = False
            self.last_move_pos = None
            self.selection_offset = QtCore.QPointF(0, 0)
            return
        if self.selection_pixmap and self.path and (not self.selection_offset.isNull()):
            self.apply_move()
            return
        if len(self.points) > 2:
            p = QtGui.QPainterPath(); p.moveTo(self.points[0])
            for pt in self.points[1:]:
                p.lineTo(pt)
            p.closeSubpath()
            self.path = p
            self.extract_selection_pixmap()
        else:
            self.points.clear(); self.path = None; self.selection_pixmap = None
        self.canvas.update()

    def extract_selection_pixmap(self):
        tgt = self._get_active_layer_pixmap()
        if not tgt or tgt.isNull() or not self.path:
            return
        rect = self.path.boundingRect().toRect().adjusted(-1, -1, 1, 1)
        rect = rect.intersected(QtCore.QRect(0, 0, tgt.width(), tgt.height()))
        if rect.isEmpty():
            return
        pm = QtGui.QPixmap(rect.width(), rect.height())
        pm.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pm)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(-rect.topLeft())
        painter.setClipPath(self.path)
        painter.drawPixmap(0, 0, tgt)
        painter.end()
        self._init_selection_state(pm, rect.topLeft())

    def apply_move(self):
        if not self.selection_pixmap or self.selection_rect.isNull():
            return
        tgt = self._get_active_layer_pixmap()
        if not tgt:
            return
        if self.canvas.window_ref and hasattr(self.canvas.window_ref, 'push_undo_snapshot'):
            self.canvas.window_ref.push_undo_snapshot()
        w = self.selection_pixmap.width(); h = self.selection_pixmap.height()
        result = QtGui.QImage(w, h, QtGui.QImage.Format_ARGB32_Premultiplied)
        result.fill(0)
        p = QtGui.QPainter(result)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        p.translate(self.selection_anchor)
        p.setTransform(self.selection_transform, True)
        p.translate(-self.selection_anchor)
        p.drawPixmap(0, 0, self.selection_pixmap)
        p.end()
        painter = QtGui.QPainter(tgt)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
        painter.fillRect(self.selection_rect, QtCore.Qt.transparent)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        origin = self.selection_rect.topLeft() + self.selection_offset
        painter.drawImage(int(origin.x()), int(origin.y()), result)
        painter.end()
        self._update_after_draw()
        if self.path is not None:
            top_left_delta = (origin - self.selection_rect.topLeft())
            self.path.translate(top_left_delta.x(), top_left_delta.y())
        self.selection_pixmap = None
        self.selection_rect = QtCore.QRectF()
        self.selection_offset = QtCore.QPointF(0, 0)
        self.selection_transform = QtGui.QTransform()
        self.in_transform = False

    def copy_selection(self):
        if self.selection_pixmap is None and self.path:
            self.extract_selection_pixmap()
        self.copied_pixmap = self.selection_pixmap and QtGui.QPixmap(self.selection_pixmap)
        if self.copied_pixmap:
            QtWidgets.QApplication.clipboard().setPixmap(self.copied_pixmap)

    def paste_selection(self):
        clip = QtWidgets.QApplication.clipboard(); pm = clip.pixmap()
        if pm.isNull():
            if self.copied_pixmap is None:
                return
            pm = self.copied_pixmap
        self._init_selection_state(QtGui.QPixmap(pm), QtCore.QPoint(0, 0))
        self.path = QtGui.QPainterPath(); self.path.addRect(0, 0, pm.width(), pm.height())
        self.points = []
        self.selection_offset = QtCore.QPointF(10, 10)
        self.in_transform = False
        self.canvas.update()

    def _ensure_selection(self):
        if self.selection_pixmap is None and self.path:
            self.extract_selection_pixmap()

    def _accumulate_transform(self, t: QtGui.QTransform):
        if self.selection_pixmap is None:
            return
        self.selection_transform = t * self.selection_transform
        self.in_transform = True
        self.canvas.update()

    def rotate_90(self, clockwise: bool = True):
        self._ensure_selection()
        if self.selection_pixmap is None:
            return
        angle = 90 if clockwise else -90
        self._accumulate_transform(QtGui.QTransform().rotate(angle))

    def rotate_angle(self, degrees: float):
        if abs(degrees) < 0.01:
            return
        self._ensure_selection()
        if self.selection_pixmap is None:
            return
        self._accumulate_transform(QtGui.QTransform().rotate(degrees))

    def flip(self, horizontal: bool = True):
        self._ensure_selection()
        if self.selection_pixmap is None:
            return
        t = QtGui.QTransform().scale(-1 if horizontal else 1, 1 if horizontal else -1)
        self._accumulate_transform(t)

    def invert_selection(self):
        tgt = self._get_active_layer_pixmap()
        if not tgt or tgt.isNull():
            return
        whole = QtGui.QPainterPath(); whole.addRect(0, 0, tgt.width(), tgt.height())
        self.path = whole.subtracted(self.path) if self.path else whole
        self.points.clear()
        self.selection_pixmap = None
        self.selection_rect = QtCore.QRectF()
        self.selection_offset = QtCore.QPointF(0, 0)
        self.selection_transform = QtGui.QTransform()
        self.in_transform = False
        self.extract_selection_pixmap()
        self.canvas.update()

    def select_all(self):
        tgt = self._get_active_layer_pixmap()
        if not tgt or tgt.isNull():
            return
        self.path = QtGui.QPainterPath(); self.path.addRect(0, 0, tgt.width(), tgt.height())
        self.points.clear()
        self.selection_pixmap = None
        self.selection_rect = QtCore.QRectF()
        self.selection_offset = QtCore.QPointF(0, 0)
        self.selection_transform = QtGui.QTransform()
        self.in_transform = False
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
        if self.selection_pixmap and not self.selection_rect.isNull():
            origin = self.selection_rect.topLeft() + self.selection_offset
            painter.save()
            painter.translate(origin + self.selection_anchor)
            painter.setTransform(self.selection_transform, True)
            painter.translate(-self.selection_anchor)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
            painter.setOpacity(1.0 if (self.in_transform and self.selection_offset.isNull()) else 0.75)
            painter.drawPixmap(0, 0, self.selection_pixmap)
            pen = QtGui.QPen(QtGui.QColor(0, 170, 255, 220), 1, QtCore.Qt.DashLine)
            painter.setPen(pen); painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(0, 0, self.selection_pixmap.width()-1, self.selection_pixmap.height()-1)
            painter.restore()

    def apply_action(self, pixmap: QtGui.QPixmap):
        pass

    def cancel_selection(self):
        self.points.clear()
        self.path = None
        self.selection_pixmap = None
        self.selection_rect = QtCore.QRectF()
        self.selection_offset = QtCore.QPointF(0, 0)
        self.selection_anchor = QtCore.QPointF(0, 0)
        self.selection_transform = QtGui.QTransform()
        self.copied_pixmap = None
        self.dragging_selection = False
        self.last_move_pos = None
        self.in_transform = False
        self.canvas.update()


class HandTool(BaseTool):
    name = "hand"
    requires_snapshot = False

    def __init__(self, canvas):
        super().__init__(canvas)
        self.dragging = False
        self.last_pos = None
        self.original_cursor = None

    def activate(self):
        self.original_cursor = self.canvas.cursor()
        self.canvas.setCursor(QtCore.Qt.OpenHandCursor)

    def deactivate(self):
        if self.original_cursor is not None:
            self.canvas.setCursor(self.original_cursor)
        self.dragging = False
        self.last_pos = None

    def on_mouse_press(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self.canvas.setCursor(QtCore.Qt.ClosedHandCursor)

    def on_mouse_move(self, event):
        if not self.dragging or self.last_pos is None:
            return
        parent = self.canvas.parent()
        while parent and not isinstance(parent, QtWidgets.QScrollArea):
            parent = parent.parent()
        if not isinstance(parent, QtWidgets.QScrollArea):
            return
        current_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
        dx = current_pos.x() - self.last_pos.x(); dy = current_pos.y() - self.last_pos.y()
        h_bar = parent.horizontalScrollBar(); v_bar = parent.verticalScrollBar()
        h_bar.setValue(h_bar.value() - dx); v_bar.setValue(v_bar.value() - dy)
        self.last_pos = current_pos

    def on_mouse_release(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.dragging:
            self.dragging = False
            self.last_pos = None
            self.canvas.setCursor(QtCore.Qt.OpenHandCursor)


class BrushTool(BaseTool):
    name = "brush"
    requires_snapshot = True

    def __init__(self, canvas):
        super().__init__(canvas)
        self.last_point = None
        self.mode = 0  # 0 duro redondo, 1 suave, 2 cuadrado

    def set_mode(self, mode: int):
        self.mode = max(0, min(2, mode))

    def activate(self):
        self.canvas.setCursor(QtCore.Qt.CrossCursor)

    def on_mouse_press(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.last_point = self._overlay_point(event)
        self._draw_point(self.last_point)

    def on_mouse_move(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton) or self.last_point is None:
            return
        pt = self._overlay_point(event)
        self._draw_line(self.last_point, pt)
        self.last_point = pt

    def on_mouse_release(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.last_point = None

    def _draw_point(self, pt: QtCore.QPoint):
        pm = self._get_active_layer_pixmap()
        if not pm:
            return
        painter = QtGui.QPainter(pm)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        color = self.canvas.pen_color
        if self.mode == 0:
            pen = QtGui.QPen(color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setPen(pen); painter.drawPoint(pt)
        elif self.mode == 2:  # cuadrado
            half = self.canvas.pen_width // 2
            painter.fillRect(QtCore.QRect(pt.x()-half, pt.y()-half, self.canvas.pen_width, self.canvas.pen_width), color)
        else:  # modo suave
            self._draw_soft_brush(painter, pt)
        painter.end(); self._update_after_draw()

    def _draw_line(self, a: QtCore.QPoint, b: QtCore.QPoint):
        if a == b:
            self._draw_point(a); return
        pm = self._get_active_layer_pixmap()
        if not pm:
            return
        painter = QtGui.QPainter(pm)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        color = self.canvas.pen_color
        if self.mode == 0:
            pen = QtGui.QPen(color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setPen(pen); painter.drawLine(a, b)
        elif self.mode == 2:
            pen = QtGui.QPen(color, 1)
            painter.setPen(pen)
            # Bresenham simple + cuadrados
            dx = b.x() - a.x(); dy = b.y() - a.y(); steps = max(abs(dx), abs(dy))
            if steps == 0:
                steps = 1
            for i in range(steps + 1):
                x = int(a.x() + dx * i / steps); y = int(a.y() + dy * i / steps)
                half = self.canvas.pen_width // 2
                painter.fillRect(QtCore.QRect(x-half, y-half, self.canvas.pen_width, self.canvas.pen_width), color)
        else:
            # dibujar con puntos suaves a lo largo
            dx = b.x() - a.x(); dy = b.y() - a.y(); steps = max(abs(dx), abs(dy))
            if steps == 0:
                steps = 1
            for i in range(steps + 1):
                x = int(a.x() + dx * i / steps); y = int(a.y() + dy * i / steps)
                self._draw_soft_brush(painter, QtCore.QPoint(x, y))
        painter.end(); self._update_after_draw()

    def _draw_soft_brush(self, painter: QtGui.QPainter, pt: QtCore.QPoint):
        size = self.canvas.pen_width
        if size < 1:
            size = 1
        pm = QtGui.QPixmap(size, size); pm.fill(QtCore.Qt.transparent)
        grad = QtGui.QRadialGradient(size/2, size/2, size/2)
        col = QtGui.QColor(self.canvas.pen_color)
        col.setAlpha(255)
        edge = QtGui.QColor(col); edge.setAlpha(0)
        grad.setColorAt(0.0, col); grad.setColorAt(1.0, edge)
        p = QtGui.QPainter(pm); p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.setBrush(QtGui.QBrush(grad)); p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(0, 0, size, size); p.end()
        top_left = QtCore.QPoint(pt.x() - size//2, pt.y() - size//2)
        painter.drawPixmap(top_left, pm)


class EraserTool(BrushTool):
    name = "eraser"

    def _draw_point(self, pt: QtCore.QPoint):
        pm = self._get_active_layer_pixmap()
        if not pm:
            return
        painter = QtGui.QPainter(pm)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        if self.mode == 0:  # círculo duro
            pen = QtGui.QPen(QtCore.Qt.transparent, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            painter.setPen(pen); painter.drawPoint(pt)
        elif self.mode == 2:  # cuadrado
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            half = self.canvas.pen_width // 2
            painter.fillRect(QtCore.QRect(pt.x()-half, pt.y()-half, self.canvas.pen_width, self.canvas.pen_width), QtCore.Qt.transparent)
        else:  # suave
            size = self.canvas.pen_width
            pm_mask = QtGui.QPixmap(size, size); pm_mask.fill(QtCore.Qt.transparent)
            grad = QtGui.QRadialGradient(size/2, size/2, size/2)
            inner = QtGui.QColor(0, 0, 0, 255); outer = QtGui.QColor(0, 0, 0, 0)
            grad.setColorAt(0.0, inner); grad.setColorAt(1.0, outer)
            p = QtGui.QPainter(pm_mask); p.setRenderHint(QtGui.QPainter.Antialiasing, True)
            p.setBrush(QtGui.QBrush(grad)); p.setPen(QtCore.Qt.NoPen); p.drawEllipse(0, 0, size, size); p.end()
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
            tl = QtCore.QPoint(pt.x()-size//2, pt.y()-size//2)
            painter.drawPixmap(tl, pm_mask)
        painter.end(); self._update_after_draw()

    def _draw_line(self, a: QtCore.QPoint, b: QtCore.QPoint):
        # Simple interpolación de puntos usando método de punto
        dx = b.x() - a.x(); dy = b.y() - a.y(); steps = max(abs(dx), abs(dy))
        if steps == 0:
            self._draw_point(a); return
        for i in range(steps + 1):
            x = int(a.x() + dx * i / steps); y = int(a.y() + dy * i / steps)
            self._draw_point(QtCore.QPoint(x, y))


class LineTool(BaseTool):
    name = "line"
    requires_snapshot = True

    def __init__(self, canvas):
        super().__init__(canvas)
        self.start = None
        self.temp_pixmap = None

    def activate(self):
        self.canvas.setCursor(QtCore.Qt.CrossCursor)

    def on_mouse_press(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return
        self.start = self._overlay_point(event)
        base = self._get_active_layer_pixmap()
        self.temp_pixmap = QtGui.QPixmap(base) if base else None

    def on_mouse_move(self, event):
        if self.start is None or not (event.buttons() & QtCore.Qt.LeftButton) or self.temp_pixmap is None:
            return
        current = self._overlay_point(event)
        base_layer = self._get_active_layer_pixmap()
        if base_layer is None:
            return
        # Restaurar base y dibujar línea de previsualización
        base_layer.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(base_layer)
        painter.drawPixmap(0, 0, self.temp_pixmap)
        pen = QtGui.QPen(self.canvas.pen_color, self.canvas.pen_width, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.drawLine(self.start, current)
        painter.end(); self._update_after_draw()

    def on_mouse_release(self, event):
        if event.button() != QtCore.Qt.LeftButton or self.start is None:
            return
        self.start = None; self.temp_pixmap = None



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
