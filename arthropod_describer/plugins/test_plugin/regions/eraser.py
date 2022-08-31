from typing import Optional, Set, List

import numpy as np

from arthropod_describer.common.common import Info
from arthropod_describer.common.photo import Photo, LabelImg
from arthropod_describer.common.plugin import RegionComputation


class RegionEraser(RegionComputation):
    """
    NAME: Region eraser
    DESCRIPTION: Erases regions with the selected labels.

    REGION_RESTRICTED
    """

    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None, storage=None) -> List[LabelImg]:
        cop = photo['Labels'].clone()
        for lab in labels:
            cop = np.where(cop.label_image == lab, 0, cop.label_image)
        return [cop]
