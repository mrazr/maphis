import abc
import collections
import functools
import json
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Set

import cv2 as cv
import numpy as np
import typing

from PySide2.QtCore import QObject
from PySide2.QtGui import QImage
from PySide2.QtWidgets import QMessageBox, QWidget

from arthropod_describer.common.label_hierarchy import LabelHierarchy
from arthropod_describer.common.label_image import LabelImgInfo, RegionProperty
from arthropod_describer.common.local_photo import LocalPhoto
from arthropod_describer.common.photo import Photo, Subscriber, UpdateContext
from arthropod_describer.common.storage import IMAGE_REFEX, TIF_REGEX, Storage
from arthropod_describer.common.units import Value, CompoundUnit, BaseUnit, SIPrefix, Unit
from arthropod_describer.common.utils import ScaleSetting, ScaleLineInfo

logger = logging.getLogger("model.photo_loader")


# restructure the folder to the proposed directory structure
def restructure_folder(folder: Path, image_regex: Optional[re.Pattern]=IMAGE_REFEX, parents: bool = False,
                       label_folders: List[str] = None):
    if len(label_folders) is None or len(label_folders) == 0:
        return
    image_folder = folder / 'images'
    logger.info(f'restructuring folder {folder}')
    if not image_folder.exists():
        image_folder.mkdir(parents=parents)
        image_files = [file for file in os.scandir(folder) if image_regex.match(file.name) is not None]
        for direntry in image_files:
            logger.info(f'moving {direntry.path} to {image_folder / direntry.name}')
            os.rename(direntry.path, image_folder / direntry.name)

    for label_folder in label_folders:
        logger.info(f'attempting to create {label_folder} directory')
        (folder / label_folder).mkdir(exist_ok=True)


def get_image_names(folder: Path, image_regex: re.Pattern=TIF_REGEX) -> List[str]:
    # returns image names matching the image_regex in the `folder`
    return list(sorted([file.name for file in os.scandir(folder) if image_regex.match(file.name) is not None]))


