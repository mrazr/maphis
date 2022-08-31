import copy
import typing
from typing import Optional

import numpy as np
from skimage import img_as_ubyte
from skimage.color import rgb2hsv
from skimage.feature import graycoprops, graycomatrix

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, PropertyType
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache
from arthropod_describer.common.units import UnitStore, convert_value
from arthropod_describer.common.user_params import UserParam


class GLCMASM(PropertyComputation):
    """
    GROUP: GLCM properties
    NAME: ASM
    DESCRIPTION: GLCM ASM of the region
    KEY: ASM
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)

    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> \
            typing.List[RegionProperty]:

        if 'photo_hsv' not in regions_cache.data_storage:
            regions_cache.data_storage['photo_hsv'] = rgb2hsv(photo.image)

        photo_image_hsv = regions_cache.data_storage['photo_hsv']
        props: typing.List[RegionProperty] = []

        lab_img = photo['Labels'].label_image
        refl = photo['Reflections'].label_image

        distances_in_mm = [0.02, 0.04, 0.06]  # The GLCM will be calculated for these distances (in mm). TODO: Allow this to be user-specified (at least from some config file).
        if photo.image_scale is not None and photo.image_scale.value > 0:
            unit_store = UnitStore()
            scale_in_px_per_mm = convert_value(photo.image_scale, unit_store.units["px/mm"])
            distances_in_px = [round(x * scale_in_px_per_mm.value) for x in distances_in_mm]
        else:
            distances_in_px = [1, 2, 3]
        #print(f"distances_in_px: {distances_in_px}")

        angles = [0, np.pi / 2, np.pi, 3 * np.pi / 2]  # The GLCM will be calculated for these angles (in radians). TODO: Maybe turn on the symmetry in graycomatrix(), and only use half the range of the angles?

        for label in region_labels:
            # Prepare a list of all GLCM properties requested for the current label, e.g. ["contrast", "homogeneity"].
            # properties_for_current_label = [glcm_property for glcm_property, label_list in prop_labels.items() if label in label_list]

            # Binary mask of the current region, excluding the reflections.
            # current_region_mask = np.logical_and(lab_img == label, refl == 0)
            if label not in regions_cache.regions:
                continue

            region_obj = regions_cache.regions[label]
            top, left, height, width = region_obj.bbox
            refl_roi = refl[top:top + height, left:left + width]

            current_region_mask = np.logical_and(region_obj.mask, refl_roi)
            photo_image_hsv_roi = photo_image_hsv[region_obj.bbox[1]:region_obj.bbox[1] + region_obj.mask.shape[0],
                                  region_obj.bbox[0]:region_obj.bbox[0] + region_obj.mask.shape[1]]

            # Prepare the GLCMs for all channels.
            filtered_glcms: typing.List[typing.Any] = []
            for current_channel in range(3):
                current_channel_values = img_as_ubyte(photo_image_hsv_roi[:, :, current_channel])
                # Make sure no pixel has the max value, so we can do the +1 in the next step, and use "0" exclusively as "pixels to be ignored".
                current_channel_values[current_channel_values == np.iinfo(current_channel_values.dtype).max] = np.iinfo(current_channel_values.dtype).max - 1
                current_channel_values_masked = current_channel_values + 1
                current_channel_values_masked[current_region_mask == 0] = 0
                # Whole image GLCM with pixels outside the current region zeroed-out, as a base for the filtered version.
                glcm = graycomatrix(current_channel_values_masked, distances_in_px, angles)
                # GLCM of only the pixels belonging to the current region.
                filtered_glcms.append(glcm[1:, 1:, :, :])

            # Extract the requested properties from the GLCMs for each channel and append to props.
            # for glcm_property in properties_for_current_label:
            current_property_values_for_all_channels = []
            for current_channel in range(3):
                current_property_values_for_current_channel = graycoprops(filtered_glcms[current_channel], prop='ASM').tolist()
                current_property_values_for_all_channels.append(current_property_values_for_current_channel)
            # Append the results to props -- each requested property as one item containing three matrices (one for each HSV channel).
            prop = self.example(self.info.key)
            prop.label = int(label)
            prop.info = copy.deepcopy(self.info)
            prop.value = (np.array(current_property_values_for_all_channels), self._no_unit)
            # prop.prop_type = PropertyType.NDArray  # TODO: Maybe create a specific property type `Matrix` for this?
            # prop.val_names = ["H", "S", "V"]
            # prop.num_vals = 3
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
        prop.value = None
        prop.val_names = ['H', 'S', 'V']
        prop.row_names = ['distance 0.02 mm', 'distance 0.04 mm', 'distance 0.06 mm']
        prop.col_names = ['angle 0°', 'angle 90°', 'angle 180°', 'angle 270°']
        prop.num_vals = 3
        prop.prop_type = PropertyType.NDArray
        prop.info = copy.deepcopy(self.info)
        return prop

    def target_worksheet(self, prop_name: str) -> str:
        return "GLCM"

    @property
    def group(self) -> str:
        return super().group
