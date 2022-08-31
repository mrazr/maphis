from typing import List, Optional, Dict, Tuple

from PySide2.QtCore import QObject, Signal

from arthropod_describer.common.label_change import DoType, CommandEntry
from arthropod_describer.common.state import State
from arthropod_describer.common.storage import Storage

ImageName = str
LabelName = str
CommandName = str


class UndoRedo(QObject):
    enable = Signal([ImageName, LabelName, DoType, bool, CommandName])

    def __init__(self, photo_name: str, label_name: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.photo_name: str = photo_name
        self.label_name: str = label_name
        self.undo_stack: List[List[CommandEntry]] = []
        self.redo_stack: List[List[CommandEntry]] = []

    def get(self, do_type: DoType) -> List[List[CommandEntry]]:
        return self.undo_stack if do_type == DoType.Undo else self.redo_stack

    def has_commands(self) -> Tuple[bool, bool]:
        return len(self.undo_stack) > 0, len(self.redo_stack) > 0

    def pop(self, do_type: DoType) -> Optional[List[CommandEntry]]:
        if len(self.get(do_type)) == 0:
            return None
        cmds = self.get(do_type).pop()
        enable = len(self.get(do_type)) > 0
        self.enable.emit(self.photo_name, self.label_name, do_type, enable, '' if not enable else cmds[0].source)
        return cmds

    def push(self, do_type: DoType, cmds: List[CommandEntry]):
        self.get(do_type).append(cmds)
        self.enable.emit(self.photo_name, self.label_name, do_type, True, cmds[0].source)

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.enable.emit(self.photo_name, self.label_name, DoType.Undo, False, '')
        self.enable.emit(self.photo_name, self.label_name, DoType.Do, False, '')

    def clear_undo(self):
        self.undo_stack.clear()
        self.enable.emit(self.photo_name, self.label_name, DoType.Undo, False, '')

    def clear_redo(self):
        self.redo_stack.clear()
        self.enable.emit(self.photo_name, self.label_name, DoType.Do, False, '')


class UndoManager(QObject):
    enable_undo_redo = Signal([ImageName, LabelName, DoType, bool, CommandName])

    def __init__(self, state: State, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.state: State = state
        self.storage: Optional[Storage] = None
        # self.undo_redo_store: Dict[str, Dict[str, UndoRedo]] = {}
        self.undo_redo_store: Dict[str, UndoRedo] = {}
        self._all_undo_redos: List[UndoRedo] = []

    def initialize(self, storage: Storage):
        self.save()
        self.storage = storage
        self.load()

    def save(self):
        # TODO save to disk
        for undo_redo in self._all_undo_redos:
            undo_redo.enable.disconnect(self.enable_undo_redo.emit)
        self._all_undo_redos.clear()
        self.undo_redo_store.clear()

    def load(self):
        # TODO load from self.storage.location
        for image_name in self.storage.image_names:
            if image_name in self.undo_redo_store:
                continue
            # photo = self.storage.get_photo_by_name(image_name, load_image=False)
            self.undo_redo_store[image_name] = UndoRedo(image_name, '')
            self.undo_redo_store[image_name].enable.connect(self.enable_undo_redo.emit)
            # undo_redo: Dict[str, UndoRedo] = {}
            # for label_name in photo.label_images_.keys():
            #     undo_redo[label_name] = UndoRedo(image_name, label_name)
            #     self._all_undo_redos.append(undo_redo[label_name])
            #     undo_redo[label_name].enable.connect(self.enable_undo_redo.emit)
            # self.undo_redo_store[image_name] = undo_redo

    def get_undo_redo(self, photo_name: str, label_name: str) -> UndoRedo:
        return self.undo_redo_store[photo_name]

    def get_all_undo_redo(self, photo_name: str) -> Dict[str, UndoRedo]:
        return self.undo_redo_store[photo_name]

    @property
    def current_undo_redo(self) -> UndoRedo:
        return self.undo_redo_store[self.state.current_photo.image_name]
