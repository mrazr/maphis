import datetime
import logging
import time
from queue import Queue
from typing import Optional, Tuple

import PySide2
import cv2
import numba
import numpy as np
import qimage2ndarray
import scipy
from PySide2.QtCore import Qt, Signal, QRectF
from PySide2.QtGui import QRegion, QBitmap, QImage, QColor, QPainter, QBrush, QTransform
from PySide2.QtWidgets import QGraphicsSceneMouseEvent, QGraphicsItem, QStyleOptionGraphicsItem, QWidget, \
    QGraphicsSceneHoverEvent
from scipy import ndimage
import skimage.morphology as M
from skimage import io

from arthropod_describer.common.label_change import CommandEntry
from arthropod_describer.common.layer import Layer
from arthropod_describer.common.photo import Photo, LabelImg
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import EditContext, Tool

logger = logging.getLogger("LabelLayer")


class LabelLayer(Layer):
    label_img_modified = Signal(CommandEntry)
    label_picked = Signal(int)
    label_hovered = Signal(int)
    constraint_up = Signal(int)
    constraint_down = Signal(int)
    cycle_constraint = Signal(int, int)

    def __init__(self, state: State, parent: Optional[PySide2.QtWidgets.QGraphicsItem] = None):
        super().__init__(state, parent)
        self.state = state

        self.showing_full_mask = True

        self.viz_clip_region: QRegion = QRegion()
        self.viz_mask: QBitmap = None
        self.viz_mask_buffer: QImage = QImage()
        self.viz_mask_nd: np.ndarray = None
        self._label_img: LabelImg = None
        self._label_qimage: Optional[QImage] = None

        self.outline_1px_nd: np.ndarray = None
        self.outline_nd: np.ndarray = None
        self.outline_mask: QBitmap = QBitmap()
        self.outline_mask_buffer: QImage = QImage()
        self.outline_width: int = 3

        self._outline_update_queue: Queue[Tuple[int, int, int, int]] = Queue()

        self._nd_img: Optional[np.ndarray] = None

        self.current_tool: Optional[Tool] = None

        self.clip_region: QRegion = QRegion()
        self._clip_nd: np.ndarray = None
        self._clip_qimg = QImage()
        self.clip_mask = QBitmap()

        self.restricted_clip_region: QRegion = QRegion()

        self.state.new_label_constraint.connect(self.recompute_masks)

        #self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)

    def set_tool(self, tool: Optional[Tool], reset_current: bool = True):
        self.current_tool = tool

    def _create_context(self) -> Optional[EditContext]:
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

    def recompute_masks(self, _):
        self.compute_clip_mask()
        self.compute_viz_mask()

    def set_photo(self, photo: Optional[Photo], reset_tool: bool = True):
        if photo is None:
            logger.info('set_photo(None)')
            self.setVisible(False)
            return
        else:
            logger.info(f'set_photo({photo.image_name}), {photo.image_size}')
            self.setVisible(True)
        lbl = self.state.current_photo[self.state.current_label_name]
        self.set_label_image(lbl, 0)

    def set_label_name(self, label_name: str):
        lbl = self.state.current_photo[label_name]
        level = self.state.current_label_level
        self.set_label_image(lbl, level)

    def set_label_image(self, mask: LabelImg, level: int):
        logger.info(f'set_label_image, size = {mask.size}')
        self.prepareGeometryChange()
        self._label_img = mask
        self._recolor_image()
        self.compute_clip_mask()
        self.outline_nd = 0 * np.ones_like(self.state.current_photo[self.state.current_label_name].label_image,
                                           dtype=np.uint8)
        if not self.showing_full_mask:
            self.draw_outline()
        self.compute_viz_mask()

    def _recolor_image(self):
        #if self._label_img is None or self._label_img._label_img is None: #not self._label_img.is_set:
        #    self._label_qimage = None
        #    return
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
        logger.info(f'_recolor_image(), _label_qimage size = {self._label_qimage.size()}')
        logger.info(f'_recolor_image(), state.current_photo size = {self.state.current_photo.image_size}')
        self.update()

    def boundingRect(self):
        if self._label_qimage is None:
            return QRectF()
        return self._label_qimage.rect()

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...):
        if self._label_qimage is not None:
            painter.save()
            if not self.showing_full_mask:
                painter.setClipRegion(self.viz_clip_region, Qt.ReplaceClip)
            painter.drawImage(option.rect, self._label_qimage)
            painter.setClipRegion(self.restricted_clip_region, Qt.ReplaceClip)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            painter.fillRect(self.boundingRect(), QBrush(QColor.fromRgb(0, 0, 0, 200)))  #, Qt.Dense5Pattern))
            painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
            painter.restore()

    def switch_label_level(self, level: int):
        self._recolor_image()
        if not self.showing_full_mask:
            self.draw_outline()

    def draw_outline(self, bbox: Optional[Tuple[int, int, int, int]] = None, compute_from_viz: bool = True):
        # print(self.state.current_label_level)
        level_img = self.state.current_photo[self.state.current_label_name][self.state.current_label_level]
        timestamp = str(datetime.datetime.now().time()).replace(":", "_")
        if bbox is not None:
            # print(f'using bbox = {bbox}')
            bbox = list(bbox)
            bbox[0] -= 10
            bbox[1] += 10
            bbox[2] -= 10
            bbox[3] += 10
            if compute_from_viz:
                level_img = qimage2ndarray.raw_view(self._label_qimage.copy(bbox[2], bbox[0],
                                                                            bbox[3] - bbox[2] + 1, bbox[1] - bbox[0] + 1))
                # la = self._label_qimage.copy(bbox[2], bbox[0], bbox[3] - bbox[2], bbox[1] - bbox[0])
                # la.save(f'C:\\Users\\radoslav\\Desktop\\levs\\lev_{timestamp}.png')
                # print(level_img.dtype)
            else:
                level_img = level_img[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            outline = compute_outline2(level_img) #compute_outline(level_img).astype(np.uint8)
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
            # self.outline_mask.save(f'C:\\Users\\radoslav\\Desktop\\whole_outline\\outline_{timestamp}.png')
            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\partial_outline\\partial_{timestamp}.png', outline)
        else:
            if compute_from_viz:
                level_img = qimage2ndarray.raw_view(self._label_qimage)
            self.outline_1px_nd = compute_outline2(level_img) #compute_outline(level_img).astype(np.uint8)
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
        self.compute_viz_mask(None, compute_from_viz=True)
        self.update()

    def change_outline_width(self, value: int):
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
        # FIXME Temporary fix for darkening the label image when switching from filled style to outline style
        self.change_outline_width(self.outline_width+1)
        self.change_outline_width(self.outline_width-1)

    def show_mask(self):
        self._recolor_image()
        self.outline_nd = np.zeros_like(self._label_img.label_image, dtype=np.uint8)
        self.compute_viz_mask()
        self.showing_full_mask = True

    def rotate(self, ccw: bool = True):
        transform = QTransform()
        transform.rotate(90 * (-1 if ccw else 1))
        self.prepareGeometryChange()
        self._label_qimage = self._label_qimage.transformed(transform)
        self.viz_mask = self.viz_mask.transformed(transform)
        self.viz_clip_region = QRegion(self.viz_mask)
        self.viz_mask_buffer = self.viz_mask_buffer.transformed(transform)
        self.viz_mask_nd = ndimage.rotate(self.viz_mask_nd, 90 if ccw else -90)  #T.rotate(self.viz_mask_nd, 90 * (-1 if ccw else 1), order=0)

        self._clip_nd = ndimage.rotate(self._clip_nd, 90 if ccw else -90)  #T.rotate(self._clip_nd, 90 * (-1 if ccw else 1))
        self.clip_mask = self.clip_mask.transformed(transform)
        self.clip_region = QRegion(self.clip_mask)

        b = QBitmap(self.viz_mask.size())
        b.fill(QColor.fromRgb(0, 0, 0, 0))
        reg = QRegion(b)
        self.restricted_clip_region = self.viz_clip_region ^ reg if self.showing_full_mask else self.clip_region ^ reg
        self.update()

    def handle_primary_label_changed(self):
        if self.state.redraw_canvas:
            self.compute_clip_mask()
            self.compute_viz_mask()

    def compute_clip_mask(self):
        if self.state.current_photo is None:
            return
        if self.state.constraint_label == 0 or self.state.current_constraint.label_name is None:
            clip_mask = 255 * np.ones(self.state.current_photo[self.state.current_label_name].label_image.shape, dtype=np.uint8)
        else:
            #lab_hier = self.state.label_hierarchy
            #level_img = self.state.current_photo[self.state.current_constraint.label_name][lab_hier.get_level(self.state.constraint_label)]#[self.state.current_constraint.label_level]
            #hier_mask = lab_hier.label_mask(self.state.constraint_label)
            #prefix = self.state.constraint_label & hier_mask
            #clip_mask = 255 * (level_img == prefix).astype(np.uint8)
            constr_label = self.state.current_constraint.label_name
            lab_hier = self.state.storage.get_label_hierarchy2(constr_label)
            level_img = self.state.current_photo[constr_label][lab_hier.get_level(self.state.current_constraint.label_node.label)]
            hier_mask = lab_hier.label_mask(self.state.current_constraint.label_node.label)
            prefix = self.state.current_constraint.label_node.label & hier_mask
            clip_mask = 255 * (level_img == prefix).astype(np.uint8)
        self._clip_nd = np.require(clip_mask, np.uint8, 'C')
        self._clip_qimg = QImage(self._clip_nd.data, self._clip_nd.shape[1], self._clip_nd.shape[0],
                                 self._clip_nd.strides[0], QImage.Format_Grayscale8)
        self._clip_qimg.invertPixels()
        self.clip_mask = QBitmap.fromImage(self._clip_qimg, Qt.AutoColor)
        self.clip_region = QRegion(self.clip_mask)

    def compute_viz_mask(self, bbox: Optional[Tuple[int, int, int, int]] = None, compute_from_viz: bool = False):
        lab_hier = self.state.label_hierarchy
        if bbox is not None:
            # self.viz_mask_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1] = ~np.bitwise_and(
            #     ~self._clip_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1],
            #     ~self.outline_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            # )
            # self.viz_mask_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1] = self.outline_nd[bbox[0]:bbox[1] + 1, bbox[2]:bbox[3] + 1]
            specimen_mask = self.state.current_photo[self.state.current_label_name].label_image[bbox[0]:bbox[1]+1,
                            bbox[2]:bbox[3]+1]
            specimen_mask = 255 * (specimen_mask > 0).astype(np.uint8)
            self.viz_mask_nd[bbox[0]:bbox[1] + 1, bbox[2]:bbox[3] + 1] = ~np.bitwise_and(
                specimen_mask,
                ~self.outline_nd[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            )
        else:
            # self.viz_mask_nd = ~np.bitwise_and(~self._clip_nd, ~self.outline_nd)
            # self.viz_mask_nd = self.outline_nd
            if not compute_from_viz:
                specimen_mask = 255 * (self.state.current_photo[self.state.current_label_name].label_image > 0).astype(
                    np.uint8)
            else:
                specimen_mask = 255 * (qimage2ndarray.raw_view(self._label_qimage) > 0).astype(np.uint8)
            self.viz_mask_nd = ~np.bitwise_and(specimen_mask, ~self.outline_nd)
        # io.imsave('C:\\Users\\radoslav\\Desktop\\specimen.png', (specimen_mask).astype(np.uint8), check_contrast=False)
        # io.imsave('C:\\Users\\radoslav\\Desktop\\outline_nd.png', (255 * (self.outline_nd > 0)).astype(np.uint8), check_contrast=False)
        # io.imsave('C:\\Users\\radoslav\\Desktop\\viz_mask_nd.png', (255 * (self.viz_mask_nd > 0)).astype(np.uint8), check_contrast=False)
        self.viz_mask_buffer = QImage(self.viz_mask_nd.data, self.viz_mask_nd.shape[1], self.viz_mask_nd.shape[0],
                                      self.viz_mask_nd.strides[0], QImage.Format_Grayscale8)
        self.viz_mask = QBitmap.fromImage(self.viz_mask_buffer)
        self.viz_clip_region = QRegion(self.viz_mask)
        b = QBitmap(self.viz_mask.size())
        b.fill(QColor.fromRgb(0, 0, 0, 0))
        reg = QRegion(b)
        # self.restricted_clip_region = self.viz_clip_region ^ reg if self.showing_full_mask else self.clip_region ^ reg
        self.restricted_clip_region = self.clip_region ^ reg
        self.update()

    def mouse_press(self, event: QGraphicsSceneMouseEvent):
        if event.buttons() & Qt.MiddleButton:
            QGraphicsItem.mousePressEvent(self, event)
            return
        elif event.button() & Qt.LeftButton:
            if self.current_tool is not None:
                hovered_label = self.state.current_photo[self.state.current_label_name][self.state.current_label_level][
                    event.pos().toPoint().toTuple()[::-1]]

                self.current_tool.left_press(None, event.pos().toPoint(), self._create_context())

                if not self.showing_full_mask:
                    self.draw_outline(None)

            self.update()
        elif event.button() & Qt.RightButton:
            if self.current_tool is not None:
                self.current_tool.right_press(None, event.pos().toPoint(), self._create_context())
            self.update()
        # QGraphicsItem.mousePressEvent(self, event)

    def mouse_move(self, event: QGraphicsSceneMouseEvent):
        if event.button() & Qt.RightButton:
            return
        elif event.buttons() & Qt.LeftButton:
            if self.current_tool is not None and self.current_tool.active:
                ctx = self._create_context()
                cmds, rect = self.current_tool.mouse_move(None, event.pos().toPoint(),
                                                       event.lastPos().toPoint(),
                                                       ctx)
                bbox = [rect.top(), rect.top() + rect.height(),
                        rect.left(), rect.left() + rect.width()]
                if not self.showing_full_mask and rect.isValid():
                    self._outline_update_queue.put_nowait(bbox)
                    bbox_ = self._outline_update_queue.get_nowait()
                    self.draw_outline(None)  # TODO eventually do use `bbox_` to avoid recomputing the outline for the whole image
            self.update()

    def mouse_release(self, event: QGraphicsSceneMouseEvent):
        if event.button() & Qt.RightButton:
            if self.current_tool is not None:
                self.current_tool.right_release(None, event.pos().toPoint(),
                                                self._create_context())
            self.label_picked.emit(self._label_img[self.state.current_label_level][event.pos().toPoint().toTuple()[::-1]])
            return
        if self.current_tool is not None:
            cmd, bbox = self.current_tool.left_release(None, event.pos().toPoint(),
                                                       self._create_context())
            if cmd is not None:
                cmd.image_name = self.state.current_photo.image_name
                cmd.label_name = self.state.current_label_name
                self.label_img_modified.emit(cmd)

            # TODO: Is this "while" block okay/necessary? What is its putpose, why does it seem to draw the outline several times, but only if the queue is non-empty?
            #       To fix a bug with the outline not updating after using a knife or a polygon, a call to draw_outline() had to be added below anyway (was needed even if the queue was empty).
            while not self._outline_update_queue.empty():
                bbox = self._outline_update_queue.get_nowait()
                self.draw_outline(None)
            #self.tool_cursor.setVisible(True)

            if not self.showing_full_mask:
                self.draw_outline(None)

        self.update()

    def mouse_double_click(self, event: QGraphicsSceneMouseEvent):
        if self.current_tool is not None and self.current_tool.active:
            cmd, bbox = self.current_tool.mouse_double_click(None, event.pos().toPoint(),
                                                             self._create_context())
            if cmd is not None:
                cmd.image_name = self.state.current_photo.image_name
                cmd.label_name = self.state.current_label_name
                self.label_img_modified.emit(cmd)
        self.update()

    def hover_enter(self, event: QGraphicsSceneHoverEvent):
        #if self.tool_cursor is not None:
        #    self.tool_cursor.setVisible(True)
        pass

    def hover_move(self, event: QGraphicsSceneHoverEvent):
        ev = event.pos().toPoint()
        if not (0 <= ev.x() < self._label_qimage.width()) or not (0 <= ev.y() < self._label_qimage.height()):
            return
        #if self.current_tool is not None and self.tool_cursor is not None:
        #    self.tool_cursor.setPos(event.pos())
        #    self.tool_cursor.setVisible(True)
        #    self.update()
        label = self.state.current_photo[self.state.current_label_name].label_image[ev.toTuple()[::-1]]
        leveled_label = self.state.label_hierarchy.level_mask(self.state.current_label_level) & label
        lab_img = self.state.current_photo[self.state.current_label_name]
        if (reg_props := lab_img.get_region_props(leveled_label)) is not None:
            tooltip = self.state.label_hierarchy.nodes[leveled_label].name + '\n'
            for reg_prop in reg_props.values():
                tooltip = tooltip + str(reg_prop) + '\n'
            self.setToolTip(tooltip)
        else:
            self.setToolTip('')
        self.label_hovered.emit(leveled_label)

    def hover_leave(self, event: QGraphicsSceneHoverEvent):
        self.label_hovered.emit(-1)

    def wheelEvent(self, event:PySide2.QtWidgets.QGraphicsSceneWheelEvent):
        label = self.state.current_photo[self.state.current_label_name].label_image[event.pos().toPoint().toTuple()[::-1]]
        leveled_label = self.state.label_hierarchy.level_mask(self.state.current_label_level) & label
        if event.modifiers() & Qt.ControlModifier:
            if event.delta() < 0:
                # self.constraint_down.emit(leveled_label)
                self.cycle_constraint.emit(leveled_label, 1)
            else:
                # self.constraint_up.emit(leveled_label)
                self.cycle_constraint.emit(leveled_label, -1)
        elif event.modifiers() & Qt.ShiftModifier > 0:
            if self.current_tool is not None:
                self.current_tool.mouse_wheel(event.delta(), None, None, None)


diff_filter = np.array([
    [0, -1, 0],
    [-1, 4, -1],
    [0, -1, 0]
], dtype=np.int32)


def compute_outline2(label_img: np.ndarray) -> np.ndarray:
    sums = scipy.ndimage.convolve(label_img, diff_filter)
    return 255 * (sums == 0).astype(np.uint8)


@numba.jit
def compute_outline(label_img: np.ndarray) -> np.ndarray:
    # result = np.zeros(label_img.shape + (1,), dtype=label_img.dtype)
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
                        result[y, x] = 0  # label_img[y, x]
    return result


@numba.jit
def outside(y, x, shape):
    return y < 0 or y >= shape[0] or x < 0 or x >= shape[1]
