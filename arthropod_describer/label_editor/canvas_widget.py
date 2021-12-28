import typing

from PySide2.QtCore import QPointF, Signal, QRectF, QPoint, Slot
from PySide2.QtGui import QPixmap, QImage, QPainter, Qt, QBrush, QBitmap, QRegion
from PySide2.QtWidgets import QGraphicsItem, QGraphicsPixmapItem, QGraphicsSceneMouseEvent, \
    QStyleOptionGraphicsItem, QWidget, QGraphicsObject, QGraphicsSceneHoverEvent
import numpy as np

from arthropod_describer.common.colormap import Colormap
from arthropod_describer.common.state import State
from arthropod_describer.tools.tool import Tool
from arthropod_describer.label_editor.mask_widget import MaskWidget
from arthropod_describer.common.photo import Photo, LabelImg, LabelType


class EditableMask:
    def __init__(self):
        self._mask: typing.Optional[LabelImg] = None
        self._colormap = None

    def set_mask(self, mask: LabelImg, colormap):
        self._mask = mask
        self._colormap = colormap


class ToolCursor(QGraphicsItem):
    def __init__(self, parent):
        QGraphicsItem.__init__(self, parent)
        self.cursor_image: QImage = QImage()
        self.cursor_pos = QPoint()
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self) -> QRectF:
        if self.cursor_image is None:
            return QRectF()
        return self.cursor_image.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget:typing.Optional[QWidget]=...):
        painter.save()
        painter.drawImage(self.boundingRect().x() - self.cursor_image.width() // 2,
                          self.boundingRect().y() - self.cursor_image.height() // 2,
                          self.cursor_image)
        painter.restore()

    def set_pos(self, pos: QPoint):
        self.cursor_pos = self.mapFromScene(pos)
        self.setPos(pos)
        self.setVisible(True)
        self.update()

    def set_cursor(self, curs: typing.Optional[QImage]):
        self.prepareGeometryChange()
        if curs is None:
            self.setVisible(False)
        self.cursor_image = curs


