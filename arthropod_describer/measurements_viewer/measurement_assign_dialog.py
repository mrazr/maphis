import typing
from functools import partial

import PySide2
from PySide2.QtCore import Qt, QItemSelection, QModelIndex, QItemSelectionModel, Signal
from PySide2.QtGui import QIcon, QPixmap, QColor, QBrush
from PySide2.QtWidgets import QDialog, QTreeWidgetItem, QTreeWidget, QAbstractItemView, QDialogButtonBox, QVBoxLayout, \
    QWidget, QGroupBox

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_hierarchy import Node
from arthropod_describer.common.label_tree_model import LabelTreeModel, LabelTreeMode
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.state import State
from arthropod_describer.common.user_params import UserParam, UserParamWidgetBinding, create_params_widget
from arthropod_describer.measurements_viewer.ui_measurement_assign_dialog import Ui_MeasurementAssignDialog
from arthropod_describer.plugin_manager import RegionCompsListModel
from arthropod_describer.color_tolerance_dialog import ColorToleranceDialog

ABS_KEY_ROLE = Qt.UserRole
PARENT_KEY_ROLE = Qt.UserRole + 1
PROP_KEY_ROLE = Qt.UserRole + 2
LABEL_ROLE = Qt.UserRole + 3
LEAF_ITEM_ROLE = Qt.UserRole + 4


