import typing

from PySide2.QtCore import QPointF, Signal, QRectF, QPoint, Slot
from PySide2.QtGui import QPixmap, QColor, QImage, QPainter, Qt, QCursor, QBrush
from PySide2.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsPixmapItem, QGraphicsSceneMouseEvent, \
    QStyleOptionGraphicsItem, QWidget, QGraphicsObject, QGraphicsSceneHoverEvent
import numpy as np
from skimage import draw

from tools.tool import Tool
from mask_widget import MaskWidget
from model.photo import Photo, Mask, MaskType


class EditableMask:
    def __init__(self):
        self._mask: typing.Optional[Mask] = None
        self._colormap = None

    def set_mask(self, mask: Mask, colormap):
        self._mask = mask
        self._colormap = colormap


class ToolCursor(QGraphicsItem):
    def __init__(self, parent):
        QGraphicsItem.__init__(self, parent)
        self.cursor_image: QImage = QImage()
        self.cursor_pos = QPoint()
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self) -> QRectF:
        return self.cursor_image.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget:typing.Optional[QWidget]=...):
        #painter.drawImage(self.cursor_pos.x() - self.cursor_image.width() // 2,
        #                  self.cursor_pos.y() - self.cursor_image.height() // 2,
        #                  self.cursor_image)
        painter.drawImage(self.boundingRect().x() - self.cursor_image.width() // 2,
                          self.boundingRect().y() - self.cursor_image.height() // 2,
                          self.cursor_image)

    def set_pos(self, pos: QPoint):
        self.cursor_pos = self.mapFromScene(pos)
        self.setPos(pos)
        self.setVisible(False)
        self.update()

    def set_cursor(self, curs: QImage):
        self.prepareGeometryChange()
        self.cursor_image = curs


