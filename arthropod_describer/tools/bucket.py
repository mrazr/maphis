import typing

import numpy as np
from PySide2.QtCore import QPoint
from PySide2.QtGui import QImage, QPainter, QColor
from skimage.segmentation import flood

from arthropod_describer.common.label_change import LabelChange, label_difference_to_label_changes
from arthropod_describer.common.tool import Tool, EditContext
from arthropod_describer.common.user_params import ToolUserParam

TOOL_CLASS_NAME = 'Bucket'


class Tool_Bucket(Tool):
    def __init__(self):
        Tool.__init__(self)
        self._tool_id = -1
        self.cmap = None
        self._secondary_label = None
        self._primary_label = None
        self._tool_name = 'Bucket'

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cursor_image(self) -> QImage:
        return QImage()

    @property
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        return {}

    def set_user_param(self, param_name: str, value: typing.Any):
        pass

    @property
    def active(self) -> bool:
        return False

    def update_primary_label(self, label: int):
        self._primary_label = label

    def update_secondary_label(self, label: int):
        self._secondary_label = label

    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        if cmap is None:
            return
        self.cmap = cmap

    def left_release(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> typing.List[LabelChange]:
        picked_label = ctx.label_img.label_img[pos.y(), pos.x()]
        # TODO should probably make distinction between connectivity for bg and fg, definitely
        flood_mask = flood(ctx.label_img.label_img, pos.toTuple()[::-1], connectivity=1)
        flood_coords = np.nonzero(flood_mask)
        lab_change = LabelChange(np.nonzero(flood_mask), ctx.label, picked_label, ctx.label_img.label_type)
        color = QColor(*ctx.colormap[ctx.label]).rgba()
        for y, x in zip(*flood_coords):
            ctx.label_viz.setPixel(x, y, color)

        return [lab_change]
