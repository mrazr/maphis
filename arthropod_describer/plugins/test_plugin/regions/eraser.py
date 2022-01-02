from typing import Optional, Set

import numpy as np

from arthropod_describer.common.photo import Photo, LabelType
from arthropod_describer.common.plugin import RegionComputation, Info


class RegionEraser(RegionComputation):
    """
    NAME: Region eraser
    DESC: Erases regions with the selected labels.

    REGION_RESTRICTED
    """

    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    @property
    def requires(self) -> Set[LabelType]:
        return {LabelType.REGIONS}

    @property
    def computes(self) -> Set[LabelType]:
        return {LabelType.REGIONS}

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None) -> Set[LabelType]:
        cop = photo.segments_mask.label_img.copy()
        for lab in labels:
            cop = np.where(cop == lab, 0, cop)
        photo.segments_mask = cop
        return {LabelType.REGIONS}
