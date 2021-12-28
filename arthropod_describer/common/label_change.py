import typing
from dataclasses import dataclass, field
from enum import IntEnum

import numpy as np

from arthropod_describer.common.photo import LabelType


@dataclass(eq=False)
class LabelChange:
    coords: typing.Tuple[np.ndarray, np.ndarray]
    new_label: int
    old_label: int
    label_type: LabelType

    def swap_labels(self) -> 'LabelChange':
        return LabelChange(self.coords, self.old_label, self.new_label, self.label_type)


class DoType(IntEnum):
    Do = 0,
    Undo = 1,


@dataclass(eq=False)
class CommandEntry:
    change_chain: typing.List[LabelChange] = field(default_factory=list)
    do_type: DoType = DoType.Do

    def add_label_change(self, change: LabelChange):
        self.change_chain.append(change)
