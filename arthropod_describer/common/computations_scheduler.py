import dataclasses
import typing

import numpy as np

from arthropod_describer.common.label_image import RegionProperty
from arthropod_describer.common.photo import Photo
from arthropod_describer.common.plugin import PropertyComputation
from arthropod_describer.common.regions_cache import RegionsCache


class ComputationsScheduler:
    def __init__(self, props_by_regions: typing.Dict[int, typing.List[PropertyComputation]]):
        self.props_by_regions: typing.Dict[int, typing.List[PropertyComputation]] = props_by_regions
        self.regions_labels: typing.Set[int] = set(props_by_regions.keys())

    def run(self, photo: Photo, label_name: str) -> typing.List[RegionProperty]:
        regions_cache = RegionsCache(self.regions_labels, photo, label_name)

        props: typing.List[RegionProperty] = []

        for label, prop_comps in self.props_by_regions.items():
            for prop_comp in prop_comps:
                pass