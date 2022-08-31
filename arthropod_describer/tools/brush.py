import importlib.resources
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from PySide2.QtCore import QPoint, Slot, QRect
from PySide2.QtGui import QImage, QPainter, QColor, QBrush, QPen, QBitmap, QRegion, QPaintDevice, Qt, QPixmap, QIcon
from skimage import draw
import skimage.morphology as M
import qimage2ndarray

from arthropod_describer.common.photo import LabelImg
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, EditContext
from arthropod_describer.common.user_params import UserParam, ParamType
from arthropod_describer.common.label_change import LabelChange, label_difference_to_label_changes, CommandEntry

TOOL_CLASS_NAME = 'Brush'


class Tool_Brush(Tool):
    def __init__(self, state: State):
        Tool.__init__(self, state)
        self._tool_name = "Brush"
        self._user_params = {'Radius': UserParam('Radius', ParamType.INT, 9, min_val=1, max_val=75, step=2)}
        self._user_params['Radius'].default_instance.value_changed.connect(lambda e: self.cursor_changed.emit(self.tool_id, self.cursor_image))
        self._current_img = None
        self.edit_mask = QImage()
        self.edit_painter = QPainter(self.edit_mask)
        radius = self._user_params['Radius'].value

        self.state = state

        self._primary_label: int = 0
        self._secondary_label: int = 0

        self.commands: List[CommandEntry] = []
        self.label_changes: List[LabelChange] = []

        self._brush_mask: np.ndarray = M.disk(radius, np.uint16)
        self._brush_icon = QImage()
        self._brush_center = np.array([radius, radius])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center
        self.modified_coords: List[np.ndarray] = []
        self._active = False

        with importlib.resources.path("tools.icons", "brush.png") as path:
            self._tool_icon = QIcon(str(path))

        self._update_icon()

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cursor_image(self) -> QImage:
        radius = self._user_params['Radius'].value
        self._brush_mask = M.disk(radius, np.uint16)
        self._brush_center = np.array([radius, radius])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center
        self._update_icon()
        return self._brush_icon

    @property
    def user_params(self) -> Dict[str, UserParam]:
        return self._user_params

    def set_user_param(self, param_name: str, value: Any) -> Any:
        if param_name not in self._user_params.keys():
            return None
        param: UserParam = self._user_params[param_name]
        if param.param_type == ParamType.INT:
            if value % 2 == 0:
                value += 1
            self._user_params[param_name].value = value
        elif param.param_type == ParamType.BOOL:
            pass
        self._user_params[param_name].value = value
        if param_name == 'Radius':
            self.cursor_changed.emit(self.tool_id, self.cursor_image)
        return value

    def get_auto_scroll_distance(self):
        return Tool.get_auto_scroll_distance(self) + self._user_params['Radius'].value * self.state.current_view_transform.m11()

    def left_press(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        self._active = True
        self._current_img = ctx.image
        self._primary_label = ctx.label
        self.label_changes = []
        if self.edit_mask.size().toTuple() == ctx.label_img.label_image.shape[::-1]:
            self.edit_mask.fill(QColor(0, 0, 0))
        else:
            self.edit_mask = QImage(ctx.label_img.label_image.shape[1],
                                    ctx.label_img.label_image.shape[0], QImage.Format_Grayscale8)
            self.edit_mask.fill(QColor(0, 0, 0))
        return self.mouse_move(painter, pos, pos, ctx)

    def mouse_move(self, painter: QPainter, new_pos: QPoint, old_pos: QPoint, ctx: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        if not self.active:
            return None, QRect()
        if ctx.label != self._primary_label:
            self.label_changes.extend(self.get_label_changes(ctx.label_img))
            self.edit_mask.fill(QColor(0, 0, 0))
            self._primary_label = ctx.label
        #brush_color = QColor.fromRgb(*self.cmap[ctx.label])
        brush_color = QColor.fromRgb(*self.state.colormap[ctx.label])
        if ctx.label == 0:
            #brush_color = QColor.fromRgb(20, 20, 200, 255)
            brush_color = QColor(Qt.transparent)

        rr, cc = draw.line(old_pos.y(), old_pos.x(),
                           new_pos.y(), new_pos.x())

        self.paint_on(ctx.label_viz, rr, cc, QPen(brush_color), QBrush(brush_color), ctx.clip_region)
        brush_color = QColor(255, 255, 255, 255)
        self.paint_on(self.edit_mask, rr, cc, QPen(brush_color), QBrush(brush_color), ctx.clip_region)

        rad = self.user_params['Radius'].value
        top, bottom = np.min(rr) - rad, np.max(rr) + rad
        left, right = np.min(cc) - rad, np.max(cc) + rad
        return None, QRect(left, top, right - left + 1, bottom - top + 1)

    def left_release(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        self._active = False
        #edit_nd = np.squeeze(qimage2ndarray.byte_view(self.edit_mask))
        #lab_diff = np.where(edit_nd > 0, ctx.label, -1) #np.where(qimage2ndarray(self.edit_mask) > 0, ctx.label, -1)
        #lab_changes = label_difference_to_label_changes(lab_diff, ctx.label_img)
        #if len(lab_changes) == 0:
        #    return None, QRect()
        return self.get_command(ctx.label_img), QRect() #CommandEntry(lab_changes, update_canvas=False), QRect()

    def mouse_wheel(self, delta: int, painter: QPainter, pos: QPoint, context: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        my_delta = 2 if delta > 0 else -2
        curr_rad = self.user_params['Radius'].value
        new_rad = max(1, curr_rad + my_delta)
        # print(f'delta is {delta}')
        self.user_params['Radius'].value = new_rad
        self.cursor_changed.emit(self.tool_id, self.cursor_image)
        return None, QRect()

    def get_command(self, lab_img: LabelImg) -> Optional[CommandEntry]:
        edit_nd = np.squeeze(qimage2ndarray.byte_view(self.edit_mask))
        lab_diff = np.where(edit_nd > 0, self._primary_label, -1) #np.where(qimage2ndarray(self.edit_mask) > 0, ctx.label, -1)
        yy, xx = np.nonzero(lab_diff >= 0)
        top, left, bottom, right = np.min(yy), np.min(xx), np.max(yy), np.max(xx)
        # lab_diff_ = lab_diff[top:bottom+1, left:right+1]
        lab_changes = label_difference_to_label_changes(lab_diff, lab_img, (top, bottom+1, left, right+1))
        all_label_changes = self.label_changes
        self.label_changes = []
        all_label_changes.extend(lab_changes)
        if len(all_label_changes) == 0:
            return None
        return CommandEntry(all_label_changes, update_canvas=False, source=self.tool_name)

    def get_label_changes(self, lab_img: LabelImg) -> List[LabelChange]:
        edit_nd = np.squeeze(qimage2ndarray.byte_view(self.edit_mask))
        lab_diff = np.where(edit_nd > 0, self._primary_label, -1) #np.where(qimage2ndarray(self.edit_mask) > 0, ctx.label, -1)
        return label_difference_to_label_changes(lab_diff, lab_img)

    #def right_press(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> List[LabelChange]:
    #    return np.array([]), -1

    #def right_release(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> List[LabelChange]:
    #    return np.array([]), -1

    #def middle_click(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> List[LabelChange]:
    #    pass

    @property
    def active(self) -> bool:
        return self._active

    @property
    def viz_active(self) -> bool:
        return self._active

    @Slot(int)
    def update_primary_label(self, label: int):
        if not self.active:
            self._primary_label = label
        self._update_icon()

    @Slot(int)
    def update_secondary_label(self, label: int):
        self._secondary_label = label

    def _update_icon(self):
        if self.state.colormap is not None and len(self.state.colormap.keys()) > 0:
            sz = self._brush_mask.shape
            self._brush_mask = self.state.primary_label * self._brush_mask #self._primary_label * self._brush_mask
            self._brush_icon = QImage(sz[1], sz[0], QImage.Format_ARGB32)
            self._brush_icon.fill(QColor(0, 0, 0, 0))
            #brush_color = QColor.fromRgb(*self.cmap[self.state.primary_label])
            brush_color = QColor.fromRgb(*self.state.colormap[self.state.primary_label])
            painter = QPainter(self._brush_icon)
            painter.setPen(brush_color)
            radius = self.user_params['Radius'].value
            painter.setBrush(QBrush(brush_color))
            painter.drawEllipse(QPoint(radius, radius), radius, radius)

            # Add a crosshair "hole" for pipetting
            if radius > 1:
                original_composition_mode = painter.compositionMode()
                painter.setCompositionMode(painter.CompositionMode_Clear)
                painter.setPen(QColor(255, 255, 255, 0))
                painter.drawLine(radius - 2, radius, radius + 2, radius)
                painter.drawLine(radius, radius - 2, radius, radius + 2)
                painter.setCompositionMode(original_composition_mode)

    @Slot(dict)
    def color_map_changed(self, cmap: Dict[int, Tuple[int, int, int]]):
        if cmap is None:
            return
        self._update_icon()

    #@property
    #def tool_id(self) -> int:
    #    return self._tool_id

    #def set_tool_id(self, tool_id: int):
    #    self._tool_id = tool_id

    def paint_on(self, canvas: QPaintDevice, rr, cc, pen: QPen, brush: QBrush, clip_mask: Optional[QRegion]):
        painter = QPainter(canvas)
        if clip_mask is not None:
            painter.setClipRegion(clip_mask, Qt.ReplaceClip)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setPen(pen)
        painter.setBrush(brush)
        for x, y in zip(cc, rr):
            painter.drawEllipse(QPoint(x, y), self.user_params['Radius'].value,
                                self.user_params['Radius'].value)
        painter.end()
