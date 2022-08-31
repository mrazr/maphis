import copy
import typing
from typing import Optional

import numpy as np
import scipy.ndimage
from skimage.morphology import binary_erosion

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.units import Value
from arthropod_describer.common.user_params import UserParam
from arthropod_describer.plugins.test_plugin.properties.geodesic_utils import compute_longest_geodesic, \
    find_shortest_path


class MeanWidth(PropertyComputation):
    """
    GROUP: Basic properties
    NAME: Mean width
    DESCRIPTION: Mean width of a region (px or mm)
    KEY: mean_width
    """

    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:
        lab_img = photo['Labels']
        props: typing.List[RegionProperty] = []

        for label in region_labels:
            bin_img = lab_img.mask_for(label)
            if not np.any(bin_img):
                continue
            # geodesic, length, bbox = get_longest_geodesic2(bin_img)
            # bin_roi = bin_img[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            gdist, px1, px2 = compute_longest_geodesic(bin_img)
            geodesic = find_shortest_path(bin_img, px1, px2)
            geodesic = ([px[1] for px in geodesic], [px[0] for px in geodesic])
            outline = np.logical_and(bin_img, binary_erosion(bin_img, footprint=np.ones((3, 3), dtype=np.uint8)))
            dst: np.ndarray = scipy.ndimage.distance_transform_edt(outline)
            mean_width = np.mean(2.0 * dst[geodesic[0], geodesic[1]])
            if np.isnan(mean_width):
                # TODO inspect `get_longest_geodesic2` function
                mean_width = -42.0

            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\mean_width\\{label}_bin_roi.png', bin_roi, check_contrast=False)
            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\mean_width\\{label}_outline.png', outline, check_contrast=False)
            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\mean_width\\{label}_dst.png',
            #           (255.0 * (dst / (np.max(dst) + 1e-6))).astype(np.uint8), check_contrast=False)

            prop = RegionProperty()
            prop.info = copy.deepcopy(self.info)
            prop.prop_type = PropertyType.Scalar
            prop.label = label
            if photo.image_scale is not None:
                prop.value = Value(float(mean_width), self._px_unit) / photo.image_scale
                # prop.unit = 'mm'
            else:
                prop.value = Value(float(mean_width), self._px_unit)
                # prop.unit = 'px'
            prop.num_vals = 1
            prop.val_names = ['Mean width']
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
        return super(MeanWidth, self).target_worksheet(self.info.key)

    @property
    def group(self) -> str:
        return super().group
