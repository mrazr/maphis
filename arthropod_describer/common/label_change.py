import json
import typing
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional, Tuple, Union, Any

import numpy as np

from arthropod_describer.common.photo import LabelImg


@dataclass(eq=False)
class LabelChange:
    """Class representing a set of pixels (`coords`) changing their value from `old_label` to `new_label`.

    coords: the pixels that changed their value
    new_label: their new value
    old_label: their previous value
    label_name: which label image this change pertains to
    _change_bbox: a bounding box enclosing the pixels (`coords`)
    """
    coords: typing.Tuple[np.ndarray, np.ndarray]
    new_label: int
    old_label: int
    label_name: str
    _change_bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None

    def swap_labels(self) -> 'LabelChange':
        return LabelChange(self.coords, self.old_label, self.new_label, self.label_name)

    @property
    def bbox(self) -> typing.Tuple[int, int, int, int]:
        if self._change_bbox is None:
            self._change_bbox = (np.min(self.coords[0]), np.max(self.coords[0]),
                                 np.min(self.coords[1]), np.max(self.coords[1]))
        return self._change_bbox

    def local_coords(self, bbox: Optional[Tuple[int, int, int, int]]) -> typing.Tuple[np.ndarray, np.ndarray]:
        bbox_ = self.bbox if bbox is None else bbox
        return self.coords[0] - bbox_[0], self.coords[1] - bbox_[2]

    @classmethod
    def from_dict(cls, obj: typing.Dict[str, Any]) -> 'LabelChange':
        return LabelChange(
            (np.array(decode_rle(obj['coords'][0])), np.array(decode_rle(obj['coords'][1]))),
            obj['new_label'],
            obj['old_label'],
            obj['label_name'],
            obj['_change_bbox']
        )


class DoType(IntEnum):
    Do = 0,
    Undo = 1,


class CommandKind(IntEnum):
    LabelImgChange = 0,
    Rot_90_CW = 1,
    Rot_90_CCW = -1

    def invert(self) -> 'CommandKind':
        return CommandKind(-1 * self)


@dataclass(eq=False)
class CommandEntry:
    """A class representing an edit command.

    change_chain: see `LabelChange`
    do_type: whether this command is either Undo or Do(Redo)
    _bbox: a box enclosing all modified pixels
    update_canvas: whether to update the view
    source: name of the tool/plugin that is responsible for the change. Will appear in Edit menu as e.g. 'Undo {source}`
    image_name: name of the photo that was of whose label image was modified
    label_name: name of the label image that this command pertains to
    old_approval: what was the approval before this change?
    new_approval: what is the approval after this change?
    command_kind: see `CommandKind`
    """
    change_chain: typing.List[LabelChange] = field(default_factory=list)
    do_type: DoType = DoType.Do
    _bbox: typing.Optional[typing.Tuple[int, int, int, int]] = None
    update_canvas: bool = True
    source: str = ''
    image_name: str = ''
    label_name: str = ''
    old_approval: str = ''
    new_approval: str = ''
    command_kind: CommandKind = CommandKind.LabelImgChange

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

    @classmethod
    def from_dict(cls, obj: typing.Dict[str, Any]) -> 'CommandEntry':
        return CommandEntry(
            #[LabelChange.from_dict(lab_ch_dict) for lab_ch_dict in obj['change_chain']],
            obj['change_chain'],
            DoType(obj['do_type']),
            obj['_bbox'],
            obj['update_canvas'],
            obj['source']
        )


def ce_object_hook(obj: typing.Dict[str, Any]) -> Union[CommandEntry, LabelChange]:
    if 'coords' in obj:
        return LabelChange.from_dict(obj)
    return CommandEntry.from_dict(obj)


# TODO maybe remove this
class CommandEntryJsonEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, LabelChange):
            return {
                'coords': (encode_into_rle(o.coords[0].tolist()), encode_into_rle(o.coords[1].tolist())),
                'new_label': o.new_label,
                'old_label': o.old_label,
                'label_name': o.label_name,
                '_change_bbox': o._change_bbox
            }
        elif isinstance(o, CommandEntry):
            return {
                'change_chain': [self.default(change) for change in o.change_chain],
                'do_type': o.do_type,
                '_bbox': o._bbox,
                'update_canvas': o.update_canvas
            }
        elif isinstance(o, np.integer):
            return int(o)
        else:
            return super().default(o)


def encode_into_rle(arr: List[int]) -> List[int]:
    rle = [arr[0], 1]
    i = 0
    for val in arr[1:]:
        if val == rle[2 * i]:
            rle[2 * i + 1] += 1
        else:
            rle.append(val)
            rle.append(1)
            i += 1
    return rle


