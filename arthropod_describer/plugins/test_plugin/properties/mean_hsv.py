import copy
import typing
from typing import Optional

import numpy as np
from skimage.color import rgb2hsv

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.user_params import UserParam


class MeanHSV(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Mean HSV
    DESCRIPTION: Mean HSV of a region
    KEY: mean_hsv
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:

        props: typing.List[RegionProperty] = []

        lab_img = photo['Labels']
        hsv_img = rgb2hsv(photo.image)
        hsv_img[:, :, 0] = 360 * hsv_img[:, :, 0]

        reflection = photo['Reflections'].label_image

        for label in region_labels:
            region_mask = np.logical_and(lab_img.mask_for(label), reflection == 0)
            ys, xs = np.nonzero(region_mask)

            if len(ys) == 0:
                continue

            hues = hsv_img[ys, xs, 0]

            hue_radians = np.pi * hues / 180.0

            avg_sin = np.mean(np.sin(hue_radians))
            avg_cos = np.mean(np.cos(hue_radians))

            average_vector_angle = np.arctan2(avg_sin, avg_cos)

            average_vector_degrees = np.mod((180.0 / np.pi) * average_vector_angle, 360)

            average_vector_length = np.sqrt(avg_sin * avg_sin + avg_cos * avg_cos)

            mean_sat = np.mean(hsv_img[ys, xs, 1])
            mean_val = np.mean(hsv_img[ys, xs, 2])

            prop = copy.deepcopy(self.example('mean_hsv'))
            prop.value = ([float(average_vector_degrees),
                           100 * float(mean_sat * average_vector_length),
                           100 * float(mean_val)],
                          self._no_unit)
            prop.label = label
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
        prop.num_vals = 3
        prop.prop_type = PropertyType.IntensityHSV
        prop.val_names = ['H', 'S', 'V']
        return prop

    def target_worksheet(self, prop_name: str) -> str:
        return super(MeanHSV, self).target_worksheet(self.info.key)

    @property
    def group(self) -> str:
        return super().group
