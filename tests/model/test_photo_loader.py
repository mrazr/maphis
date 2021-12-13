import os
import unittest
import tempfile
import random
from pathlib import Path
import shutil

import numpy as np
import skimage.io as io

import arthropod_describer.model.photo_loader as ploader


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.tiff_files = [tempfile.mkstemp(suffix='.tiff', dir=self.folder)[1] for _ in range(4)]
        self.files = [file for file in self.tiff_files]
        self.files.extend([tempfile.mkstemp(suffix=random.choice(['.png', '.txt']), dir=self.folder)[1] for _ in range(4)])

    def tearDown(self) -> None:
        shutil.rmtree(self.folder)

    def test_restructure(self):
        ploader.restructure_folder(self.folder)
        image_folder = self.folder / 'images'
        self.assertTrue(image_folder.exists())

    def test_local_storage1(self):
        strg = ploader.MockStorage.load_from(self.folder)
        sorted_tiffs = list(sorted([Path(entry.path) for entry in os.scandir(self.folder / 'images')]))
        self.assertEqual(strg.image_paths, sorted_tiffs)

    def test_segments_masks_folder(self):
        strg = ploader.MockStorage.load_from(self.folder)
        self.assertTrue((self.folder / ploader.SEGMENTS_MASK_DIR).exists())

    def test_bugs_masks_folder(self):
        strg = ploader.MockStorage(self.folder)
        self.assertTrue((self.folder / ploader.BUG_MASK_DIR).exists())

    def test_reflection_masks_folder(self):
        strg = ploader.MockStorage.load_from(self.folder)
        self.assertTrue((self.folder / ploader.REFLECTION_MASK_DIR).exists())

    def test_image_names(self):
        strg = ploader.MockStorage.load_from(self.folder)
        sorted_tiffs = list(sorted([entry.name for entry in os.scandir(self.folder / 'images')]))
        self.assertEqual(strg.image_names, sorted_tiffs)

if __name__ == '__main__':
    unittest.main()