def decode_rle(rle: List[int]) -> List[int]:
    values = []
    for i in range(len(rle) // 2):
        _vals = [rle[2 * i] for _ in range(2 * i + 1)]
        values.extend(_vals)
    return values


def remove_coords(cmd: CommandEntry) -> Tuple[CommandEntry, List[Tuple[np.ndarray, np.ndarray]]]:
    coords_list: List[Tuple[np.ndarray, np.ndarray]] = []
    for lab_change in cmd.change_chain:
        coords_list.append(lab_change.coords)
        lab_change.coords = ([], [])
    return cmd, coords_list


def compute_label_difference(old_label: np.ndarray, new_label: np.ndarray) -> np.ndarray:
    """Returns an image that contains values from `new_label` where `new_label` has different values from `old_label`,
    otherwise contains `-1`."""
    non_equal_mask = old_label != new_label
    return np.where(non_equal_mask, new_label, -1)


def label_difference_to_command(label_diff: np.ndarray, label_img: LabelImg, bbox: Optional[Tuple[int, int, int, int]]=None) -> CommandEntry:
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
    return CommandEntry(label_difference_to_label_changes(label_diff, label_img, bbox))


def label_difference_to_label_changes(label_diff: np.ndarray, label_img: LabelImg,
                                      bbox: Optional[Tuple[int, int, int, int]] = None) -> List[LabelChange]:
    """
    For a label difference image and a `LabelImg` returns a list of `LabelChange`.
    What is a label difference image, see the function `compute_label_difference`.
    """
    if bbox is not None:
        lab_diff = label_diff[bbox[0]:bbox[1], bbox[2]:bbox[3]]
        lab_nd = label_img.label_image[bbox[0]:bbox[1], bbox[2]:bbox[3]]
    else:
        bbox = (0, 0, 0, 0)
        lab_diff = label_diff
        lab_nd = label_img.label_image
    # label_nd = label_img.label_image
    new_labels = np.unique(lab_diff)  # these are all the new labels that were painted in by the user (except -1 which means `no change`)
    if -1 in new_labels:
        new_labels = new_labels[1:]  # filter out the -1 label which is the first on in the returned array

    label_changes: List[LabelChange] = []

    # now for each `label` in `new_labels` we need to generate one or more `LabelChange` objects
    # if `label` was painted over a region with a single label, say `1`, we would need to generate only one `LabelChange`,
    # specifying the coordinates of the pixels painted over and their old label value (`1`) and their new label value (`label`).
    # The number of `LabelChange` objects we need to create for `label` depends on how many different labels were painted
    # over by `label`.
    for label in new_labels:
        old_and_new = np.where(lab_diff == label, lab_nd, -1)  # reveal only those pixels of `label_nd` where `label_diff` is equal to `label`
        old_labels = np.unique(old_and_new)  # Get the all the different labels that were painted over by `label`.
        if -1 in old_labels:  # get rid of -1 (`no change`)
            old_labels = old_labels[1:]
        for old_label in old_labels:  # here we are actually creating the `LabelChange` objects, the pixels changing their value from `old_label` to `label`.
            yy, xx = np.nonzero(old_and_new == old_label)  # these are the coordinates of the pixels
            label_changes.append(LabelChange((yy+bbox[0], xx+bbox[2]), label, old_label, label_img.label_semantic))

    return label_changes


def restrict_label_to_mask(label: Union[LabelImg, np.ndarray], mask: Union[LabelImg, np.ndarray]) -> Optional[CommandEntry]:
    """
    Checks whether `label`-s non-zero entries are located entirely within `mask` and if not, returns a CommandEntry
    which, when performed on `label` will modify `label` so that it is contained inside `mask`.
    :param label: LabelImg or np.ndarray
    :param mask: LabelImg or np.ndarray
    :return: CommandEntry if `label` is not contained within `mask` else None
    """

    label_mask = label.label_image != 0
    mask_mask = mask.label_image != 0

    within = np.all(np.logical_and(label_mask, mask_mask) == label_mask)

    if within:
        return None

    to_modify = np.logical_xor(label_mask, mask_mask)

    edit_img = np.where(to_modify, label.label_image, -1)

    return label_difference_to_command(edit_img, label)


# TODO remove this
#def propagate_mask_changes_to(label_img: LabelImg, command: CommandEntry) -> Optional[CommandEntry]:
#    if label_img.label_type == LabelType.BUG:
#        return None
#
#    label_nd = label_img.label_image
#
#    label_modifications = {}
#
#    for change in command.change_chain:
#        if change.new_label > 0:  # augmentation of mask, so `label_img` is within the mask
#            continue
#
#        labels = label_nd[change.coords[0], change.coords[1]]
#
#        for label, y, x in zip(labels, *change.coords):
#            label_coords_list_tuple = label_modifications.setdefault(label, ([], []))
#            label_coords_list_tuple[0].append(y)
#            label_coords_list_tuple[1].append(x)
#    label_changes = [LabelChange(coords_list_tuple, 0, label, label_img.label_type) for label, coords_list_tuple in
#                     label_modifications.items()]
#    return CommandEntry(label_changes, label_type=label_img.label_type)


def generate_change_command(old_lab_img: LabelImg, new_label: np.ndarray) -> Optional[CommandEntry]:
    lab_diff = compute_label_difference(old_lab_img.label_image, new_label)
    return label_difference_to_command(lab_diff, old_lab_img)


def generate_command_from_coordinates(label_img: LabelImg, coords_x: List[int], coords_y: List[int], new_label: int) -> CommandEntry:
    lab_img = label_img.label_image
    values = lab_img[coords_y, coords_x]

    unique_values = np.unique(values)

    change_chain: List[LabelChange] = []

    for val in unique_values:
        r, c = coords_y[values == val], coords_x[values == val]
        lab_change = LabelChange((r, c), new_label=new_label, old_label=val, label_name=label_img.label_semantic)
        change_chain.append(lab_change)

    return CommandEntry(change_chain=change_chain)

