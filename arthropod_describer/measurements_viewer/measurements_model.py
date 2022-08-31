import typing
from typing import Dict
import functools

import PySide2
import numpy as np
import qimage2ndarray
from PySide2.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide2.QtGui import QVector3D, QColor, QPixmap
from skimage.color import hsv2rgb

from arthropod_describer.common.label_image import PropertyType
from arthropod_describer.common.state import State
from arthropod_describer.common.utils import vector_to_img

PropKey = str
Label = int
PropName = str
PhotoName = str


class MeasurementsTableModel(QAbstractTableModel):

    def __init__(self, state: State, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(parent)

        self.column_names: typing.List[str] = []
        self.prop_tuple_list: typing.List[typing.Tuple[Label, PropKey, PropName]] = []
        self.state: State = state
        self.single_photo_mode: bool = True
        self.header_labels: typing.List[str] = []
        self.labels: typing.List[int] = []
        self.displayed_property_key: str = ''
        self._display_intensity_in_color: bool = True  # color value will either be displayed as QColor(True) or numbers(False)

    def rowCount(self, parent:PySide2.QtCore.QModelIndex=QModelIndex()) -> int:
        if self.state.storage is None:
            return 0
        return self.state.storage.image_count
        pass

    def columnCount(self, parent:PySide2.QtCore.QModelIndex=QModelIndex()) -> int:
        if self.state.storage is None:
            return 0
        return len(self.column_names)

    def data(self, index:PySide2.QtCore.QModelIndex, role:int=Qt.DisplayRole) -> typing.Any:
        if self.state.storage is None:
            return None
        photo = self.state.storage.get_photo_by_idx(index.row(), load_image=False)
        label = self.prop_tuple_list[index.column()][0]
        props = photo['Labels'].get_region_props(label)

        if role == Qt.UserRole:
            return label
        elif role == Qt.UserRole + 1:
            return self.prop_tuple_list[index.column()][1]
        elif role == Qt.UserRole + 2:
            return self.prop_tuple_list[index.column()][2]
        elif role == Qt.UserRole + 3:
            return photo.image_name

        if props is None:
            if role == Qt.DisplayRole:
                return 'N/A'
            return None
        #if self.displayed_property_key not in props:
        #    return None
        prop_key = self.prop_tuple_list[index.column()][1]
        if prop_key not in props:
            if role == Qt.DisplayRole:
                return 'N/A'
            return None
        prop = props[prop_key]
        if role == Qt.DisplayRole:
            if prop.prop_type in {PropertyType.Scalar, PropertyType.String}:
                return str(prop.value)
            if (prop.prop_type == PropertyType.Intensity or prop.prop_type == PropertyType.IntensityHSV) and not self._display_intensity_in_color:
                str_val = ''
                vals = prop.value[0] if prop.num_vals > 1 else [prop.value]
                for i, val in enumerate(vals):
                    if type(val) == float:
                        str_val = str_val + f', {val:.3f} {prop.val_names[i]}'
                    else:
                        str_val = str_val + f', {val} {prop.val_names[i]}'
                return str_val.strip(',')
            # if prop.prop_type == PropertyType.Vector:
            #     return prop.format_value()
            if prop.prop_type == PropertyType.NDArray:
                val: np.ndarray = prop.value[0]
                return f'{val.shape[1:]} matrices for {",".join(prop.val_names)}'
            return None
        if role == Qt.BackgroundRole:
            if self._display_intensity_in_color:
                if prop.prop_type == PropertyType.Intensity:
                    if prop.num_vals == 1:
                        return QColor.fromRgbF(*(prop.value / 255.0, ) * 3)
                    elif prop.num_vals == 3:
                        clr = [val / 255.0 for val in prop.value[0]]
                        return QColor.fromRgbF(*clr)
                elif prop.prop_type == PropertyType.IntensityHSV:
                    val = prop.value[0]
                    arr = np.array([[val[0] / 360.0, val[1] / 100.0, val[2] / 100.0]])
                    clr = hsv2rgb(arr).tolist()[0]
                    return QColor.fromRgbF(*clr)
        if role == Qt.DecorationRole:
            if prop.prop_type == PropertyType.Vector:
                if prop.vector_viz is None:
                    viz = vector_to_img(prop.value[0], (128, 24))
                    prop.vector_viz = QPixmap.fromImage(qimage2ndarray.array2qimage(viz))
                return prop.vector_viz
        if role == Qt.UserRole + 4:
            return prop
        return None

    def headerData(self, section:int, orientation:PySide2.QtCore.Qt.Orientation, role:int=Qt.DisplayRole) -> typing.Any:
        if self.state.storage is None:
            return None
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.column_names[section]
            if orientation == Qt.Vertical:
                return self.state.storage.image_names[section]
        return None

    def display_property(self, prop_key: str):
        self.displayed_property_key = prop_key
        lab_hierarchy = self.state.label_hierarchy
        header_labels = set()
        labels = set()
        for i in range(self.state.storage.image_count):
            photo = self.state.storage.get_photo_by_idx(i, load_image=False)
            #header_labels = header_labels.union({self.state.colormap.label_names[prop.label] for prop in photo['Labels'].prop_list})
            labels = labels.union({prop.label for prop in photo['Labels'].prop_list})
        self.labels = list(labels)
        self.labels.sort()
        # TODO REMOVE
        #self.header_labels = [self.state.colormap.label_names[label] for label in self.labels]
        self.header_labels = [lab_hierarchy.nodes[label].name for label in self.labels]
        start = self.index(0, 0)
        end = self.index(self.rowCount()-1, self.columnCount() - 1)
        self.dataChanged.emit(start, end)

    def display_intensity_in_color(self, in_color: bool = True):
        self._display_intensity_in_color = in_color
        start = self.index(0, 0)
        end = self.index(self.rowCount()-1, self.columnCount() - 1)
        self.dataChanged.emit(start, end)

    def update_model(self):
        prop_tuple_set: typing.Set[typing.Tuple[Label, PropKey, PropName]] = set()
        for i in range(self.state.storage.image_count):
            photo = self.state.storage.get_photo_by_idx(i, load_image=False)
            for prop in photo['Labels'].prop_list:
                #prop_tuple = (prop.info.key, prop.label, prop.info.name)
                prop_tuple = (prop.label, prop.info.key, prop.info.name)
                prop_tuple_set.add(prop_tuple)
        self.prop_tuple_list = list(sorted(prop_tuple_set, key=lambda tup: tup[:2]))  # same count as column count
        #self.column_names = [f'{tup[2]}:{self.state.colormap.label_names[tup[1]]}' for tup in self.prop_tuple_list]
        self.column_names.clear()
        #cur_prop_key = ''
        # TODO replace hardcoded `Labels`
        hierarchy = self.state.storage.get_label_hierarchy2('Labels')
        cur_label = -1
        for label, key, name in self.prop_tuple_list:
            #if cur_prop_key != key:
            #if cur_label != label:
                #col_name = f'{name}:{self.state.colormap.label_names[label]}'
                # TODO REMOVE
                #col_name = f'{self.state.colormap.label_names[label]}:{name}'
            col_name = f'{hierarchy.nodes[label].name}:{name}'
            #cur_label = label
                #cur_prop_key = key
            #else:
                #col_name = f':{self.state.colormap.label_names[label]}'
            #    col_name = f':{name}'
            self.column_names.append(col_name)
        start = self.index(0, 0)
        end = self.index(self.rowCount()-1, self.columnCount() - 1)
        self.dataChanged.emit(start, end)


