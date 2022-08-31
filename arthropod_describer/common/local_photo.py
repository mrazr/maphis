from pathlib import Path
from typing import Dict

import typing

import cv2
import numpy as np
from PIL import Image
from PySide2.QtGui import QImage
from skimage import io

from arthropod_describer.common.label_image import LabelImgInfo, LabelImg
from arthropod_describer.common.photo import Photo, Subscriber, UpdateContext
from arthropod_describer.common.units import Value
from arthropod_describer.common.utils import ScaleSetting


class LocalPhoto(Photo):

    def __init__(self, folder: Path, img_name: str, lbl_image_info: Dict[str, LabelImgInfo], subs: Subscriber):
        self._tags: typing.Set[str] = set()
        self._dirty_flag: bool = False
        self._image: typing.Optional[np.ndarray] = None
        self._image_path = folder / img_name
        self._bug_bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None

        self._label_images: Dict[str, LabelImg] = {}
        self._label_image_info: Dict[str, LabelImgInfo] = lbl_image_info
        #self._label_image_types = lbl_image_types

        self._scale: typing.Optional[Value] = None
        self._scale_setting: typing.Optional[ScaleSetting] = ScaleSetting()

        self._lab_approvals: Dict[str, typing.Optional[str]] = {lbl_name: None for lbl_name in lbl_image_info.keys()}
        with Image.open(self._image_path) as im:
            self._image_size = im.size
            self._np_size = self._image_size[::-1]
            self.format = im.format

        # create the label images
        for lbl_name in self._label_image_info.keys():
            lbl_img = self[lbl_name]

        self.__subscriber: Subscriber = subs
        self._thumbnail: typing.Optional[QImage] = None

    @property
    def image(self) -> np.ndarray:
        if self._image is None:
            #self._image = io.imread(str(self._image_path))
            with Image.open(self._image_path) as im:
                self._image = np.asarray(im)
                # This is a workaround around RGBA images
                if self._image.shape[2] > 3:
                    self._image = self._image[:, :, :3]
        return self._image

    @property
    def image_name(self) -> str:
        return self._image_path.name

    @property
    def image_path(self) -> Path:
        return self._image_path

    @image_path.setter
    def image_path(self, path: Path):
        raise NotImplementedError('Changing path is not implemented')

    @property
    def image_size(self) -> typing.Tuple[int, int]:
        return self._image_size

    def __getitem__(self, lab_name: str) -> typing.Optional[LabelImg]:
        if lab_name not in self._label_images:
            lab_fname = self._image_path.name + '.tif'
            self._label_images[lab_name] = LabelImg.create2(self._image_path.parent.parent / lab_name / lab_fname,
                                                            self.image_size, label_info=self.label_image_info[lab_name],
                                                            label_name=lab_name)
        lab = self._label_images[lab_name]
        return lab

    @property
    def bug_bbox(self) -> typing.Optional[typing.Tuple[int, int, int, int]]:
        return self._bug_bbox

    def recompute_bbox(self):
        pass
        #coords = np.nonzero(self._regions_image.label_img)
        #if len(coords[0]) == 0:
        #    top, left = 0, 0
        #    bottom, right = self.regions_image.label_img.shape
        #else:
        #    top, left = np.min(coords[0]), np.min(coords[1])
        #    bottom, right = np.max(coords[0]), np.max(coords[1])
        #self._bug_bbox = [left, top, right, bottom]

    @property
    def label_images_(self) -> Dict[str, LabelImg]:
        return self._label_images

    @property
    def label_image_info(self) -> Dict[str, LabelImgInfo]:
        return self._label_image_info

    @property
    def image_scale(self) -> typing.Optional[Value]:
        return self._scale_setting.scale

    @image_scale.setter
    def image_scale(self, scale: typing.Optional[Value]):
        self._scale_setting.scale = scale

    @property
    def scale_setting(self) -> typing.Optional[ScaleSetting]:
        return self._scale_setting

    @scale_setting.setter
    def scale_setting(self, setting: typing.Optional[ScaleSetting]):
        self._scale_setting = setting
        self._subscriber.notify(self.image_name, UpdateContext.Photo, {'type': 'image_scale'})

    @property
    def approved(self) -> Dict[str, typing.Optional[str]]:
        return self._lab_approvals

    def rotate(self, ccw: bool):
        loaded = self._image is not None
        if not loaded:
            self._image = io.imread(str(self._image_path))
        if self.scale_setting is not None and self.scale_setting.scale_line is not None:
            mid = (round(self.image_size[0] * 0.5), round(self.image_size[1] * 0.5))
            self.scale_setting.scale_line.rotate(ccw, mid)
        self._image = cv2.rotate(self._image, cv2.ROTATE_90_COUNTERCLOCKWISE if ccw else cv2.ROTATE_90_CLOCKWISE) #skimage.transform.rotate(self._image, 90 * (-1 if ccw else 1), order=2)
        self._image = np.ascontiguousarray(self._image, dtype=self._image.dtype)
        self._dirty_flag = True
        self._np_size = self._image.shape[:2]
        self._image_size = self._np_size[::-1]
        for lab_img in self._label_images.values():
            lab_img.rotate(ccw)
        if not loaded:
            self.save()
            self._image = None
        self.save()
        self.__subscriber.notify(self.image_name, UpdateContext.Photo, {'operation':
                                                                            'rot_90_ccw' if ccw else 'rot_90_cw'})

    def resize(self, factor: float):
        loaded = self._image is not None
        print(f'resizing with factor {factor}')
        # TODO adapt measurements, or at least signal that the measurements are not up-to-date anymore!
        if self._scale_setting is not None and self._scale_setting.scale is not None:
            # print(f'changing scale from {self._scale} to {self._scale * factor}')
            self._scale_setting.scale *= factor
        if not loaded:
            self._image = io.imread(str(self._image_path))
        self._dirty_flag = True
        im = Image.fromarray(self._image)
        print(f'old size is {self._image_size}')
        size = (int(round(factor * self._image_size[0])),
                int(round(factor * self._image_size[1])))
        self._image_size = size
        print(f'new size if {self._image_size}')
        self._np_size = self._image_size[::-1]
        im = im.resize(self._image_size, resample=2)
        self._image = np.asarray(im)
        for lbl_img in self._label_images.values():
            lbl_img.resize(factor)
        if not loaded:
            self.save()
            self._image = None
        if self.scale_setting is not None and self.scale_setting.scale_line is not None:
            mid = (round(self.image_size[0] * 0.5), round(self.image_size[1] * 0.5))
            self.scale_setting.scale_line.scale(factor, (0, 0))

        self.__subscriber.notify(self.image_name, UpdateContext.Photo,
                                 {'operation': 'resize',
                                  'factor': factor})

    def save(self):
        if self.has_unsaved_changes:
            if self._dirty_flag:
                if self._image is not None:
                    #im = Image.fromarray(self._image)
                    #im.save(self._image_path)
                    if self.format != 'TIFF':
                        bgr = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
                        cv2.imwrite(str(self._image_path), bgr)
                    else:
                        im = Image.fromarray(self._image)
                        im.save(self._image_path)
            for lab_img in self._label_images.values():
                lab_img.save()
        self._dirty_flag = False

    def unload(self):
        self.save()
        self._image = None

        for lab_img in self._label_images.values():
            lab_img.unload()

    def has_segmentation_for(self, label_name: str) -> bool:
        return self._label_images[label_name].is_segmented

    @property
    def has_unsaved_changes(self) -> bool:
        return self._dirty_flag or any([lab.has_unsaved_changed for lab in self._label_images.values()])

    @property
    def _subscriber(self) -> Subscriber:
        return self.__subscriber

    @property
    def tags(self) -> typing.Set[str]:
        return self._tags

    @tags.setter
    def tags(self, _tags: typing.Set[str]):
        self._tags = {tag for tag in _tags if not tag.isspace() and len(tag) > 0}
        self._subscriber.notify(self.image_name, UpdateContext.Photo,
                                {'tags': {
                                    'added': list(self._tags),
                                    'removed': []
                                }})

    def add_tag(self, tag: str):
        if tag in self._tags or len(tag) == 0 or tag.isspace():
            return
        self._tags.add(tag)
        self._subscriber.notify(self.image_name, UpdateContext.Photo,
                                {'tags': {
                                    'added': [tag],
                                    'removed': []
                                }})

    def remove_tag(self, tag: str):
        if tag not in self._tags:
            return

        self._tags.remove(tag)
        self._subscriber.notify(self.image_name, UpdateContext.Photo,
                                {'tags': {
                                    'added': [],
                                    'removed': [tag]
                                }})

    def toggle_tag(self, tag: str, enabled: bool):
        if enabled:
            self.add_tag(tag)
        else:
            self.remove_tag(tag)

    @property
    def thumbnail(self) -> typing.Optional[QImage]:
        return self._thumbnail

    @thumbnail.setter
    def thumbnail(self, thumbnail: typing.Optional[QImage]):
        self._thumbnail = thumbnail
        # TODO fire signal to notify of thumbnail change
