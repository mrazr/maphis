from typing import List, Optional, Set

import numpy as np
from skimage import io

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import LabelImg
from arthropod_describer.common.photo import Photo

from arthropod_describer.common.plugin import RegionComputation
from arthropod_describer.plugins.test_plugin.properties.geodesic_utils import get_longest_geodesic2, \
    geodesic_distance_for_skeleton


class RegionDivider(RegionComputation):
    """
    NAME: Region divider
    DESCRIPTION: A method to divide given regions into 'n' regions, where 'n' is the number of children of each region in the given label hierarchy.

    REGION_RESTRICTED
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None, storage=None) -> List[LabelImg]:
        # TODO `labels` for now is hard-coded for `legXY` (X is {1,..,4}, Y is {L, R} regions
        labels = [16908544, 16908800, 16909056, 16909312, 16909568, 16909824, 16910080, 16910336]
        lbl_img = photo.label_images_['Labels']
        lab_hier = lbl_img.label_hierarchy

        for label in labels:
            if len(lab_hier.children[label]) == 0:
                continue
            region = lbl_img.label_image == label
            geodesic, length, bbox = get_longest_geodesic2(region)

            region_ = region[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]

            if len(geodesic) == 0:
                continue

            num_sections = len(lab_hier.children[label])

            step = len(geodesic) // num_sections

            geod_dsts: np.ndarray = np.zeros((region_.shape[0], region_.shape[1], num_sections+1), dtype=np.float32)
            geod_dsts[:, :, 0] = 99999.0
            for i, lab_child in enumerate(lab_hier.children[label]):
                section_mid = geodesic[i * step + step // 2]
                geod_dst = geodesic_distance_for_skeleton(region_, section_mid)
                geod_dst = np.where(geod_dst < 0, 999999.0, geod_dst)
                geod_dsts[:, :, i+1] = geod_dst

            argmins = np.argmin(geod_dsts, axis=-1)

            result_lbl = lbl_img.label_image
            for i, lab_child in enumerate(lab_hier.children[label]):
                result_lbl[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1] = np.where(argmins == i + 1,
                                                                            lab_child,
                                                                            result_lbl[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1])

        return [lbl_img]

