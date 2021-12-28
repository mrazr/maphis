import abc
from enum import IntEnum, Enum
import typing
from pathlib import Path
import time

import cv2 as cv
import numpy as np
from PySide2.QtGui import QImage, QColor
from PySide2.QtCore import QSize
from skimage import io


class LabelType(IntEnum):
    BUG = 0,
    REGIONS = 1,
    REFLECTION = 2,

#MaskType = Enum('MaskType', {'MASK': 0, 'SEGMENTS': 1, 'REFLECTIONS': 2})


class LabelImg:
    def __init__(self):
        self.label_img: typing.Optional[np.ndarray] = None
        self._path: typing.Optional[Path] = None
        self.color_map: typing.Dict[int, typing.Tuple[int, int, int]] = {}
        self._type = None

    @classmethod
    def create(cls, size: typing.Tuple[int, int], mask_type) -> 'LabelImg':
        mask = LabelImg()
        mask.label_img = np.zeros(size, np.uint16)
        mask._type = mask_type
        mask.color_map = {0: (0, 0, 0)}
        return mask

    @classmethod
    def assign_to_photo(cls, photo: 'Photo', label_type: LabelType) -> 'LabelImg':
        lbl_img = LabelImg.create(photo.image.size().toTuple(), label_type)
        photo.assign_mask(lbl_img)
        return lbl_img

    @property
    def path(self) -> typing.Optional[Path]:
        if self._path is not None:
            return self._path
        return None

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def label_type(self) -> LabelType:
        return self._type

    @property
    def label_image(self) -> np.ndarray:
        return self.label_img

    @label_image.setter
    def label_image(self, lbl_nd: np.ndarray):
        self.label_img = lbl_nd

    # only for now
    def reload(self):
        # TODO remove the `1000 * ` part
        img = 1000 * np.logical_not(io.imread(str(self._path)))
        self.label_img = img
        self.color_map = {label: QColor.fromRgb(*tuple(np.random.randint(0, 256, (3,))), 100).rgba() for label in np.unique(self.label_img)}
        self.color_map[0] = QColor.fromRgb(0, 0, 0, 0).rgba()

    @classmethod
    def load(cls, path: Path, label_type: LabelType) -> 'LabelImg':
        now = time.time()
        lbl = LabelImg()
        lbl._type = label_type
        lbl._path = path
        return lbl


class Photo(abc.ABC):
    @property
    @abc.abstractmethod
    def image_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def image_path(self) -> Path:
        pass

    @property
    @abc.abstractmethod
    def image(self) -> QImage:
        pass

    @property
    @abc.abstractmethod
    def bug_mask(self) -> LabelImg:
        pass

    @bug_mask.setter
    @abc.abstractmethod
    def bug_mask(self, mask):
        pass

    @property
    @abc.abstractmethod
    def segments_mask(self) -> LabelImg:
        pass

    @segments_mask.setter
    def segments_mask(self, mask):
        pass

    @property
    @abc.abstractmethod
    def reflection_mask(self) -> LabelImg:
        pass

    @reflection_mask.setter
    @abc.abstractmethod
    def reflection_mask(self, mask):
        pass

    def assign_mask(self, mask: LabelImg):
        if mask.label_type == LabelType.BUG:
            self.bug_mask = mask
        elif mask.label_type == LabelType.REGIONS:
            self.segments_mask = mask
        else:
            self.reflection_mask = mask

    @property
    def label_dict(self) -> typing.Dict[LabelType, LabelImg]:
        return {LabelType.BUG: self.bug_mask,
                LabelType.REGIONS: self.segments_mask,
                LabelType.REFLECTION: self.reflection_mask}


class LocalPhoto(Photo):
    def __init__(self, folder: Path, img_name: str):
        self._image: typing.Optional[QImage] = None #QImage(str(folder / 'images' / img_name))
        self._image_path = folder / 'images' / img_name
        self._bug_mask = LabelImg.load(folder / 'masks' / f'maska - {img_name}', LabelType.BUG)
        self._segments_mask: typing.Optional[LabelImg] = LabelImg.load(folder / 'masks' / f'maska - {img_name}', LabelType.REGIONS) #None
        self._reflection_mask: typing.Optional[LabelImg] = LabelImg.load(folder / 'masks' / f'maska - {img_name}', LabelType.REFLECTION) #None

    @property
    def image(self) -> QImage:
        return self._image

    @property
    def image_name(self) -> str:
        return self._image_path.name

    @property
    def image_path(self) -> Path:
        return self._image_path

    @property
    def bug_mask(self) -> typing.Optional[LabelImg]:
        if self._bug_mask is None:
            self._bug_mask = LabelImg.create(self.image.size().toTuple(), LabelType.BUG) #QImage(self.image.size(), QImage.Format_Grayscale8)
        return self._bug_mask

    @bug_mask.setter
    def bug_mask(self, mask: LabelImg):
        self._bug_mask = mask

    @property
    def segments_mask(self) -> typing.Optional[LabelImg]:
        if self._segments_mask is None:
            self._segments_mask = LabelImg.create(self.image.size().toTuple(), LabelType.REGIONS) #QImage(self.image.size(), QImage.Format_Grayscale16)
        return self._segments_mask

    @segments_mask.setter
    def segments_mask(self, mask: LabelImg):
        # TODO make sure `mask` is subset of self._bug_mask
        self._segments_mask = mask

    @property
    def reflection_mask(self) -> typing.Optional[LabelImg]:
        if self._reflection_mask is None:
            self._reflection_mask = LabelImg.create(self.image.size().toTuple(), LabelType.REFLECTION) #QImage(self.image.size(), QImage.Format_Grayscale8)
        return self._reflection_mask

    @reflection_mask.setter
    def reflection_mask(self, mask: LabelImg):
        # TODO make sure `mask` is subset of self._bug_mask
        self._reflection_mask = mask
