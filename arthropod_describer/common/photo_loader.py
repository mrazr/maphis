import abc
from pathlib import Path
import re
import typing
import os
import logging

import cv2 as cv
import numpy as np
from PySide2.QtGui import QImage

from arthropod_describer.common.photo import LocalPhoto, Photo
from arthropod_describer.common.colormap import Colormap

logger = logging.getLogger("model.photo_loader")

TIF_REGEX = re.compile(".*\.tif")

BUG_MASK_DIR = 'bug_masks'
SEGMENTS_MASK_DIR = 'segments_masks'
REFLECTION_MASK_DIR = 'reflection_masks'


# restructure the folder to the proposed directory structure
def restructure_folder(folder: Path, image_regex: typing.Optional[re.Pattern]=TIF_REGEX):
    image_folder = folder / 'images'
    logger.info(f'restructuring folder {folder}')
    if not image_folder.exists():
        image_folder.mkdir()
        image_files = [file for file in os.scandir(folder) if image_regex.match(file.name) is not None]
        for direntry in image_files:
            logger.info(f'moving {direntry.path} to {image_folder / direntry.name}')
            os.rename(direntry.path, image_folder / direntry.name)
    logger.info(f'attempting to create {BUG_MASK_DIR} directory')
    (folder / BUG_MASK_DIR).mkdir(exist_ok=True)

    logger.info(f'attempting to create {SEGMENTS_MASK_DIR} directory')
    (folder / SEGMENTS_MASK_DIR).mkdir(exist_ok=True)

    logger.info(f'attempting to create {REFLECTION_MASK_DIR} directory')
    (folder / REFLECTION_MASK_DIR).mkdir(exist_ok=True)


def get_image_names(folder: Path, image_regex: re.Pattern=TIF_REGEX) -> typing.List[str]:
    # returns image names matching the image_regex in the `folder`
    return list(sorted([file.name for file in os.scandir(folder) if image_regex.match(file.name) is not None]))


class Storage(abc.ABC):
    @property
    @abc.abstractmethod
    def image_names(self):
        pass

    @property
    @abc.abstractmethod
    def location(self) -> Path:
        pass

    @property
    @abc.abstractmethod
    def image_count(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def image_paths(self) -> typing.List[str]:
        pass

    @abc.abstractmethod
    def get_photo_by_name(self, name: str) -> Photo:
        pass

    @abc.abstractmethod
    def get_photo_by_idx(self, idx: int) -> Photo:
        pass

    @classmethod
    @abc.abstractmethod
    def load_from(cls, folder: Path, image_regex: re.Pattern=TIF_REGEX):
        pass

    @property
    @abc.abstractmethod
    def colormap(self) -> Colormap:
        pass


class LocalStorage(Storage):
    def __init__(self, folder: Path, image_regex: re.Pattern=TIF_REGEX):
        self._location = folder
        restructure_folder(self._location)

        self._image_folder = self._location / 'images'
        self._image_regex = image_regex
        self._image_names = get_image_names(self._image_folder, self._image_regex)
        self._image_paths = [self._image_folder / img_name for img_name in self._image_names]
        self._image_names_indices: typing.Dict[str, int] = {name: i for i, name in enumerate(self._image_names)}

        self._images: typing.List[Photo] = []

        self._bug_masks_folder = self._location / 'bug_masks'

        self._segments_masks_folder = self._location / 'segments_masks'

        self._reflection_masks_folder = self._location / 'reflection_masks'

        self._loaded_photo: typing.Optional[Photo] = None #only for now

        self._colormap = None
        cmap_path = self._location / 'colormap.json'
        if cmap_path.exists():
            self._colormap = Colormap(cmap_path=cmap_path)
            print("hej")

    def _load_photo(self, img_name: str) -> LocalPhoto:
        return LocalPhoto(self._location, img_name) # TODO handle loading masks

    @property
    def location(self) -> Path:
        return self._location

    @classmethod
    def load_from(cls, folder: Path, image_regex: re.Pattern=TIF_REGEX) -> 'LocalStorage':
        strg = LocalStorage(folder, image_regex)
        strg._images = [strg._load_photo(img_name) for img_name in strg._image_names]
        return strg

    def get_photo_by_idx(self, idx: int) -> Photo:
        assert 0 <= idx < len(self._image_names)
        photo = self._images[idx]

        if self._loaded_photo is not None:
            self._loaded_photo._image = None
            self._loaded_photo.bug_mask.label_image = None
            self._loaded_photo.segments_mask.label_image = None
            self._loaded_photo.reflection_mask.label_image = None

        photo._image = QImage(str(photo.image_path))
        photo.bug_mask.reload()
        photo.segments_mask.reload()
        photo.reflection_mask.reload()

        #show_imgs([255 * resize(photo.bug_mask.label_img.astype(np.uint8))])

        self._loaded_photo = photo
        return self._loaded_photo

    def get_photo_by_name(self, name: str) -> Photo:
        assert name in self._image_names
        return self.get_photo_by_idx(self._image_names_indices[name])

    @property
    def image_count(self) -> int:
        return len(self._image_names)

    @property
    def image_paths(self) -> typing.List[str]:
        return self._image_paths

    @property
    def image_names(self) -> typing.List[str]:
        return self._image_names

    @property
    def colormap(self) -> Colormap:
        return self._colormap


class MockStorage(LocalStorage):
    def __init__(self, folder: Path, image_regex: re.Pattern=TIF_REGEX):
        super().__init__(folder, image_regex)

    @classmethod
    def load_from(cls, folder: Path, image_regex: re.Pattern=TIF_REGEX) -> 'MockStorage':
        strg = MockStorage(folder, image_regex)
        strg._images = [QImage(256, 256, QImage.Format_Grayscale16) for _ in range(strg.image_count)]
        return strg


def resize(img: np.ndarray) -> np.ndarray:
    return cv.resize(img, (0, 0), fx=0.5, fy=0.5, interpolation=cv.INTER_NEAREST)


def show_imgs(imgs):
    if isinstance(imgs, np.ndarray):
        imgs = [imgs]
    for i, img in enumerate(imgs):
        cv.imshow(f'img_{i}', img)
    cv.waitKey(0)
    cv.destroyAllWindows()