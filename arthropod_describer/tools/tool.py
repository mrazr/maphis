import abc
import enum
import typing

import numpy as np
import skimage.morphology as M


class ParamType(enum.IntEnum):
    INT = 0,
    STR = 1,
    BOOL = 2,


class ToolUserParam:
    def __init__(self, name: str, param_type: ParamType, default_value):
        self.name = name
        self.param_type = param_type
        self.default_value = default_value
        self.value = self.default_value


class Tool(abc.ABC):
    @abc.abstractmethod
    def __init__(self):
        self.tool_id = -1

    def set_id(self, tool_id: int):
        self.tool_id = tool_id

    @property
    @abc.abstractmethod
    def tool_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def cursor_image(self) -> np.ndarray:
        pass

    #@property
    #@abc.abstractmethod
    #def icon(self) -> np.ndarray:
    #    pass

    @property
    @abc.abstractmethod
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        pass

    @abc.abstractmethod
    def set_user_param(self, param_name: str, value: typing.Any):
        pass

    @abc.abstractmethod
    def left_press(self, pos: typing.Tuple[int, int], img: np.ndarray, label: int):
        pass

    @property
    @abc.abstractmethod
    def active(self) -> bool:
        pass

    def left_release(self, pos: typing.Tuple[int, int], label: int):
        pass

    def right_press(self, pos: typing.Tuple[int, int], img: np.ndarray, label: int):
        pass

    def right_release(self, pos: typing.Tuple[int, int], label: int):
        pass

    def middle_click(self, pos: typing.Tuple[int, int], label: int):
        pass

    def mouse_move(self, pos: typing.Tuple[int, int], label: int):
        pass


class Brush(Tool):
    def __init__(self):
        Tool.__init__(self)
        self._tool_name = "Brush"
        self._user_params = {'radius': ToolUserParam('radius', ParamType.INT, 9)}
        self._current_img = None
        radius = self._user_params['radius'].value
        self._brush_mask = 255 * M.disk(radius)
        self._brush_center = np.array([radius, radius])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center
        self.modified_coords: typing.List[np.ndarray] = []
        self._active = False

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cursor_image(self) -> np.ndarray:
        radius = self._user_params['radius'].value
        self._brush_mask = 255 * M.disk(radius)
        self._brush_center = np.array([radius, radius])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center
        return self._brush_mask

    @property
    def user_params(self) -> typing.Dict[str, ToolUserParam]:
        return self._user_params

    def set_user_param(self, param_name: str, value: typing.Any) -> typing.Any:
        if param_name not in self._user_params.keys():
            return None
        param: ToolUserParam = self._user_params[param_name]
        if param.param_type == ParamType.INT:
            if value % 2 == 0:
                value += 1
            self._user_params[param_name].value = value
        elif param.param_type == ParamType.BOOL:
            pass
        self._user_params[param_name].value = value
        return value

    def left_press(self, pos: typing.Tuple[int, int], img: np.ndarray, label: int) -> typing.List[np.ndarray]:
        self._active = True
        self.modified_coords.clear()
        self._current_img = img
        return self.mouse_move(pos, label)

    def mouse_move(self, pos: typing.Tuple[int, int], label: int) -> typing.List[np.ndarray]:
        if not self.active:
            return []
        coords = list(self._brush_coords + np.array(pos))
        self.modified_coords.extend(coords)
        return coords

    def left_release(self, pos: typing.Tuple[int, int], label: int) -> typing.List[np.ndarray]:
        self._active = False
        return self.modified_coords

    @property
    def active(self) -> bool:
        return self._active
