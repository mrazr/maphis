from typing import Dict, Tuple

import numpy as np
import typing

from PySide2.QtCore import Signal, QObject

from arthropod_describer.common.label_change import LabelChange, CommandEntry, DoType, CommandKind
from arthropod_describer.common.photo import Photo, UpdateContext
from arthropod_describer.common.state import State
from arthropod_describer.common.storage import Storage
from arthropod_describer.common.undo_manager import UndoManager

ImageName = str
LabelName = str
LabelApproval = str
DependentLabelName = str
LastObservedTime = int


class EditCommandExecutor(QObject):
    """
    Executes edit commands (`CommandEntry`) and handles undo/redo stacks.
    """
    label_image_modified = Signal([ImageName, LabelName])
    label_approval_changed = Signal([ImageName, LabelName, LabelApproval])

    def __init__(self, state: State, parent: typing.Optional[QObject] = None):
        super().__init__(parent)
        self.state: State = state
        self.dependencies: Dict[ImageName, Dict[DependentLabelName, Tuple[LabelName, LastObservedTime]]] = {}
        self.undo_manager: UndoManager = UndoManager(state)
        self._storage: typing.Optional[Storage] = None

    def initialize(self, state: State):
        if self._storage is not None:
            self._storage.update_photo.disconnect(self._handle_update_photo)
        self._storage = self.state.storage
        self._storage.update_photo.connect(self._handle_update_photo)
        self.dependencies.clear()
        self.state = state
        self.undo_manager.initialize(self.state.storage)

        self.update_dependencies()

    def _handle_update_photo(self, img_name: str, ctx: UpdateContext, data: typing.Optional[typing.Dict[str, typing.Any]]):
        if ctx == UpdateContext.Photo:
            # if data is None or 'operation' not in data:
            #     return
            # if not data['operation'].startswith('rot'):
            #     return
            # rot_type = CommandKind.Rot_90_CW if data['operation'] == 'rot_90_ccw' else CommandKind.Rot_90_CCW
            # cmd = CommandEntry([], do_type=DoType.Undo, image_name=img_name, command_kind=rot_type)
            self.undo_manager.undo_redo_store[img_name].clear()
            # self.undo_manager.undo_redo_store[img_name].undo_stack.append([cmd])

    def update(self):
        self.update_dependencies()
        self.undo_manager.load()

    def update_dependencies(self):
        for image_name in self.state.storage.image_names:
            self.dependencies[image_name] = {}
            photo = self.state.storage.get_photo_by_name(image_name)
            for label_name in self.state.storage.label_image_names:
                if (depends_on := self.state.storage.label_img_info[label_name].constrain_to) is not None:
                    self.dependencies[image_name][label_name] = (depends_on, photo[depends_on].timestamp)

    def change_labels(self, label_img: np.ndarray, change: LabelChange):
        """Change the values in `label_img` according to `change`"""
        label_img[change.coords[0], change.coords[1]] = change.new_label

    def _filter_against_mask(self, change: LabelChange, image_name: str, label_name: str):
        lab_img = self.state.storage.get_photo_by_name(image_name)[label_name]
        mask = lab_img.mask_for(lab_img.label_hierarchy.mask_label.label)
        # TODO handle `change.bbox` == None
        mask_roi = mask[change.bbox[0]:change.bbox[1]+1,
                   change.bbox[2]:change.bbox[3]+1]
        pixels = set([(t[0]+change.bbox[0], t[1]+change.bbox[2]) for t in np.argwhere(mask_roi)])
        change_pixels = set(zip(change.coords[0], change.coords[1]))

        valid_pixels = pixels.intersection(change_pixels)
        change.coords = [pixel[0] for pixel in valid_pixels], [pixel[1] for pixel in valid_pixels]

    def do_command(self, command: CommandEntry) -> typing.Optional[CommandEntry]:
        reverse_command = CommandEntry(source=command.source, image_name=command.image_name,
                                       label_name=command.label_name,
                                       old_approval=command.new_approval,
                                       new_approval=command.old_approval)
        if command.command_kind == CommandKind.LabelImgChange:
            labels_changed = set()
            for change in command.change_chain:
                # label_img = self.state.current_photo[change.label_name].label_image
                photo = self.state.storage.get_photo_by_name(command.image_name)
                label_img = photo[command.label_name]
                leave_loaded = label_img.is_set
                label_img_nd = label_img.label_image
                if label_img.label_info.constrain_to is not None:
                    self._filter_against_mask(change, photo.image_name, label_img.label_info.constrain_to)
                if len(change.coords[0]) == 0:
                    continue
                self.change_labels(label_img_nd, change)
                label_img.label_image = label_img_nd
                self.state.current_photo[change.label_name].set_dirty()
                # label_img.save()
                if not leave_loaded:
                    label_img.unload()
                reverse_command.add_label_change(change.swap_labels())
                labels_changed.add(change.label_name)
        else:
            photo = self.state.storage.get_photo_by_name(command.image_name, False)
            photo.rotate(command.command_kind == CommandKind.Rot_90_CCW)
        reverse_command.do_type = DoType.Undo if command.do_type == DoType.Do else DoType.Do
        reverse_command.command_kind = reverse_command.command_kind.invert()
        self.label_approval_changed.emit(reverse_command.image_name, reverse_command.label_name, command.new_approval)

        # for label_name in labels_changed:
        #     self.label_image_modified.emit(command.image_name, label_name)

        return reverse_command if len(reverse_command.change_chain) > 0 else None

    def do_commands(self, commands: typing.List[CommandEntry], img_name: typing.Optional[str] = None):
        reverse_commands = [rev_cmd for command in commands if (rev_cmd := self.do_command(command)) is not None]
        if len(reverse_commands) == 0:
            return
        do_type = reverse_commands[0].do_type

        undo_redo = self.undo_manager.current_undo_redo if img_name is None else self.undo_manager.undo_redo_store[img_name]

        undo_redo.push(do_type, reverse_commands)
        labels_to_update = set([(cmd.image_name, cmd.label_name) for cmd in commands])

        for image_name, label_name in labels_to_update:
            self.label_image_modified.emit(image_name, label_name)

    def enforce_within_mask(self, photo: Photo, label_name: LabelName):
        if label_name not in self.dependencies[photo.image_name]:
            return
        mask_label_name, last_timestamp = self.dependencies[photo.image_name][label_name]
        mask_label_img = photo[mask_label_name]
        if last_timestamp >= mask_label_img.timestamp:
            return
        label_img = photo[label_name]
        keep_loaded = label_img.is_set

        lab_hier = mask_label_img.label_hierarchy

        mask_label = lab_hier.mask_label.label
        mask_level = lab_hier.get_level(mask_label)

        level_mask = mask_label_img[mask_level] == mask_label

        label_img.label_image = np.where(level_mask, label_img.label_image, 0).astype(np.uint32)

        if not keep_loaded:
            label_img.unload()
