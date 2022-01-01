from typing import Optional, Set, List

import cv2
import numpy as np

from arthropod_describer.common.photo import Photo, LabelType
from arthropod_describer.common.plugin import RegionComputation
from arthropod_describer.common.tool import qimage2ndarray
from arthropod_describer.common.user_params import ToolUserParam


class BodyComp(RegionComputation):
    """
    NAME: Primitive bug body finder.
    DESC: Labels the whole body of a bug based on thresholding the blue channel.

    USER_PARAMS:
        NAME: Blue threshold
        KEY: threshold
        PARAM_TYPE: INT
        VALUE: 200
        DEFAULT_VALUE: 200
        MIN_VALUE: 0
        MAX_VALUE: 255
    """
    def __init__(self):
        RegionComputation.__init__(self, None)
        self._user_params = ToolUserParam.load_params_from_doc_str(self.__doc__)

    @property
    def requires(self) -> Set[LabelType]:
        return {}

    @property
    def computes(self) -> Set[LabelType]:
        return {}

    @property
    def user_params(self) -> List[ToolUserParam]:
        return list(self._user_params.values())

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None) -> Set[LabelType]:
        blue_chan = qimage2ndarray(photo.image)[:, :, 2]
        bug = (blue_chan < self._user_params['threshold'].value).astype(np.uint16)
        bug = cv2.morphologyEx(bug, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                                               (15, 15)))
        photo.bug_mask.label_img = 1000 * bug
        photo.segments_mask.label_img = 1000 * bug
        return {LabelType.REGIONS, LabelType.BUG}