class LocalStorage(Storage):
    def __init__(self, folder: Path, lbl_images_info: Path,
                 image_regex: re.Pattern=IMAGE_REFEX, scale: Optional[float] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._location = folder
        # if isinstance(lbl_images_info, Path):
            # lbl_image_types = LocalStorage.load_label_image_types(lbl_image_info)
        self._default_label, _lbl_images_infos = LocalStorage.load_label_image_info(lbl_images_info)
        # else:
        #     with open(folder / 'label_images_info.json', 'w') as f:
        #         json.dump(lbl_images_info, f)
        #     _lbl_images_infos = lbl_images_info['label_images']
        #     self._default_label = lbl_images_info['default_label_image']
        self._lbl_img_info: Dict[str, LabelImgInfo] = _lbl_images_infos

        self._image_folder = self._location / 'images'
        self._image_regex = image_regex
        self._image_names = get_image_names(self._image_folder, self._image_regex)
        self._image_names_indices: Dict[str, int] = {name: i for i, name in enumerate(self._image_names)}

        self._label_hierarchy: Optional[LabelHierarchy] = None

        self._images: List[Photo] = []

        self._loaded_photo: Optional[LocalPhoto] = None #only for now

        self._images = [self._load_photo(img_name) for img_name in self._image_names]
        self._image_paths = [self._image_folder / img_name for img_name in self._image_names]

        self.photo_info: Dict[str, Any] = {}

        self._label_hierarchies: Dict[str, LabelHierarchy] = {}
        self._load_label_hierarchies()
        self._label_names: Set[str] = set(self._lbl_img_info.keys())

        if not (path := self.location / 'photo_info.json').exists():
            for img in self._images:
                for lbl_name in self._lbl_img_info.keys():
                    img.approved[lbl_name] = None
                    img[lbl_name].is_segmented = False
                img.image_scale = scale
            self.save()

        with open(self.location / 'photo_info.json') as f:
            photo_info = json.load(f)

        self._tag_useg_counter: collections.Counter = collections.Counter()

        for img in self._images:
            img.tags = set(photo_info[img.image_name].setdefault('tags', list()))
            for lbl_name in self._label_names:
                img.approved[lbl_name] = photo_info[img.image_name]['label_images_info'][lbl_name]['approved']
                if 'segmented' not in photo_info[img.image_name]['label_images_info'][lbl_name]:
                    _lab = img[lbl_name].label_image  # just to initialize LabelImg.is_segmented, see property label_image
                else:
                    img[lbl_name].is_segmented = photo_info[img.image_name]['label_images_info'][lbl_name]['segmented']
                if (maybe_scale := photo_info[img.image_name]['scale']) is not None:
                    img.image_scale = eval(maybe_scale)
                else:
                    img.image_scale = maybe_scale
                scale_info = photo_info[img.image_name]['scale_info']
                # img.scale_setting = ScaleSetting(reference_length=eval(scale_info['reference_length']),
                #                                  scale=eval(scale_info['scale']),
                #                                  scale_line=eval(scale_info['scale_line']))
                img.scale_setting = ScaleSetting.from_dict(photo_info[img.image_name]['scale_info'])

        self._properties: typing.Dict[str, typing.Dict[str, RegionProperty]]

    def _load_label_hierarchies(self):
        for label_name in self._lbl_img_info.keys():
            if (lab_hier_path := self._location / f'{label_name}_labels.json').exists():
                self._label_hierarchies[label_name] = LabelHierarchy.load(lab_hier_path)

    def get_label_hierarchy2(self, label_name: str) -> Optional[LabelHierarchy]:
        return self._label_hierarchies.get(label_name, None)

    def set_label_hierarchy2(self, label_name: str, lab_hier: LabelHierarchy):
        self._label_hierarchies[label_name] = lab_hier

    def _load_photo(self, img_name: str) -> LocalPhoto:
        return LocalPhoto(self._location / 'images', img_name, self._lbl_img_info, self) # TODO handle loading masks

    @property
    def location(self) -> Path:
        return self._location

    @classmethod
    def load_from(cls, folder: Path, image_regex: re.Pattern=IMAGE_REFEX) -> 'LocalStorage':
        strg = LocalStorage(folder, lbl_images_info=folder / 'label_images_info.json', image_regex=image_regex)
        return strg

    # TODO REMOVE
    # @classmethod
    # def load_label_image_types(cls, path: Path) -> Dict[str, LabelImgType]:
    #     with open(path) as f:
    #         lbl_image_types = json.load(f)
    #     for k, v in lbl_image_types.items():
    #         lbl_image_types[k] = LabelImgType(int(v))
    #     return lbl_image_types

    @classmethod
    def load_label_image_info(cls, path: Path) -> typing.Tuple[str, Dict[str, LabelImgInfo]]:
        with open(path) as f:
            lbl_imgs_info = json.load(f)
        lbl_infos: Dict[str, LabelImgInfo] = {}
        for label_name, label_info in lbl_imgs_info['label_images'].items():
            lbl_infos[label_name] = LabelImgInfo(label_name, is_default=label_name == lbl_imgs_info['default_label_image'],
                                                 always_constrain_to=label_info['always_constrain_to'],
                                                 allow_constrain_to=label_info['allow_constrain_to'])
        return lbl_imgs_info['default_label_image'], lbl_infos

    @property
    def default_label_image(self) -> str:
        return self._default_label

    def get_photo_by_idx(self, idx: int, load_image: bool=True) -> Photo:
        #assert 0 <= idx < len(self._image_names)
        photo = self._images[idx]
        #if load_image and self._loaded_photo is not None and self._loaded_photo.image_name != photo.image_name:
        #    self._loaded_photo.unload()
        #    self._loaded_photo = None
        #    self._loaded_photo = photo
        #if load_image:
        #    if self._loaded_photo is not None and self._loaded_photo._dirty_flag:
        #        self._loaded_photo.save()
        #        self._loaded_photo._image = None
        #    photo._image = io.imread(str(photo.image_path)) #QImage(str(photo.image_path))
        #    self._loaded_photo = photo
        for label_name in self._lbl_img_info.keys():
            photo[label_name].label_hierarchy = self._label_hierarchies[label_name]
        return photo

    def get_photo_by_name(self, name: str, load_image: bool=True) -> Photo:
        assert name in self._image_names
        return self.get_photo_by_idx(self._image_names_indices[name], load_image=load_image)

    @property
    def image_count(self) -> int:
        return len(self._image_names)

    @property
    def image_paths(self) -> List[str]:
        return self._image_paths

    @property
    def image_names(self) -> List[str]:
        return self._image_names

    @property
    def images(self) -> List[Photo]:
        return self._images

    def reset_photo(self, photo: Photo):
        pass

    @property
    def label_hierarchy(self) -> LabelHierarchy:
        return self._label_hierarchy

    @label_hierarchy.setter
    def label_hierarchy(self, lab_hier: LabelHierarchy):
        # TODO handle changes to the label image
        self._label_hierarchy = lab_hier
        for photo in self._images:
            #photo.regions_image.label_hierarchy = self._label_hierarchy
            for label_name, lab_img in photo.label_images_.items():
                lab_img.label_hierarchy = lab_hier

    def is_approved(self, index: int) -> bool:
        lb_h = self.get_label_hierarchy2('Labels')
        return self._images[index].approved['Labels'] == lb_h.mask_names[-1]

    def save(self) -> bool:
        #try:
        for photo in self._images:
            if photo.has_unsaved_changes:
                photo.save()
        if self._loaded_photo is not None:
            self._loaded_photo.save()
            for _, lbl_img in self._loaded_photo.label_images_.items():
                lbl_img.save()
        photo_info = {img.image_name: {
            # 'px/mm': img.image_scale,
            'scale': repr(img.image_scale),
            'scale_info': {
                'reference_length': repr(img.scale_setting.reference_length),
                'scale': repr(img.scale_setting.scale),
                'scale_line': repr(img.scale_setting.scale_line),
                'scale_marker_bbox': repr(img.scale_setting.scale_marker_bbox)
            },
            'approved': {
                lbl_name: img.approved[lbl_name] for lbl_name in self._label_names
            },
            'label_images_info': {lbl_name: {
                'approved': img.approved[lbl_name],
                'segmented': img.has_segmentation_for(lbl_name)
            } for lbl_name in self._label_names},
            'tags': list(img.tags)
        } for img in self._images}
        with open(self.location / 'photo_info.json', 'w') as f:
            json.dump(photo_info, f, indent=2)

        for label_name in self._label_names:
            if label_name not in self._label_hierarchies:
                continue
            with open(self._location / f'{label_name}_labels.json', 'w') as f:
                lab_hier: LabelHierarchy = self._label_hierarchies[label_name]
                json.dump(lab_hier.to_dict(), f, indent=2)

        #except IOError as e:
        #    logger.error(e.strerror)
        #    return False
        #except Exception as e:
        #    print('what')
        #finally:
        #    return True
        return True

    def include_photos(self, photo_names: List[str], scale: Optional[int]):
        new_images = [self._load_photo(img_name) for img_name in photo_names]
        new_paths = [self._image_folder / img_name for img_name in photo_names]

        for img in new_images:
            for lbl_name in self._label_names:
                img.approved[lbl_name] = None
                img.image_scale = scale
        self._images.extend(new_images)
        self._image_paths.extend(new_paths)
        self._image_names.extend(photo_names)
        self._image_names_indices = {name: i for i, name in enumerate(self._image_names)}
        self.storage_update.emit({'photos': {'included': photo_names, 'deleted': []}})
        self.save()

    @property
    def storage_name(self) -> str:
        return self._location.name

    @storage_name.setter
    def storage_name(self, name: str):
        #self._storage_name = name
        pass

    def get_approval(self, name_or_index: Union[str, int], label_name: str) -> str:
        if isinstance(name_or_index, str):
            photo = self.get_photo_by_name(name_or_index)
        else:
            photo = self.get_photo_by_idx(name_or_index)
        return photo.approved[label_name]

    def used_regions(self, label_name: str) -> Set[int]:
        regions = set()
        for photo in self._images:
            regions = regions.union(photo[label_name].used_labels)
        return regions

    @property
    def label_image_names(self) -> Set[str]:
        return self._label_names

    @property
    def label_img_info(self) -> Dict[str, LabelImgInfo]:
        return self._lbl_img_info

    def notify(self, img_name: str, ctx: UpdateContext, data: Optional[Dict[str, typing.Any]] = None):
        # print(f'relaying update event {ctx} with data {data} for the photo {img_name}')
        # TODO react to change in tag change event
        storage_update_data: typing.Dict[str, typing.Any] = {
        }
        if 'tags' in data:
            storage_update_data['tags'] = {}
            for tag in data['tags']['added']:
                if tag not in self._tag_useg_counter:
                    storage_update_data['tags'].setdefault('new', set()).add(tag)
                self._tag_useg_counter.update([tag])
            for tag in data['tags']['removed']:
                self._tag_useg_counter.subtract([tag])
                if self._tag_useg_counter[tag] < 1:
                    storage_update_data['tags'].setdefault('deleted', set()).add(tag)
        self.update_photo.emit(img_name, ctx, data)
        self.storage_update.emit(storage_update_data)

    def delete_photo(self, img_name: str, parent: QWidget) -> bool:
        idx = self.image_names.index(img_name)
        photo = self.get_photo_by_idx(idx)

        # First delete the photo from the Storage
        self._images = [photo for i, photo in enumerate(self._images) if i != idx]
        self._image_paths = [path for i, path in enumerate(self._image_paths) if i != idx]
        self._image_names.remove(photo.image_name)
        # del self._image_names_indices[photo.image_name]
        self._image_names_indices = {name: i for i, name in enumerate(self._image_names)}

        # Emit signal that a photo was deleted, this will mainly trigger the update for the image list
        self.storage_update.emit({'photos': {'deleted': [img_name]}})

        try:
            os.remove(photo.image_path)
        except PermissionError:
            QMessageBox.critical(parent, "Failure", f'Cannot delete the file {photo.image_path}! Maybe it is opened in another program?',
                                 QMessageBox.Ok, QMessageBox.Ok)
            return False
        except FileNotFoundError:
            QMessageBox.critical(parent, "Failure", f'The file {photo.image_path} no longer exists!',
                                 QMessageBox.Ok, QMessageBox.Ok)
        photo_tags = list(photo.tags)
        # Update the counts for individual tags, if a tag reaches the count 0, emit a signal
        self._tag_useg_counter.subtract(photo_tags)
        deleted_tags = [tag for tag in photo_tags if self._tag_useg_counter[tag] == 0]
        self.storage_update.emit({'tags': {'deleted': deleted_tags}})

        for lbl_img in photo.label_images_.values():
            if lbl_img.path.exists():
                delete_file(lbl_img.path, parent)
            if (meas_path := Path(f'{lbl_img.path}_measurements.json')).exists():
                delete_file(meas_path, parent)

        return True

    @property
    def used_tags(self) -> typing.Set[str]:
        tags: typing.Set[str] = set()
        for photo in self._images:
            tags = tags.union(photo.tags)
        return tags

    def photos_satisfying_tags(self, tags: typing.Set[str]) -> typing.List[Photo]:
        tag_photos_map: typing.Dict[str, typing.Set[Photo]] = {}
        for photo in self._images:
            for tag in photo.tags:
                tag_photos_map.setdefault(tag, set()).add(photo)
        sat = functools.reduce(set.intersection, [tag_photos_map.setdefault(tag, set()) for tag in tags], set(self._images))
        return list(sat)

    @property
    def properties(self) -> typing.Dict[str, typing.Dict[str, RegionProperty]]:
        return self._properties


def delete_file(fpath: Path, parent: QWidget) -> bool:
    try:
        os.remove(fpath)
    except PermissionError:
        QMessageBox.critical(parent, "Failure",
                             f'Cannot delete the file {fpath}! Maybe it is opened in another program?',
                             QMessageBox.Ok, QMessageBox.Ok)
        return False
    except FileNotFoundError:
        QMessageBox.critical(parent, "Failure", f'The file {fpath} no longer exists!',
                             QMessageBox.Ok, QMessageBox.Ok)
    return True


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