class CanvasWidget(QGraphicsObject):
    left_press = Signal(QPointF)
    right_press = Signal()
    wheel_press = Signal()
    wheel_move = Signal()
    label_changed = Signal(np.ndarray)

    def __init__(self, state: State, parent=None):
        QGraphicsObject.__init__(self, parent)
        self.state = state
        self._current_tool: typing.Optional[Tool] = None
        self.photo: typing.Optional[Photo] = None

        self.masks: typing.Optional[typing.Dict[LabelType, LabelImg]] = None
        self.colormaps = {LabelType.BUG: [],
                          LabelType.REGIONS: [],
                          LabelType.REFLECTION: []}

        self._image_pixmap = None
        self.image_gpixmap = None

        self._mask_pixmap = None
        self.mask_gpixmap = None

        self._segments_pixmap = None
        self.segments_gpixmap = None

        self._reflection_pixmap = None
        self._reflection_gpixmap = None

        self.mask_pixmaps: typing.Dict[LabelType, QPixmap] = {}

        self.mask_gpixmaps: typing.Dict[LabelType, QGraphicsPixmapItem] = {}

        self.mask_widgets: typing.Dict[LabelType, MaskWidget] = {}

        self.canvas_rect = QRectF()

        self.cursor_image: typing.Optional[QImage] = None

        self.cur_mouse_pos: QPoint = QPoint()
        self.setAcceptHoverEvents(True)

        self.cursor__: typing.Optional[ToolCursor] = None
        self.current_mask_shown: LabelType = LabelType.BUG
        self.clip_mask: QBitmap = QBitmap()
        self._clip_nd: np.ndarray = None
        self._clip_qimg = QImage()
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

        self.mask_pixmaps: typing.Dict[LabelType, QPixmap] = {
            LabelType.BUG: self._mask_pixmap,
            LabelType.REGIONS: self._segments_pixmap,
            LabelType.REFLECTION: self._reflection_pixmap
        }

        self.mask_gpixmaps: typing.Dict[LabelType, QGraphicsPixmapItem] = {
            LabelType.BUG: self._mask_gpixmap,
            LabelType.REGIONS: self._segments_gpixmap,
            LabelType.REFLECTION: self._reflection_gpixmap
        }

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[LabelType.BUG] = mask_w
        mask_w.setPos(0, 0)
        mask_w.setZValue(1)

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[LabelType.REGIONS] = mask_w
        mask_w.setPos(0, 0)
        mask_w.setZValue(2)

        mask_w = MaskWidget()
        self.scene().addItem(mask_w)
        self.mask_widgets[LabelType.REFLECTION] = mask_w
        mask_w.setPos(0, 0)
        mask_w.setZValue(3)

        self.cursor__ = ToolCursor(None)
        self.scene().addItem(self.cursor__)
        self.cursor__.setPos(0, 0)
        self.cursor__.setZValue(10)

        self.state.photo_changed.connect(self.set_photo)
        self.state.colormap_changed.connect(self._handle_colormap_changed)

    def boundingRect(self) -> QRectF:
        if self.photo is not None:
            return self.canvas_rect
        return QRectF()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget:typing.Optional[QWidget]=...):
        pass

    def set_photo(self, photo: Photo):
        self.photo = photo

        self.masks = self.photo.label_dict

        self._set_pixmaps(photo.image, self._image_pixmap, self.image_gpixmap)

        for mask_type in self.masks.keys():
            self.mask_gpixmaps[mask_type].setVisible(False)
            self.mask_widgets[mask_type].set_mask_image(self.masks[mask_type])
            #mw = self.mask_widgets[mask_type]._mask_image

            #cmap = [QColor.fromRgb(*np.random.randint(0, 255, (3,)), 150).rgba() for _ in range(256)] #for _ in range(self.mask_widgets[mask_type]._mask_image.colorCount())]
            #self.mask_widgets[mask_type].set_color_map(cmap)
            #self.cursor__.cursor_image.setColorTable(cmap)
            #print(mw.format())
            #print(mw.colorCount())
            #print(mw.colorTable())
            #self.colormaps[mask_type] = cmap
            #self.setVisible(True)
            #self.cursor__.update()
        self.update_clip_mask()
        self.set_mask_shown(self.current_mask_shown, True)

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
                painter = QPainter(self.mask_widgets[self.current_mask_shown]._mask_image)
                if self.current_mask_shown != LabelType.BUG:
                    clip_region = QRegion(self.clip_mask)
                    painter.setClipRegion(clip_region, Qt.ClipOperation.ReplaceClip)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                self._current_tool.left_press(painter, event.pos().toPoint(),
                                              self.mask_widgets[self.current_mask_shown]._mask_image, 1)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        img = self.mask_widgets[LabelType.BUG]._mask_image
        if self._current_tool is not None:
            painter = QPainter(self.mask_widgets[self.current_mask_shown]._mask_image)
            painter.setBrush(QBrush(img.color(1)))
            old_pos = event.lastPos().toPoint()
            new_pos = event.pos().toPoint()
            if self.current_mask_shown != LabelType.BUG:
                clip_region = QRegion(self.clip_mask)
                painter.setClipRegion(clip_region, Qt.ClipOperation.ReplaceClip)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            self._current_tool.mouse_move(painter, new_pos, old_pos, 1)
            self.cursor__.set_pos(event.scenePos())
            self.update()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if self._current_tool is not None:
            img = self.mask_widgets[self.current_mask_shown]._mask_image
            painter = QPainter(img)
            if self.current_mask_shown != LabelType.BUG:
                pass
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            # `edit_img` is an integer img, where non-zero elements denote pixels that were painted currently, and their integer value
            # denotes the label that was assigned to those pixels
            edit_img, label = self._current_tool.left_release(painter, event.pos().toPoint().toTuple(), 1)
            lab_img = self.photo.label_dict[self.current_mask_shown].label_img.astype(np.uint8)
            self.label_changed.emit(edit_img)
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        if self._current_tool is None:
            return
        self.cursor__.setVisible(True)
        self.update()

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        if self._current_tool is None:
            return
        self.cur_mouse_pos = event.pos().toPoint()
        self.cursor__.set_pos(self.cur_mouse_pos)
        self.update()

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        if self._current_tool is None:
            return
        self.cursor__.setVisible(False)
        self.update()

    def set_current_tool(self, tool: Tool):
        self._current_tool = tool
        #self.cursor_image = QImage(bytess, crs.shape[1], crs.shape[0], QImage.)
        self.cursor_image = self._current_tool.cursor_image #QImage(tool.cursor_image.data, sz[1], sz[0], sz[1], QImage.Format_Grayscale16)
        self.cursor_image.setColorTable(self.colormaps[LabelType.BUG])
        self.cursor__.set_cursor(self.cursor_image)
        self.cursor__.setOpacity(0.25)
        self.update()

    def set_mask_shown(self, mask_type: LabelType, is_shown: bool):
        #self.mask_gpixmaps[mask_type].setVisible(is_shown)
        self.mask_widgets[mask_type].setVisible(is_shown)
        self.mask_widgets[mask_type].setOpacity(0.25)
        if self.masks is None:
            print("away")
            return
        if is_shown:
            print(f'setting cmap for {mask_type}')
            self.current_mask_shown = mask_type
            #self.cursor__.cursor_image.setColorTable(self.colormaps[mask_type])
            #self._current_tool.color_map_changed(self.masks[mask_type].color_map)
            if self._current_tool is not None:
                self.cursor__.set_cursor(self._current_tool.cursor_image)
            else:
                self.cursor__.set_cursor(None)
            #print(f'cmap for cursor is now {self.cursor__.cursor_image.colorTable()}')
            #if mask_type == LabelType.BUG:
            #    self.mask_widgets[LabelType.BUG]._mask_image.save(f'/home/radoslav/mask_bug.png')
            #elif mask_type == LabelType.REGIONS:
            #    self.mask_widgets[LabelType.REGIONS]._mask_image.save(f'/home/radoslav/mask_reg.png')
            #else:
            #    self.mask_widgets[LabelType.REFLECTION]._mask_image.save(f'/home/radoslav/mask_reflection.png')
            print(f'cmap is {self.masks[mask_type].color_map}')

    @Slot(bool, QPoint)
    def handle_view_dragging(self, dragging: bool, mouse_pos: QPoint):
        print("handle view drag")
        self.cursor__.set_pos(mouse_pos)
        self.cursor__.setVisible(not dragging)
        self.update()
    
    def update_label(self, label_type: LabelType):
        self.mask_widgets[label_type].set_mask_image(self.masks[label_type])
        if label_type == LabelType.BUG:
            self.update_clip_mask()

    def update_clip_mask(self):
        clip_mask = 255 * (self.photo.bug_mask.label_image > 0).astype(np.uint8)
        self._clip_nd = np.require(clip_mask, np.uint8, 'C')
        #io.imsave('/home/radoslav/clip_np.png', self._clip_nd)
        self._clip_qimg = QImage(self._clip_nd.data, self._clip_nd.shape[1], self._clip_nd.shape[0], self._clip_nd.strides[0], QImage.Format_Grayscale8)
        self._clip_qimg.invertPixels()
        #self._clip_qimg.save('/home/radoslav/clip_mask.png')
        self.clip_mask = QBitmap.fromImage(self._clip_qimg, Qt.AutoColor)

    def _handle_colormap_changed(self, colormap: Colormap):
        for mask_widget in self.mask_widgets.values():
            mask_widget.set_color_map(colormap)