__all__ = ['Base', 'Versioned', 'Identifiable', 'Item', 'ArgsItem',
           'DataItem', 'FieldItem', 'DictableItem', 'JsItem']

import inspect
import itertools
import json
from collections import defaultdict

import base64
from typing import Iterable

import compas
import compas.geometry
from collections.abc import Callable
import numpy as np

from vcs.utils import HashVersion

from mm.exceptions import MModelException


class Base(Callable):
    """
    Base Abstract class
    """

    def __init__(self, *args, **kwargs):
        self.__call__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__()

        self.__dict__.update(kwargs)
        self._dtype = self.__class__.__name__


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
        super().__init__(*args, **kwargs)

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


class Item(Identifiable):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


class ArgsItem(Item):
    def __init__(self, *args, **kwargs):
        self.init_args = locals()
        self.arg_spec = inspect.getfullargspec(self.__class__.__init__)
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(ArgsItem, self).__call__(*args, **kwargs)
        self.new_args = locals()

    def __getinitargs__(self):
        return self.init_args

    def __getnewargs__(self):
        return self.new_args


class HistoryArgItem(ArgsItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with open(f"tmp/{self.uid}", "wb") as fp:
            fp.write(base64.b64encode((json.dumps(self.__dict__['init_args']['kwargs']) + '\n').encode()))

    def __call__(self, *args, **kwargs):
        super(HistoryArgItem, self).__call__(*args, **kwargs)
        with open(f"tmp/{self.uid}", "ab") as fp:
            fp.write(base64.b64encode((json.dumps(self.__dict__['new_args']['kwargs']) + '\n').encode()))

    @classmethod
    def read_log(cls, path):
        with open(f"{path}", "rb") as fp:
            data = eval(base64.b64decode(fp.read()))
            print(data)
        return cls(**data)


class member_table(dict):
    def __init__(self):
        self.member_names = []

    def __setitem__(self, key, value):
        # if the key is not already defined, add to the
        # list of keys.
        if key not in self:
            self.member_names.append(key)

        # Call superclass
        dict.__setitem__(self, key, value)


class DataItem(Item):
    """
    Check name

    MModelException: The class name does not match the descriptor signature!
    classname: B, input name: A

    """
    _exclude = {"exclude", "custom_fields", "default_fields"}
    dtype: str


    @property
    def metadata(self):
        return dict(metadata=dict(self.custom_fields))

    @property
    def custom_fields(self):
        _fields = []

        for k in self.__dict__.keys():
            if not (k in self.exclude) and (not hasattr(self.__class__, k)):
                _fields.append((k, getattr(self, k)))
        return _fields

    @property
    def default_fields(self):
        _fields = []
        for k in self.__dict__.keys():
            if not (k in self.exclude) and hasattr(self.__class__, k):
                _fields.append((k, getattr(self, k)))
        _fields.append(("metadata", dict()))
        return _fields

    @property
    def mro_items(self):
        l = []
        for base in self.__class__.__bases__:
            if issubclass(base, DataItem):
                l.append(base)
        return l

    @property
    def exclude(self):
        for base in self.mro_items:
            self._exclude.update(base._exclude)
        return self._exclude

    @exclude.setter
    def exclude(self, v):
        self._exclude.add(v)

class FieldItem(Item):
    fields = []
    exclude = ("fields", "base_fields", "custom_fields", "del_keys", "__array__", "uid")

    def __init__(self, *args, **kwargs):

        self.custom_fields = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.custom_fields = []
        self.base_fields = []
        super().__call__(*args, **kwargs)

        self.check_fields()

    def check_fields(self):
        self.__class__.fields = []
        self.custom_fields = []
        for k in self.__dict__.keys():
            if k in self.exclude:
                continue
            else:
                if hasattr(self.__class__, k):
                    self.__class__.fields.append(k)
                    self.base_fields.append(k)
                else:

                    self.custom_fields.append(k)


class ItemFormatter:
    _dtype = "ItemFormatter"
    format_spec = {"_dtype"}

    def __format__(self, format_spec: set = None):

        s = ''

        if format_spec is None:
            format_spec = self.__class__.format_spec

        elif format_spec is not None:
            format_spec.update(self.__class__.format_spec)
        else:
            pass
        for k in format_spec:
            s += f"{k}={getattr(self, k)} ,"

        return "{}({})".format(self.__class__.__name__, s[:-1])

    def __str__(self):
        """
        Item Format str
        """

        return self.__format__()

    def __repr__(self):
        return f"<{self.__format__()} at {hex(id(self))}>"


class DictableItem(FieldItem, ItemFormatter):
    fields = []
    exclude = ('args', 'kw', 'aliases', "fields", "uid", "__array__")
    format_spec = {"uid", "version"}

    def __format__(self, format_spec=None):

        return super(DictableItem, self).__format__(format_spec=format_spec)

    def __str__(self):

        return self.__format__(format_spec=set(self.__class__.fields))

    def __repr__(self):

        return f"<{self.__format__(format_spec=set(self.__class__.fields))} at {self.uid}>"

    def __hash__(self):
        st = ""
        for k, v in self.to_dict().items():

            if not ((k in self.exclude) or (k == "metadata")):
                try:
                    iter(v)

                    if not isinstance(v, str):
                        #print(f'hash iter {v}')
                        st.join([hex(int(n)) for n in np.asarray(np.ndarray(v) * 100, _dtype=int)])
                    else:
                        continue
                except:
                    #print(f'hash not iter {v}')
                    if isinstance(v, int) or isinstance(v, float):
                        st += hex(int(v * 100))
                    else:
                        continue

        return st

    def to_dict(self):
        st: dict = {'metadata': {}}

        for k, v in self.__dict__.items():
            k = k[1:] if k[0] == "_" else k
            if k in self.exclude:
                pass
            else:

                try:
                    iter(v)
                    if isinstance(list(itertools.chain(v))[0], DictableItem):
                        dct = list(map(lambda x: x.to_dict(), v))
                    else:
                        dct = v
                except:
                    if isinstance(v, DictableItem):
                        dct = v.to_dict()
                    else:

                        dct = v

                if k in self.__class__.fields:

                    st |= {k: dct}
                else:
                    st['metadata'] |= {k: dct}

        return st

    def encode(self, **kwargs):
        return compas.json_dumps(self.to_dict(), **kwargs)

    def to_data(self):
        data = self.to_dict()
        data |= {"guid": self.uuid}
        return data

    def to_json(self):
        return self.encode()

    def b64encode(self, **kwargs):
        return base64.b64encode(self.encode(**kwargs).encode())

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.__dict__["hash"] = self.__hash__()

    def to_compas(self):
        ...


class JsItem(DictableItem):
    schema_js = dict()
