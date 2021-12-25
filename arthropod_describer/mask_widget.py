import typing

import cv2 as cv
import numpy as np
from PySide2.QtCore import QRectF
from PySide2.QtGui import QPixmap, QImage, QPainter, QColor, Qt, QBitmap
from PySide2.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QWidget, QStyleOptionGraphicsItem

from model.photo import LabelImg, LabelType


class MaskWidget(QGraphicsItem):
    def __init__(self):
        QGraphicsItem.__init__(self)
        self._mask_image: typing.Optional[QImage] = None
        self._colormap = None
        self._ndimg = None
        self.setAcceptedMouseButtons(Qt.NoButton)

    def set_mask_image(self, mask: LabelImg):
        self.prepareGeometryChange()
        cmap = np.array([QColor(0, 0, 0, 0).rgba() for _ in range(np.max(mask.label_img) + 1)])
        for l, c in mask.color_map.items():
            cmap[l] = c
        cmap = np.reshape(cmap, (-1, 1))
        self._nd_img = np.zeros((mask.label_img.shape) + (1,), np.uint32)
        _nd_img = np.take_along_axis(cmap, np.reshape(mask.label_img, (-1, 1)), 0).astype(np.uint32)
        self._nd_img = np.reshape(_nd_img, (mask.label_img.shape) + (1,)).astype(np.uint32)
        self._mask_image = QImage(self._nd_img.data,
                                  self._nd_img.shape[1], self._nd_img.shape[0],
                                  4 * self._nd_img.shape[1], QImage.Format_ARGB32)
        self.update()

    def set_color_map(self, colormap: typing.List[QColor]):
        self._colormap = colormap
        self._mask_image.setColorTable(self._colormap)
        self.update()

    def boundingRect(self):
        if self._mask_image is None:
            return QRectF()
        return self._mask_image.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: typing.Optional[QWidget]=...):
        painter.drawImage(option.rect, self._mask_image)
