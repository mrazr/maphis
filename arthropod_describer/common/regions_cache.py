import dataclasses
import typing

import numpy as np

from arthropod_describer.common.photo import Photo


@dataclasses.dataclass
class Region:
    label: int
    mask: np.ndarray
    image: np.ndarray
    bbox: typing.Tuple[int, int, int, int]  # top, left, bottom, right


class RegionsCache:
    def __init__(self, region_labels: typing.Set[int], photo: Photo, label_name: str):
        self.regions: typing.Dict[int, Region] = {}
        label_img = photo[label_name]
        regions_by_level = label_img.label_hierarchy.group_by_level(region_labels)

        for level, labels in regions_by_level.items():
            label_img_on_level = label_img[level]
            for label in labels:
                region_mask = label_img_on_level == label
                yy, xx = np.nonzero(region_mask)
                if len(yy) == 0:
                    continue
                top, left, bottom, right = np.min(yy), np.min(xx), np.max(yy), np.max(xx)

                mask_roi = region_mask[top:bottom+1, left:right+1]
                image_roi = photo.image[top:bottom+1, left:right+1]

                region = Region(label, mask_roi, image_roi, (top, left, bottom-top+1, right-left+1))
                self.regions[label] = region
        self.data_storage: typing.Dict[str, typing.Any] = {}
