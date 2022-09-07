#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

from mm.baseitems import Item
import weakref


class ReplaceMapping:
    replacements = {
        "-": "_",
        " ": "__",
        ".": "___"
    }

    def __init__(self):
        super(ReplaceMapping, self).__init__()
        self.replacements = self.__class__.replacements

    @classmethod
    def replace(cls, string: str):
        for k, v in cls.replacements.items():
            if k in string:
                string = string.replace(k, v)
        return string

    @classmethod
    def replace_back(cls, string: str):
        for k, v in cls.replacements:
            if v in string:
                string = string.replace(v, k)
        return string


from typing import Mapping, MappingView



class DotView(Item, ReplaceMapping):
    """
    >>> class R2(ReplaceMapping):
    ...     replacements = {
    ...             "a": "AAAA",
    ...             "b": "NNN",
    ...             "c": "CCC"
    ...         }


    >>> class BV(DotView, R2):
    ...     ...


    >>> d = BV(**dict(a=6, b=dict(t=0, d=6)))

    >>> d.AAAA
    6
    """
    def __init__(self, dct=None, **kwargs):
        super().__init__(**kwargs)
        if dct is None:
            dct = dict()
        kwargs |= dct

        self.do_traverse(self, kwargs)



    @classmethod
    def do_traverse(cls, obj, dct):
        for k, v in dct.items():

            if isinstance(v, dict):
                new_item = cls()

                obj.__call__(**{cls.replace(k): new_item})

                cls.do_traverse(new_item, v)
            else:
                obj.__call__(**{cls.replace(k): v})


