import time
import typing
from typing import Optional

import cv2
import numba
import numpy as np
import qimage2ndarray
from PySide2.QtCore import QRectF, Signal, QTimer
from PySide2.QtGui import QImage, QPainter, QColor, Qt, QBitmap, QRegion, QBrush, QTransform
from PySide2.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem, QGraphicsSceneMouseEvent, \
    QGraphicsObject, QGraphicsSceneHoverEvent
from cv2 import cv2
from scipy import ndimage
from skimage import morphology as M

from arthropod_describer.common.label_change import CommandEntry
from arthropod_describer.common.photo import LabelImg
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, EditContext, ToolCursor


class LabelView(QGraphicsObject):
    label_img_modified = Signal(CommandEntry)
    label_picked = Signal(int)
    label_hovered = Signal(int)

    def __init__(self, state: State, label_name: str):
        QGraphicsObject.__init__(self)
        self.viz_clip_region: QRegion = QRegion()
        self.viz_mask: QBitmap = None
        self.viz_mask_buffer: QImage = QImage()
        self.viz_mask_nd: np.ndarray = None
        self._label_img: LabelImg = None
        self._label_qimage: typing.Optional[QImage] = None
        self._nd_img = None
        # self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.setAcceptHoverEvents(True)
        self.state: State = state
        self.showing_full_mask: bool = True
        self.outline_1px_nd: np.ndarray = None
        self.outline_nd: np.ndarray = None
        self.outline_mask: QBitmap = QBitmap()
        self.outline_mask_buffer: QImage = QImage()
        self.outline_width: int = 3

        self.current_tool: typing.Optional[Tool] = None
        self.tool_cursor: Optional[ToolCursor] = None

        self.clip_region: QRegion = QRegion()
        self._clip_nd: np.ndarray = None
        self._clip_qimg = QImage()
        self.clip_mask = QBitmap()

        self.restricted_clip_region: QRegion = QRegion()

        #self.constraint_level: int = -1
        #self.label_name: str = label_name

        self.tool_viz_commands = []
        self.brush_offset_idx: int = 0
        self.offset_time: int = 0
        self.marching_ants_timer = QTimer(self)
        self.marching_ants_timer.setInterval(500)
        self.marching_ants_timer.timeout.connect(self.update)

        self.march_ant_texture: QImage = QImage(32, 32, QImage.Format_Mono)
        #painter = QPainter(self.march_ant_texture)
        #painter.fillRect(self.march_ant_texture.rect(), Qt.GlobalColor.black)
        #painter.fillRect(self.march_ant_texture.rect(), QBrush())
        #painter.setBrush()
        self.state.new_label_constraint.connect(self.adapt_to_constraint)

    def adapt_to_constraint(self, _):
        self.compute_clip_mask()
        self.compute_viz_mask()

    def set_tool(self, tool: Tool, tool_cursor: Optional[ToolCursor]):
        self.current_tool = tool
        self.tool_cursor = tool_cursor

    def set_label_name(self, label_name: str):
        lbl = self.state.current_photo[label_name]
        level = self.state.current_label_level
        self.set_label_image(lbl, level)

    def set_label_image(self, mask: LabelImg, level: int):
        self.prepareGeometryChange()
        self._label_img = mask
        #self.setTransformOriginPoint(mask.size[1] * 0.5, mask.size[0] * 0.5)
        self._recolor_image()
        now = time.time()
        self.compute_clip_mask()
        print(f'computing clip mask took {time.time() - now} secs')
        now = time.time()
        self.outline_nd = 0 * np.ones_like(self.state.current_photo[self.state.current_label_name].label_image,
                                           dtype=np.uint8)
        print(f'outline_nd took {time.time() - now} secs')
        if not self.showing_full_mask:
            self.draw_outline()
        now = time.time()
        self.compute_viz_mask()
        print(f'computing viz mask took {time.time() - now} secs')

    #def set_color_map(self, colormap: ColormapItemModel):
    #    self._colormap = colormap
    #    self._recolor_image()
    #    self.update()

    def _recolor_image(self):
        if self._label_img is None or not self._label_img.is_set:
            self._label_qimage = None
            return
        if self._nd_img is None or self._label_img.label_image.shape != self._nd_img.shape:
            self._nd_img = np.zeros(self.state.current_photo[self.state.current_label_name].label_image.shape + (1,), np.uint32)
            self.outline_mask_buffer = QImage(self._nd_img.shape[1], self._nd_img.shape[0], QImage.Format_Mono)
        else:
            self._nd_img[:, :] = 0
            self.outline_mask_buffer.fill(1)
        level_img = self.state.current_photo[self.state.current_label_name][self.state.current_label_level]
        used_labels = np.unique(level_img)
        cmap = {label: QColor.fromRgb(*self.state.colormap[label]).rgba() for label in used_labels}
        if 0 in used_labels:
            cmap[0] = QColor(0, 0, 0, 0).rgba()
        for label in used_labels:
            coords = np.nonzero(level_img == label)
            self._nd_img[coords] = cmap[label]
        self._label_qimage = QImage(self._nd_img.data,
                                    self._nd_img.shape[1], self._nd_img.shape[0],
                                    4 * self._nd_img.shape[1], QImage.Format_ARGB32)
        # self.outline_mask = QImage(self._nd_img.shape[1], self._nd_img.shape[0], QImage.Format_Grayscale8)
        self.update()

    def boundingRect(self):
        if self._label_qimage is None:
            return QRectF()
        return self._label_qimage.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: typing.Optional[QWidget] = ...):
        if self._label_qimage is not None:
            painter.save()
            if self.viz_mask is not None:
                painter.setClipRegion(self.viz_clip_region, Qt.ReplaceClip)
            #if not self.showing_full_mask:
            #    reg = QRegion(self.outline_mask)
            #    painter.setClipRegion(reg, Qt.ReplaceClip)
            painter.drawImage(option.rect, self._label_qimage)
            #if not self.showing_full_mask:
            #    painter.setBrush(QBrush(QColor.fromRgb(0, 0, 0, 125), Qt.FDiagPattern))
            #    if time.time() - self.offset_time > 0.1:
            #        self.brush_offset_idx = (self.brush_offset_idx + 1) % 8
            #        self.offset_time = time.time()
            #        painter.setBrushOrigin(self.brush_offset_idx * 10, 0)
            #    painter.fillRect(self.boundingRect(), painter.brush())
            painter.setClipRegion(self.restricted_clip_region, Qt.ReplaceClip)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            painter.fillRect(self.boundingRect(), QBrush(QColor.fromRgb(0, 0, 0, 200))) #, Qt.Dense5Pattern))
            painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
            painter.restore()
            if len(self.tool_viz_commands) > 0:
                for viz_cmd in self.tool_viz_commands:
                    viz_cmd(painter)

    def switch_label_level(self, level: int):
        self._recolor_image()
        if not self.showing_full_mask:
            self.draw_outline()
        #self.compute_clip_mask()
        #mask_level = self.state.current_label_level - 1 if self.state.current_label_level > 0 else 0
        #if self.state.current_label_level == 0 and False:
        #    clip_mask = 255 * np.ones_like(self.state.current_photo.regions_image.label_img, dtype=np.uint8)
        #    self._clip_nd = np.require(clip_mask, np.uint8, 'C')
        #    self._clip_qimg = QImage(self._clip_nd.data, self._clip_nd.shape[1], self._clip_nd.shape[0],
        #                             self._clip_nd.strides[0], QImage.Format_Grayscale8)
        #else:
        #    mask = self.state.current_photo.regions_image[mask_level]
        #    clip_mask = 255 * (mask > 0).astype(np.uint8)
        #    self._clip_nd = np.require(clip_mask, np.uint8, 'C')
        #self._clip_qimg = QImage(self._clip_nd.data, self._clip_nd.shape[1], self._clip_nd.shape[0],
        #                         self._clip_nd.strides[0], QImage.Format_Grayscale8)
        #self._clip_qimg.invertPixels()
        #self.clip_mask = QBitmap.fromImage(self._clip_qimg, Qt.AutoColor)
        #self.clip_region = QRegion(self.clip_mask)

    def draw_outline(self, bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None, compute_from_viz: bool = True):
        print('redraw outline - START')
        now = time.time()
        level_img = self.state.current_photo[self.state.current_label_name][self.state.current_label_level]
        #print(f'lv took {time.time() - now}')
        if bbox is not None:
            bbox = list(bbox)
            bbox[0] -= 10
            bbox[1] += 10
            bbox[2] -= 10
            bbox[3] += 10
            if compute_from_viz:
                level_img = qimage2ndarray.raw_view(self._label_qimage.copy(bbox[2], bbox[0],
                                                                            bbox[3] - bbox[2] + 1, bbox[1] - bbox[0] + 1))
            else:
                level_img = level_img[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            outline = compute_outline(level_img).astype(np.uint8)
            self.outline_1px_nd[bbox[0]+9:bbox[1] - 10 + 1, bbox[2]+9:bbox[3] - 10 + 1] = outline[9:-10, 9:-10]
            selem = M.diamond(1)
            if self.outline_width > 1:
                self.outline_nd = cv2.morphologyEx(self.outline_1px_nd, cv2.MORPH_ERODE,
                                                   selem,
                                                   # cv2.getStructuringElement(cv2.MORPH_CROSS,
                                                   #                          2 * (2 * self.outline_width + 1,)),
                                                   borderType=cv2.BORDER_CONSTANT, borderValue=0,
                                                   iterations=self.outline_width-1)
            else:
                self.outline_nd = self.outline_1px_nd
            self.outline_mask_buffer = QImage(self.outline_nd.data, self.outline_nd.shape[1], self.outline_nd.shape[0],
                                              self.outline_nd.strides[0], QImage.Format_Grayscale8)
            self.outline_mask = QBitmap.fromImage(self.outline_mask_buffer, Qt.MonoOnly)
        else:
            if compute_from_viz:
                level_img = qimage2ndarray.raw_view(self._label_qimage)
            self.outline_1px_nd = compute_outline(level_img).astype(np.uint8)
            selem = M.diamond(1)
            if self.outline_width > 1:
                self.outline_nd = cv2.morphologyEx(self.outline_1px_nd, cv2.MORPH_ERODE,
                                                   selem,
                                                   #cv2.getStructuringElement(cv2.MORPH_CROSS,
                                                   #                          2 * (2 * self.outline_width + 1,)),
                                                   borderType=cv2.BORDER_CONSTANT, borderValue=0,
                                                   iterations=self.outline_width-1)
            else:
                self.outline_nd = self.outline_1px_nd
            self.outline_mask_buffer = QImage(self.outline_nd.data, self.outline_nd.shape[1], self.outline_nd.shape[0],
                                              self.outline_nd.strides[0], QImage.Format_Grayscale8)
            self.outline_mask = QBitmap.fromImage(self.outline_mask_buffer, Qt.MonoOnly)
        self.compute_viz_mask(bbox)
        self.update()

    def handle_outline_width_changed(self, value: int):
        if value == self.outline_width:
            return
        selem = M.diamond(1)
        if value > 1:
            self.outline_nd = cv2.morphologyEx(self.outline_1px_nd, cv2.MORPH_ERODE, selem, iterations=value-1)
        else:
            self.outline_nd = self.outline_1px_nd
        self.outline_mask_buffer = QImage(self.outline_nd.data, self.outline_nd.shape[1], self.outline_nd.shape[0],
                                          self.outline_nd.shape[1], QImage.Format_Grayscale8)
        self.outline_mask = QBitmap.fromImage(self.outline_mask_buffer, Qt.MonoOnly)
        self.outline_width = value
        self.compute_viz_mask()
        self.update()

    def show_outline(self):
        self.draw_outline()
        self.showing_full_mask = False
        #self.compute_viz_mask()
        #if not self.marching_ants_timer.isActive():
        #    self.marching_ants_timer.start()

    def show_mask(self):
        self._recolor_image()
        self.outline_nd = np.zeros_like(self._label_img.label_image, dtype=np.uint8)
        self.compute_viz_mask()
        self.showing_full_mask = True
        #if self.marching_ants_timer.isActive():
        #    self.marching_ants_timer.stop()

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            QGraphicsItem.mousePressEvent(self, event)
            return
        elif event.button() & Qt.LeftButton:
            if self.current_tool is not None:
                hovered_label = self.state.current_photo[self.state.current_label_name][self.state.current_label_level][event.pos().toPoint().toTuple()[::-1]]

                self.current_tool.left_press(None, event.pos().toPoint(), self._create_context())
            self.update()
        # QGraphicsItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() & Qt.RightButton:
            return
        elif event.buttons() & Qt.LeftButton:
            if self.current_tool is not None:
                ctx = self._create_context()
                _, rect = self.current_tool.mouse_move(None, event.pos().toPoint(),
                                             event.lastPos().toPoint(),
                                             ctx)
                bbox = [rect.top(), rect.top() + rect.height(),
                        rect.left(), rect.left() + rect.width()]
                self.tool_viz_commands = ctx.tool_viz_commands
                if not self.showing_full_mask:
                    self.draw_outline(bbox)
                if self.tool_cursor is not None:
                    self.tool_cursor.setPos(event.pos())
                    self.tool_cursor.setVisible(False)
                self.state.viz_layer.update()
            self.update()

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() & Qt.RightButton:
            if self.current_tool is not None:
                self.current_tool.right_release(None, event.pos().toPoint(),
                                               self._create_context())
            self.label_picked.emit(self._label_img[self.state.current_label_level][event.pos().toPoint().toTuple()[::-1]])
            return
        if self.tool_cursor is not None:
            cmd, bbox = self.current_tool.left_release(None, event.pos().toPoint(),
                                                       self._create_context())
            self.tool_viz_commands = []
            if cmd is not None:
                self.label_img_modified.emit(cmd)
            self.tool_cursor.setVisible(True)
        self.update()
        self.state.viz_layer.update()
        # QGraphicsItem.mouseReleaseEvent(self, event)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        if self.tool_cursor is not None:
            self.tool_cursor.setVisible(True)

    def hoverMoveEvent(self, event: QGraphicsSceneHoverEvent):
        ev = event.pos().toPoint()
        if not (0 <= ev.x() < self._label_qimage.width()) or not (0 <= ev.y() < self._label_qimage.height()):
            return
        if self.current_tool is not None and self.tool_cursor is not None:
            self.tool_cursor.setPos(event.pos())
            self.tool_cursor.setVisible(True)
            self.update()
        label = self.state.current_photo[self.state.current_label_name].label_image[ev.toTuple()[::-1]]
        leveled_label = self.state.label_hierarchy.level_mask(self.state.current_label_level) & label
        self.label_hovered.emit(leveled_label)
        lab_img = self.state.current_photo[self.state.current_label_name]
        if (reg_props := lab_img.get_region_props(label)) is not None:
            tooltip = ''
            for reg_prop in reg_props.values():
                tooltip = tooltip + str(reg_prop) + '\n'
            self.setToolTip(tooltip)
        else:
            self.setToolTip('')

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        if self.tool_cursor is not None:
            self.tool_cursor.setVisible(False)
        self.label_hovered.emit(-1)

    #def set_constraint_level(self, level: int):
    #    #self.constraint_level = self.state.current_constraint.label_level
    #    if self.state.current_photo is None:
    #        return
    #    if self.state.redraw_canvas:
    #        self.compute_clip_mask()
    #        self.compute_viz_mask()

    def handle_primary_label_changed(self):
        if self.state.redraw_canvas:
            self.compute_clip_mask()
            self.compute_viz_mask()

    def _create_context(self):
        return EditContext(self._label_img,
                           self.state.primary_label,
                           self.state.current_photo.image,
                           self.state.colormap,
                           self._label_qimage,
                           self.state.current_photo,
                           self.state.current_label_level,
                           self._clip_nd,
                           self.clip_region,
                           self._clip_nd)

    def compute_clip_mask(self):
        print('computing now clip mask')
        if self.state.current_photo is None:
            return
        if self.state.constraint_label == 0:
            clip_mask = 255 * np.ones(self.state.current_photo[self.state.current_label_name].label_image.shape, dtype=np.uint8)
        else:
            #lab_hier = self.state.storage.get_label_hierarchy(lbl_type)
            lab_hier = self.state.label_hierarchy
            level_img = self.state.current_photo[self.state.current_constraint.label_name][lab_hier.get_level(self.state.constraint_label)]#[self.state.current_constraint.label_level]
            hier_mask = lab_hier.label_mask(self.state.constraint_label)
            prefix = self.state.constraint_label & hier_mask
            clip_mask = 255 * (level_img == prefix).astype(np.uint8)
        self._clip_nd = np.require(clip_mask, np.uint8, 'C')
        self._clip_qimg = QImage(self._clip_nd.data, self._clip_nd.shape[1], self._clip_nd.shape[0],
                                 self._clip_nd.strides[0], QImage.Format_Grayscale8)
        #self._clip_qimg.save('C:\\Users\\radoslav\\Desktop\\clip_mask.png')
        self._clip_qimg.invertPixels()
        self.clip_mask = QBitmap.fromImage(self._clip_qimg, Qt.AutoColor)
        self.clip_region = QRegion(self.clip_mask)

    def compute_viz_mask(self, bbox: Optional[typing.Tuple[int, int, int, int]] = None):
        #print('computing viz mask')
        #io.imsave('/home/radoslav/arth_clip_nd.png', self._clip_nd)
        #io.imsave('/home/radoslav/arth_outline_mask.png', self.outline_nd)
        #io.imsave('/home/radoslav/arth_not_clip.png', ~self._clip_nd)
        #io.imsave('/home/radoslav/arth_not_outline.png', ~self.outline_nd)
        #io.imsave('/home/radoslav/arth_nclip_and_noutline.png', ~np.bitwise_and(~self._clip_nd, ~self.outline_nd))
        now = time.time()
        if bbox is not None:
            self.viz_mask_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1] = ~np.bitwise_and(
                ~self._clip_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1],
                ~self.outline_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            )
        else:
            self.viz_mask_nd = ~np.bitwise_and(~self._clip_nd, ~self.outline_nd)
        self.viz_mask_buffer = QImage(self.viz_mask_nd.data, self.viz_mask_nd.shape[1], self.viz_mask_nd.shape[0],
                                      self.viz_mask_nd.strides[0], QImage.Format_Grayscale8)
        self.viz_mask = QBitmap.fromImage(self.viz_mask_buffer)
        #self.viz_mask.save('/home/radoslav/arth_viz_mask.png')
        self.viz_clip_region = QRegion(self.viz_mask)
        b = QBitmap(self.viz_mask.size())
        b.fill(QColor.fromRgb(0, 0, 0, 0))
        #b.save('/home/radoslav/arth_viz_clip_reg.png')
        reg = QRegion(b)
        self.restricted_clip_region = self.viz_clip_region ^ reg if self.showing_full_mask else self.clip_region ^ reg
        #io.imsave('/home/radoslav/arth_clip_and_outline.png', self.viz_mask_nd)
        #print(f'computing {"with" if bbox is not None else "without"} bbox took {time.time() - now} secs')
        self.update()

    def rotate(self, ccw: bool = True):
        transform = QTransform()
        transform.rotate(90 * (-1 if ccw else 1))
        self.prepareGeometryChange()
        self._label_qimage = self._label_qimage.transformed(transform)
        self.viz_mask = self.viz_mask.transformed(transform)
        self.viz_clip_region = QRegion(self.viz_mask)
        self.viz_mask_buffer = self.viz_mask_buffer.transformed(transform)
        self.viz_mask_nd = ndimage.rotate(self.viz_mask_nd, 90 if ccw else -90) #T.rotate(self.viz_mask_nd, 90 * (-1 if ccw else 1), order=0)

        self._clip_nd = ndimage.rotate(self._clip_nd, 90 if ccw else -90) #T.rotate(self._clip_nd, 90 * (-1 if ccw else 1))
        #self._clip_qimg = self._clip_qimg.transformed(transform)
        self.clip_mask = self.clip_mask.transformed(transform)
        self.clip_region = QRegion(self.clip_mask)

        b = QBitmap(self.viz_mask.size())
        b.fill(QColor.fromRgb(0, 0, 0, 0))
        reg = QRegion(b)
        self.restricted_clip_region = self.viz_clip_region ^ reg if self.showing_full_mask else self.clip_region ^ reg
        self.update()

@numba.njit
def compute_outline(label_img: np.ndarray) -> np.ndarray:
    #result = np.zeros(label_img.shape + (1,), dtype=label_img.dtype)
    result = 255 * np.ones(label_img.shape, dtype=np.uint8)
    d = [-1, 0, 1]
    for y in range(label_img.shape[0]):
        for x in range(label_img.shape[1]):
            if label_img[y, x] == 0:
                continue
            lab = label_img[y, x]
            for k in d:
                for j in d:
                    if k == 0 and j == 0 or outside(y + k, x + j, label_img.shape) or abs(k) + abs(j) > 1:
                        continue
                    if label_img[y + k, x + j] != lab:
                        result[y, x] = 0 # label_img[y, x]
    return result


@numba.njit
def outside(y, x, shape):
    return y < 0 or y >= shape[0] or x < 0 or x >= shape[1]
