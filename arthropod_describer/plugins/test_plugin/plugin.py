from typing import Optional, List
import sys

from arthropod_describer.common.plugin import Plugin, PropertyComputation, RegionComputation, Info
from arthropod_describer.common.tool import Tool
from arthropod_describer.plugins.test_plugin.regions.body import BodyComp
from arthropod_describer.plugins.test_plugin.regions.eraser import RegionEraser
from arthropod_describer.plugins.test_plugin.regions.legs import LegsRegion


class TestPlugin(Plugin):
    """
    NAME: Test
    DESCRIPTION: This is a test plugin for the arthropod describer tool
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)
        self._region_computations = [LegsRegion(), BodyComp(), RegionEraser()]

    @property
    def plugin_id(self) -> int:
        return super().plugin_id

    @property
    def region_computations(self) -> Optional[List[RegionComputation]]:
        return self._region_computations

    @property
    def property_computations(self) -> Optional[List[PropertyComputation]]:
        return super().property_computations

    @property
    def tools(self) -> Optional[List[Tool]]:
        return super().tools
