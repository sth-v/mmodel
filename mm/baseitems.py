__all__ = ['Base', 'Versioned', 'Identifiable', 'Item', 'ArgsItem',
           'DefaultFildItem', 'FieldItem', 'DictableItem','JsItem']

import base64
import copy
import inspect
import itertools
import json
from abc import abstractmethod
from collections import defaultdict
from typing import Any, Optional
import base64
import compas

from collections.abc import Callable
import numpy as np

from vcs import Version, HashVersion

from mm.exceptions import MModelException


class Base(Callable):
    """
    Base Abstract class
    """

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.dtype = self.__class__.__name__

        self.__call__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(Base, self).__call__()
        self.__dict__.update(kwargs)


class Versioned(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _version(self):
        self.version = HashVersion().__hex__()

    def __eq__(self, other):
        return hex(self.version) == hex(other.version)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self._version()


import uuid


class Identifiable(Versioned):
    def __init__(self, *args, **kwargs):
        self._uuid = uuid.uuid4().hex
        super().__init__()

    @property
    def uid(self):
        return hex(id(self))

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, v):
        self._uuid = v

    def __hash__(self):
        ...

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


class Item(Identifiable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(self, *args, **kwargs)


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


class DefaultFildItem(Item):
    """
    Check name

    MModelException: The class name does not match the descriptor signature!
    classname: B, input name: A

    """

    fields = dict(
        uuid=''
    )

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


class FieldItem(DefaultFildItem):
    def __init__(self, *args, **kwargs):
        self.fields |= super().fields
        super().__init__(*args, **kwargs)


class DictableItem(FieldItem):
    fields = dict()
    del_keys = ['args', 'kw', 'aliases', "dfields", "uid", "__array__"]
    format_spec = "_uid", "version"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __format__(self, format_spec=None):
        s = ''

        if format_spec is None:
            for k in self.format_spec:
                s += f"{k}={self.__dict__[k]} ,"
        else:
            for k in format_spec:
                s += f"{k}={self.__dict__[k]} ,"
        return "{}({})".format(self.__class__.__name__, s[:-1])

    def __str__(self):
        return self.__format__()

    def __repr__(self):
        _d = self.to_dict()
        reprdict = {'uid': self._uid}
        for r in self.fields.keys():
            reprdict[r] = _d[r]

        return self.__str__() + f" object at {hex(id(self))}"

    def __hash__(self):
        st = ""
        for k, v in self.to_dict().items():

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

    def to_dict(self):
        st: dict = {'metadata': {}}

        for k, v in self.__dict__.items():
            k = k[1:] if k[0] == "_" else k
            if k in self.del_keys:
                pass
            else:

                try:
                    iter(v)
                    if isinstance(list(itertools.chain(v))[0], DictableItem):
                        vdct = list(map(lambda x: x.to_dict(), v))
                    else:
                        vdct = v
                except:
                    if isinstance(v, DictableItem):
                        vdct = v.to_dict()
                    else:

                        vdct = v

                if k in self.fields.keys():

                    st |= {k: vdct}
                else:
                    st['metadata'] |= {k: vdct}

        return st

    def encode(self, **kwargs):
        return compas.json_dumps(self.to_dict(), **kwargs)

    def to_json(self):
        return self.encode()

    def b64encode(self, **kwargs):
        return base64.b64encode(self.encode(**kwargs).encode())

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.__dict__["hash"] = self.__hash__()


class JsItem(DictableItem):
    schema_js = dict()


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
