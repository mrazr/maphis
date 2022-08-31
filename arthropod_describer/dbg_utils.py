import re
import shutil
import tempfile
import random
from pathlib import Path

from PySide2.QtGui import QImage

import arthropod_describer.common.local_storage as ploader


class MockStorage(ploader.LocalStorage):
    def __init__(self, folder: Path, image_regex: re.Pattern= ploader.TIF_REGEX):
        super().__init__(folder, image_regex)

    @classmethod
    def load_from(cls, folder: Path, image_regex: re.Pattern= ploader.TIF_REGEX) -> 'MockStorage':
        strg = MockStorage(folder, image_regex)
        strg._images = [QImage(256, 256, QImage.Format_Grayscale16) for _ in range(strg.image_count)]
        return strg

    @classmethod
    def create(cls) -> 'MockStorage':
        folder = Path(tempfile.mkdtemp())
        for _ in range(random.randint(4, 10)):
            tempfile.mkstemp(suffix='.tiff', dir=folder)
        return MockStorage.load_from(folder)

    def destroy(self):
        shutil.rmtree(self.location)