class MeasurementAssignDialog(QDialog):
    compute_measurements = Signal(dict)

    def __init__(self, state: State, comp_model: RegionCompsListModel, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)
        self.ui = Ui_MeasurementAssignDialog()
        self.ui.setupUi(self)
        self.ui.labelTree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.ui.btnAssign.clicked.connect(self.assign_measurements)

        self.ui.assignmentTree.itemSelectionChanged.connect(self.assignment_selection_changed)
        self.ui.assignmentTree.clicked.connect(tree_item_double_click_handler(self.ui.assignmentTree))
        self.ui.assignmentTree.selectionModel().selectionChanged.connect(self.deselect_ancestors_of_leaves)

        self.ui.measurementTree.itemSelectionChanged.connect(self.measurement_selection_changed)

        self.ui.btnLabelSelectAll.clicked.connect(self.ui.labelTree.selectAll)
        self.ui.btnLabelDeselectAll.clicked.connect(self.ui.labelTree.clearSelection)

        self.ui.btnMeasSelectAll.clicked.connect(self.ui.measurementTree.selectAll)
        self.ui.btnMeasDeselectAll.clicked.connect(self.ui.measurementTree.clearSelection)

        self.ui.btnAssignmentSelectAll.clicked.connect(self.ui.assignmentTree.selectAll)
        self.ui.btnAssignmentDeselectAll.clicked.connect(self.ui.assignmentTree.clearSelection)

        self.ui.btnAssignmentRemove.clicked.connect(self.remove_assignments)

        self.ui.btnDemoSelectColorAndTolerance.clicked.connect(self.demo_select_color_and_tolerance)

        self.ui.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)

        self.ui.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.accept)

        self.state = state
        self._label_tree_model = LabelTreeModel(self.state, LabelTreeMode.Choosing)
        self.ui.labelTree.setModel(self._label_tree_model)
        self.ui.labelTree.selectionModel().selectionChanged.connect(self.label_selection_changed)
        self.ui.labelTree.setStyleSheet('QTreeView::item:disabled {color: #c0c0c0;}')

        self.comps_model = comp_model

        self.measurement_items: typing.List[QTreeWidgetItem] = []

        self.label_items: typing.Dict[int, QTreeWidgetItem] = {}

        # self.assignments: typing.Dict[str, typing.Set[int]] = {}
        self.assignments: typing.Dict[str, typing.Set[int]] = {}
        self.assignment_items: typing.List[QTreeWidgetItem] = []
        self.assignment_prop_items: typing.Dict[str, QTreeWidgetItem] = {}
        self.assignment_label_items: typing.Dict[int, QTreeWidgetItem] = {}

        self._setup_demo_color_tolerance_dialog()

        self.settings_layout = QVBoxLayout()
        self.ui.scrollAreaWidgetContents.setLayout(self.settings_layout)
        self.param_settings_for_props: typing.Dict[str, typing.List[UserParam]] = {}
        self.param_bindings_for_props: typing.Dict[str, UserParamWidgetBinding] = {}
        self.param_widgets_for_props: typing.Dict[str, QWidget] = {}

    def _populate_label_tree(self):
        self.ui.labelTree.clear()
        hierarchy = self.state.storage.get_label_hierarchy2('Labels')
        colormap = hierarchy.colormap
        codes = [hierarchy.code(label) for label in hierarchy.labels]
        codes.sort()
        parent = self.ui.labelTree
        sibling = None
        stack = []
        depth = -1
        used_labels = self.state.storage.used_regions('Labels')
        print(used_labels)
        for code in codes[1:]:
            label = hierarchy.label(code)
            code_depth = hierarchy.get_level(hierarchy.label(code))
            if code_depth > depth:
                if depth >= 0:
                    stack.append(parent)
                parent = parent if sibling is None else sibling
                depth = code_depth
                sibling = None
            elif code_depth < depth:
                pop_count = depth - code_depth
                if pop_count > 1:
                    for _ in range(pop_count - 1):
                        sibling = stack.pop()
                else:
                    sibling = parent
                parent = stack.pop()
                depth = code_depth
            twidget = QTreeWidgetItem(parent, after=sibling)
            twidget.setExpanded(True)
            label = hierarchy.label(code)
            label_node = hierarchy.nodes[label]
            # TODO REMOVE
            #twidget.setText(0, self.state.colormap.label_names[label])
            twidget.setText(0, label_node.name)
            twidget.setData(0, Qt.UserRole, label)
            pixmap = QPixmap(24, 24)
            pixmap.fill(QColor.fromRgb(*colormap[label]))
            icon = QIcon(pixmap)
            twidget.setIcon(0, icon)
            self.label_items[label] = twidget
            if label in used_labels or any(map(partial(hierarchy.is_ancestor_of, label), used_labels)):
                twidget.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            else:
                twidget.setFlags(Qt.ItemIsEnabled)
                twidget.setForeground(0, QBrush(QColor.fromRgb(120, 120, 120)))
            sibling = twidget
        self.ui.labelTree.addTopLevelItem(stack[2])
        self.ui.labelTree.doubleClicked.connect(tree_item_double_click_handler(self.ui.labelTree))

    def _populate_measurement_comps_tree(self):
        prop_comps: typing.List[PropertyComputation] = self.comps_model.region_comps
        self.ui.measurementTree.clear()
        group_items: typing.Dict[str, QTreeWidgetItem] = {}

        for prop_comp in prop_comps:
            if prop_comp.group not in group_items:
                _item = QTreeWidgetItem(self.ui.measurementTree)
                _item.setText(0, prop_comp.group)
                _item.setFlags(Qt.ItemIsEnabled)
                group_items[prop_comp.group] = _item
            parent = group_items[prop_comp.group]
            # parent = QTreeWidgetItem(self.ui.measurementTree)
            # parent.setText(0, prop_comp.info.name)
            # parent.setData(0, Qt.UserRole, prop_comp.info.key)
            # parent.setFlags(Qt.ItemIsEnabled)
            for prop in prop_comp.computes.values():
                kid = QTreeWidgetItem(parent)
                kid.setText(0, prop.name)
                kid.setToolTip(0, prop.description)
                kid.setData(0, Qt.UserRole, prop_comp.info.key)
                parent.addChild(kid)
        self.ui.measurementTree.expandAll()
        self.ui.measurementTree.doubleClicked.connect(tree_item_double_click_handler(self.ui.measurementTree))

    def _populate_assignment_tree(self):
        self.ui.assignmentTree.clear()
        top_level = []
        prop_comps: typing.List[PropertyComputation] = self.comps_model.region_comps
        for prop_comp in prop_comps:
            twidget = QTreeWidgetItem(self.ui.assignmentTree)
            twidget.setText(0, prop_comp.info.name)
            twidget.setData(0, ABS_KEY_ROLE, prop_comp.info.key)
            twidget.setData(0, LEAF_ITEM_ROLE, False)
            twidget.setFlags(Qt.ItemIsEnabled)
            top_level.append(twidget)
            twidget.setHidden(True)
            twidget.setExpanded(True)
            props: typing.List[Info] = list(prop_comp.computes.values())
            for prop in props:
                absolute_key = f'{prop_comp.info.key}.{prop.key}'
                self.assignments[absolute_key] = set()
                kid = QTreeWidgetItem()
                kid.setText(0, prop.name)
                kid.setToolTip(0, prop.description)
                kid.setData(0, ABS_KEY_ROLE, absolute_key)
                kid.setData(0, LEAF_ITEM_ROLE, False)
                kid.setExpanded(True)
                kid.setHidden(True)
                kid.setFlags(Qt.ItemIsEnabled)
                twidget.addChild(kid)
                self.assignment_prop_items[absolute_key] = kid
        self.ui.assignmentTree.addTopLevelItems(top_level)
        self.assignment_items = top_level

    def show_dialog(self) -> typing.Dict[str, typing.Set[int]]:
        # self._populate_label_tree()
        self._populate_measurement_comps_tree()
        # self._populate_assignment_tree()
        self._label_tree_model = LabelTreeModel(self.state, LabelTreeMode.Choosing)
        self.ui.labelTree.setModel(self._label_tree_model)
        self.ui.labelTree.expandAll()
        self.ui.labelTree.selectionModel().selectionChanged.connect(self.label_selection_changed)
        if self.exec_() == QDialog.Accepted:
            return self.assignments
            #self.compute_measurements.emit(self.assignments)
            #computations = {}
            #for prop_path, labels in self.assignments.items():
            #    dot_splits = prop_path.split('.')
            #    prop_name = dot_splits.pop()
            #    comp_key = '.'.join(dot_splits)
            #    prop_labels = computations.setdefault(comp_key, {})
            #    prop_labels[prop_name] = labels
            #for computation_key, prop_labels in computations.items():
            #    print(f'{computation_key} will compute {prop_labels}')
            #for i in range(self.state.storage.image_count):
            #    photo = self.state.storage.get_photo_by_idx(i)
            #    for computation_key, prop_labels in computations.items():
            #        computation: PropertyComputation = self.comps_model.computations_dict[computation_key]
            #        reg_props = computation(photo, prop_labels)
            #        for prop in reg_props:
            #            prop.info.key = f'{computation_key}.{prop.info.key}'
            #            photo['Labels'].set_region_prop(prop.label, prop)
        else:
            self.assignment_label_items.clear()
            self.assignments.clear()
            self.ui.assignmentTree.clear()
            self.ui.buttonBox.button(QDialogButtonBox.Apply).setEnabled(False)
            return {}

    # def assign_measurements_(self):
    #     # label_selection: typing.List[QTreeWidgetItem] = self.ui.labelTree.selectedItems()
    #     label_selection: typing.List[QModelIndex] = self.ui.labelTree.selectedIndexes()
    #     prop_selection: typing.List[QModelIndex] = self.ui.measurementTree.selectedIndexes()
    #     # TODO replace hardcoded `Labels`
    #     hierarchy = self.state.storage.get_label_hierarchy2('Labels')
    #     for prop_idx in prop_selection:
    #         if not prop_idx.parent().isValid():
    #             continue
    #         parent = prop_idx.parent()
    #         parent_key = self.ui.measurementTree.model().data(parent, Qt.UserRole)
    #         prop_key = self.ui.measurementTree.model().data(prop_idx, Qt.UserRole)
    #         absolute_key = f'{parent_key}.{prop_key}'
    #         prop_item = self.assignment_prop_items[absolute_key]
    #         for lab_index in label_selection:
    #             lab_node: Node = lab_index.internalPointer()
    #             if (label := lab_node.label) not in self.assignments.setdefault(absolute_key, set()):
    #                 self.assignments[absolute_key].add(label)
    #                 twidget = QTreeWidgetItem()
    #                 #label_node = self.state.label_hierarchy.nodes[label]
    #                 label_node = hierarchy.nodes[label]
    #                 # TODO REMOVE
    #                 #twidget.setText(0, self.state.colormap.label_names[label])
    #                 twidget.setText(0, label_node.name)
    #                 twidget.setIcon(0, self.label_items[label].icon(0))
    #                 twidget.setData(0, ABS_KEY_ROLE, f'{absolute_key}')
    #                 twidget.setData(0, PARENT_KEY_ROLE, parent_key)
    #                 twidget.setData(0, PROP_KEY_ROLE, prop_key)
    #                 twidget.setData(0, LABEL_ROLE, label)
    #                 twidget.setData(0, LEAF_ITEM_ROLE, True)
    #                 prop_item.addChild(twidget)
    #         prop_item.setExpanded(True)
    #         parent_item = self.assignment_items[parent.row()]
    #         parent_item.setHidden(False)
    #         prop_item.setHidden(False)
    #     for prop_item in self.assignment_prop_items.values():
    #         prop_item.setHidden(prop_item.childCount() == 0)
    #
    #     self.ui.buttonBox.button(QDialogButtonBox.Apply).setEnabled(len(self.assignments) > 0)

    def assign_measurements(self):
        # to each label in `label_selection` assigns all props in `prop_selection` and stores the assignments
        # in `self.assignments` and also in the QTreeView self.ui.measurementTree

        label_selection: typing.List[QModelIndex] = self.ui.labelTree.selectedIndexes()
        prop_selection: typing.List[QModelIndex] = self.ui.measurementTree.selectedIndexes()
        # TODO replace hardcoded `Labels`
        hierarchy = self.state.storage.get_label_hierarchy2('Labels')

        for label_index in label_selection:
            if not label_index.isValid():
                continue
            label_node: Node = label_index.internalPointer()
            if label_node.label not in self.assignment_label_items:
                label_item = QTreeWidgetItem()
                label_item.setText(0, label_node.name)
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor(*label_node.color))
                label_item.setIcon(0, QIcon(pixmap))
                label_item.setData(0, LABEL_ROLE, label_node.label)
                label_item.setData(0, LEAF_ITEM_ROLE, False)
                self.ui.assignmentTree.addTopLevelItem(label_item)
                self.assignment_label_items[label_node.label] = label_item
            label_tree_item: QTreeWidgetItem = self.assignment_label_items[label_node.label]
            for prop_idx in prop_selection:
                prop_parent = prop_idx.parent()  # The Plugin index that is the parent of `prop_idx`
                parent_key = self.ui.measurementTree.model().data(prop_parent, Qt.UserRole)  # unique key of the parent
                prop_key = self.ui.measurementTree.model().data(prop_idx, Qt.UserRole)
                # absolute_key = f'{parent_key}.{prop_key}'
                absolute_key = prop_key
                # if absolute_key not in self.assignments.setdefault(label_node.label, set()):
                computation = self.comps_model.computations_dict[prop_key]
                if prop_key not in self.param_widgets_for_props and len(computation.user_params) > 0:
                    widget = create_params_widget(computation.user_params, self.state)
                    binding = UserParamWidgetBinding(self.state)
                    binding.bind(computation.user_params, widget)
                    group = QGroupBox()
                    group.setTitle(computation.info.name)
                    layout = QVBoxLayout()
                    layout.addWidget(widget)
                    group.setLayout(layout)
                    self.param_widgets_for_props[prop_key] = group
                    self.param_bindings_for_props[prop_key] = binding
                    self.settings_layout.addWidget(group)
                if label_node.label not in self.assignments.setdefault(absolute_key, set()):
                    # self.assignments[label_node.label].add(absolute_key)
                    self.assignments[absolute_key].add(label_node.label)
                    twidget = QTreeWidgetItem()
                    # twidget.setText(0, self.comps_model.computations_dict[parent_key].computes[prop_key].name)
                    twidget.setText(0, self.comps_model.computations_dict[prop_key].info.name)
                    twidget.setData(0, ABS_KEY_ROLE, f'{absolute_key}')
                    # twidget.setData(0, PARENT_KEY_ROLE, parent_key)
                    # twidget.setData(0, PROP_KEY_ROLE, prop_key)
                    twidget.setData(0, LABEL_ROLE, label_node.label)
                    twidget.setData(0, LEAF_ITEM_ROLE, True)
                    label_tree_item.addChild(twidget)
            label_tree_item.setExpanded(True)
            label_tree_item.setHidden(label_tree_item.childCount() == 0)

        self.ui.buttonBox.button(QDialogButtonBox.Apply).setEnabled(len(self.assignments) > 0)

    def label_selection_changed(self, sel, des):
        self.enable_assign_button()

    def measurement_selection_changed(self):
        self.enable_assign_button()

    def assignment_selection_changed(self):
        self.ui.btnAssignmentRemove.setEnabled(len(self.ui.assignmentTree.selectedIndexes()) > 0)

    def enable_assign_button(self):
        self.ui.btnAssign.setEnabled(len(self.ui.labelTree.selectedIndexes()) > 0 and
                                     len(self.ui.measurementTree.selectedIndexes()) > 0)

    def remove_assignments(self):
        items: typing.List[QTreeWidgetItem] = self.ui.assignmentTree.selectedItems()
        deleted: typing.Set[str] = set()

        leaves: typing.List[QTreeWidgetItem] = [item for item in items if item.data(0, LEAF_ITEM_ROLE)]
        nodes: typing.List[QTreeWidgetItem] = [item for item in items if not item.data(0, LEAF_ITEM_ROLE)]

        for leaf in leaves:
            key = leaf.data(0, ABS_KEY_ROLE)
            leaf.parent().removeChild(leaf)
            self.assignments[key].remove(leaf.data(0, LABEL_ROLE))
            if len(self.assignments[key]) == 0:
                del self.assignments[key]
                if key in self.param_widgets_for_props:
                    widget = self.param_widgets_for_props[key]
                    self.settings_layout.removeWidget(widget)
                    widget.deleteLater()
                    del self.param_widgets_for_props[key]
                    del self.param_bindings_for_props[key]
                # del self.param_settings_for_props[key]
            self.ui.assignmentTree.removeItemWidget(leaf, 0)

        for node in self.assignment_label_items.values():
            if node.childCount() == 0:
                node.setHidden(True)
        for node in self.assignment_items:
            node.setHidden(all([node.child(i).isHidden() for i in range(node.childCount())]))

        print(self.assignments)
        self.ui.buttonBox.button(QDialogButtonBox.Apply).setEnabled(len(self.assignments) > 0)
        self.ui.assignmentTree.update()

    def deselect_ancestors_of_leaves(self, selected: QItemSelection, deselected: QItemSelection):
        for index in deselected.indexes():
            if index.child(0, 0).isValid():
                continue
            parent = index.parent()
            while parent.isValid():
                self.ui.assignmentTree.selectionModel().select(parent, QItemSelectionModel.Deselect)
                parent = parent.parent()

    def _setup_demo_color_tolerance_dialog(self):
        self._color_tolerance_dialog = ColorToleranceDialog(self.state)
        self._color_tolerance_dialog.hide()

    def demo_select_color_and_tolerance(self):
        self._color_tolerance_dialog.get_color_and_tolerances()


def tree_item_double_click_handler(tree_widget: QTreeWidget):
    def select_subtree(index: QModelIndex):
        print(id(tree_widget))
        if not index.child(0, 0).isValid():
            return
        stack = [index]
        while len(stack) > 0:
            idx = stack.pop()
            if idx.isValid():
                curr_idx = idx.child(0, 0)
                child_idx = 0
                indexes_to_select = []
                while curr_idx.isValid():
                    indexes_to_select.append(curr_idx)
                    stack.append(curr_idx)
                    child_idx += 1
                    curr_idx = idx.child(child_idx, 0)
                if len(indexes_to_select) > 0:
                    tree_widget.selectionModel().select(QItemSelection(indexes_to_select[0], indexes_to_select[-1]),
                                                        QItemSelectionModel.Select)
    return select_subtree


def visit_subtree(root: QTreeWidgetItem):
    stack = [root]
    while len(stack) > 0:
        item = stack.pop()
        for i in range(len(item.childCount())):
            stack.append(item.child(i))
        yield item
    yield None
