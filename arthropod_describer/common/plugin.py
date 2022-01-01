import abc
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Optional, Set, List, Any, Union, Literal
import os
import inspect

from arthropod_describer.common.label_change import CommandEntry
from arthropod_describer.common.photo import LabelType, Photo
from arthropod_describer.common.tool import Tool
from arthropod_describer.common.user_params import ToolUserParam


@dataclass
class Info:
    name: str = ''
    description: str = ''

    @classmethod
    def load_from_doc_str(cls, obj: Union['Plugin', 'RegionComputation', 'RegionProperty', 'PropertyComputation']) \
            -> 'Info':

        doc_str = obj.__doc__
        lines = [line for line in doc_str.splitlines() if len(line) > 0]

        name = lines[0].split(':')[1].strip()
        desc = lines[1].split(':')[1].strip()

        return Info(name, desc)


class RegionComputation:
    def __init__(self, info: Optional[Info] = None):
        self.info = Info.load_from_doc_str(self) if info is None else info

    @property
    @abc.abstractmethod
    def requires(self) -> Set[LabelType]:
        pass

    @property
    @abc.abstractmethod
    def computes(self) -> Set[LabelType]:
        pass

    @abc.abstractmethod
    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None) -> Set[LabelType]:
        pass

    @property
    def user_params(self) -> List[ToolUserParam]:
        return []


class RegionProperty:
    def __init__(self, info: Optional[Info] = None):
        self.info = Info.load_from_doc_str(self) if info is None else info
        self.label: int = -1
        self.value: Any = None


class PropertyComputation:
    def __init__(self, info: Optional[Info] = None):
        self.info = Info.load_from_doc_str(self) if info is None else info

    @abc.abstractmethod
    def __call__(self, photo: Photo, labels: List[int]) -> RegionProperty:
        pass


class Plugin:
    def __init__(self, info: Optional[Info] = None):
        self._plugin_id = -1
        self.info = Info.load_from_doc_str(self) if info is None else info

    @property
    def plugin_id(self) -> int:
        return self._plugin_id

    @property
    def region_computations(self) -> Optional[List[RegionComputation]]:
        return None

    @property
    def property_computations(self) -> Optional[List[PropertyComputation]]:
        return None

    @property
    def tools(self) -> Optional[List[Tool]]:
        return None

    def _load_info_from_doc(self) -> Info:
        doc_str = self.__doc__
        lines = [line for line in doc_str.splitlines() if len(line) > 0]

        name = lines[0].split(':')[1].strip()
        desc = lines[1].split(':')[1].strip()

        return Info(name, desc)
