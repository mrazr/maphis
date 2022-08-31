import copy
import typing
from typing import List, Optional

import numpy as np
import skimage

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.units import Value, Unit, BaseUnit, SIPrefix
from arthropod_describer.common.user_params import UserParam


class Circularity(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Circularity
    DESCRIPTION: Circularity (0.0 to 1.0, where 1.0 = perfect circle)
    KEY: circularity
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:

        lab_img = photo['Labels'].label_image
        reg_props = skimage.measure.regionprops_table(lab_img, photo.image,
                                                      properties=['label', 'perimeter'])  #perimeter_measurement_flavor])
        props: List[RegionProperty] = []

        for idx, label in enumerate(reg_props['label']):
            if label not in region_labels:
                continue

            perimeter = reg_props['perimeter'][idx]#[perimeter_measurement_flavor][idx]
            area = int(np.count_nonzero(lab_img == label))
            if perimeter == 0:
                circularity = 0 # TODO: Careful about division by zero (can we somehow return N/A here?)
            else:
                circularity = np.clip((4 * np.pi * area) / (perimeter ** 2), 0.0, 1.0)
            #print(f'idx: {idx}, label: {label}')
            #print(f'  perimeter: {perimeter}')
            #print(f'  area: {area}')
            #print(f'  circularity: {circularity}')

            prop = RegionProperty()
            prop.label = int(label)
            prop.info = copy.deepcopy(self.info)
            prop.value = Value(float(circularity), self._no_unit)
            # prop.unit = '' # TODO: Is this ok for a unitless property?
            prop.prop_type = PropertyType.Scalar
            prop.val_names = [self.info.name]
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
        return {self.info.key: self.info}

    def example(self, prop_name: str) -> RegionProperty:
        prop = RegionProperty()
        prop.label = 0
        prop.info = copy.deepcopy(self.info)
        # prop.value = int(np.count_nonzero(lab_img == label))
        prop.value = Value(0, self._no_unit)
        prop.prop_type = PropertyType.Scalar
        prop.val_names = [self.info.name]
        prop.num_vals = 1
        return prop

    def target_worksheet(self, prop_name: str) -> str:
        return super(Circularity, self).target_worksheet(self.info.key)

    @property
    def group(self) -> str:
        return super().group
