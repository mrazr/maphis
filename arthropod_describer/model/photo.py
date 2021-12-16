import abc
from enum import IntEnum, Enum
import typing
from pathlib import Path

from PySide2.QtGui import QImage
from PySide2.QtCore import QSize


class MaskType(IntEnum):
    BUG = 0,
    REGIONS = 1,
    REFLECTION = 2,

#MaskType = Enum('MaskType', {'MASK': 0, 'SEGMENTS': 1, 'REFLECTIONS': 2})


class Mask:
    def __init__(self):
        self._mask = None #QImage(QSize(*size), QImage.Format_Grayscale16)
        self._path: typing.Optional[Path] = None
        self._type = None

    @classmethod
    def create(cls, size: typing.Tuple[int, int], mask_type) -> 'Mask':
        mask = Mask()
        format = QImage.Format_Grayscale16 if mask_type.REGIONS else QImage.Format_Grayscale8
        mask._mask = QImage(QSize(*size), format)
        mask._type = mask_type
        return mask

    @classmethod
    def assign_to_photo(cls, photo: 'Photo', mask_type: MaskType) -> 'Mask':
        mask = Mask.create(photo.image.size().toTuple(), mask_type)
        photo.assign_mask(mask)
        return mask

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

    @property
    def mask(self) -> QImage:
        return self._mask

    @classmethod
    def load(cls, path: Path, mask_type: MaskType) -> 'Mask':
        mask = Mask()
        img = QImage(str(path))
        mask._mask = img
        mask._type = mask_type
        mask._path = path
        return mask


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
        if mask.mask_type == MaskType.BUG:
            self.bug_mask = mask
        elif mask.mask_type == MaskType.REGIONS:
            self.segments_mask = mask
        else:
            self.reflection_mask = mask

    def mask_dict(self) -> typing.Dict[MaskType, Mask]:
        return {MaskType.BUG: self.bug_mask,
                MaskType.REGIONS: self.segments_mask,
                MaskType.REFLECTION: self.reflection_mask}


class LocalPhoto(Photo):
    def __init__(self, folder: Path, img_name: str):
        self._image = QImage(str(folder / 'images' / img_name))
        self._image_path = folder / 'images' / img_name
        self._bug_mask = Mask.load(folder / 'masks' / f'maska - {img_name}', MaskType.BUG)
        self._segments_mask: typing.Optional[Mask] = Mask.load(folder / 'masks' / f'maska - {img_name}', MaskType.BUG) #None
        self._reflection_mask: typing.Optional[Mask] = Mask.load(folder / 'masks' / f'maska - {img_name}', MaskType.BUG) #None

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
        if self._bug_mask is None:
            self._bug_mask = Mask.create(self.image.size().toTuple(), MaskType.BUG) #QImage(self.image.size(), QImage.Format_Grayscale8)
        return self._bug_mask

    @bug_mask.setter
    def bug_mask(self, mask: Mask):
        self._bug_mask = mask

    @property
    def segments_mask(self) -> typing.Optional[Mask]:
        if self._segments_mask is None:
            self._segments_mask = Mask.create(self.image.size().toTuple(), MaskType.REGIONS) #QImage(self.image.size(), QImage.Format_Grayscale16)
        return self._segments_mask

    @segments_mask.setter
    def segments_mask(self, mask: Mask):
        # TODO make sure `mask` is subset of self._bug_mask
        self._segments_mask = mask

    @property
    def reflection_mask(self) -> typing.Optional[Mask]:
        if self._reflection_mask is None:
            self._reflection_mask = Mask.create(self.image.size().toTuple(), MaskType.REFLECTION) #QImage(self.image.size(), QImage.Format_Grayscale8)
        return self._reflection_mask

    @reflection_mask.setter
    def reflection_mask(self, mask: Mask):
        # TODO make sure `mask` is subset of self._bug_mask
        self._reflection_mask = mask
