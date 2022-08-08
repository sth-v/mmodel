__all__ = ['Item', 'RequiredFildItem', 'HashVersion', 'Version']

import base64
import copy
import inspect
import json
from abc import abstractmethod
from collections import defaultdict
from typing import Any, Optional

import compas

from collections.abc import Callable
import numpy as np

from vcs import Version, HashVersion

from mm.exceptions import MModelException


class Versioned(object):
    def __init__(self):
        self.version = HashVersion()

    def _version(self):
        self.version = HashVersion()

    def __eq__(self, other):
        return hex(self.version) == hex(other.version)


class Identifiable(Versioned):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._uid = None

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, val):
        self._uid = hex(val)


class Item(Identifiable):
    """
    Base Abstract class
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.uid = id(self)
        self.__call__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.__dict__.update(kwargs)
        self._version()

    def __hash__(self):
        ...


class ArgsItem(Item):
    def __init__(self, *args, **kwargs):
        self.initargs = locals()
        self._insp = inspect.getfullargspec(self.__class__.__init__)
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(ArgsItem, self).__call__(*args, **kwargs)
        self.newargs = locals()

    def __getinitargs__(self):
        return self.initargs

    def __getnewargs__(self):
        return self.newargs


class HistoryArgItem(ArgsItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open(f"tmp/{self.uid}", "wb") as fp:
            fp.write(base64.b64encode((json.dumps(self.__dict__['initargs']['kwargs']) + '\n').encode()))

    def __call__(self, *args, **kwargs):
        super(HistoryArgItem, self).__call__(*args, **kwargs)
        with open(f"tmp/{self.uid}", "ab") as fp:
            fp.write(base64.b64encode((json.dumps(self.__dict__['newargs']['kwargs']) + '\n').encode()))

    @classmethod
    def read_log(cls, path):
        with open(f"{path}", "rb") as fp:
            data = eval(base64.b64decode(fp.read()))
            print(data)
        return cls(**data)



class RequiredFildItem(Item):
    """
    Check name

    MModelException: The class name does not match the descriptor signature!
    classname: B, input name: A

    """

    fields: Optional[Any]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self._dfields = defaultdict(**self.fields)
        kwargs |= dict(zip(self._dfields.keys(), args[:len(self._dfields.keys())]))

        super().__call__(**kwargs)
        for field in self.__class__.fields.keys():
            if field not in self.__dict__.keys():
                self.__field_missing__(field, kwargs)

    @classmethod
    def __field_missing__(cls, key, kws):
        if key in cls.fields.keys():
            raise MModelException(
                f"Miss required field: {key} in {cls.__name__}!")


class DictableElement(RequiredFildItem):
    del_keys = ['args', 'kw', 'aliases']

    def __init__(self, *args, **kwargs):
        super(RequiredFildItem, self).__init__(*args, **kwargs)

    def __str__(self):
        return compas.json_dumps(self.encode(), pretty=True)

    def __repr__(self):
        _d = self.encode()
        reprdict = {'uid': self._uid}
        for r in self.fields.keys():
            reprdict[r] = _d[r]

        return compas.json_dumps(reprdict, pretty=True)

    def __hash__(self):
        st = ""
        for k, v in self.encode().items():

            if not ((k in self.del_keys) or (k == "metadata")):
                try:
                    iter(v)

                    if not isinstance(v, str):
                        print(f'hash iter {v}')
                        st.join([hex(int(n)) for n in np.asarray(np.ndarray(v) * 100, dtype=int)])
                    else:
                        continue
                except:
                    print(f'hash not iter {v}')
                    if isinstance(v, int) or isinstance(v, float):
                        st += hex(int(v * 100))
                    else:
                        continue

        return st

    def encode(self):
        st: dict = {'metadata': {}}

        for k, v in self.__dict__.items():
            k = k[1:] if k[0] == "_" else k
            if k in self.del_keys:
                pass
            else:
                try:

                    vdct = v.encode()
                except:

                    vdct = v

                if k in self.fields.keys():

                    st |= {k: vdct}
                else:
                    st['metadata'] |= {k: vdct}

        return st

    def __call__(self, *args, **kwargs):
        super(DictableElement, self).__call__(*args, **kwargs)
        self.__dict__["hash"] = self.__hash__()


"""

class Item(BaseFieldsInterface):
    required_fields = {'name'}

    def __init__(self, *args, **kwargs):

        key = list(self.required_fields)[0]
        if key not in kwargs.keys():
            kwargs['name'] = self.__class__.__name__

        elif not (kwargs[key] == self.__class__.__name__):

            raise MModelException(
                f"The class name does not match the descriptor signature!"
                f"\nclassname: {self.__class__.__name__}, input name: {key}")
        else:
            pass
        super().__init__(*args, **kwargs)


class VNElement(Item):
    
    """
