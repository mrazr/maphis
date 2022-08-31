import copy
import typing
from typing import Optional

import numpy as np
import skimage

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache
from arthropod_describer.common.units import Value
from arthropod_describer.common.user_params import UserParam


class MaxFeret(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Max feret diameter
    DESCRIPTION: Maximum Feret diameter (px or mm)
    KEY: max_feret
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:
        props: typing.List[RegionProperty] = []

        for label in region_labels:
            if label not in regions_cache.regions:
                continue
            region_obj = regions_cache.regions[label]
            reg_props = skimage.measure.regionprops_table(region_obj.mask.astype(np.uint8), region_obj.image,
                                                          properties=['label', 'feret_diameter_max'])

            prop = RegionProperty()
            prop.label = int(label)
            prop.info = copy.deepcopy(self.info)
            prop.value = Value(float(reg_props['feret_diameter_max'][0]), self._px_unit)
            if photo.image_scale is not None and photo.image_scale.value > 0:
                prop.value = prop.value / photo.image_scale
                prop.unit = 'mm'  # TODO sync unit with the units in Photo
            else:
                prop.unit = 'px'
            prop.prop_type = PropertyType.Scalar
            prop.val_names = ['Max Feret']
            prop.num_vals = 1
            props.append(prop)
        return props

    @property
    def user_params(self) -> typing.List[UserParam]:
        return super().user_params

    @property
    def region_restricted(self) -> bool:
        return super().region_restricted

    @property
    def computes(self) -> typing.Dict[str, Info]:
        return {self.info.key: self.info}

    def example(self, prop_name: str) -> RegionProperty:
        prop = RegionProperty()
        prop.label = 0
        prop.info = copy.deepcopy(self.info)
        prop.value = None
        prop.num_vals = 1
        prop.prop_type = PropertyType.Scalar
        prop.val_names = []
        return prop

    def target_worksheet(self, prop_name: str) -> str:
        return super(MaxFeret, self).target_worksheet(self.info.key)

    @property
    def group(self) -> str:
        return super().group
