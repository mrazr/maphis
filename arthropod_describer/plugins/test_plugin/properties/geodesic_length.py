import copy
import typing
from typing import Optional

import skimage.io
from skimage.morphology import skeletonize, medial_axis

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.units import Value
from arthropod_describer.common.user_params import UserParam
from arthropod_describer.plugins.test_plugin.properties.geodesic_utils import compute_longest_geodesic, \
    compute_longest_geodesic_perf


class GeodesicLength(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Geodesic length
    DESCRIPTION: Geodesic length (px or mm)
    KEY: geodesic_length
    """

    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:
        # lab_img = photo['Labels'].label_image
        props: typing.List[RegionProperty] = []
        for label in region_labels:
            # _, length = get_longest_geodesic(lab_img, label)
            if label not in regions_cache.regions:
                continue
            region_obj = regions_cache.regions[label]
            # length, _, _ = compute_longest_geodesic(region_obj.mask)
            # skeleton = skeletonize(region_obj.mask)
            length = compute_longest_geodesic_perf(region_obj.mask)
            # compute_longest_geodesic(lab_img == label)
            if length < 0:
                continue
            prop = RegionProperty()
            prop.label = int(label)
            prop.info = copy.deepcopy(self.info)
            value = Value(float(length), self._px_unit)
            if photo.image_scale is not None:
                # prop.unit = 'mm'
                prop.value = value / photo.image_scale
            else:
                prop.value = value
            prop.val_names = ['Geodesic length']
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
        return super(GeodesicLength, self).target_worksheet(self.info.key)

    @property
    def group(self) -> str:
        return super().group
