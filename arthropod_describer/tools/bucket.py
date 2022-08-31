import importlib.resources
import typing
from typing import Tuple, Optional

import numpy as np
from PySide2.QtCore import QPoint, QRect
from PySide2.QtGui import QImage, QPainter, QColor, QRegion, QIcon, Qt
from skimage.segmentation import flood

from arthropod_describer.common.label_change import label_difference_to_command, CommandEntry, compute_label_difference
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, EditContext, clip_mask_from_bool_nd
from arthropod_describer.common.user_params import UserParam

TOOL_CLASS_NAME = 'Bucket'


class Tool_Bucket(Tool):
    def __init__(self, state: State):
        Tool.__init__(self, state)
        self._tool_id = -1
        self.cmap = None
        self._secondary_label = None
        self._primary_label = None
        self._tool_name = 'Bucket'
        with importlib.resources.path("tools.icons", "paint-bucket.png") as path:
            self._tool_icon = QIcon(str(path))

    @property
    def tool_name(self) -> str:
        return self._tool_name

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

    def update_primary_label(self, label: int):
        self._primary_label = label

    def update_secondary_label(self, label: int):
        self._secondary_label = label

    def color_map_changed(self, cmap: typing.Dict[int, typing.Tuple[int, int, int]]):
        if cmap is None:
            return
        self.cmap = cmap

    def left_release(self, painter: QPainter, pos: QPoint, ctx: EditContext) -> Tuple[Optional[CommandEntry], QRect]:
        picked_label = ctx.label_img[ctx.label_level][pos.y(), pos.x()]
        if picked_label == ctx.label or \
                (ctx.label_level > 0 and ctx.edit_mask[pos.y(), pos.x()] > 0): # In edit_mask, pixels with value 0 are pixels we are not allowed to modify.
                #(ctx.label_img.label_type != LabelType.BUG and ctx.photo.bug_mask.label_img[pos.y(), pos.x()] == 0):
            return None, QRect()
        if ctx.edit_mask is not None: # TODO 0 label does not respect label image
            label_img_negative_bg = np.where(ctx.edit_mask == 0, ctx.label_img[ctx.label_level], -1)
            flood_mask = flood(label_img_negative_bg, pos.toTuple()[::-1], connectivity=1)
        else:
            flood_mask = flood(ctx.label_img.label_image, pos.toTuple()[::-1], connectivity=1)
        new_label = np.where(flood_mask > 0, ctx.label, ctx.label_img.label_image)
        lab_diff = compute_label_difference(ctx.label_img.label_image, new_label)

        color = QColor(*ctx.colormap[ctx.label])
        if ctx.label == 0:
            color.setAlpha(0)

        flood_bitmap = clip_mask_from_bool_nd(flood_mask)
        clip_reg = QRegion(flood_bitmap)
        painter = QPainter(ctx.label_viz)
        painter.setClipRegion(clip_reg)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(0, 0, ctx.label_img.label_image.shape[1], ctx.label_img.label_image.shape[0],
                         color)
        painter.end()
        cmd = label_difference_to_command(lab_diff, ctx.label_img)
        cmd.source = self.tool_name
        bbox = cmd.bbox
        return cmd, QRect(bbox[2], bbox[0], bbox[2]+bbox[3]+1, bbox[0]+bbox[1]+1)
