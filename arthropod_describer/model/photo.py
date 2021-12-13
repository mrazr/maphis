import abc
from enum import IntEnum
import typing
from pathlib import Path

from PySide2.QtGui import QImage
from PySide2.QtCore import QSize


class MaskType(IntEnum):
    BUG_MASK = 0,
    SEGMENTS_MASK = 1,
    REFLECTION_MASK = 2,


class Mask:
    def __init__(self, size: typing.Tuple[int, int], mask_type: MaskType):
        self._mask = QImage(QSize(*size), QImage.Format_Grayscale16)
        self._path: typing.Optional[Path] = None
        self._type = mask_type

    @classmethod
    def assign_to_photo(cls, photo: 'Photo', mask_type: MaskType) -> 'Mask':
        mask = Mask(photo.image.size().toTuple(), mask_type=mask_type)
        photo.assign_mask(mask)

    @property
    def path(self) -> typing.Optional[Path]:
        if self._path is not None:
            return self._path
        return None

    @property
    def mask_name(self) -> str:
        return self.path.name

    @property
    def mask_type(self) -> MaskType:
        return self._type


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
    def bug_mask(self):
        pass

    @bug_mask.setter
    @abc.abstractmethod
    def bug_mask(self, mask):
        pass

    @property
    @abc.abstractmethod
    def segments_mask(self):
        pass

    @segments_mask.setter
    def segments_mask(self, mask):
        pass

    @property
    @abc.abstractmethod
    def reflection_mask(self):
        pass

    @reflection_mask.setter
    @abc.abstractmethod
    def reflection_mask(self, mask):
        pass

    def assign_mask(self, mask: Mask):
        if mask.mask_type == MaskType.BUG_MASK:
            self.bug_mask = mask
        elif mask.mask_type == MaskType.SEGMENTS_MASK:
            self.segments_mask = mask
        else:
            self.reflection_mask = mask


class LocalPhoto(Photo):
    def __init__(self, path: Path):
        self._image = QImage(str(path))
        self._image_path = path
        self._bug_mask: typing.Optional[Mask] = None
        self._segments_mask: typing.Optional[Mask] = None
        self._reflection_mask: typing.Optional[Mask] = None

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
    def bug_mask(self) -> typing.Optional[Mask]:
        return self._bug_mask

    @bug_mask.setter
    def bug_mask(self, mask: Mask):
        self._bug_mask = mask

    @property
    def segments_mask(self) -> typing.Optional[Mask]:
        return self._segments_mask

    @segments_mask.setter
    def segments_mask(self, mask: Mask):
        # TODO make sure `mask` is subset of self._bug_mask
        self._segments_mask = mask

    @property
    def reflection_mask(self) -> typing.Optional[Mask]:
        return self._reflection_mask

    @reflection_mask.setter
    def reflection_mask(self, mask: Mask):
        # TODO make sure `mask` is subset of self._bug_mask
        self._reflection_mask = mask
