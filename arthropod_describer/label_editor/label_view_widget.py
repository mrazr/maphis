import typing

import numpy as np
from PySide2.QtCore import QRectF
from PySide2.QtGui import QImage, QPainter, QColor, Qt
from PySide2.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem

from arthropod_describer.common.colormap import Colormap
from arthropod_describer.common.photo import LabelImg


class LabelView(QGraphicsItem):
    def __init__(self):
        QGraphicsItem.__init__(self)
        self._label_img: LabelImg = None
        self._label_qimage: typing.Optional[QImage] = None
        self._colormap: Colormap = None
        self._nd_img = None
        self.setAcceptedMouseButtons(Qt.NoButton)

    def set_label_image(self, mask: LabelImg):
        self.prepareGeometryChange()
        self._label_img = mask
        self._recolor_image()
        #cmap = np.array([QColor(0, 0, 0, 0).rgba() for _ in range(np.max(mask.label_img) + 1)])
        #for l, c in mask.color_map.items():
        #    cmap[l] = c
        #cmap = np.reshape(cmap, (-1, 1))
        #self._nd_img = np.zeros((mask.label_img.shape) + (1,), np.uint32)
        #_nd_img = np.take_along_axis(cmap, np.reshape(mask.label_img, (-1, 1)), 0).astype(np.uint32)
        #self._nd_img = np.reshape(_nd_img, (mask.label_img.shape) + (1,)).astype(np.uint32)
        #self._mask_image = QImage(self._nd_img.data,
        #                          self._nd_img.shape[1], self._nd_img.shape[0],
        #                          4 * self._nd_img.shape[1], QImage.Format_ARGB32)
        #self.update()

    def set_color_map(self, colormap: Colormap):
        self._colormap = colormap
        self._recolor_image()
        self.update()

    def _recolor_image(self):
        if self._label_img is None or not self._label_img.is_set:
            self._label_qimage = None
            #self.setVisible(False)
            return
        self._nd_img = np.zeros(self._label_img.label_img.shape + (1,), np.uint32)
        used_labels = np.unique(self._label_img.label_img)
        cmap = {label: QColor.fromRgb(*self._colormap.colormap[label]).rgba() for label in used_labels}
        for label in used_labels:
            #self._nd_img = np.where(self._label_img.label_img == label, cmap[label], self._nd_img)
            coords = np.nonzero(self._label_img.label_img == label)
            self._nd_img[coords] = cmap[label]
        self._label_qimage = QImage(self._nd_img.data,
                                    self._nd_img.shape[1], self._nd_img.shape[0],
                                    4 * self._nd_img.shape[1], QImage.Format_ARGB32)
        self.update()

    def boundingRect(self):
        if self._label_qimage is None:
            return QRectF()
        return self._label_qimage.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: typing.Optional[QWidget]=...):
        if self._label_qimage is not None:
            painter.drawImage(option.rect, self._label_qimage)
