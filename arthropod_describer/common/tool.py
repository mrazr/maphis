import abc
import typing
from typing import Dict, Tuple, List, Any, Optional

import numpy as np
from PySide2.QtCore import QPoint, Slot, QObject, Signal, QRectF, QRect
from PySide2.QtGui import QPainter, QImage, QBitmap, Qt, QRegion, QIcon, QPen, QPainterPath, QBrush
from PySide2.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget

from arthropod_describer.common.label_change import LabelChange, CommandEntry
from arthropod_describer.common.photo import LabelImg, Photo
from arthropod_describer.common.state import State
from arthropod_describer.common.user_params import UserParam

PaintCommand = typing.Callable[[QPainter], None]

class EditContext:
    def __init__(self, label_img: LabelImg, label: int, image: QImage, colormap: Dict[int, Tuple[int, int, int]],
                 label_viz: QImage, photo: Photo, label_level: int, edit_mask: np.ndarray, clip_region: Optional[QRegion], clip_mask: np.ndarray):
        self.label_img: LabelImg = label_img
        self.image = image
        self.label = label
        self.colormap = colormap
        self.label_viz = label_viz
        self.tool_viz_commands: List[Any] = []
        self.photo: Photo = photo
        self.label_level: int = label_level
        self.edit_mask: np.ndarray = edit_mask
        self.clip_region = clip_region
        self.clip_mask: np.ndarray = clip_mask


class ToolCursor(QGraphicsItem):
    def __init__(self, parent):
        QGraphicsItem.__init__(self, parent)
        self.cursor_image: QImage = QImage()
        self.cursor_shape: Qt.CursorShape = Qt.ArrowCursor
        self.cursor_pos = QPoint()
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self) -> QRectF:
        if self.cursor_image is None:
            return QRectF()
        return self.cursor_image.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget:typing.Optional[QWidget]=...):
        if self.cursor_image is None:
            return
        painter.save()
        painter.drawImage(self.boundingRect().x() - self.cursor_image.width() // 2,
                          self.boundingRect().y() - self.cursor_image.height() // 2,
                          self.cursor_image)
        painter.restore()

    def set_pos(self, pos: QPoint):
        self.cursor_pos = self.mapFromScene(pos)
        self.setPos(pos)
        #self.setVisible(True)
        self.update()

    def set_cursor(self, curs: typing.Optional[typing.Union[QImage, Qt.CursorShape]]):
        self.prepareGeometryChange()
        if curs is None:
            self.setVisible(False)
            self.cursor_image = None
        else:
            self.cursor_image = curs

    def set_shown(self, shown: bool = True):
        self.setVisible(shown)


class Tool(QObject):
    DEFAULT_AUTO_SCROLL_DISTANCE = 64

    cursor_changed = Signal([int, QImage])
    current_value = Signal(list)
    update_viz = Signal()

    def __init__(self, state: State, parent: QObject = None):
        QObject.__init__(self, parent)
        self.tool_id = -42
        self._tool_icon = None
        self.state = state

    def set_tool_id(self, tool_id: int):
        self.tool_id = tool_id

    @property
    def tool_icon(self) -> Optional[QIcon]:
        return self._tool_icon

    @property
    @abc.abstractmethod
    def tool_name(self) -> str:
        pass

    @property
    def cursor_image(self) -> Optional[typing.Union[QImage, Qt.CursorShape]]:
        return Qt.ArrowCursor

    @property
    def user_params(self) -> typing.Dict[str, UserParam]:
        return {}

    def set_user_param(self, param_name: str, value: typing.Any):
        pass

    @property
    def active(self) -> bool:
        return False

    @property
    def viz_active(self) -> bool:
        return False

    @property
    def value_storage(self) -> Optional[Any]:
        return None

    def left_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def left_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def right_press(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        lab_img = self.state.current_photo[self.state.current_label_name]
        level_img = lab_img[self.state.current_label_level]
        label = level_img[pos.y(), pos.x()]
        self.state.primary_label = label
        return None, QRect()

    def right_release(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def middle_click(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def mouse_double_click(self, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def mouse_wheel(self, delta: int, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        return None, QRect()

    def get_auto_scroll_distance(self):
        return self.DEFAULT_AUTO_SCROLL_DISTANCE

    def should_auto_scroll_with_left_button_released(self):
        return False

    def viz_left_press(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_left_release(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_right_press(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_right_release(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_mouse_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_mouse_double_click(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_mouse_wheel(self, delta: int, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_hover_enter(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_hover_leave(self, pos: QPoint) -> List[PaintCommand]:
        return []

    def viz_hover_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        return []

    @Slot(int)
    def update_primary_label(self, label: int):
        pass

    @Slot(int)
    def update_secondary_label(self, label: int):
        pass

    @Slot(dict)
    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        pass

    def reset_tool(self):
        pass

    @property
    def viz_commands(self) -> List[PaintCommand]:
        return []

    def set_out_widget(self, widg: typing.Optional[QWidget]) -> bool:
        return False


def qimage2ndarray(img: QImage) -> np.ndarray:
    img_ = img
    dtype = np.uint8
    shape = img_.size().toTuple()[::-1]
    if img.format() == QImage.Format_ARGB32:
        img_ = img.convertToFormat(QImage.Format_RGB32)
        dtype = np.uint32
    elif img.format() == QImage.Format_RGB32:
        img_ = QImage.convertToFormat(img_, QImage.Format_RGB888)
        dtype = np.uint8
        shape = shape + (3,)
    elif img.format() == QImage.Format_Grayscale8:
        dtype = np.uint8
    nd = np.frombuffer(img_.constBits(), dtype, count=img_.sizeInBytes())
    buffer = np.ascontiguousarray(nd, dtype)
    #return np.reshape(np.frombuffer(img_.constBits(), dtype), shape).astype(dtype)
    return np.reshape(buffer, shape)


def clip_mask_from_bool_nd(bin_img: np.ndarray) -> QBitmap:
    clip_mask = 255 * (bin_img > 0).astype(np.uint8)
    clip_mask = np.require(clip_mask, np.uint8, 'C')
    clip_img = QImage(clip_mask.data, clip_mask.shape[1], clip_mask.shape[0], clip_mask.strides[0],
                             QImage.Format_Grayscale8)
    clip_img.invertPixels()
    return QBitmap.fromImage(clip_img, Qt.AutoColor)


def line_command(p1: QPoint, p2: QPoint, pen: QPen) -> PaintCommand:
    def paint(painter: QPainter):
        painter.save()
        painter.setPen(pen)
        painter.drawLine(p1, p2)
        painter.restore()
    return paint


def text_command(p: QPoint, text: str, pen: QPen) -> PaintCommand:
    def paint(painter: QPainter):
        painter.save()
        painter.setPen(pen)
        painter.drawText(p, text)
        painter.restore()
    return paint


def fill_path_command(path: QPainterPath, pen: QPen, brush: QBrush) -> PaintCommand:
    def paint(painter: QPainter):
        painter.save()
        painter.setPen(pen)
        painter.fillPath(path, brush)
        painter.restore()
    return paint