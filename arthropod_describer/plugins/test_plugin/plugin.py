from typing import Optional, List

from arthropod_describer.common.plugin import Plugin
from arthropod_describer.common.common import Info
from arthropod_describer.common.tool import Tool


class TestPlugin(Plugin):
    """
    NAME: Test
    DESCRIPTION: This is a test plugin for the arthropod describer tool
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)
