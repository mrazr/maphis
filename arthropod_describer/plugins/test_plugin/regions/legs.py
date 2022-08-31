from typing import Optional, Set, List

import cv2 as cv
import numpy as np

from arthropod_describer.common.photo import Photo, LabelImg
from arthropod_describer.common.plugin import RegionComputation
from arthropod_describer.common.user_params import UserParam


class LegsRegion(RegionComputation):
    """
    NAME: LegRegions
    DESCRIPTION: Identifies leg regions from a bug mask.

    USER_PARAMS:
            PARAM_NAME: Max leg width
            PARAM_KEY: max_leg_width
            PARAM_DESC: Maximum width of legs in pixels
            PARAM_TYPE: INT
            DEFAULT_VALUE: 25
            MIN_VALUE: 3
            MAX_VALUE: 125
    """
    def __init__(self):
        super().__init__(None)

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None, storage=None) -> List[LabelImg]:
        reg_lbl = photo['Labels']
        diam = self._user_params['max_leg_width'].value
        bin = 255 * (reg_lbl.label_image > 0).astype(np.uint8)
        body = cv.morphologyEx(bin, cv.MORPH_OPEN,
                              cv.getStructuringElement(cv.MORPH_ELLIPSE, (diam, diam)))
        legs = bin - body
        leg_label = photo['Labels'].label_hierarchy.label('1:2:0:0')
        body_label = photo['Labels'].label_hierarchy.label('1:1:0:0')
        legs = np.where(legs > 0, leg_label, 0).astype(np.uint32)
        body = np.where(body > 0, body_label, legs).astype(np.uint32)
        new_lab = photo['Labels'].clone()
        new_lab.label_image = body
        return [new_lab]

    @property
    def user_params(self) -> List[UserParam]:
        return list(self._user_params.values())


