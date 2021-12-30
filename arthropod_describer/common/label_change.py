import typing
from typing import List, Optional, Tuple, Union
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
    _change_bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None

    def swap_labels(self) -> 'LabelChange':
        return LabelChange(self.coords, self.old_label, self.new_label, self.label_type)

    @property
    def bbox(self) -> typing.Tuple[int, int, int, int]:
        if self._change_bbox is None:
            self._change_bbox = (np.min(self.coords[0]), np.max(self.coords[0]),
                                 np.min(self.coords[1]), np.max(self.coords[1]))
        return self._change_bbox

    def local_coords(self, bbox: Optional[Tuple[int, int, int, int]]) -> typing.Tuple[np.ndarray, np.ndarray]:
        bbox_ = self.bbox if bbox is None else bbox
        return self.coords[0] - bbox_[0], self.coords[1] - bbox_[2]


class DoType(IntEnum):
    Do = 0,
    Undo = 1,


@dataclass(eq=False)
class CommandEntry:
    change_chain: typing.List[LabelChange] = field(default_factory=list)
    do_type: DoType = DoType.Do
    _bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None
    label_type: LabelType = LabelType.REGIONS
    update_canvas: bool = True

    def add_label_change(self, change: LabelChange):
        self.change_chain.append(change)

    @property
    def bbox(self) -> typing.Tuple[int, int, int, int]:
        if self._bbox is None:
            bbox = list(self.change_chain[0].bbox)
            for change in self.change_chain[1:]:
                bbox2 = change.bbox
                bbox[0] = min(bbox[0], bbox2[0])
                bbox[1] = max(bbox[1], bbox2[1])
                bbox[2] = min(bbox[2], bbox2[2])
                bbox[3] = max(bbox[3], bbox2[3])
            self._bbox = tuple(bbox)
        return self._bbox


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
    return CommandEntry(label_difference_to_label_changes(label_diff, label_img), label_type=label_img.label_type)


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


def restrict_label_to_mask(label: Union[LabelImg, np.ndarray], mask: Union[LabelImg, np.ndarray]) -> Optional[CommandEntry]:
    """
    Checks whether `label`-s non-zero entries are located entirely within `mask` and if not, returns a CommandEntry
    which, when performed on `label` will modify `label` so that it is contained inside `mask`.
    :param label: LabelImg or np.ndarray
    :param mask: LabelImg or np.ndarray
    :return: CommandEntry if `label` is not contained within `mask` else None
    """

    label_mask = label.label_img != 0
    mask_mask = mask.label_img != 0

    within = np.all(np.logical_and(label_mask, mask_mask) == label_mask)

    if within:
        return None

    to_modify = np.logical_xor(label_mask, mask_mask)

    edit_img = np.where(to_modify, label.label_img, -1)

    return label_difference_to_command(edit_img, label)


def propagate_mask_changes_to(label_img: LabelImg, command: CommandEntry) -> Optional[CommandEntry]:
    if label_img.label_type == LabelType.BUG:
        return None

    label_nd = label_img.label_img

    label_modifications = {}

    for change in command.change_chain:
        if change.new_label > 0:  # augmentation of mask, so `label_img` is within the mask
            continue

        labels = label_nd[change.coords[0], change.coords[1]]

        for label, y, x in zip(labels, *change.coords):
            label_coords_list_tuple = label_modifications.setdefault(label, ([], []))
            label_coords_list_tuple[0].append(y)
            label_coords_list_tuple[1].append(x)
    label_changes = [LabelChange(coords_list_tuple, 0, label, label_img.label_type) for label, coords_list_tuple in
                     label_modifications.items()]
    return CommandEntry(label_changes, label_type=label_img.label_type)
