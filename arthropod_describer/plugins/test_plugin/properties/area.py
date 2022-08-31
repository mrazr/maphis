import copy
import typing
from typing import List, Optional

import numpy as np

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.units import Value
from arthropod_describer.common.user_params import UserParam


class Area(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Area
    DESCRIPTION: Area of the region (px or mm\u00b2)
    KEY: area

    USER_PARAMS:
        PARAM_NAME: Magic number
        PARAM_TYPE: INT
        PARAM_KEY: magic_number
        VALUE: 42
        MIN_VALUE: 40
        MAX_VALUE: 45

        PARAM_NAME: Magic word
        PARAM_TYPE: STR
        PARAM_KEY: magic_word
        VALUE: please

        PARAM_NAME: Yes/No
        PARAM_TYPE: BOOL
        PARAM_KEY: magic_bool
        VALUE: True
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
    typing.List[RegionProperty]:

        props: typing.List[RegionProperty] = []

        for region_label in region_labels:
            if region_label not in regions_cache.regions:
                continue
            region: Region = regions_cache.regions[region_label]

            prop = RegionProperty()
            prop.label = region.label
            prop.info = copy.deepcopy(self.info)
            # prop.value = int(np.count_nonzero(lab_img == label))
            value = Value(int(np.count_nonzero(region.mask)), self._px_unit * self._px_unit)
            if photo.image_scale is not None and photo.image_scale.value > 0:
                prop.value = value / (photo.image_scale * photo.image_scale)
                # prop.unit = 'mm\u00b2'  # TODO sync unit with the units in Photo
            else:
                prop.value = value
            prop.prop_type = PropertyType.Scalar
            prop.val_names = ['Area']
            prop.num_vals = 1
            props.append(prop)
        return props

    @property
    def user_params(self) -> List[UserParam]:
        return super().user_params

    @property
    def region_restricted(self) -> bool:
        return super().region_restricted

    @property
    def computes(self) -> typing.Dict[str, Info]:
        return {'area': self.info}

    def example(self, prop_name: str) -> RegionProperty:
        prop = RegionProperty()
        prop.label = 0
        prop.info = copy.deepcopy(self.info)
        # prop.value = int(np.count_nonzero(lab_img == label))
        prop.value = Value(0, self._px_unit * self._px_unit)
        prop.prop_type = PropertyType.Scalar
        prop.val_names = ['Area']
        prop.num_vals = 1
        return prop

    def target_worksheet(self, prop_name: str) -> str:
        return super(Area, self).target_worksheet('area')

    @property
    def group(self) -> str:
        return super().group
