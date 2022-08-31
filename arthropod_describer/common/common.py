import typing
from dataclasses import dataclass
from typing import Union

from arthropod_describer.common.utils import get_dict_from_doc_str


@dataclass
class Info:
    name: str = ''
    description: str = ''
    key: str = ''

    @classmethod
    def load_from_doc_str(cls, doc_str: str) \
            -> 'Info':
        if doc_str is None or doc_str == '':
            return Info()
        key_vals = get_dict_from_doc_str(doc_str)

        # name = key_vals['NAME']
        # desc = key_vals['DESCRIPTION']
        #
        # return Info(name, desc)

        return Info.load_from_dict(key_vals)

    @classmethod
    def load_from_dict(cls, doc_dict: typing.Dict[str, str]) -> 'Info':
        name = doc_dict['NAME']
        desc = doc_dict['DESCRIPTION']

        if 'KEY' in doc_dict:
            key = doc_dict['KEY']
        else:
            key = name

        return Info(name, desc, key=key)

