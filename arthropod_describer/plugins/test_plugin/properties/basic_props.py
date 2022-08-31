import functools
import operator
import time
import typing
from pathlib import Path
from typing import Optional, List
import copy

import cv2
import numpy as np
import skimage.measure
from skimage import io
from skimage.color import rgb2hsv
from skimage.morphology import binary_erosion
import skimage.transform
import scipy.ndimage
from sklearn.decomposition import PCA

from arthropod_describer.common.label_hierarchy import LabelHierarchy
from arthropod_describer.common.label_image import RegionProperty, PropertyType, LabelImg
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.common import Info
from arthropod_describer.common.regions_cache import RegionsCache, Region
from arthropod_describer.common.units import Value, Unit, SIPrefix, BaseUnit
from .geodesic_utils import get_longest_geodesic, get_longest_geodesic2, compute_longest_geodesic, find_shortest_path


class BasicProperties:
    """
    NAME: Basic properties
    DESCRIPTION: Computes basic region properties.

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
            # 'area': Info('Area', key='area', description='Area of the region (px or mm\u00b2)'),
            'mean_intensity': Info('Mean intensity', key='mean_intensity', description='Mean intensity (R, G, B)'),
            'circularity': Info('Circularity', key='circularity', description='Circularity (0.0 to 1.0, where 1.0 = perfect circle)'),
            'max_feret': Info('Max Feret', key='max_feret', description='Maximum Feret diameter (px or mm)'),
            'geodesic_length': Info('Geodesic length', key='geodesic_length', description='Geodesic length (px or mm)'),
            'mean_width': Info('Mean width', key='mean_width', description='Mean width of a region (px or mm)'),
            'contour': Info('Contour', key='contour', description='Compute contour feature vector'),
            'mean_hsv': Info('Mean HSV', key='mean_hsv', description='Mean HSV of a region')
        }

    def _compute_mean_intensity(self, region: Region, refl: np.ndarray) -> List[RegionProperty]:
        # mask = np.logical_xor(lab_img > 0, refl > 0)
        # label_img = np.where(mask, lab_img, 0)

        # reg_props = skimage.measure.regionprops_table(label_img, photo,
        #                                               properties=['label', 'mean_intensity'])

        top, left, height, width = region.bbox
        refl_roi = refl[top:top + height, left:left + width]

        mask = np.logical_xor(region.mask, refl_roi > 0)

        yy, xx = np.nonzero(mask)

        pixels = region.image[yy, xx]

        mean_intensity = np.mean(pixels, axis=0)

        prop = RegionProperty()
        prop.info = copy.deepcopy(self.example('mean_intensity').info)
        prop.label = int(region.label)
        prop.value = (mean_intensity.tolist(), self._no_unit)
        prop.prop_type = PropertyType.Intensity
        prop.num_vals = 3
        prop.val_names = ['R', 'G', 'B']

        return [prop]

        props: List[RegionProperty] = []
        for idx, label in enumerate(reg_props['label']):
            if label not in labels:
                continue
            prop = RegionProperty()
            prop.info = copy.deepcopy(self._available_props['mean_intensity'])
            prop.label = int(label)
            prop.value = ([
                float(reg_props['mean_intensity-0'][idx]),
                float(reg_props['mean_intensity-1'][idx]),
                float(reg_props['mean_intensity-2'][idx])
            ], self._no_unit)
            prop.prop_type = PropertyType.Intensity
            prop.num_vals = 3
            prop.val_names = ['R', 'G', 'B']
            props.append(prop)
        return props

    def _compute_area(self, region: Region, photo: Photo) -> List[RegionProperty]:
        props = []

        prop = RegionProperty()
        prop.label = region.label
        prop.info = copy.deepcopy(self._available_props['area'])
        # prop.value = int(np.count_nonzero(lab_img == label))
        value = Value(int(np.count_nonzero(region.mask)), self._px_unit * self._px_unit)
        if photo.image_scale is not None and photo.image_scale.value > 0:
            prop.value = value / (photo.image_scale * photo.image_scale)
            # prop.unit = 'mm\u00b2'  # TODO sync unit with the units in Photo
        else:
            prop.value = value
        prop.prop_type = PropertyType.Scalar
        prop.val_names = ['Area']
        prop.num_vals = 1
        props.append(prop)
        return props

    def _compute_max_feret(self, lab_img: np.ndarray, labels: typing.Set[int], photo: Photo) -> List[RegionProperty]:
        reg_props = skimage.measure.regionprops_table(lab_img, photo.image,
                                                      properties=['label', 'feret_diameter_max'])

        props: List[RegionProperty] = []

        for idx, label in enumerate(reg_props['label']):
            if label not in labels:
                continue

            prop = RegionProperty()
            prop.label = int(label)
            prop.info = copy.deepcopy(self._available_props['max_feret'])
            prop.value = Value(float(reg_props['feret_diameter_max'][idx]), self._px_unit)
            if photo.image_scale is not None and photo.image_scale.value > 0:
                # prop.value /= photo.image_scale
                prop.value = prop.value / photo.image_scale
                prop.unit = 'mm'  # TODO sync unit with the units in Photo
            else:
                prop.unit = 'px'
            prop.prop_type = PropertyType.Scalar
            prop.val_names = ['Max Feret']
            prop.num_vals = 1
            props.append(prop)
        return props

    def _compute_circularity(self, lab_img: np.ndarray, labels: typing.Set[int], photo: Photo, perimeter_measurement_flavor: str) -> List[RegionProperty]:
        # 'perimeter' or 'perimeter_crofton' is possible as perimeter_measurement_flavor
        reg_props = skimage.measure.regionprops_table(lab_img, photo.image,
                                                      properties=['label', perimeter_measurement_flavor])
        props: List[RegionProperty] = []

        for idx, label in enumerate(reg_props['label']):
            if label not in labels:
                continue

            perimeter = reg_props[perimeter_measurement_flavor][idx]
            area = int(np.count_nonzero(lab_img == label))
            if perimeter == 0:
                circularity = 0 # TODO: Careful about division by zero (can we somehow return N/A here?)
            else:
                circularity = np.clip((4 * np.pi * area) / (perimeter ** 2), 0.0, 1.0)
            #print(f'idx: {idx}, label: {label}')
            #print(f'  perimeter: {perimeter}')
            #print(f'  area: {area}')
            #print(f'  circularity: {circularity}')

            prop = RegionProperty()
            prop.label = int(label)
            prop.info = copy.deepcopy(self._available_props['circularity'])
            prop.value = Value(float(circularity), Unit(BaseUnit.none, SIPrefix.none, dim=0))
            # prop.unit = '' # TODO: Is this ok for a unitless property?
            prop.prop_type = PropertyType.Scalar
            prop.val_names = ['Circularity']
            prop.num_vals = 1
            props.append(prop)
        return props

    def _compute_geodesic_length(self, lab_img: np.ndarray, labels: typing.Set[int], photo: Photo) -> List[RegionProperty]:
        props: List[RegionProperty] = []
        for label in labels:
            # _, length = get_longest_geodesic(lab_img, label)
            length, _, _ = compute_longest_geodesic(lab_img == label)
            # compute_longest_geodesic(lab_img == label)
            if length < 0:
                continue
            prop = RegionProperty()
            prop.label = int(label)
            prop.info = copy.deepcopy(self._available_props['geodesic_length'])
            value = Value(float(length), self._px_unit)
            if photo.image_scale is not None:
                # prop.unit = 'mm'
                prop.value = value / photo.image_scale
            else:
                prop.value = value
            prop.val_names = ['Geodesic length']
            prop.num_vals = 1
            props.append(prop)
        return props

    def _compute_mean_width(self, lab_img: LabelImg, labels: typing.Set[int], photo: Photo) -> List[RegionProperty]:
        props: List[RegionProperty] = []

        for label in labels:
            bin_img = lab_img.mask_for(label)
            if not np.any(bin_img):
                continue
            # geodesic, length, bbox = get_longest_geodesic2(bin_img)
            # bin_roi = bin_img[bbox[0]:bbox[1]+1, bbox[2]:bbox[3]+1]
            gdist, px1, px2 = compute_longest_geodesic(bin_img)
            geodesic = find_shortest_path(bin_img, px1, px2)
            geodesic = ([px[1] for px in geodesic], [px[0] for px in geodesic])
            outline = np.logical_and(bin_img, binary_erosion(bin_img, footprint=np.ones((3, 3), dtype=np.uint8)))
            dst: np.ndarray = scipy.ndimage.distance_transform_edt(outline)
            mean_width = np.mean(2.0 * dst[geodesic[0], geodesic[1]])
            if np.isnan(mean_width):
                # TODO inspect `get_longest_geodesic2` function
                mean_width = -42.0

            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\mean_width\\{label}_bin_roi.png', bin_roi, check_contrast=False)
            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\mean_width\\{label}_outline.png', outline, check_contrast=False)
            # io.imsave(f'C:\\Users\\radoslav\\Desktop\\mean_width\\{label}_dst.png',
            #           (255.0 * (dst / (np.max(dst) + 1e-6))).astype(np.uint8), check_contrast=False)

            prop = RegionProperty()
            prop.info = copy.deepcopy(self._available_props['mean_width'])
            prop.prop_type = PropertyType.Scalar
            prop.label = label
            if photo.image_scale is not None:
                prop.value = Value(float(mean_width), self._px_unit) / photo.image_scale
                # prop.unit = 'mm'
            else:
                prop.value = Value(float(mean_width), self._px_unit)
                # prop.unit = 'px'
            prop.num_vals = 1
            prop.val_names = ['Mean width']
            props.append(prop)
        return props

    def _compute_contour_feature_vector(self, lab_img: np.ndarray, labels: typing.Set[int], photo: Photo,
                                        lab_hier: LabelHierarchy) -> List[RegionProperty]:
        props: List[RegionProperty] = []
        # folder = 'radoslav\\Desktop\\contours'
        #folder = 'Karel\\Desktop\\arthropods_debug'
        # path = Path(f'C:\\Users\\{folder}\\{photo.image_name}')
        # if not path.exists():
        #    path.mkdir()
        for label in labels:
            # lab_path = path / lab_hier.nodes[label].name
            # if not lab_path.exists():
            #    lab_path.mkdir()
            region = lab_img == label
            if not np.any(region):
                continue

            pixels = np.argwhere(region)  # format (y, x)

            top, left = np.min(pixels[:,0]), np.min(pixels[:,1])
            bottom, right = np.max(pixels[:,0]), np.max(pixels[:,1])

            roi = region[top:bottom+1, left:right+1]

            roi_rgb = cv2.cvtColor(255 * roi.astype(np.uint8), cv2.COLOR_GRAY2BGR)

            # cv2.imwrite(str(lab_path / 'region.png'), roi_rgb)

            # pixels = pixels - np.array([top, left])  # make local to `roi`
            yy, xx = np.nonzero(roi)

            x_c, y_c = round(np.mean(xx)), round(np.mean(yy))  # centroid for nonzero pixels in `roi`

            # roi_cent = cv2.circle(roi_rgb, (x_c, y_c), 3, [0, 255, 0])

            # cv2.imwrite(str(lab_path / 'roi_centroid.png'), roi_cent)

            reg_orient = skimage.measure.regionprops_table(1 * roi, properties=('orientation',))

            # get the angle between y-axis and the major axis of the region in `roi`
            angle = np.rad2deg(reg_orient['orientation'][0])

            # pca = PCA(n_components=2)  # compute principal axes for `pixels[::-1]` format (x, y)
            # pca.fit(pixels[::-1])

            # angle = np.rad2deg(np.arccos(np.dot(np.array([0.0, -1.0]), pca.components_[-1])))

            # axis = cv2.line(roi_rgb, (x_c, y_c), (round(x_c + 100 * pca.components_[-1][0]),
            #                                       round(y_c + 100 * pca.components_[-1][1])),
            #                                       [255, 0, 0], 2)

            # cv2.imwrite(str(lab_path / 'axis.png'), axis)

            # rotate `roi` so that the major axis coincides with y-axis
            rotated = skimage.transform.rotate(roi, angle=-angle, center=(x_c, y_c), resize=True)

            # io.imsave(str(lab_path / 'roi_rotated.png'), rotated)

            # outline = np.logical_xor(rotated, binary_erosion(rotated, footprint=np.ones((3, 3))))
            outline = np.logical_xor(rotated, cv2.erode(255 * rotated.astype(np.uint8), np.ones((3, 3)),
                                                        borderValue=0, borderType=cv2.BORDER_CONSTANT) > 0)

            # io.imsave(str(lab_path / 'outline.png'), outline)

            outline_yy, outline_xx = np.nonzero(outline)

            xs_by_y: typing.Dict[int, List[int]] = {}

            for y, x in zip(outline_yy, outline_xx):
                xs_by_y.setdefault(y, []).append(x)

            outline_yy = np.unique(outline_yy)

            # y_sort_inds = np.argsort(outline_yy)

            step = outline_yy.shape[0] / 40.0

            feat_vector: List[float] = []

            # indices_ = outline_yy.tolist() #list(outline_yy[y_sort_inds])
            # indices = indices_[::step]

            # print(f'height is {outline_yy.shape} and step is {step}')
            # print(f'indices are {indices}')

            # if (last_idx := max(y_sort_inds)) not in indices:
            #     indices.append(last_idx)

            # viz = cv2.cvtColor(255 * outline.copy().astype(np.uint8), cv2.COLOR_GRAY2BGR)

            y_start = outline_yy[0]
            y_curr = y_start
            offset = 0

            for i in range(40):
                y_curr = min(int(round(y_start + offset)), max(outline_yy))
                offset += step
                # y = [idx]
                left = min(xs_by_y[y_curr])
                right = max(xs_by_y[y_curr])

                # viz[y_curr, left] = [255, 0, 0]
                # viz[y_curr, right] = [0, 255, 0]

                width = 0.5 * (right - left + 1)
                if photo.image_scale is not None:
                    width /= photo.image_scale.value
                feat_vector.append(width)
            # print(f'computed contour vector for {photo.image_name}: {feat_vector}')
            # cv2.imwrite(str(lab_path / 'viz.png'), viz)
            prop = self.example('contour')
            if photo.image_scale is not None:
                prop.value = (feat_vector, self._px_unit / photo.image_scale.unit)
            else:
                prop.value = (feat_vector, self._px_unit)
            prop.label = label
            props.append(prop)
        return props

    def _compute_mean_hsv(self, lab_img: np.ndarray, labels: typing.Set[int], photo: Photo,
                                        lab_hier: LabelHierarchy) -> List[RegionProperty]:
        props: List[RegionProperty] = []

        hsv_img = rgb2hsv(photo.image)
        hsv_img[:, :, 0] = 360 * hsv_img[:, :, 0]

        reflection = photo['Reflections'].label_image

        for label in labels:
            region_mask = np.logical_and(lab_img == label, reflection == 0)
            ys, xs = np.nonzero(region_mask)

            if len(ys) == 0:
                continue

            hues = hsv_img[ys, xs, 0]

            hue_radians = np.pi * hues / 180.0

            avg_sin = np.mean(np.sin(hue_radians))
            avg_cos = np.mean(np.cos(hue_radians))

            average_vector_angle = np.arctan2(avg_sin, avg_cos)

            average_vector_degrees = np.mod((180.0 / np.pi) * average_vector_angle, 360)

            average_vector_length = np.sqrt(avg_sin * avg_sin + avg_cos * avg_cos)

            mean_sat = np.mean(hsv_img[ys, xs, 1])
            mean_val = np.mean(hsv_img[ys, xs, 2])

            prop = copy.deepcopy(self.example('mean_hsv'))
            prop.value = ([float(average_vector_degrees),
                           100 * float(mean_sat * average_vector_length),
                           100 * float(mean_val)],
                          self._no_unit)
            prop.label = label
            props.append(prop)

        return props

    def __call__(self, photo: Photo, prop_labels: typing.Dict[int, typing.Set[str]], regions_cache: RegionsCache) \
            -> List[RegionProperty]:
        reg_img = photo['Labels']

        props = []

        # all_labels: typing.Set[int] = set(functools.reduce(set.union, prop_labels.keys())) # all_labels -- All labels for which the user requested any property to be computed.

        level_groups = reg_img.label_hierarchy.group_by_level(set(prop_labels.keys()))
        now = time.time()
        for region_label, prop_strs in prop_labels.items():
            if region_label not in regions_cache.regions:
                continue
            region: Region = regions_cache.regions[region_label]
            for prop_str in prop_strs:
                if prop_str == 'mean_intensity':
                    _props = self._compute_mean_intensity(region, photo['Reflections'].label_image)
                elif prop_str == 'area':
                    _props = self._compute_area(region, photo)
                # elif prop_str == 'circularity':
                #     _props = self._compute_circularity(level_img, level_labels_for_prop, photo, 'perimeter')
                # elif prop_str == 'max_feret':
                #     _props = self._compute_max_feret(level_img, level_labels_for_prop, photo)
                # elif prop_str == 'geodesic_length':
                #     _props = self._compute_geodesic_length(level_img, level_labels_for_prop, photo)
                # elif prop_str == 'mean_width':
                #     _props = self._compute_mean_width(reg_img, labels, photo)
                # elif prop_str == 'contour':
                #     _props = self._compute_contour_feature_vector(level_img, level_labels_for_prop, photo,
                #                                                   reg_img.label_hierarchy)
                # elif prop_str == 'mean_hsv':
                #     _props = self._compute_mean_hsv(level_img, level_labels_for_prop, photo, reg_img.label_hierarchy)
                else:
                    print(f'property {prop_str} not fully implemented')
                    _props = []
                props.extend(_props)
        print(f'took {time.time() - now} secs')
        return props


        for level, level_labels in level_groups.items():
            level_img = reg_img[level]
            for prop_str, labels in prop_labels.items():
                level_labels_for_prop = labels.intersection(level_labels)
                if prop_str == 'mean_intensity':
                    _props = self._compute_mean_intensity(level_img, photo['Reflections'].label_image, photo.image,
                                                          level_labels_for_prop)
                elif prop_str == 'area':
                    _props = self._compute_area(level_img, level_labels_for_prop, photo)
                elif prop_str == 'circularity':
                    _props = self._compute_circularity(level_img, level_labels_for_prop, photo, 'perimeter')
                elif prop_str == 'max_feret':
                    _props = self._compute_max_feret(level_img, level_labels_for_prop, photo)
                elif prop_str == 'geodesic_length':
                    _props = self._compute_geodesic_length(level_img, level_labels_for_prop, photo)
                elif prop_str == 'mean_width':
                    _props = self._compute_mean_width(reg_img, labels, photo)
                elif prop_str == 'contour':
                    _props = self._compute_contour_feature_vector(level_img, level_labels_for_prop, photo,
                                                                  reg_img.label_hierarchy)
                elif prop_str == 'mean_hsv':
                    _props = self._compute_mean_hsv(level_img, level_labels_for_prop, photo, reg_img.label_hierarchy)
                else:
                    print(f'property {prop_str} not fully implemented')
                    _props = []
                props.extend(_props)
            #reg_props = skimage.measure.regionprops(level_img, intensity_image=photo.image)
            #for prop_str, labels in prop_labels.items():
            #    example_prop = self.example(prop_str)
            #    for _prop in reg_props:
            #        if _prop.label not in labels:
            #            continue
            #        reg_prop = RegionProperty()
            #        reg_prop.info = copy.deepcopy(prop_info_dict[prop_str])
            #        reg_prop.label = _prop.label
            #        reg_prop.value = operator.attrgetter(prop_str)(_prop)
            #        reg_prop.prop_type = example_prop.prop_type
            #        reg_prop.num_vals = example_prop.num_vals
            #        reg_prop.val_names = example_prop.val_names
            #        if isinstance(reg_prop.value, np.integer):
            #            reg_prop.value = int(reg_prop.value)
            #        elif isinstance(reg_prop.value, np.float):
            #            reg_prop.value = float(reg_prop.value)
            #        elif isinstance(reg_prop.value, np.ndarray):
            #            reg_prop.value = reg_prop.value.tolist()
            #        props.append(reg_prop)
        return props


    #def __call__(self, photo: Photo, prop_labels: typing.Dict[str, typing.Set[int]]):
    #    reg_img = photo['Labels']

    #    region_props = skimage.measure.regionprops(reg_img.label_image, photo.image)

    #    props = []
    #    prop_info_dict = {info.key: info for info in self._available_props}
    #    for reg_prop in region_props:
    #        for prop_name, labels in prop_labels.items():
    #            if reg_prop.label not in labels:
    #                continue
    #            reg_property = RegionProperty()
    #            reg_property.info = copy.deepcopy(prop_info_dict[prop_name])
    #            reg_property.label = reg_prop.label
    #            reg_property.value = operator.attrgetter(prop_name)(reg_prop)
    #            if reg_property.info.name == 'Area':
    #                reg_property.prop_type = PropertyType.Scalar
    #            else:
    #                reg_property.prop_type = PropertyType.Intensity
    #                reg_property.num_vals = len(reg_property.value)
    #                reg_property.val_names = ['R', 'G', 'B'] if reg_property.num_vals == 3 else ['']
    #            if isinstance(reg_property.value, np.integer):
    #                reg_property.value = int(reg_property.value)
    #            elif isinstance(reg_property.value, np.float):
    #                reg_property.value = float(reg_property.value)
    #            elif isinstance(reg_property.value, np.ndarray):
    #                reg_property.value = reg_property.value.tolist()
    #            props.append(reg_property)
    #    return props

    @property
    def computes(self) -> typing.Dict[str, Info]:
        return self._available_props

    def example(self, prop_key: str) -> RegionProperty:
        prop = RegionProperty()
        prop.label = 0
        prop.value = None
        if prop_key == 'area':
            prop.info = copy.deepcopy(self._available_props['area'])
            prop.num_vals = 1
            prop.prop_type = PropertyType.Scalar
            prop.val_names = []
        elif prop_key == 'mean_intensity':
            prop.info = copy.deepcopy(self._available_props['mean_intensity'])
            prop.num_vals = 3
            prop.prop_type = PropertyType.Intensity
            prop.val_names = ['R', 'G', 'B']
        elif prop_key == 'circularity':
            prop.info = copy.deepcopy(self._available_props['circularity'])
            prop.num_vals = 1
            prop.prop_type = PropertyType.Scalar
            prop.val_names = []
        elif prop_key == 'max_feret':
            prop.info = copy.deepcopy(self._available_props['max_feret'])
            prop.num_vals = 1
            prop.prop_type = PropertyType.Scalar
            prop.val_names = []
        elif prop_key == 'geodesic_length':
            prop.info = copy.deepcopy(self._available_props['geodesic_length'])
            prop.num_vals = 1
            prop.prop_type = PropertyType.Scalar
            prop.val_names = []
        elif prop_key == 'mean_width':
            prop.info = copy.deepcopy(self._available_props['mean_width'])
            prop.num_vals = 1
            prop.prop_type = PropertyType.Scalar
            prop.val_names = []
        elif prop_key == 'contour':
            prop.info = copy.deepcopy(self._available_props['contour'])
            prop.num_vals = 40
            prop.prop_type = PropertyType.Vector
            prop.val_names = []
        elif prop_key == 'mean_hsv':
            prop.info = copy.deepcopy(self._available_props['mean_hsv'])
            prop.num_vals = 3
            prop.prop_type = PropertyType.IntensityHSV
            prop.val_names = ['H', 'S', 'V']
        else:
            # Log an error when encountering unknown property key
            print(f'property {prop_key} not fully implemented')
        return prop

    def target_worksheet(self, prop_key: str) -> str:
        if prop_key == 'contour':
            return 'Contour'
        return super().target_worksheet(prop_key)


