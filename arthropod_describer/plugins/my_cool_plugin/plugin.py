from typing import Optional

from arthropod_describer.common.common import Info
from arthropod_describer.common.plugin import Plugin


class CoolPlugin(Plugin):
    """
    NAME: Cool
    DESCRIPTION: A very cool plugin.
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)
