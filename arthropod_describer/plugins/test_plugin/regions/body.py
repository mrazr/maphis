from typing import Optional, Set, List

import cv2
import numpy as np

from arthropod_describer.common.photo import Photo, LabelImg
from arthropod_describer.common.plugin import RegionComputation
from arthropod_describer.common.user_params import UserParam


class BodyComp(RegionComputation):
    """
    NAME: Primitive bug body finder.
    DESCRIPTION: Labels the whole body of a bug based on thresholding the blue channel.

    USER_PARAMS:
        PARAM_NAME: Blue threshold
        PARAM_KEY: threshold
        PARAM_TYPE: INT
        VALUE: 200
        DEFAULT_VALUE: 200
        MIN_VALUE: 0
        MAX_VALUE: 255

        PARAM_NAME: Filter size for small components
        PARAM_KEY: filter_size
        PARAM_TYPE: INT
        VALUE: 25
        DEFAULT_VALUE: 25
        MIN_VALUE: 1
        MAX_VALUE: 55
    """
    def __init__(self):
        RegionComputation.__init__(self, None)
        self._user_params = UserParam.load_params_from_doc_str(self.__doc__)

    @property
    def user_params(self) -> List[UserParam]:
        return list(self._user_params.values())

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None, storage=None) -> List[LabelImg]:
        #blue_chan = qimage2ndarray(photo.image)[:, :, 2]
        print(f'obtained {labels} restrictions')
        blue_chan = photo.image[:, :, 2]
        bug = (blue_chan < self._user_params['threshold'].value).astype(np.uint16)
        bug = cv2.morphologyEx(bug, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                                               (15, 15)))
        sz = self._user_params['filter_size'].value
        bug = cv2.morphologyEx(bug, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                                              (sz, sz)))
        label = photo['Labels'].label_hierarchy.label('1:0:0:0')
        new_label = photo['Labels'].clone()
        new_label.label_image = label * bug
        return [new_label]
