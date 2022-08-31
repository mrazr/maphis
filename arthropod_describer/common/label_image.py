import json
from enum import IntEnum
from pathlib import Path
from typing import Optional, Any, List, Dict, Tuple, Union
import time

import numpy as np
import typing
from PIL import Image
from PySide2.QtGui import QPixmap
from scipy import ndimage
from skimage import io

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_hierarchy import LabelHierarchy
from arthropod_describer.common.units import Value, CompoundUnit, Unit, BaseUnit, SIPrefix


class PropertyType(IntEnum):
    String = 0,
    Scalar = 1,
    Vector = 2,
    Intensity = 3,
    Other = 4
    NDArray = 5
    IntensityHSV = 6


class RegionProperty:
    def __init__(self):
        self._info: Optional[Info] = None
        self.label: int = -1
        self.value: Optional[Union[Value, Tuple[List[Any], Union[CompoundUnit, Unit]]]] = None  # either Value, or a tuple of list of values(float, int...) and a Unit
        self.prop_type: PropertyType = PropertyType.Scalar
        self.num_vals: int = 1
        self.val_names: List[str] = []  # names of individual scalar values or matrices
        self.col_names: List[str] = []  # in the case when self.prop_type = PropertyType.NDArray
        self.row_names: List[str] = []  # same here
        self.vector_viz: Optional[QPixmap] = None

        self._str_rep: str = ''
        self._update_str_rep()

    @property
    def info(self) -> Optional[Info]:
        return self._info

    @info.setter
    def info(self, info: Optional[Info]):
        self._info = info
        self._update_str_rep()

    def __str__(self) -> str:
        # return f'{self.info.name}: {self.format_value()} {self.unit}'
        if len(self._str_rep) == 0:
            self._update_str_rep()
        return self._str_rep

    def _update_str_rep(self):
        if self.value is None:
            return
        if isinstance(self.value, Value):
            self._str_rep = f'{"" if self._info is None else self._info.name}: {self.value}'
            return
        val_str = self.format_value()
        self._str_rep = f'{"" if self._info is None else self.info.name}: {val_str} {self.value[1]}'

    def format_value(self) -> str:
        if self.prop_type == PropertyType.Scalar:  # So self.value is of type `Value`
            # if type(self.value) == float:
            #     return f'{self.value:.2f}'
            return str(self.value)
        elif self.prop_type == PropertyType.Intensity: # self.value is of type Tuple[List[Any], CompoundUnit]
            if self.num_vals == 1:
                if type(self.value[0][0]) == float:
                    return f'{self.value[0][0]:.2f} {self.val_names[0]}'
                return f'{self.value[0][0]} {self.val_names[0]}'
            else:
                val_string = '('
                for i in range(self.num_vals):
                    val_string += f'{self.value[0][i]:.2f} {self.val_names[i]}, '
                return val_string[:-2] + ')'
        elif self.prop_type == PropertyType.Vector:
            val_string = ''
            for i in range(self.num_vals):
                val_string += f'{self.value[0][i]:.2f}, '
            return val_string[:-2]
        else:
            val_string = ''
            #print(f"self.prop_type: {self.prop_type}")
            #print(f"self.num_vals: {self.num_vals}")
            #print(f"self.value: {self.value}")
            for i in range(self.num_vals):
                val_string += f'{self.value[0][i]}, '
            #print(f"val_string[:-2]: {val_string[:-2]}")
            return val_string[:-2]
        raise ValueError(f'Unsupported type of value: {type(self.value)}')

    @classmethod
    def from_dict(cls, dict_obj: Dict[str, Any]) -> 'RegionProperty':
        reg_prop = RegionProperty()
        reg_prop.label = dict_obj['label']
        reg_prop.prop_type = PropertyType(dict_obj['prop_type'])
        if reg_prop.prop_type == PropertyType.NDArray:
            path_unit = eval(dict_obj['value'])
            reg_prop.value = (np.load(path_unit[0]), path_unit[1])
        else:
            reg_prop.value = eval(dict_obj['value'])
        # reg_prop.unit = dict_obj['unit']
        reg_prop.num_vals = dict_obj['num_vals']
        reg_prop.val_names = dict_obj['val_names']
        reg_prop.col_names = dict_obj['col_names']
        reg_prop.row_names = dict_obj['row_names']
        info = Info()
        info.name = dict_obj['name']
        info.key = dict_obj['key']
        info.description = dict_obj['description']
        reg_prop.info = info
        return reg_prop


class LabelImgType(IntEnum):
    Mask = 0,
    Regions = 1,


class LabelImgInfo:
    """Info about a particular `LabelImg` object."""
    def __init__(self, label_name: str, is_default: bool, always_constrain_to: Optional[str] = None,
                 allow_constrain_to: Optional[List[str]] = None):
        self.name: str = label_name
        self.is_default = is_default  # if this is the default label image to show at startup
        self.constrain_to: Optional[str] = always_constrain_to  # whether the editing should be always constrained to some other label image
        self.can_constrain_to: Optional[List[str]] = allow_constrain_to  # what other label images can serve as constraints

        if self.constrain_to is not None:
            self.can_constrain_to = None

    @property
    def can_be_constrained(self) -> bool:
        return self.constrain_to is not None or self.can_constrain_to is not None


