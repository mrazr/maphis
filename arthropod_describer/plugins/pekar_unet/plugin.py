from typing import Optional

from arthropod_describer.common.common import Info
from arthropod_describer.common.plugin import Plugin


class UNetPlugin(Plugin):
    """
    NAME: UNet Pekar
    DESCRIPTION: Labels semantic parts in an image with UNet.
    """
    def __init__(self, info: Optional[Info] = None):
        super().__init__(info)