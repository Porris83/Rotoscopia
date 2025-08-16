import cv2
import numpy as np
from PIL import Image
from PySide6 import QtGui


def cvimg_to_qimage(cv_img):
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


def qpixmap_to_pil(pix):
    qimg = pix.toImage().convertToFormat(QtGui.QImage.Format_RGBA8888)
    w = qimg.width(); h = qimg.height(); ptr = qimg.bits()
    try:
        bc = qimg.sizeInBytes()
    except AttributeError:
        bc = qimg.byteCount()
    arr = np.frombuffer(ptr, np.uint8, count=bc).reshape((h, w, 4)).copy()
    return Image.fromarray(arr, mode='RGBA')
