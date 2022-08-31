import copy
import typing
from typing import Optional

import numpy as np

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.user_params import UserParam


class MeanIntensity(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Mean intensity
    DESCRIPTION: Mean intensity (R, G, B)
    KEY: mean_intensity
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:

        props: typing.List[RegionProperty] = []
        refl = photo['Reflections'].label_image

        for region_label in region_labels:
            if region_label not in regions_cache.regions:
                continue
            region: Region = regions_cache.regions[region_label]

            top, left, height, width = region.bbox
            refl_roi = refl[top:top + height, left:left + width]

            mask = np.logical_xor(region.mask, refl_roi > 0)

            yy, xx = np.nonzero(mask)

            pixels = region.image[yy, xx]

            mean_intensity = np.mean(pixels, axis=0)

            prop = RegionProperty()
            prop.info = copy.deepcopy(self.example('mean_intensity').info)
            prop.label = int(region.label)
            prop.value = (mean_intensity.tolist(), self._no_unit)
            prop.prop_type = PropertyType.Intensity
            prop.num_vals = 3
            prop.val_names = ['R', 'G', 'B']

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
        prop.prop_type = PropertyType.Intensity
        prop.val_names = ['R', 'G', 'B']
        prop.num_vals = 3
        return prop

    def target_worksheet(self, prop_name: str) -> str:
        return super(MeanIntensity, self).target_worksheet(self.info.key)

    @property
    def group(self) -> str:
        return super().group
