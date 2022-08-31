import functools
import typing
from pathlib import Path
from typing import Optional, List, Any
import copy

import numpy as np
import skimage.measure
from skimage import io
import scipy.ndimage

from skimage.color import rgb2hsv
from skimage import img_as_ubyte
from skimage.feature import graycomatrix, graycoprops

from arthropod_describer.common.label_hierarchy import LabelHierarchy
from arthropod_describer.common.label_image import RegionProperty, PropertyType, LabelImg
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.common import Info
from arthropod_describer.common.units import Value, Unit, SIPrefix, BaseUnit, UnitStore, convert_value


class GLCMProperties:
    """
    NAME: GLCM properties
    DESCRIPTION: Computes properties from grey level co-occurrence matrix.

    REGION_RESTRICTED

    USER_PARAMS:
        PARAM_NAME: ABC
        PARAM_KEY: abc
        PARAM_TYPE: INT
        VALUE: 10
        MIN_VALUE: 5
        MAX_VALUE: 25
    """

    def __init__(self, info: Optional[Info] = None):
        PropertyComputation.__init__(self, info)
        self.info = Info.load_from_doc_str(self.__doc__)
        self._px_unit: Unit = Unit(BaseUnit.px, prefix=SIPrefix.none, dim=1)
        self._no_unit: Unit = Unit(BaseUnit.none, prefix=SIPrefix.none, dim=0)
        self._available_props = {
            "contrast":      Info("Contrast",      key="contrast",      description="GLCM contrast of the region"),
            "dissimilarity": Info("Dissimilarity", key="dissimilarity", description="GLCM dissimilarity of the region"),
            "homogeneity":   Info("Homogeneity",   key="homogeneity",   description="GLCM homogeneity of the region"),
            "ASM":           Info("ASM",           key="ASM",           description="GLCM ASM of the region"),
            "energy":        Info("Energy",        key="energy",        description="GLCM energy of the region"),
            "correlation":   Info("Correlation",   key="correlation",   description="GLCM correlation of the region")
        }



    def _compute_glcm_properties(self, lab_img: np.ndarray, refl: np.ndarray, photo: Photo, labels: typing.Set[int], prop_labels: typing.Dict[str, typing.Set[int]], lab_hier: LabelHierarchy) -> List[RegionProperty]:
        photo_image_hsv = rgb2hsv(photo.image)
        props: List[RegionProperty] = []

        distances_in_mm = [0.02, 0.04, 0.06]  # The GLCM will be calculated for these distances (in mm). TODO: Allow this to be user-specified (at least from some config file).
        if photo.image_scale is not None and photo.image_scale.value > 0:
            unit_store = UnitStore()
            scale_in_px_per_mm = convert_value(photo.image_scale, unit_store.units["px/mm"])
            distances_in_px = [round(x * scale_in_px_per_mm.value) for x in distances_in_mm]
        else:
            distances_in_px = [1, 2, 3]
        #print(f"distances_in_px: {distances_in_px}")

        angles = [0, np.pi / 2, np.pi, 3 * np.pi / 2]  # The GLCM will be calculated for these angles (in radians). TODO: Maybe turn on the symmetry in graycomatrix(), and only use half the range of the angles?


        for label in labels:
            # Prepare a list of all GLCM properties requested for the current label, e.g. ["contrast", "homogeneity"].
            properties_for_current_label = [glcm_property for glcm_property, label_list in prop_labels.items() if label in label_list]

            # Binary mask of the current region, excluding the reflections.
            current_region_mask = np.logical_and(lab_img == label, refl == 0)

            # Prepare the GLCMs for all channels.
            filtered_glcms: List[Any] = []
            for current_channel in range(3):
                current_channel_values = img_as_ubyte(photo_image_hsv[:, :, current_channel])
                # Make sure no pixel has the max value, so we can do the +1 in the next step, and use "0" exclusively as "pixels to be ignored".
                current_channel_values[current_channel_values == np.iinfo(current_channel_values.dtype).max] = np.iinfo(current_channel_values.dtype).max - 1
                current_channel_values_masked = current_channel_values + 1
                current_channel_values_masked[current_region_mask == 0] = 0
                # Whole image GLCM with pixels outside the current region zeroed-out, as a base for the filtered version.
                glcm = graycomatrix(current_channel_values_masked, distances_in_px, angles)
                # GLCM of only the pixels belonging to the current region.
                filtered_glcms.append(glcm[1:, 1:, :, :])

            # Extract the requested properties from the GLCMs for each channel and append to props.
            for glcm_property in properties_for_current_label:
                current_property_values_for_all_channels = []
                for current_channel in range(3):
                    current_property_values_for_current_channel = graycoprops(filtered_glcms[current_channel], prop=glcm_property).tolist()
                    current_property_values_for_all_channels.append(current_property_values_for_current_channel)
                # Append the results to props -- each requested property as one item containing three matrices (one for each HSV channel).
                prop = self.example(glcm_property)
                prop.label = int(label)
                prop.info = copy.deepcopy(self._available_props[glcm_property])
                prop.value = (np.array(current_property_values_for_all_channels), self._no_unit)
                # prop.prop_type = PropertyType.NDArray  # TODO: Maybe create a specific property type `Matrix` for this?
                # prop.val_names = ["H", "S", "V"]
                # prop.num_vals = 3
                props.append(prop)
        return props





    def __call__(self, photo: Photo, prop_labels: typing.Dict[str, typing.Set[int]]):
        reg_img = photo["Labels"]

        props = []

        all_labels: typing.Set[int] = set(functools.reduce(set.union, prop_labels.values()))

        level_groups = reg_img.label_hierarchy.group_by_level(all_labels)

        for level, level_labels in level_groups.items():
            level_img = reg_img[level]
            _props = self._compute_glcm_properties(level_img, photo["Reflections"].label_image, photo, level_groups[level], prop_labels, reg_img.label_hierarchy)
            props.extend(_props)
        return props


    @property
    def computes(self) -> typing.Dict[str, Info]:
        return self._available_props

    def example(self, prop_key: str) -> RegionProperty:
        prop = RegionProperty()
        prop.label = 0
        prop.value = None
        prop.val_names = ['H', 'S', 'V']
        prop.row_names = ['distance 0.02 mm', 'distance 0.04 mm', 'distance 0.06 mm']
        prop.col_names = ['angle 0°', 'angle 90°', 'angle 180°', 'angle 270°']
        prop.num_vals = 3
        prop.prop_type = PropertyType.NDArray
        prop.info = copy.deepcopy(self._available_props[prop_key])
        # TODO: What is the purpose of this example() function? (It is called from MeasurementsViewer._tabular_export_routine().) How to treat the individual properties here?
        # print(f"property {prop_key} not fully implemented")
        #if prop_key == "contrast":
        #    prop.info = copy.deepcopy(self._available_props["contrast"])
        #    prop.num_vals = 1
        #    prop.prop_type = PropertyType.Scalar
        #    prop.val_names = []
        #elif prop_key == "homogeneity":
        #    prop.info = copy.deepcopy(self._available_props["homogeneity"])
        #    prop.num_vals = 1
        #    prop.prop_type = PropertyType.Scalar
        #    prop.val_names = []
        #else:
        #    # Log an error when encountering unknown property key
        #    print(f"property {prop_key} not fully implemented")
        return prop

    def target_worksheet(self, prop_key: str) -> str:
        return "GLCM"


