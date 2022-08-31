import copy
import os
import subprocess
import typing
from pathlib import Path
from typing import Optional

import numpy as np
import scipy.ndimage
import skimage
from skimage import img_as_ubyte
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
    NAME: Mean width (cpp)
    DESCRIPTION: Mean width of a region (px or mm)
    KEY: mean_width_cpp
    """

    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:
        lab_img = photo['Labels']
        props: typing.List[RegionProperty] = []

        for label in region_labels:
            if label not in regions_cache.regions:
                continue
            bin_img = regions_cache.regions[label].mask
            if not np.any(bin_img):
                continue

            region_obj = regions_cache.regions[label]
            bin_path = Path(__file__).parent / 'bin/geodesic_length.exe'
            reg_path = Path(__file__).parent / f'body_region_{photo.image_name}.png'
            skimage.io.imsave(str(reg_path), img_as_ubyte(region_obj.mask), check_contrast=False)
            out_path = Path(__file__).parent / f'result_{photo.image_name}.txt'
            args = [
                str(bin_path),
                str(reg_path),
                str(out_path)
            ]

            return_obj = subprocess.run(args, cwd=str(bin_path.parent))
            if return_obj.returncode != 0:
                os.remove(reg_path)
                os.remove(out_path)
                continue
            geodesic_xx, geodesic_yy = [], []

            with open(out_path) as f:
                lines = f.readlines()
                # length = float(lines[0].strip())
                src_split = lines[1].strip().split(',')
                # src_pixel = (int(src_split[0]), int(src_split[1]))

                dst_split = lines[2].strip().split(',')
                # dst_pixel = (int(dst_split[0]), int(dst_split[1]))

                geodesic_pixels_str = lines[3].split(';')

                for pixel_str in geodesic_pixels_str:
                    if pixel_str == '':
                        continue
                    spl = pixel_str.split(',')
                    x, y = int(spl[0]), int(spl[1])

                    geodesic_xx.append(x)
                    geodesic_yy.append(y)

            outline = np.logical_and(bin_img, binary_erosion(bin_img, footprint=np.ones((3, 3), dtype=np.uint8)))
            dst: np.ndarray = scipy.ndimage.distance_transform_edt(outline)
            mean_width = np.mean(2.0 * dst[geodesic_yy, geodesic_xx])
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
            os.remove(reg_path)
            os.remove(out_path)
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
