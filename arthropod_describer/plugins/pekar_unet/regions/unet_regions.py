import logging
from datetime import datetime

import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Set, Optional, List

import numpy as np
from skimage import io

from arthropod_describer.common.photo import Photo, LabelImg
from arthropod_describer.common.plugin import RegionComputation


class UNetRegions(RegionComputation):
    """
    NAME: Body parts segmenter
    DESCRIPTION: Labels the parts of an insect.
    """

    def __init__(self):
        RegionComputation.__init__(self, None)
        self.bin_path = Path(__file__).parent / 'pekar_unet' / 'bin'
        self.unet_path = self.bin_path / 'UNetSegmentationPlugin.exe'
        self.leg_segment_path = self.bin_path / 'LegSegmentsPlugin.exe'
        self.std_reflection_path = self.bin_path / 'StandardDeviationReflectionsPlugin.exe'

    def __call__(self, photo: Photo, labels: Optional[Set[int]] = None, storage=None) -> List[LabelImg]:
        img_loc = photo.image_path

        with tempfile.TemporaryDirectory() as out_d:
            temp_out_d = Path(out_d)

            os.mkdir(temp_out_d / 'maskfolder')
            os.mkdir(temp_out_d / 'reflectionsfolder')

            out_mask = temp_out_d / 'maskfolder' / f'unapprovedmask-temp____{img_loc.name}'
            out_refl = temp_out_d / 'reflectionsfolder' / f'unapprovedreflections-temp____{img_loc.name}'
            out_reg = temp_out_d / 'regionsfolder'
            reg_img_path = out_reg / f'unapprovedregions____{img_loc.name}'
            reg_xml_path = out_reg / f'unapprovedregions____{img_loc.name}.xml'

            os.mkdir(out_reg)

            args = [
                str(self.unet_path),
                "r",
                str(img_loc),
                str(out_mask)
            ]
            print(f"Running plugin:\n{args}\n")
            logging.info(f"{datetime.now()} Running plugin:\n{args}\n")
            returncode = subprocess.run(args, cwd=str(self.bin_path.parent))

            # compute reflections binary image
            args = [
                str(self.std_reflection_path),
                "r",
                str(img_loc),
                str(out_mask),
                str(out_refl)

            ]
            print(f"Running plugin:\n{args}\n")
            logging.info(f"{datetime.now()} Running plugin:\n{args}\n")
            returncode = subprocess.run(args, cwd=str(self.bin_path.parent))

            # finally, divide legs into sections
            args = [
                str(self.leg_segment_path),
                "r",
                str(img_loc),
                str(out_mask),
                str(out_refl),
                str(reg_img_path),
                str(reg_xml_path)

            ]
            print(f"Running plugin:\n{args}\n")
            logging.info(f"{datetime.now()} Running plugin:\n{args}\n")
            returncode = subprocess.run(args, cwd=str(self.bin_path.parent))

            reg_img = io.imread(str(reg_img_path))

            root = ET.parse(out_reg / f'{reg_img_path.name}.xml')

            used_labels = [ident.text for ident in root.iter('identifier')]

            lab_hier = photo['Labels'].label_hierarchy
            mapping = {int(label): lab_hier.label(lab_hier.sep.join(list(label))) for label in used_labels}

            result_img = np.zeros_like(reg_img, dtype=np.uint32)
            for lab in mapping.keys():
                coords = np.nonzero(reg_img == lab)
                result_img[coords] = mapping[lab]
            io.imsave(str(img_loc.parent.parent / 'Labels' / f'{img_loc.name}.tif'), result_img, check_contrast=False)
            #io.imsave(str(img_loc.parent.parent / 'Labels' / f'viz_{img_loc.name}'), color.label2rgb(result_img))
            new_lab = photo['Labels'].clone()
            new_lab.label_image = result_img

            ref_img = io.imread(str(out_refl))
            ref_lab_hier = photo['Reflections'].label_hierarchy
            ref_lab_img = photo['Reflections']
            reflection_label = [lab for lab in ref_lab_hier.labels if lab > 0][0]

            ref_lab_img.label_image = np.where(ref_img > 0, reflection_label, 0).astype(np.uint32)

            return [new_lab, ref_lab_img]