class LabelImg:
    """A class representing a label image.

    image_size: (int, int) in format (height, width) format
    """
    def __init__(self, image_size: Tuple[int, int]):
        self._label_img: Optional[np.ndarray] = None
        self.size = image_size
        self._path: typing.Optional[Path] = None
        self._bbox: typing.Optional[typing.Tuple[int, int, int, int]]
        self._region_props: Dict[int, Dict[str, RegionProperty]] = {}
        self._label_hierarchy: Optional[LabelHierarchy] = None
        self.label_img_type: LabelImgType = LabelImgType.Regions
        self.label_info: typing.Optional[LabelImgInfo] = None
        self.label_semantic: str = ''
        self._used_labels: Optional[typing.Set[int]] = None
        self._dirty_flag: bool = False
        self.prop_list: typing.List[RegionProperty] = []
        self.timestamp: int = -1
        self.is_segmented: bool = False

    @property
    def path(self) -> typing.Optional[Path]:
        if self._path is not None:
            return self._path
        return None

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def label_image(self) -> np.ndarray:
        if self._label_img is None:
            if self._path.exists():
                self._label_img = io.imread(str(self._path))
                self.is_segmented = bool(np.any(self._label_img > 0))
            else:
                self._label_img = np.zeros(self.size[::-1], np.uint32)
        return self._label_img

    @label_image.setter
    def label_image(self, lbl_nd: np.ndarray):
        if self._label_img is None:
            self._label_img = lbl_nd
        else:
            self.set_image(lbl_nd)
        self.is_segmented = bool(np.any(self._label_img > 0))
        self._dirty_flag = True

    @property
    def is_set(self) -> bool:
        return self._label_img is not None

    def reload(self):
        if self._path.exists():
            loaded_img = io.imread(str(self._path))
            self._label_img = loaded_img.astype(np.uint32)
            self._used_labels = set(np.unique(self._label_img))
        else:
            self._label_img = np.zeros(self.size[::-1], dtype=np.uint32)
            self._used_labels = {0}

    def unload(self):
        self.save()
        self._label_img = None

    def _serialize_prop_value(self, reg_prop: RegionProperty) -> Union[typing.Any, str]:
        """Returns a representation of `RegionProperty.value` in a form suitable for serialization in .json."""
        if reg_prop.prop_type == PropertyType.NDArray:
            path = f'{self._path}_{reg_prop.info.name}_{reg_prop.label}.npy'
            np.save(path, reg_prop.value[0])
            return repr((path, reg_prop.value[1]))  # return path to the serialized ndarray and the unit that the array is in
        return repr(reg_prop.value)

    def save(self):
        if self._dirty_flag:
            if self._label_img is not None:
                self._used_labels = set(np.unique(self._label_img))
                io.imsave(str(self._path), self._label_img, check_contrast=False)
                #im = Image.fromarray(self._label_img)
                #im.save(self._path)
            prop_dict = {
                self.label_hierarchy.code(label): {
                    'measurements': [
                        {
                            'name': prop.info.name,
                            'label': prop.label,
                            'value': self._serialize_prop_value(prop),
                            # 'unit': prop.unit,
                            'prop_type': prop.prop_type,
                            'num_vals': prop.num_vals,
                            'val_names': prop.val_names,
                            'col_names': prop.col_names,
                            'row_names': prop.row_names,
                            'key': prop.info.key,
                            'description': prop.info.description
                        }
                        for prop in prop_dict.values()
                    ]
                } for label, prop_dict in self._region_props.items()
            }
            with open(f'{self._path}_measurements.json', 'w') as f:
                json.dump(prop_dict, f, indent=2)
            self._dirty_flag = False

    @classmethod
    def create2(cls, path: Path, image_size: typing.Tuple[int, int], label_info: LabelImgInfo, label_name: str) -> 'LabelImg':
        """Creates new `LabelImg` object.

        path: Path - where this label image should be stored
        image_size: (height, width)
        label_info: LabelImgInfo
        label_name: str - not used, stored in `label_info`
        """
        lbl = LabelImg(image_size)
        #lbl._type = label_type
        lbl._path = path
        #lbl.label_img_type = label_type
        lbl.label_info = label_info
        lbl.label_semantic = label_info.name
        lbl._load_measurements()
        return lbl

    def make_empty(self, size: typing.Tuple[int, int]):
        self._label_img = np.zeros(size, np.uint32)
        self._used_labels = {0}

    def set_image(self, img: np.ndarray):
        if self._label_img is not None and img is not None:
            if self._label_img.shape != img.shape:
                raise ValueError(f'The shape must be {self._label_img.shape}, got {img.shape}.')
            elif self._label_img.dtype != img.dtype:
                raise ValueError(f'The dtype must be {self._label_img.dtype}, got {img.dtype}.')
        self._label_img = img
        self._dirty_flag = True

    def clone(self) -> 'LabelImg':
        lbl = LabelImg(self.size)
        lbl._path = self._path
        lbl._label_img = self._label_img.copy() if self._label_img is not None else None
        # lbl.label_img_type = self.label_img_type
        lbl.label_info = self.label_info
        lbl.label_semantic = self.label_semantic
        lbl._label_hierarchy = self._label_hierarchy
        lbl._used_labels = self._used_labels
        lbl._dirty_flag = self._dirty_flag
        return lbl

    def _compute_bbox(self):
        coords = np.nonzero(self._label_img)
        top, left = np.min(coords[0]), np.min(coords[1])
        bottom, right = np.max(coords[0]), np.max(coords[1])
        self._bug_bbox = [left, top, right, bottom]

    @property
    def region_props(self) -> Dict[int, Dict[str, RegionProperty]]:
        """Returns a dictionary of (label -> (property_key -> `RegionProperty`) pairs."""
        return self._region_props

    @region_props.setter
    def region_props(self, props: Dict[int, Dict[str, RegionProperty]]):
        for label, props in props.items():
            label_props = self._region_props.setdefault(label, dict())
            for prop_key, prop in props.items():
                label_props[prop_key] = prop
                #label_prop = label_props.setdefault(prop_key, RegionProperty())
                #label_prop.label = prop.label
                #label_prop.info = prop.info
                #label_prop.value = prop.value
                #label_prop.unit = prop.unit
                #label_prop.prop_type = prop.prop_type
                #label_prop.num_vals = prop.num_vals
        self._dirty_flag = True

    def clear_region_props(self):
        self._region_props.clear()

    def set_region_prop(self, region_label: int, prop: RegionProperty):
        self.region_props = {region_label: {prop.info.key: prop}}
        self.prop_list.append(prop)

    def get_region_props(self, region_label: int) -> Optional[Dict[str, RegionProperty]]:
        """Returns (property_key -> `RegionProperty) for `region_label`."""
        if region_label in self._region_props:
            return self._region_props[region_label]
        return None

    @property
    def label_hierarchy(self) -> LabelHierarchy:
        return self._label_hierarchy

    @label_hierarchy.setter
    def label_hierarchy(self, lab_hier: LabelHierarchy):
        # TODO handle possible changes to the label image
        self._label_hierarchy = lab_hier

    def __getitem__(self, level: int) -> Optional[np.ndarray]:
        """Returns a label image generated from this one, where all the labels are from the level `level` of `label_hierarchy`."""
        if self._label_hierarchy is None:
            return self.label_image
        if level >= len(self._label_hierarchy.masks):
            return None
        level_mask = self._label_hierarchy.level_mask(level)
        return np.bitwise_and(self.label_image, level_mask)

    @property
    def used_labels(self) -> Optional[typing.Set[int]]:
        """Returns the set of labels that are present in this label image."""
        if self._dirty_flag or self._used_labels is None:
            self._used_labels = set(np.unique(self.label_image))
            self._dirty_flag = False
        return self._used_labels

    def set_dirty(self):
        self._dirty_flag = True
        self.timestamp = time.time()

    def _load_measurements(self):
        if (path := Path(f'{str(self._path)}_measurements.json')).exists():
            with open(path) as f:
                props = json.load(f)
            for code in props.keys():
                for prop_dict in props[code]['measurements']:
                    reg_prop = RegionProperty.from_dict(prop_dict)
                    self.set_region_prop(reg_prop.label, reg_prop)
            self._dirty_flag = False

    def rotate(self, ccw: bool):
        unload = self._label_img is not None
        if self._label_img is None:
            self.reload()
        self._label_img = ndimage.rotate(self._label_img, 90 if ccw else -90, order=0, prefilter=False)
        self._dirty_flag = True
        if unload:
            self.unload()

    #def save(self):
    #    if self._dirty_flag:
    #        self.unload()
    #        self._dirty_flag = False

    def resize(self, factor: float):
        unload = self._label_img is not None
        if self._label_img is None:
            self.reload()
        im = Image.fromarray(self._label_img)
        sz = (int(round(factor * self.size[0])),
              int(round(factor * self.size[1])))
        self.size = sz
        im = im.resize(sz, resample=Image.NEAREST)
        self._label_img = np.asarray(im, dtype=np.uint32)
        self._dirty_flag = True
        if unload:
            self.unload()

    def mask_for(self, label: int) -> np.ndarray:
        """Returns a binary (np.bool) image where `True` values mark pixels whose value is `label` or are descendants of `label`."""
        level = self.label_hierarchy.get_level(label)
        level_img = self[level]
        return level_img == label

    @property
    def has_unsaved_changed(self) -> bool:
        return self._dirty_flag
