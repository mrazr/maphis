import dataclasses
import typing
from copy import deepcopy
from pathlib import Path
import importlib.resources
import platform

import cv2
import numpy as np
from PySide2.QtCore import Qt, QPoint
from PySide2.QtGui import QImage, QCursor
from PySide2.QtWidgets import QFileDialog, QWidget
import pytesseract

from arthropod_describer.common.units import Value, Unit, BaseUnit, CompoundUnit, SIPrefix


def choose_folder(parent: QWidget, title = "Open folder", path: typing.Optional[Path] = None) -> typing.Optional[Path]:
    """Shows a file dialog and lets the user choose a folder.

    :param parent: Widget parent for the file dialog.
    :type parent: QWidget
    :param title: Title for the file dialog.
    :type title: str
    :param path: Optional path to set as the initial location of the file dialog.
    :type path: pathlib.Path

    :returns: Optional path if user confirmed their choice
    :rtype: pathlib.Path
    """
    file_dialog = QFileDialog(parent)
    if path is not None:
        file_dialog.setDirectory(str(path))
    file_dialog.setFileMode(QFileDialog.Directory)
    file_dialog.setWindowTitle(title)
    file_dialog.setWindowModality(Qt.WindowModal)
    if file_dialog.exec_():
        file_path = Path(file_dialog.selectedFiles()[0])
        return file_path
    return None


def get_dict_from_doc_str(doc_str: str) -> typing.Dict[str, str]:
    lines = [line for line in doc_str.splitlines() if len(line) > 0 and not line.isspace()]

    splits = [line.split(':') for line in lines]
    splits = [split for split in splits if len(split) == 2]

    return {split[0].strip(): split[1].strip() for split in splits}


def is_valid_annotation_project(path: Path, req_folders: typing.List[str]) -> bool:
    return all([(path / folder).exists() for folder in req_folders])


def get_scale_marker_roi(img: np.ndarray) -> typing.Tuple[np.ndarray, typing.Tuple[int, int, int, int]]:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    gray_ = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9)))

    _, th = cv2.threshold(gray_, 245, 255, cv2.THRESH_BINARY)

    closed = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
    closed = cv2.morphologyEx(closed, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))

    N, label_img, stats, centroids = cv2.connectedComponentsWithStats(closed, None, None, None, 4)

    ratios: typing.List[float] = []

    for i in range(N):
        l, t, w, h = stats[i, [cv2.CC_STAT_LEFT, cv2.CC_STAT_TOP, cv2.CC_STAT_WIDTH, cv2.CC_STAT_HEIGHT]]
        if int(l)+int(w) > closed.shape[1] or int(t)+int(h) > closed.shape[0]:
            ratios.append(-42)
            continue
        nonzeros = np.count_nonzero(th[t:t+h, l:l+w])
        bbox_area = w * h
        ratios.append(nonzeros / bbox_area)

    idxs = np.argsort(ratios)
    largest_idx = idxs[-1]

    top, left, height, width = stats[largest_idx, [cv2.CC_STAT_TOP, cv2.CC_STAT_LEFT, cv2.CC_STAT_HEIGHT, cv2.CC_STAT_WIDTH]]

    return gray[top:top+height, left:left+width], (left, top, width, height)


def get_scale_line_ends(scale_marker: np.ndarray) -> typing.Tuple[int, int, int, int]:
    roi = scale_marker
    height, width = scale_marker.shape[0], scale_marker.shape[1]
    inv_roi = 255 - roi
    _, inv_roi = cv2.threshold(inv_roi, 245, 255, cv2.THRESH_BINARY)

    if height > width:
        print('height > width')
        only_line = cv2.morphologyEx(inv_roi, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15)),
                                     borderType=cv2.BORDER_CONSTANT, borderValue=0)

        nonzero = np.nonzero(only_line)

        if len(nonzero[0]) == 0:
            return -1, 0, 0, 0

        p1_y, p1_x = np.min(nonzero[0]), np.min(nonzero[1])
        p2_y = np.max(nonzero[0])
        p2_x = p1_x
    else:
        print('width > height')
        only_line = cv2.morphologyEx(inv_roi, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1)),
                                     borderType=cv2.BORDER_CONSTANT, borderValue=0)

        nonzero = np.nonzero(only_line)

        if len(nonzero[0]) == 0:
            print("Scale line not found")
            return -1, -1, -1, -1

        p1_y, p1_x = np.min(nonzero[0]), np.min(nonzero[1])
        p2_x = np.max(nonzero[1])
        p2_y = p1_y

    return p1_x, p1_y, p2_x, p2_y


def get_reference_length(img: np.ndarray) -> typing.Tuple[str, np.ndarray]:
    if platform.system() == 'Windows':
        with importlib.resources.path('arthropod_describer.bin', 'Tesseract-OCR') as p:
            pytesseract.pytesseract.tesseract_cmd = str(p / 'tesseract.exe')
    else:
        print('am on linux probably')
    rot = img
    for i in range(4):
        rot = cv2.rotate(rot, cv2.ROTATE_90_CLOCKWISE)
        text = pytesseract.image_to_string(rot)
        if len(text) == 0:
            continue
        if text[0].isdigit() and rot.shape[1] >= rot.shape[0]:
            return text, rot
    return '', img


