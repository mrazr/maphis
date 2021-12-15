import typing

from PySide2.QtCore import QRectF
from PySide2.QtGui import QPixmap, QImage, QPainter, QColor
from PySide2.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QWidget, QStyleOptionGraphicsItem


class MaskWidget(QGraphicsItem):
    def __init__(self):
        QGraphicsItem.__init__(self)
        self._mask_image: typing.Optional[QImage] = None
        self._colormap = None

    def set_mask_image(self, mask: QImage):
        self.prepareGeometryChange()
        self._mask_image = mask
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
