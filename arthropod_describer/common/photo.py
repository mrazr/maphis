import abc
import time
import typing
from enum import IntEnum
from pathlib import Path
from typing import Dict, Optional

import PySide2
import cv2
import numpy as np
from PIL import Image
from PySide2.QtCore import QObject
from PySide2.QtGui import QImage
from skimage import io

from arthropod_describer.common.label_image import LabelImg, LabelImgInfo
from arthropod_describer.common.units import Value
from arthropod_describer.common.utils import ScaleSetting


class UpdateContext(IntEnum):
    Photo = 0,
    LabelImg = 1,
    Measurements = 2,


class Subscriber(QObject):
    def __init__(self, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)

    def notify(self, img_name: str, ctx: UpdateContext, data: Optional[Dict[str, typing.Any]] = None):
        pass


class Photo(abc.ABC):

    @property
    @abc.abstractmethod
    def _subscriber(self) -> Subscriber:
        pass

    @property
    @abc.abstractmethod
    def image_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def image_path(self) -> Path:
        pass

    @image_path.setter
    @abc.abstractmethod
    def image_path(self, path: Path):
        return Path()

    @property
    @abc.abstractmethod
    def image(self) -> np.ndarray:
        pass

    @property
    @abc.abstractmethod
    def image_size(self) -> typing.Tuple[int, int]:
        """
        Should return (width, height)
        """
        pass

    @abc.abstractmethod
    def __getitem__(self, label_name: str) -> LabelImg: #item: LabelType) -> LabelImg:
        pass

    # TODO remove this
    @property
    def bug_bbox(self) -> typing.Optional[typing.Tuple[int, int, int, int]]:
        return None

    # TODO remove this
    def recompute_bbox(self):
        pass

    @property
    @abc.abstractmethod
    def label_images_(self) -> Dict[str, LabelImg]:
        pass

    @property
    @abc.abstractmethod
    def label_image_info(self) -> Dict[str, LabelImgInfo]:
        pass

    @property
    def image_scale(self) -> Optional[Value]:
        return None

    @image_scale.setter
    def image_scale(self, scale: Optional[Value]):
        pass

    @property
    def scale_setting(self) -> Optional[ScaleSetting]:
        return None

    @scale_setting.setter
    def scale_setting(self, setting: Optional[ScaleSetting]):
        pass

    # TODO rename this to 'approvals'
    @property
    def approved(self) -> Dict[str, Optional[str]]:
        pass

    @abc.abstractmethod
    def has_segmentation_for(self, label_name: str) -> bool:
        return False

    @abc.abstractmethod
    def rotate(self, ccw: bool):
        pass

    @abc.abstractmethod
    def resize(self, factor: float):
        pass

    @abc.abstractmethod
    def save(self):
        pass

    @property
    @abc.abstractmethod
    def has_unsaved_changes(self) -> bool:
        pass

    @property
    def tags(self) -> typing.Set[str]:
        return set()

    @tags.setter
    def tags(self, _tags: typing.Set[str]):
        pass

    def add_tag(self, tag: str):
        pass

    def remove_tag(self, tag: str):
        pass

    def toggle_tag(self, tag: str, enabled: bool):
        pass

    @property
    def thumbnail(self) -> typing.Optional[QImage]:
        return QImage()

    @thumbnail.setter
    def thumbnail(self, thumb: typing.Optional[QImage]):
        pass

    def __hash__(self) -> int:
        return hash(self.image_path)


# TODO move this in 'arthropod_describer.common' or use a function from the package nd2qimage
def nd2qimage(nd: np.ndarray) -> QImage:
    if nd.ndim == 3:
        # assume RGB888
        return QImage(nd.data, nd.shape[1], nd.shape[0], nd.strides[0], QImage.Format_RGB888)
    return QImage()

