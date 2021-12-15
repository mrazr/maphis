import abc
import enum
import typing

import numpy as np


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
                             #'invert': ToolUserParam('invert', ParamType.BOOL, False)}
        self._current_img = None
        radius = self._user_params['radius'].value
        self._brush_mask = 255 * np.ones((radius, radius), np.uint8)
        self._brush_center = np.array([radius // 2, radius // 2])
        self._brush_coords = np.argwhere(self._brush_mask > 0) - self._brush_center

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def cursor_image(self) -> np.ndarray:
        radius = self._user_params['radius'].value
        self._brush_mask = 255 * np.ones((radius, radius), np.uint8)
        self._brush_center = np.array([radius // 2, radius // 2])
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
            #print(f'{"checked" if value else "unchecked"} bool param {param_name}')
        self._user_params[param_name].value = value
        return value

    def left_press(self, pos: typing.Tuple[int, int], img: np.ndarray, label: int):
        self._current_img = img
        coords = self._brush_coords + np.array(pos)
        img[coords[:, 0], coords[:, 1]] = label
