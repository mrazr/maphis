import typing

from PySide2.QtCore import QPointF, Signal, QRectF
from PySide2.QtGui import QPixmap, QColor, QImage, QPainter, Qt
from PySide2.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsPixmapItem, QGraphicsSceneMouseEvent, \
    QStyleOptionGraphicsItem, QWidget, QGraphicsObject
import numpy as np

from mask_widget import MaskWidget
from model.photo import Photo, Mask, MaskType


class EditableMask:
    def __init__(self):
        self._mask: typing.Optional[Mask] = None
        self._colormap = None

    def set_mask(self, mask: Mask, colormap):
        self._mask = mask
        self._colormap = colormap


class CanvasWidget(QGraphicsObject):
    left_press = Signal(QPointF)
    right_press = Signal()
    wheel_press = Signal()
    wheel_move = Signal()

    def __init__(self, parent=None):
        QGraphicsObject.__init__(self, parent)
        self.photo: typing.Optional[Photo] = None

        self.masks: typing.Optional[typing.Dict[MaskType, Mask]] = None
        self.colormaps = {MaskType.BUG_MASK: [],
                          MaskType.SEGMENTS_MASK: [],
                          MaskType.REFLECTION_MASK: []}

        self._image_pixmap = None
        self.image_gpixmap = None

        self._mask_pixmap = None
        self.mask_gpixmap = None

        self._segments_pixmap = None
        self.segments_gpixmap = None

        self._reflection_pixmap = None
        self._reflection_gpixmap = None

        self.mask_pixmaps: typing.Dict[MaskType, QPixmap] = {}

        self.mask_gpixmaps: typing.Dict[MaskType, QGraphicsPixmapItem] = {}

        self.mask_widgets: typing.Dict[MaskType, MaskWidget] = {}

        self.canvas_rect = QRectF()

    def initialize(self):
        self._image_pixmap = QPixmap()
        self.image_gpixmap = self.scene().addPixmap(self._image_pixmap)

        self._mask_pixmap = QPixmap()
        self._mask_gpixmap = self.scene().addPixmap(self._mask_pixmap)

        self._segments_pixmap = QPixmap()
        self._segments_gpixmap = self.scene().addPixmap(self._segments_pixmap)

        self._reflection_pixmap = QPixmap()
        self._reflection_gpixmap = self.scene().addPixmap(self._reflection_pixmap)

        self.mask_pixmaps: typing.Dict[MaskType, QPixmap] = {
            MaskType.BUG_MASK: self._mask_pixmap,
            MaskType.SEGMENTS_MASK: self._segments_pixmap,
            MaskType.REFLECTION_MASK: self._reflection_pixmap
        }

        self.mask_gpixmaps: typing.Dict[MaskType, QGraphicsPixmapItem] = {
            MaskType.BUG_MASK: self._mask_gpixmap,
            MaskType.SEGMENTS_MASK: self._segments_gpixmap,
            MaskType.REFLECTION_MASK: self._reflection_gpixmap
        }

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[MaskType.BUG_MASK] = mask_w
        mask_w.setPos(0, 0)

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[MaskType.SEGMENTS_MASK] = mask_w
        mask_w.setPos(0, 0)

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[MaskType.REFLECTION_MASK] = mask_w
        mask_w.setPos(0, 0)

    def boundingRect(self) -> QRectF:
        if self.photo is not None:
            return self.canvas_rect
        return QRectF()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget:typing.Optional[QWidget]=...):
        pass

    def set_photo(self, photo: Photo):
        self.photo = photo

        self.masks = self.photo.mask_dict()

        self._set_pixmaps(photo.image, self._image_pixmap, self.image_gpixmap)

        for mask_type in self.masks.keys():
            self.mask_gpixmaps[mask_type].setVisible(False)
            #self._set_pixmaps(self.masks[mask_type].mask, self.mask_pixmaps[mask_type], self.mask_gpixmaps[mask_type])
            self.mask_widgets[mask_type].set_mask_image(self.masks[mask_type].mask)
            self.mask_widgets[mask_type].set_color_map([QColor.fromRgb(*np.random.randint(0, 255, (3,)), 100).rgba()])

    def set_color_map(self, color_map: typing.List[QColor], mask_type: MaskType):
        self.colormaps[mask_type] = color_map
        self.masks[mask_type].mask.setColorTable(color_map)

    def _set_pixmaps(self, image: QImage, pixmap: QPixmap, gpixmap: QGraphicsPixmapItem):
        pixmap.convertFromImage(image, Qt.MonoOnly)
        self.prepareGeometryChange()
        gpixmap.setPixmap(pixmap)

        gpixmap.setPos(QPointF(0.0, 0.0))
        gpixmap.setTransformOriginPoint(pixmap.rect().center())
        self.canvas_rect = gpixmap.boundingRect()
        gpixmap.update()
        self.scene().setSceneRect(self.canvas_rect)
        self.scene().update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.left_press.emit(event.pos())

    def set_mask_shown(self, mask_type: MaskType, is_shown: bool):
        self.mask_gpixmaps[mask_type].setVisible(is_shown)