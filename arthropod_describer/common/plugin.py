import abc
import logging
import typing
from typing import Optional, Set, List, Union

from arthropod_describer.common.common import Info
from arthropod_describer.common.label_image import RegionProperty, LabelImg
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.regions_cache import RegionsCache
from arthropod_describer.common.state import State
from arthropod_describer.common.tool import Tool
from arthropod_describer.common.units import Unit, BaseUnit, SIPrefix
from arthropod_describer.common.user_params import UserParam
from arthropod_describer.common.utils import get_dict_from_doc_str

logging.basicConfig(filename='arthropod_logger.log', level=logging.INFO, format="%(asctime)s %(filename)-30s %(levelname)-8s %(message)s")
logger = logging.getLogger("plugin.py")

class RegionComputation:
    def __init__(self, info: Optional[Info] = None):
        self.info = Info.load_from_doc_str(self.__doc__) if info is None else info
        self._region_restricted = "REGION_RESTRICTED" in self.__doc__
        self._user_params = UserParam.load_params_from_doc_str(self.__doc__)

    @abc.abstractmethod
    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None, storage=None) -> List[LabelImg]:
        pass

    @property
    def user_params(self) -> List[UserParam]:
        return list(self._user_params.values())

    @property
    def region_restricted(self) -> bool:
        return self._region_restricted


class PropertyComputation:
    def __init__(self, info: Optional[Info] = None):
        doc_dict = get_dict_from_doc_str(self.__doc__)
        self.info = Info.load_from_dict(doc_dict) if info is None else info
        self._user_params = UserParam.load_params_from_doc_str(self.__doc__)
        self._region_restricted = self.__doc__ is not None and "REGION_RESTRICTED" in self.__doc__
        self._group = doc_dict['GROUP'] if 'GROUP' in doc_dict else 'General'
        self._px_unit: Unit = Unit(BaseUnit.px, prefix=SIPrefix.none, dim=1)
        self._no_unit: Unit = Unit(BaseUnit.none, prefix=SIPrefix.none, dim=0)

    @abc.abstractmethod
    def __call__(self, photo: Photo, region_labels: typing.List[int], regions_cache: RegionsCache) -> typing.List[RegionProperty]:
        pass

    @property
    def user_params(self) -> List[UserParam]:
        return list(self._user_params.values())

    @property
    def region_restricted(self) -> bool:
        return self._region_restricted

    @property
    @abc.abstractmethod
    def computes(self) -> typing.Dict[str, Info]:
        pass

    @abc.abstractmethod
    def example(self, prop_name: str) -> RegionProperty:
        pass

    def target_worksheet(self, prop_name: str) -> str:
        return 'common'

    @property
    def group(self) -> str:
        return self._group


class GeneralAction:
    def __init__(self, info: Optional[Info] = None):
        doc_dict = get_dict_from_doc_str(self.__doc__)
        self.info = Info.load_from_dict(doc_dict) if info is None else info
        self._user_params = UserParam.load_params_from_doc_str(self.__doc__)
        self._group = doc_dict['GROUP'] if 'GROUP' in doc_dict else 'General'

    @abc.abstractmethod
    def __call__(self, state: State) -> None:
        pass

    @property
    def user_params(self) -> List[UserParam]:
        return list(self._user_params.values())

    @property
    def group(self) -> str:
        return self._group


class Plugin:
    def __init__(self, info: Optional[Info] = None):
        self._plugin_id = -1
        self.info = Info.load_from_doc_str(self.__doc__) if info is None else info
        self._region_computations: List[RegionComputation] = []
        self._property_computations: List[PropertyComputation] = []
        self._general_actions: List[GeneralAction] = []

    @property
    def plugin_id(self) -> int:
        return self._plugin_id

    @property
    def region_computations(self) -> Optional[List[RegionComputation]]:
        return self._region_computations

    @property
    def property_computations(self) -> Optional[List[PropertyComputation]]:
        return self._property_computations

    @property
    def general_actions(self) -> Optional[List[GeneralAction]]:
        return self._general_actions

    @property
    def tools(self) -> Optional[List[Tool]]:
        return None

    def _load_info_from_doc(self) -> Info:
        doc_str = self.__doc__
        lines = [line for line in doc_str.splitlines() if len(line) > 0]

        name = lines[0].split(':')[1].strip()
        desc = lines[1].split(':')[1].strip()

        return Info(name, desc)

    def register_computation(self, cls):
        try:
            obj: Union[RegionComputation, PropertyComputation, GeneralAction] = cls()
            obj.info.key = cls.__module__
            if issubclass(cls, RegionComputation):
                self._region_computations.append(obj)
            elif issubclass(cls, PropertyComputation):
                self._property_computations.append(obj)
            else:
                self._general_actions.append(obj)
        except AttributeError:
            logger.error(f'Could not register computation {cls}.')


def global_computation_key(global_property_key: str) -> str:
    return '.'.join(global_property_key.split('.')[:-1])


def local_property_key(global_property_key: str) -> str:
    return global_property_key.split('.')[-1]