import typing
from typing import List
from dataclasses import dataclass, field
from enum import IntEnum

import numpy as np

from arthropod_describer.common.photo import LabelType, LabelImg


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


def compute_label_difference(old_label: np.ndarray, new_label: np.ndarray) -> np.ndarray:
    non_equal_mask = old_label != new_label
    return np.where(non_equal_mask, new_label, -1)


def label_difference_to_command(label_diff: np.ndarray, label_img: LabelImg) -> CommandEntry:
    #label_nd = label_img.label_img
    #new_labels = np.unique(label_diff)[1:]  # filter out the -1 label which is the first on in the returned array
    #command = CommandEntry()

    #for label in new_labels:
    #    old_and_new = np.where(label_diff == label, label_nd, -1)
    #    old_labels = np.unique(old_and_new)[1:]  # filter out -1
    #    for old_label in old_labels:
    #        coords = np.nonzero(old_and_new == old_label)
    #        change = LabelChange(coords, label, old_label, label_img.label_type)
    #        command.add_label_change(change)
    #
    #return command
    return CommandEntry(label_difference_to_label_changes(label_diff, label_img))


def label_difference_to_label_changes(label_diff: np.ndarray, label_img: LabelImg) -> List[LabelChange]:
    label_nd = label_img.label_img
    new_labels = np.unique(label_diff)[1:]  # filter out the -1 label which is the first on in the returned array

    label_changes: List[LabelChange] = []

    for label in new_labels:
        old_and_new = np.where(label_diff == label, label_nd, -1)
        old_labels = np.unique(old_and_new)[1:]  # filter out -1
        for old_label in old_labels:
            coords = np.nonzero(old_and_new == old_label)
            label_changes.append(LabelChange(coords, label, old_label, label_img.label_type))

    return label_changes
