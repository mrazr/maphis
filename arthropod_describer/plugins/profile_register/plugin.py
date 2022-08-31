from typing import Optional

from arthropod_describer.common.common import Info
from arthropod_describer.common.plugin import Plugin


class ContourRegisterPlugin(Plugin):
    """
    NAME: Contour register
    DESCRIPTION: Contour register plugin
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)