class CanvasWidget(QGraphicsObject):
    left_press = Signal(QPointF)
    right_press = Signal()
    wheel_press = Signal()
    wheel_move = Signal()

    def __init__(self, parent=None):
        QGraphicsObject.__init__(self, parent)
        self._current_tool: typing.Optional[Tool] = None
        self.photo: typing.Optional[Photo] = None

        self.masks: typing.Optional[typing.Dict[MaskType, Mask]] = None
        self.colormaps = {MaskType.BUG: [],
                          MaskType.REGIONS: [],
                          MaskType.REFLECTION: []}

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

        self.cursor_image: typing.Optional[QImage] = None

        self.cur_mouse_pos: QPoint = QPoint()
        self.setAcceptHoverEvents(True)

        self.cursor__ = None
        #self.setCursor(QCursor(Qt.CursorShape.BlankCursor))

    def initialize(self):
        self._image_pixmap = QPixmap()
        self.image_gpixmap = self.scene().addPixmap(self._image_pixmap)
        self.image_gpixmap.setZValue(0)

        self._mask_pixmap = QPixmap()
        self._mask_gpixmap = self.scene().addPixmap(self._mask_pixmap)
        self._mask_gpixmap.setZValue(1)

        self._segments_pixmap = QPixmap()
        self._segments_gpixmap = self.scene().addPixmap(self._segments_pixmap)
        self._segments_gpixmap.setZValue(2)

        self._reflection_pixmap = QPixmap()
        self._reflection_gpixmap = self.scene().addPixmap(self._reflection_pixmap)
        self._reflection_gpixmap.setZValue(3)

        self.mask_pixmaps: typing.Dict[MaskType, QPixmap] = {
            MaskType.BUG: self._mask_pixmap,
            MaskType.REGIONS: self._segments_pixmap,
            MaskType.REFLECTION: self._reflection_pixmap
        }

        self.mask_gpixmaps: typing.Dict[MaskType, QGraphicsPixmapItem] = {
            MaskType.BUG: self._mask_gpixmap,
            MaskType.REGIONS: self._segments_gpixmap,
            MaskType.REFLECTION: self._reflection_gpixmap
        }

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[MaskType.BUG] = mask_w
        mask_w.setPos(0, 0)
        mask_w.setZValue(1)

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[MaskType.REGIONS] = mask_w
        mask_w.setPos(0, 0)
        mask_w.setZValue(2)

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[MaskType.REFLECTION] = mask_w
        mask_w.setPos(0, 0)
        mask_w.setZValue(3)

        self.cursor__ = ToolCursor(None)
        self.scene().addItem(self.cursor__)
        self.cursor__.setPos(0, 0)
        self.cursor__.setZValue(10)

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
            self.mask_widgets[mask_type].set_mask_image(self.masks[mask_type].mask)
            self.mask_widgets[mask_type].set_color_map([QColor.fromRgb(*np.random.randint(0, 255, (3,)), 150).rgba()])

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
        gpixmap.setZValue(0)
        self.scene().setSceneRect(self.canvas_rect)
        self.scene().update()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        self.left_press.emit(event.scenePos())
        if event.buttons() & Qt.MouseButton.MiddleButton == 0:
            if self._current_tool is not None:
                img = self.mask_widgets[MaskType.BUG]._mask_image
                painter = QPainter(self.mask_widgets[MaskType.BUG]._mask_image)
                painter.setBrush(QBrush(img.color(1)))
                painter.drawEllipse(event.pos(), self._current_tool.user_params['radius'].value,
                                    self._current_tool.user_params['radius'].value)
                #pos = self.mapFromScene(event.scenePos())
                #coords = self._current_tool.left_press(pos.toPoint().toTuple(),
                #                                       None, 1)
                #mask = self.mask_widgets[MaskType.BUG]
                #for x, y in coords:
                #    mask._mask_image.setPixel(x, y, 1)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        img = self.mask_widgets[MaskType.BUG]._mask_image
        painter = QPainter(self.mask_widgets[MaskType.BUG]._mask_image)
        painter.setBrush(QBrush(img.color(1)))
        old_pos = event.lastPos().toPoint()
        new_pos = event.pos().toPoint()
        rr, cc = draw.line(old_pos.y(), old_pos.x(),
                           new_pos.y(), new_pos.x())
        for x, y in zip(cc, rr):
            print("OOOO")
            painter.drawEllipse(QPoint(x, y), self._current_tool.user_params['radius'].value,
                                self._current_tool.user_params['radius'].value)
        if self._current_tool is not None:
            if self._current_tool.active:
                self.cur_mouse_pos = self.cursor__.mapFromScene(event.scenePos().toPoint())
                self.cursor__.set_pos(event.scenePos())

                img = self.mask_widgets[MaskType.BUG]._mask_image
                painter = QPainter(self.mask_widgets[MaskType.BUG]._mask_image)
                painter.setBrush(QBrush(img.color(1)))
                old_pos = event.lastPos().toPoint()
                new_pos = event.pos().toPoint()
                rr, cc = draw.line(old_pos.y(), old_pos.x(),
                                        new_pos.y(), new_pos.x())
                for x, y in zip(cc, rr):
                    print("OOOO")
                    painter.drawEllipse(QPoint(x, y), self._current_tool.user_params['radius'].value,
                                        self._current_tool.user_params['radius'].value)
                #print(f'coords len {len(coords)}')
                ##coords = self._current_tool.mouse_move(event.pos().toPoint().toTuple(),
                ##                                       event.lastPos().toPoint().toTuple(),
                ##                                       1)
                #mask = self.mask_widgets[MaskType.BUG]
                #for x, y in coords:
                #    mask._mask_image.setPixel(x, y, 1)
                super().mouseMoveEvent(event)
            else:
                super().mouseMoveEvent(event)
            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._current_tool is not None:
            self._current_tool.left_release(event.pos().toPoint().toTuple(), 1)
            super().mouseReleaseEvent(event)
        #self.cursor__.setVisible(True)
        #self.cursor__.update()
        #self.update()
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self.cursor__.setVisible(True)
        self.update()

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        self.cur_mouse_pos = event.pos().toPoint()
        self.cursor__.set_pos(self.cur_mouse_pos)
        self.update()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.cursor__.setVisible(False)
        self.update()

    def set_current_tool(self, tool: Tool):
        self._current_tool = tool
        crs = self._current_tool.cursor_image
        bytess = crs.tobytes()
        #self.cursor_image = QImage(bytess, crs.shape[1], crs.shape[0], QImage.)
        sz = tool.cursor_image.shape
        self.cursor_image = QImage(tool.cursor_image.data, sz[1], sz[0], sz[1], QImage.Format_Grayscale8)
        self.cursor__.set_cursor(self.cursor_image)
        self.update()

    def set_mask_shown(self, mask_type: MaskType, is_shown: bool):
        #self.mask_gpixmaps[mask_type].setVisible(is_shown)
        self.mask_widgets[mask_type].setVisible(is_shown)

    @Slot(bool, QPoint)
    def handle_view_dragging(self, dragging: bool, mouse_pos: QPoint):
        print("handle view drag")
        self.cursor__.set_pos(mouse_pos)
        self.cursor__.setVisible(not dragging)
        self.update()
