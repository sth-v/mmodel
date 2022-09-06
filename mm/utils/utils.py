#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

from mm.baseitems import Item


class ReplaceMapping:
    replacements = {
        "-": "_",
        " ": "__",
        ".": "___"
    }

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


class DotView(Item, ReplaceMapping):

    def __init__(self, dct={}, **kwargs):
        super().__init__(**kwargs)
        kwargs |= dct
        self.dct = kwargs
        DotView.do_traverse(self, kwargs)

    @classmethod
    def do_traverse(cls, obj, dct):
        for k, v in dct.items():

            if isinstance(v, dict):
                new_item = Item()

                obj(**{cls.replace(k): new_item})

                cls.do_traverse(new_item, v)
            else:
                obj(**{cls.replace(k): v})