def vector_to_img(vec: typing.Union[np.ndarray, typing.List[float]], size: typing.Tuple[int, int]) -> np.ndarray:
    vec_min, vec_max = np.min(vec), np.max(vec)

    if isinstance(vec, list):
        vec = np.array(vec)

    stretched = (size[1] - 1) - np.round((size[1] - 1) * ((vec - vec_min) / (vec_max - vec_min + 1e-6))).astype(np.uint16)

    img = 255 * np.ones(size[::-1], np.uint8)
    step = round(size[0] / len(vec))

    for i in range(1, len(vec)):
        img = cv2.line(img, (step * (i-1), stretched[i-1]), (step * i, stretched[i]), 0, 1)

    return img


def vector_to_img2(vec: typing.Union[np.ndarray, typing.List[float]], size: typing.Tuple[int, int]) -> np.ndarray:
    vec_min, vec_max = np.min(vec), np.max(vec)

    vec_min = round(vec_min)
    vec_max = round(vec_max + 0.5)

    if isinstance(vec, list):
        vec = np.array(vec)

    stretched = (size[1] - 1) - np.round((size[1] - 1) * ((vec - vec_min) / (vec_max - vec_min + 1e-6))).astype(np.uint16)

    height = vec_max - vec_min

    # img = 255 * np.ones(size[::-1], np.uint8)
    img = 255 * np.ones((height, 256))
    step = round(256 / len(vec))

    for i in range(1, len(vec)):
        img = cv2.line(img, (step * (i-1), round(vec[i-1])), (step * i, round(vec[i])), 0, 1)

    return img


def is_cursor_inside(widget: QWidget) -> bool:
    rect = widget.rect()
    rect.moveTo(widget.mapToGlobal(QPoint(0, 0)))
    return rect.contains(QCursor.pos())


@dataclasses.dataclass
class ScaleLineInfo:
    p1: typing.Tuple[int, int]
    p2: typing.Tuple[int, int]
    length: Value

    def __repr__(self) -> str:
        return f'ScaleLineInfo(p1={repr(self.p1)}, p2={repr(self.p2)}, length={repr(self.length)})'

    def rotate(self, ccw: bool, origin: typing.Tuple[int, int]):
        p1_c = complex(self.p1[0] - origin[0], self.p1[1] - origin[1])
        p2_c = complex(self.p2[0] - origin[0], self.p2[1] - origin[1])

        p1_c = p1_c * complex(0, -1 if ccw else 1)
        p2_c = p2_c * complex(0, -1 if ccw else 1)

        p1 = (round(p1_c.real), round(p1_c.imag))
        p1 = (p1[0] + origin[1], p1[1] + origin[0])

        p2 = (round(p2_c.real), round(p2_c.imag))
        p2 = (p2[0] + origin[1], p2[1] + origin[0])

        self.p1 = p1
        self.p2 = p2

    def scale(self, f: float, o: typing.Tuple[int, int]):
        p1_ = (f * (self.p1[0] - o[0]), f * (self.p1[1] - o[1]))
        p2_ = (f * (self.p2[0] - o[0]), f * (self.p2[1] - o[1]))

        self.p1 = (round(p1_[0] + f * o[0]), round(p1_[1] + f * o[1]))
        self.p2 = (round(p2_[0] + f * o[0]), round(p2_[1] + f * o[1]))


@dataclasses.dataclass
class ScaleSetting:
    reference_length: typing.Optional[Value] = None
    scale: typing.Optional[Value] = None
    scale_line: typing.Optional[ScaleLineInfo] = None
    scale_marker_bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None
    scale_marker_img: typing.Optional[QImage] = None

    @classmethod
    def from_dict(cls, obj_dict: typing.Dict[str, typing.Any]) -> 'ScaleSetting':
        if (maybe_ref_l := obj_dict.get('reference_length')) is not None:
            ref_l = eval(maybe_ref_l)
        else:
            ref_l = None

        if (maybe_scale := obj_dict.get('scale')) is not None:
            scale = eval(maybe_scale)
        else:
            scale = None

        if (maybe_scale_line := obj_dict.get('scale_line')) is not None:
            scale_line = eval(maybe_scale_line)
        else:
            scale_line = None

        if (maybe_bbox := obj_dict.get('scale_marker_bbox')) is not None:
            scale_marker_bbox = eval(maybe_bbox)
        else:
            scale_marker_bbox = None

        return ScaleSetting(reference_length=ref_l,
                            scale=scale,
                            scale_line=scale_line,
                            scale_marker_bbox=scale_marker_bbox)

    def scale_by_factor(self, fac: float, o: typing.Tuple[int, int]):
        if self.scale is not None:
            self.scale.value *= fac
        if self.scale_line is not None:
            self.scale_line.scale(fac, o)

    def __deepcopy__(self, memodict={}):
        sc_setting = ScaleSetting(reference_length=deepcopy(self.reference_length),
                                  scale=deepcopy(self.scale),
                                  scale_line=deepcopy(self.scale_line),
                                  scale_marker_bbox=deepcopy(self.scale_marker_bbox),
                                  scale_marker_img=self.scale_marker_img)
        return sc_setting


