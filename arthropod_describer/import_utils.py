import copy
import dataclasses
import os
import platform
import shutil
import subprocess
import tempfile
import typing
from pathlib import Path
from typing import List, Tuple, Dict

import cv2
import numpy as np
from PIL import Image
from PySide2.QtCore import QObject
from PySide2.QtGui import QImage
from skimage import io, transform

from arthropod_describer.common.label_image import LabelImgInfo
from arthropod_describer.common.local_photo import LocalPhoto
from arthropod_describer.common.photo import Photo, Subscriber
from arthropod_describer.common.local_storage import Storage
from arthropod_describer.common.units import Value
from arthropod_describer.common.utils import ScaleSetting


class TempStorage(Storage):
    PxPerCm = int

    def __init__(self, image_paths: List[Path], root_folder: Path, max_size: int=0, parent: typing.Optional[QObject] = None):
        super().__init__(parent)
        self._image_paths = image_paths
        self._image_names = [image_path.name for image_path in self._image_paths]
        self.image_sizes: List[Tuple[int, int]] = []
        self.dst_image_sizes: List[Tuple[int, int]] = []
        self.image_scales: List[typing.Optional[Value]] = [None for _ in range(len(self._image_names))]
        self.rotations: List[int] = [0 for _ in range(len(self._image_names))]
        self.photos: List[TempPhoto] = []
        self.import_infos: List[ImportPhotoInfo] = []
        self.directory = Path(tempfile.mkdtemp())
        self.max_size = max_size
        self.root_folder: Path = root_folder

        # if platform.system() == "Windows":
        #     os.startfile(self.directory)
        # elif platform.system() == "Darwin":
        #     subprocess.Popen(["open", str(self.directory)])
        # else:
        #     subprocess.Popen(["xdg-open", str(self.directory)])
        #
        for idx, img_path in enumerate(self._image_paths):
            if img_path.parent == self.root_folder:
                rel_path = Path(self.root_folder.name) / '_________'
            else:
                rel_path = img_path.relative_to(self.root_folder)
            photo = TempPhoto(img_path.parent, img_path.name, self)
            import_info = ImportPhotoInfo(src_size=photo.image_size,
                                          dst_size=photo.image_size,
                                          src_path=img_path,
                                          dst_path=img_path,
                                          relative_path=rel_path,
                                          temp_folder=self.directory)
            if rel_path == Path('.'):
                import_info.relative_path = Path(self.root_folder.name)
            photo.import_info = import_info
            self.import_infos.append(import_info)
            with Image.open(img_path) as im:
                self.image_sizes.append(im.size)
                self.dst_image_sizes.append(im.size)
            self.photos.append(photo)
        self.set_max_size(self.max_size)
        self._loaded_photo: typing.Optional[TempPhoto] = None

    @property
    def location(self) -> Path:
        return self.directory

    @property
    def storage_name(self) -> str:
        return "Temporary Storage"

    @property
    def image_names(self) -> List[str]:
        # return [photo.image_name for photo in self.photos if photo.import_info.include]
        return self._image_names

    @property
    def image_count(self) -> int:
        return len(self._image_paths)

    @property
    def image_paths(self) -> List[Path]:
        return self._image_paths

    @property
    def images(self) -> List[Photo]:
        return self.photos

    def get_photo_by_name(self, name: str, load_image: bool = True) -> 'TempPhoto':
        return None

    #def get_photo_by_idx(self, idx: int, load_image: bool = True) -> Photo:
    #    file_path = self._image_paths[idx]
    #    photo = LocalPhoto(file_path.parent, file_path.name, {})
    #    photo._image = io.imread(str(file_path))
    #    photo._image = transform.resize(photo._image, self.dst_image_sizes[idx][::-1], order=0)
    #    for i in range(abs(self.rotations[idx])):
    #        photo._image = cv2.rotate(photo._image, cv2.ROTATE_90_CLOCKWISE if self.rotations[idx] > 0 else cv2.ROTATE_90_COUNTERCLOCKWISE)
    #    return photo

    def get_photo_by_idx(self, idx: int, load_image: bool = True) -> 'TempPhoto':
        if self._loaded_photo is not None and load_image:
            self._loaded_photo._image = None
            self._loaded_photo = None
        file_path = self._image_paths[idx]
        #photo = TempPhoto(file_path.parent, file_path.name)
        photo = self.photos[idx]
        #photo.dst_size = self.dst_image_sizes[idx]
        #photo.rotation = self.rotations[idx]
        if load_image:
            photo._image = io.imread(str(photo.image_path))
            # if photo._image.shape[2] > 3:
            #     photo._image = photo._image[:, :, :3]  # discard alpha channel
            # photo._image = transform.resize(photo._image, photo.import_info.dst_size[::-1], order=0)
            # for i in range(abs(photo.import_info.rotation)):
            #     photo._image = cv2.rotate(photo._image, cv2.ROTATE_90_CLOCKWISE if photo.import_info.rotation > 0 else cv2.ROTATE_90_COUNTERCLOCKWISE)
        self._loaded_photo = photo
        return photo

    def is_approved(self, index: int) -> bool:
        return True

    @property
    def default_label_image(self) -> str:
        return ''

    @property
    def label_img_info(self) -> Dict[str, LabelImgInfo]:
        return {}

    @property
    def photos_to_import(self) -> List['TempPhoto']:
        return [photo for photo in self.photos if photo.import_info.include]

    def close_storage(self):
        shutil.rmtree(self.directory)

    def _set_max_dst_sizes(self):
        for photo in self.photos:
            if self.max_size > 0:
                max_fac = min(1.0, self.max_size / max(*photo.image_size))
                # if max_fac < photo.import_info.resize_factor:
                # dst_size = (round(max_fac * photo.image_size[0]), round(max_fac * photo.image_size[1]))
                # photo.import_info.resize_factor = max_fac
                # photo.import_info.dst_size = dst_size
                photo.resize(max_fac)
                photo.import_info.max_resize_factor = max_fac
            else:
                dst_size = photo.image_size
                photo.import_info.max_resize_factor = 1.0
                photo.import_info.dst_size = dst_size
                photo.import_info.resize_factor = 1.0
                photo.resize(1.0)
            photo.import_info.scale_info = copy.deepcopy(photo.import_info.original_scale_info)
            mid = np.round(0.5 * np.array(photo.image_size))
            photo.import_info.scale_info.scale_by_factor(photo.import_info.resize_factor, mid)

    def set_max_size(self, max_size: int):
        self.max_size = max_size
        self._set_max_dst_sizes()


