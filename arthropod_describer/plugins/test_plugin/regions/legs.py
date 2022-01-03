from typing import Optional, Set, List

import numpy as np
import skimage.morphology
import cv2 as cv

from arthropod_describer.common.label_change import CommandEntry
from arthropod_describer.common.photo import Photo, LabelType

from arthropod_describer.common.plugin import RegionComputation
from arthropod_describer.common.user_params import ToolUserParam


class LegsRegion(RegionComputation):
    """
    NAME: LegRegions
    DESC: Identifies leg regions from a bug mask.

    USER_PARAMS:
            NAME: Max leg width
            KEY: max_leg_width
            DESC: Maximum width of legs in pixels
            PARAM_TYPE: INT
            DEFAULT_VALUE: 25
            MIN_VALUE: 3
            MAX_VALUE: 125
    """
    def __init__(self):
        super().__init__(None)

    @property
    def requires(self) -> Set[LabelType]:
        return {LabelType.BUG}

    @property
    def computes(self) -> Set[LabelType]:
        return {LabelType.REGIONS}

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None) -> Set[LabelType]:
        reg_lbl = photo.segments_mask
        diam = self._user_params['max_leg_width'].value
        bin = 255 * (reg_lbl.label_img > 0).astype(np.uint8)
        wth = cv.morphologyEx(bin, cv.MORPH_TOPHAT,
                              cv.getStructuringElement(cv.MORPH_ELLIPSE, (diam, diam)))
        legs = np.where(wth > 0, 1220, reg_lbl.label_img).astype(np.uint16)
        #cv.imshow('bin', cv.resize(bin, (0, 0), fx=0.5, fy=0.5))
        #cv.imshow('wth', cv.resize(wth, (0, 0), fx=0.5, fy=0.5))
        #cv.imshow('legs', cv.resize(legs, (0, 0), fx=0.5, fy=0.5))
        #cv.waitKey(0)
        #cv.destroyAllWindows()
        #cv.imwrite(f'/home/radoslav/fakulta/ad_stuff/{repr(LabelType.REGIONS)}__.tif', legs)
        photo.segments_mask.label_img = legs
        return {LabelType.REGIONS}

    @property
    def user_params(self) -> List[ToolUserParam]:
        return list(self._user_params.values())


