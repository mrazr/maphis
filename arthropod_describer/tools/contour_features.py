import typing
from typing import List, Optional, Any

import numpy as np
import scipy.linalg
import scipy.ndimage
from sklearn.decomposition import PCA
from PySide2.QtCore import QPoint, QObject
from PySide2.QtGui import QColor, QPen
from skimage import io
from skimage.morphology import binary_erosion
import skimage.transform

from arthropod_describer.common.label_image import LabelImg
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool, PaintCommand, line_command


class Too_Contour(Tool):
    def __init__(self, state: State, parent: QObject = None):
        super().__init__(state, parent)
        self.state: State = state
        self._viz_active: bool = False
        self._viz_commands: List[PaintCommand] = []

    @property
    def tool_name(self) -> str:
        return 'Contour impl.'

    @property
    def viz_active(self) -> bool:
        return self._viz_active

    def viz_left_press(self, pos: QPoint) -> List[PaintCommand]:
        self._viz_active = True
        return []

    def viz_left_release(self, pos: QPoint) -> List[PaintCommand]:
        lbl_img: LabelImg = self.state.current_photo[self.state.current_label_name]
        level_lab = lbl_img[self.state.current_label_level]
        picked_label = level_lab[pos.y(), pos.x()]

        region = lbl_img.mask_for(picked_label)

        pixels = np.argwhere(region)

        top, left = np.min(pixels[:,0]), np.min(pixels[:,1])
        bottom, right = np.max(pixels[:,0]), np.max(pixels[:,1])

        roi = region[top:bottom+1, left:right+1]

        pixels = pixels - np.array([top, left])
        yy, xx = np.nonzero(roi)

        io.imsave('C:\\Users\\radoslav\\Desktop\\region.png', roi)
        io.imsave('C:\\Users\\radoslav\\Desktop\\outline.png', np.logical_xor(roi, binary_erosion(roi, footprint=np.ones((3, 3)))))

        x_c, y_c = round(np.mean(xx)), round(np.mean(yy))

        pen = QPen(QColor(0, 255, 125))
        pen.setWidthF(1.5)

        pca = PCA(n_components=1)
        pca.fit(pixels)

        print(f'mean is {pca.mean_}')
        print(f'centroid is {y_c, x_c}')

        next_pixel = np.array([y_c + top, x_c + left]) + 150.0 * pca.components_[0]
        prev_pixel = np.array([y_c + top, x_c + left]) - 150.0 * pca.components_[0]

        angle = np.rad2deg(np.arccos(np.dot(np.array([1.0, 0.0]), pca.components_[0])))
        print(f'the angle with the y-axis is {angle} deg')

        rotated = skimage.transform.rotate(roi, angle=angle, center=(y_c, x_c), resize=True)
        print(np.any(rotated))

        io.imsave('C:\\Users\\radoslav\\Desktop\\rotated.png', rotated, check_contrast=False)

        outline = np.logical_xor(rotated, binary_erosion(rotated, footprint=np.ones((3, 3))))
        io.imsave('C:\\Users\\radoslav\\Desktop\\rotated_outline.png', outline, check_contrast=False)

        outline_yy, outline_xx = np.nonzero(outline)

        xs_by_y: typing.Dict[int, List[int]] = {}

        for y, x in zip(outline_yy, outline_xx):
            xs_by_y.setdefault(y, []).append(x)

        y_sort_inds = np.argsort(outline_yy)

        col_outline = np.zeros((outline.shape[0], outline.shape[1], 3), dtype=np.uint8)

        for idx in y_sort_inds:
            y = outline_yy[idx]
            left = min(xs_by_y[y])
            right = max(xs_by_y[y])
            col_outline[y, left] = [0, 255, 0]
            col_outline[y, right] = [0, 0, 255]

        io.imsave('C:\\Users\\radoslav\\Desktop\\left_right.png', col_outline)

        right_outline = outline.copy()

        mask_out_idx = np.argwhere(outline_xx < x_c)
        right_outline[outline_yy[mask_out_idx], outline_xx[mask_out_idx]] = False

        left_outline = outline.copy()
        mask_out_idx = np.argwhere(outline_xx > x_c)
        left_outline[outline_yy[mask_out_idx], outline_xx[mask_out_idx]] = False

        io.imsave('C:\\Users\\radoslav\\Desktop\\left_outline.png', left_outline, check_contrast=False)
        io.imsave('C:\\Users\\radoslav\\Desktop\\right_outline.png', right_outline, check_contrast=False)

        self._viz_commands = [
            line_command(QPoint(round(prev_pixel[1]), round(prev_pixel[0])),
                         QPoint(round(next_pixel[1]), round(next_pixel[0])),
                         pen)
        ]

        return self._viz_commands

    def viz_right_release(self, pos: QPoint) -> List[PaintCommand]:
        self._viz_active = False
        return []

    def viz_hover_move(self, new_pos: QPoint, old_pos: QPoint) -> List[PaintCommand]:
        return self._viz_commands