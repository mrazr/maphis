import functools
import json
import math
import operator
from pathlib import Path
from typing import List, Optional, Dict, Union, Any, Tuple, Set


class Node:
    """Label representation."""
    def __init__(self):
        self.parent: Optional[Node] = None
        self.children: List[Node] = []
        self.label: int = -1
        self.code: str = ''
        self.name: str = ''
        self.color: Tuple[int, int, int] = (255, 255, 255)  # for now

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'code': self.code,
            'color': {
                'red': self.color[0],
                'green': self.color[1],
                'blue': self.color[2]
            }
        }


class LabelHierarchy:
    """Class representing a particular hierarchy of labels.

    Lorem ipsum dolor sit amet all the waaaaaaaaaaaay.

    """

    ROOT: int = -1

    def __init__(self):
        self.masks: List[int] = []  # bit masks for all label levels, len(self.masks) = number of levels in hierarchy
        self.n_bits: int = 0  # how many bits are allocated for each label in the hierarchy
        self.named_masks: Dict[str, int] = {}  # a mapping; mask_name -> mask; self.named_masks[mask_name] = mask, where mask_name from self.mask_names, mask from self.masks
        self.mask_names: List[str] = []  # human-friendly names of masks, eg. Animal, Segments, corresponding to label levels
        self.masks_names: Dict[int, str] = {}  # a mapping; mask -> mask_name, reverse of self.named_masks
        self.counts_of_bits: List[int] = []  # a distribution of `n_bits` to `len(self.masks)` levels, self.counts_of_bits[i] = x means, x bits are allocated to i-th mask/level
        self.shifts: List[int] = []  # bit shifts for each mask, `self.shifts[0] = self.n_bits`, self.shifts[i] = self.shifts[i-1] - self.counts_of_bits[i-1]
        self.whole_mask: int = 0  # this should be 2^self.n_bits - 1
        self.sep: str = ':'  # separator for code representation of labels, e.g. 1:1:2:0
        self.labels: List[int] = []  # list of labels that are defined, ie. that make sense to use for a specific case
        self.children: Dict[int, List[int]] = {}  # a mapping; label -> list of label's children
        self.parents: Dict[int, int] = {}  # a mappping; label -> label's parent
        self.nodes: Dict[int, Node] = {}  # a mapping; label -> label's node representation
        #self.colormap: Optional[Colormap] = None
        self.colormap: Dict[int, Tuple[int, int, int]] = {}
        self.name = ''
        self._level_groups: List[Set[int]] = []
        self.mask_label: Optional[Node] = None

    @classmethod
    def are_valid_masks(cls, masks: List[int], n_bits: int = 32) -> bool:
        """
        Checks whether `masks` represents a valid distribution of masks for `n_bits`-bit labels
        For `masks` to be a valid list of masks:

        1. each mask must have only one sequence of ones, e.g. 11110000 is valid, 11110011 is not valid
        2. no two distinct masks can overlap, e.g. 11110000, 00001111 is a valid distribution;
                   11110000, 00111111  is not a valid mask distribution
        3. `masks[i]` and `masks[i+1]` must have their one-bit sequences adjacent, ie. 11110000 00001111 is valid
                    11110000, 00000111 is not valid
        4. bit-wise union of all masks must equal to `2^n_bits - 1`
        """
        if not all(map(functools.partial(cls.has_unique_sequence_of_ones, n_bits=n_bits), masks)):
            return False

        return not cls.masks_overlap(list(sorted(masks))) and cls.masks_are_adjacent(masks) and cls.masks_cover_nbits(
            masks, n_bits)

    @classmethod
    def masks_overlap(cls, masks: List[int]) -> bool:
        """Checks whether the sorted masks in `masks` have nonempty bitwise intersection."""
        masks_ = list(sorted(masks))
        for i in range(len(masks_) - 1):
            if masks_[i] & masks_[i+1]:
                return True
        return False

    @classmethod
    def masks_are_adjacent(cls, masks: List[int]) -> bool:
        """Checks whether the neighboring masks in sorted(`masks`) are adjacent w.r.t. to their one-bit sequences.
        see 3. in the docstring of `are_valid_masks`"""
        masks_ = list(sorted(masks))
        for i in range(len(masks_) - 1):
            if not (masks_[i] & (masks_[i+1] >> 1)):
                return False
        return True

    @classmethod
    def has_unique_sequence_of_ones(cls, mask: int, n_bits: int = 32) -> bool:
        """Checks whether `mask` contains a single contiguous run of `1`-s."""
        found_seq_already = False  # is True when 0 bit is encountered after a sequence of 1 bits
        ones = False  # is switched to True when encountered the first 1 bit

        for i in range(n_bits):
            bit = (mask >> i) & 1
            if bit:
                if not found_seq_already: # The first 1bit encountered, marking the first sequence of 1bits
                    ones = True
                    found_seq_already = True
                else:
                    if not ones: # This means we encountered a second sequence of 1bits, making the mask an invalid one
                        return False
            else:
                ones = False
        return True

    @classmethod
    def create(cls, masks: List[int], mask_names: Optional[List[str]] = None, n_bits: int = 32) -> \
            Optional['LabelHierarchy']:
        """Creates a new label hierarchy with the given masks in `masks`, named by `mask_names` and with a total of
        `n_bits` bits per mask."""
        if not cls.are_valid_masks(masks, n_bits):
            return None  # TODO raise Exception?
        if mask_names is None:
            mask_names = [f'level {i}' for i in range(len(masks))]

        hier = LabelHierarchy()
        hier.whole_mask = 2**n_bits - 1
        hier.masks = list(sorted(masks, reverse=True))  # sort the masks in DESC
        hier.counts_of_bits = [cls._bit_count(mask) for mask in hier.masks]  # infer the count of bits of each mask
        start = n_bits
        for bit_count in hier.counts_of_bits:  # derive the bit shift for each mask.
            start -= bit_count
            hier.shifts.append(start)
        hier.named_masks = {name: mask for name, mask in zip(mask_names, hier.masks)}
        hier.n_bits = n_bits
        hier.mask_names = mask_names
        hier.masks_names = {mask: name for name, mask in hier.named_masks.items()}

        for _ in range(len(masks)):
            hier._level_groups.append(set())

        return hier

    @classmethod
    def designate_bits(cls, counts_of_bits: List[int], mask_names: Optional[List[str]] = None, n_bits: int = 32) -> \
            Optional['LabelHierarchy']:
        """Generates `len(counts_of_bits)` masks and designates each of them its corresponding number of bits as specified
        in `counts_of_bits` out of total number of bits as specified in `n_bits`.
        Optionally gives them names as specified in `mask_names`."""
        if mask_names is None:
            mask_names = [f'level {i}' for i in range(len(counts_of_bits))]
        masks = []
        start = n_bits
        for count_of_bits in counts_of_bits:
            start -= count_of_bits
            masks.append((2**count_of_bits - 1) << start)
        return cls.create(masks, mask_names=mask_names, n_bits=n_bits)

    @classmethod
    def masks_cover_nbits(cls, masks: List[int], n_bits: int = 32) -> bool:
        """Checks whether the total number of 1-bits in all masks in `masks` is equal to `n_bits`."""
        mask = functools.reduce(operator.or_, masks)
        return mask == 2**n_bits - 1

    @classmethod
    def load(cls, path_to_json: Path) -> Optional['LabelHierarchy']:
        if not path_to_json.exists():
            return None
        with open(path_to_json) as f:
            label_hier_info = json.load(f)
        #counts_of_bits = label_hier_info['counts_of_bits']
        #mask_names = label_hier_info['mask_names']
        #return cls.designate_bits(counts_of_bits, mask_names=mask_names, n_bits=sum(counts_of_bits))
        return cls.from_dict(label_hier_info)

    def save(self, path_to_json: Path):
        with open(path_to_json, 'w') as f:
            json.dump({'counts_of_bits': self.counts_of_bits, 'mask_names': self.mask_names}, f)

    def get_level_name(self, label_or_code: Union[int, str]) -> str:
        """Returns the name of the level that the `label` as specified by `label_or_code` belongs to.

        :param label_or_code: either the integer representation of the label or its textual code.
        :type label_or_code: int or str
        :return: name of the level the input label belongs to
        :rtype: str
        """
        if type(label_or_code) == str:
            label = self.label(label_or_code)
        else:
            label = label_or_code
        return self.mask_names[self.get_level(label)]
        #for level in range(len(self.masks) - 1, -1, -1):
        #    if label & self.masks[level]:
        #        return self.mask_names[level]

    def get_level(self, label: int) -> int:
        """Returns the level the label `label` belongs to in this hierarchy."""
        if label == 0:
            return 0
        if label < 0:
            return -1
        for level in range(len(self.masks) - 1, -1, -1):
            if label & self.masks[level]:
                return level

    def get_mask(self, label: int) -> int:
        """Returns the mask of the level that the `label` belongs to."""
        return self.masks[self.get_level(label)]

    def label_mask(self, label: int) -> int:
        """
        Returns the union of self.masks[0],...,self.masks[self.get_level(label)]
        """
        level = self.get_level(label)
        mask = 0
        for i in range(level+1):
            mask = mask | self.masks[i]
        return mask

    def get_parent(self, label_or_code: Union[int, str]) -> int:
        """Returns the parent label of the label represented by `label_or_code`."""
        if type(label_or_code) == str:
            label = self.label(label_or_code)
        else:
            label = label_or_code
        # #mask = self.get_mask(label)
        # #index = self.masks.index(mask)
        # return self.get_level(label) - 1  # For top level mask (index 0), -1 is correct, meaning it does not have a parent
        return self.parents[label]

    def get_ancestors(self, label: int) -> List[int]:
        """Returns the list of ancestor labels for `label`."""
        parents = []
        curr_label = label
        while (parent := self.parents[curr_label]) > 0:
            parents.append(parent)
            curr_label = parent
        # parents.append(-1)
        return parents

    def code(self, label: int) -> str:
        """Returns the textual code representation of `label`."""
        str_code = str((self.masks[0] & label) >> self.shifts[0]) + self.sep
        for i in range(1, len(self.masks)):
            str_code += str((self.masks[i] & label) >> self.shifts[i]) + self.sep
        return str_code[:-1]

    def label(self, code: str) -> int:
        """Returns the `label` that is represented by `code`."""
        labels = code.split(self.sep)
        bits = [int(label) << shift for label, shift in zip(labels, self.shifts)]
        return functools.reduce(operator.or_, bits)

    def level_mask(self, level: int) -> int:
        """
        Returns the union of self.masks[0],...,self.masks[level].
        :param level: Number indicating the level a level mask should be returned for.
        :type level: int
        :return: The mask for the level.
        :rtype: int
        """

        mask = 0
        for l in range(level + 1):
            mask |= self.masks[l]
        return mask

    def get_label_mask_up_to(self, level: int, label: int) -> int:
        """Returns the bitwise AND of `level_mask(level) and `label`."""
        mask = 0
        for l in range(level + 1):
            mask |= self.masks[l]
        return mask & label

    def set_labels(self, labels: List[int]):
        self.labels = labels.copy()

        self.nodes.clear()
        for label in self.labels:
            node = Node()
            node.label = label
            node.code = self.code(label)
            self.nodes[label] = node
            self._level_groups[self.get_level(label)].add(label)

        self.compute_children()

    def compute_children(self):
        """Establishes descendant relations between label nodes."""
        self._create_root_node()
        if -1 in self.labels:
            self.labels.remove(-1)
        #first_idx = 1 if self.labels[0] == 0 else 0
        parent_label = -1
        label = parent_label
        depth = -1  # on depth 1 we look for children of `label` which is on level 0
        stack = [parent_label]

        for curr_label in self.labels:
            curr_depth = self.get_level(curr_label)
            self.children.setdefault(curr_label, [])
            if curr_depth == depth:
                self.nodes[parent_label].children.append(self.nodes[curr_label])
                self.nodes[curr_label].parent = self.nodes[parent_label]

                self.children.setdefault(parent_label, list()).append(curr_label)
                self.parents[curr_label] = parent_label
                label = curr_label
            elif curr_depth > depth:
                parent_label = label
                stack.append(parent_label)

                self.nodes[parent_label].children.append(self.nodes[curr_label])
                self.nodes[curr_label].parent = self.nodes[parent_label]

                self.children.setdefault(parent_label, list()).append(curr_label)
                self.parents[curr_label] = parent_label
                label = curr_label
                depth = curr_depth
            elif curr_depth < depth:
                for _ in range(depth - curr_depth):
                    stack.pop()
                parent_label = stack[-1]

                self.nodes[parent_label].children.append(self.nodes[curr_label])
                self.nodes[curr_label].parent = self.nodes[parent_label]

                self.children.setdefault(parent_label, list()).append(curr_label)
                self.parents[curr_label] = parent_label
                label = curr_label
                depth = curr_depth

    def _create_root_node(self):
        """Creates a root node. This label node is not used by the user and should not appear anywhere visible."""
        if -1 in self.nodes:
            return
        root = Node()
        root.label = -1
        root.code = '-1:0:0:0'  # whatever, this node won't be ever used for anything useful, just to have a proper rooted tree
        root.name = 'invalid'
        root.children = []
        root.parent = None

        self.nodes[-1] = root

        self.children[-1] = []
        self.parents[-1] = -1

    def is_descendant_of(self, desc: int, ance: int) -> bool:
        """Checks whether the label `desc` is actually a descendant of the label `ance`."""
        ance_mask = self.label_mask(ance)
        return (desc & ance_mask) == ance

    def is_ancestor_of(self, ance: int, label: int) -> bool:
        """Checks whether the label `ance` is actually the ancestor of the label `label`."""
        return self.is_descendant_of(label, ance)

    def add_label(self, label: int, name: str, color: Tuple[int, int, int] = (255, 255, 255)):
        """Adds a new label to the hierarchy."""
        # TODO check that `label` is not present already
        parent_label = self.get_parent(label)
        parent = None if parent_label == -1 else self.nodes[parent_label]

        self.children[label] = []
        self.parents[label] = parent_label

        label_node = Node()
        label_node.label = label
        label_node.parent = parent
        label_node.name = name
        label_node.code = self.code(label)
        label_node.children = []
        label_node.color = color

        if parent is not None:
            self.children[parent_label].append(label)
            parent.children.append(label_node)

        self.nodes[label] = label_node

        self.labels.append(label)
        self.labels.sort()

        self.colormap[label] = color

    def add_child_label(self, parent: int, name: str, color: Tuple[int, int, int]) -> Node:
        """Adds a new child label to the label `parent`."""
        last_child = max(self.children[parent], default=parent)
        if last_child != parent:
            level = self.get_level(last_child)
        else:
            level = self.get_level(parent) + 1
        mask = self.masks[level]
        child_num = last_child
        one = 1 << self.shifts[level]
        child_num += one
        label = child_num

        parent_node: Node = self.nodes[parent]

        self.children[label] = []
        self.parents[label] = parent

        label_node = Node()
        label_node.label = label
        label_node.parent = parent_node
        label_node.name = name
        label_node.code = self.code(label)
        label_node.children = []
        label_node.color = color

        if parent_node is not None:
            self.children[parent].append(label)
            parent_node.children.append(label_node)

        self.nodes[label] = label_node

        self.labels.append(label)
        self.labels.sort()

        self.colormap[label] = color

        return label_node

    @property
    def level_groups(self) -> List[Set[int]]:
        """
        Returns sets of labels grouped by level, so `level_groups[1]` is a set of labels that are on level 1 in the hierarchy.
        """
        return self._level_groups

    def group_by_level(self, labels: Union[List[int], Set[int]]) -> Dict[int, Set[int]]:
        """
        Groups the `labels` based on their level in the hierarchy.
        """
        groups: Dict[int, Set[int]] = {}
        for label in labels:
            groups.setdefault(self.get_level(label), set()).add(label)
        return groups

    def get_available_label(self, parent: int) -> int:
        """Returns the next available child label for `parent`."""
        last_child = max(self.children[parent], default=0)
        mask = self.get_mask(last_child)
        child_num = last_child & mask
        one = 1 << self.shifts[self.get_level(last_child)]
        child_num += one

        return parent | child_num

    @classmethod
    def _bit_count(cls, mask: int) -> int:
        """Returns the number of `1-bits` in `mask`."""
        bit = mask & 1
        while not bit:
            mask = mask >> 1
            bit = mask & 1
        return int(math.log2(mask + 1))

    @classmethod
    def from_dict(cls, label_hier_info: Dict[str, Any]) -> 'LabelHierarchy':
        counts_of_bits = label_hier_info['counts_of_bits']
        mask_names = label_hier_info['mask_names']
        lab_hier = cls.designate_bits(counts_of_bits, mask_names=mask_names, n_bits=sum(counts_of_bits))
        for label, label_dict in label_hier_info['labels'].items():
            node = Node()
            node.label = int(label)
            node.code = label_dict['code']
            node.name = label_dict['name']
            color = label_dict['color']
            node.color = (int(color['red']), int(color['green']), int(color['blue']))
            lab_hier.colormap[node.label] = node.color
            lab_hier.nodes[node.label] = node
            lab_hier.labels.append(node.label)
        lab_hier.labels.sort()
        lab_hier.compute_children()
        lab_hier.name = label_hier_info['name']
        if (mask_label := label_hier_info['constraint_mask_label']) is not None:
            lab_hier.mask_label = lab_hier.nodes[mask_label]
        return lab_hier

    def to_dict(self) -> Dict[str, Any]:
        json_dict = {
            'name': self.name,
            'counts_of_bits': self.counts_of_bits,
            'mask_names': self.mask_names,
            'constraint_mask_label': None if self.mask_label is None else self.mask_label.label,
            'labels': {
                label: node.to_dict() for label, node in self.nodes.items()
            }
        }
        return json_dict