@dataclasses.dataclass
class ImportPhotoInfo:
    src_size: typing.Tuple[int, int]
    dst_size: typing.Tuple[int, int]
    src_path: Path
    dst_path: Path
    relative_path: Path
    resize_factor: float = 1.0
    max_resize_factor: float = 1.0
    scale_info: ScaleSetting = dataclasses.field(default_factory=ScaleSetting)
    original_scale_info: ScaleSetting = dataclasses.field(default_factory=ScaleSetting)
    temp_folder: Path = dataclasses.field(default_factory=Path)
    rotation: int = 0  # multiples of 90 deg rotation in CW
    scale_marker: typing.Optional[QImage] = None
    include: bool = True


class TempPhoto(LocalPhoto):
    def __init__(self, folder: Path, img_name: str, subs: Subscriber, import_info: typing.Optional[ImportPhotoInfo] = None):
        super().__init__(folder, img_name, {}, subs)
        # self.dst_size: Tuple[int, int] = self.image_size
        # self.resize_factor: float = 1.0
        # self.rotation: int = 0  # number of CW(if positive)/CCW(if negative) 90deg rotations
        # self.scale_marker: typing.Optional[QImage] = None
        # self.ref_length: typing.Optional[Value] = None
        self.import_info: ImportPhotoInfo = import_info

    def resize(self, factor: float):
        # 1. load image from self.import_info.src_path
        # 2. resize according to self.import_info.resize_factor
        # 3. rotate according to self.import_info.rotation
        # 4. save to the self.import_info.temp_folder / self.image_name
        # 5. scale_line = scale(rotate(original_scale_line))
        # self._inv_transform()
        self.import_info.resize_factor = factor
        self.import_info.dst_size = (int(round(factor * self.image_size[0])),
                         int(round(factor * self.image_size[1])))
        self.import_info.scale_info = copy.deepcopy(self.import_info.original_scale_info)
        self.import_info.scale_info.scale_by_factor(self.import_info.resize_factor, np.round(0.5 * np.array(self.import_info.src_size)))
        # self._transform()

    def rotate(self, ccw: bool):
        # 1. load image from self.import_info.src_path
        # 2. rotate according to self.import_info.rotation
        # 3. resize according to self.import_info.resize_factor
        # 4. save to the self.import_info.temp_folder / self.image_name
        # 5. scale_line = scale(rotate(original_scale_line))
        # self._inv_transform()
        self.import_info.rotation += 1 if not ccw else -1
        if abs(self.import_info.rotation) == 4:
            self.import_info.rotation = 0
        # self._transform()

    def _inv_transform(self):
        sc_info = copy.deepcopy(self.import_info.scale_info)
        # ccw = self.import_info.rotation > 0
        # mid = np.round(0.5 * np.array(self.import_info.dst_size))
        # for i in range(abs(self.import_info.rotation)):
        #     sc_info.scale_line.rotate(ccw, mid if i % 2 == 0 else mid[::-1])
        #
        fac = 1.0 / self.import_info.resize_factor
        sc_info.scale_line.scale(fac, np.round(self.import_info.resize_factor * np.array(self.import_info.src_size)))

        self.import_info.original_scale_info = sc_info

    def _transform(self):
        img = cv2.imread(str(self.import_info.src_path))
        img = cv2.resize(img, (0, 0), fx=self.import_info.resize_factor, fy=self.import_info.resize_factor,
                         interpolation=cv2.INTER_AREA)

        sc_info = copy.deepcopy(self.import_info.original_scale_info)
        sc_info.scale_line.scale(self.import_info.resize_factor, np.round(0.5 * np.array(self.import_info.src_size)))

        ccw = self.import_info.rotation < 0
        for i in range(abs(self.import_info.rotation)):
            sc_info.scale_line.rotate(ccw, np.round(0.5 * np.array(img.shape[:2][::-1])))
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE if not ccw else cv2.ROTATE_90_COUNTERCLOCKWISE)
        self._image_path = self.import_info.temp_folder / self.image_name
        cv2.imwrite(str(self._image_path), img)
        self.import_info.scale_info = sc_info

    @property
    def image_path(self) -> Path:
        return self._image_path

    @image_path.setter
    def image_path(self, path: Path):
        self._image_path = path

    @property
    def image_scale(self) -> typing.Optional[Value]:
        return self.import_info.scale_info.scale

    @image_scale.setter
    def image_scale(self, scale: typing.Optional[Value]):
        self.import_info.scale_info.scale = scale

    @property
    def scale_setting(self) -> typing.Optional[ScaleSetting]:
        return self.import_info.original_scale_info

    @scale_setting.setter
    def scale_setting(self, scale_setting: typing.Optional[ScaleSetting]):
        self.import_info.original_scale_info = scale_setting
        self.import_info.scale_info = copy.deepcopy(self.import_info.original_scale_info)
        self.import_info.scale_info.scale_by_factor(self.import_info.resize_factor,
                                                    np.round(0.5 * np.array(self.import_info.src_size)))

    @property
    def tags(self) -> typing.Set[str]:
        return super().tags

    @tags.setter
    def tags(self, tags: typing.Set[str]):
        self._tags = {tag for tag in tags if not tag.isspace() and len(tag) > 0}
