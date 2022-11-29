from __future__ import annotations, absolute_import

__all__ = ['Base', 'Versioned', 'Identifiable', 'Item', 'GeometryItem', 'DictableItem',
           'DataviewInterface', 'Dataview', 'DataviewDescriptor', 'Metadata', 'ReprData', 'GeomConversionMap',
           'GeomDataItem']

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import base64
import gzip
import itertools
from abc import ABCMeta, abstractmethod
from collections import Callable, Generator
from typing import Any, Union

import numpy as np
import pydantic

import time

from versioning import Now

time.localtime(time.time())


class MultiDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __setitem__(self, k, v):

        try:
            l = dict.__getitem__(self, k)
            l.append(v)

        except:
            l = [v]

        dict.__setitem__(self, k, l)

    def __getitem__(self, __k):
        return dict.__getitem__(self, __k)


class BaseI:
    """
    Base Abstract class
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.__call__(**kwargs)

    def __call__(self, **kwargs):
        for k in kwargs:
            self.__setattr__(k, kwargs[k])

        return self


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
        return self


class Versioned(Base):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _version(self):
        self.version = Now()

    def __eq__(self, other):
        return hex(self.version) == hex(other.version)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self._version()


class VersionedI(BaseI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _version(self):
        self.version = Now()

    def __eq__(self, other):
        return hex(self.version) == hex(other.version)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self._version()


import uuid


class IdentifiableI(VersionedI):
    def __init__(self, *args, **kwargs):
        self._uuid = uuid.uuid4()
        super().__init__(*args, **kwargs)

    @property
    def uid(self):
        return hex(id(self))

    @property
    def uuid(self):
        return str(self._uuid)

    @uuid.setter
    def uuid(self, v):
        self._uuid = v

    def __hash__(self):
        ...


class Identifiable(Versioned):
    def __init__(self, *args, **kwargs):
        self._uuid = uuid.uuid4()
        super().__init__(*args, **kwargs)

    @property
    def uid(self):
        return hex(id(self))

    @property
    def uuid(self):
        return str(self._uuid)

    @uuid.setter
    def uuid(self, v):
        self._uuid = v

    def __hash__(self):
        ...


class DataviewInterface(metaclass=ABCMeta):
    include: list[str] = []
    replace: dict[str, str] = dict()

    def __init__(self, **kwargs):
        super().__init__()
        for name, constrain in kwargs.items():
            if constrain is not None: setattr(self, name, constrain)

    @abstractmethod
    def __get_dict__(self, instance, owner):
        pass


class Dataview(DataviewInterface):
    include: list[str] = []
    replace: dict[str, str] = dict()

    def __get_dict__(self, instance, owner):
        get_dict = {}
        for k in self.include:
            get_dict[self.replace[k] if k in self.replace.keys() else k] = getattr(instance, k)
        return get_dict


class DataviewDescriptor(Dataview):
    include: list[str] = []
    replace: dict[str, str] = dict()

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner) -> dict:
        return self.__get_dict__(instance, owner)


class Metadata(DataviewDescriptor):
    include = ["uid", "uuid", "dtype", "version"]
    replace = {
        "_dtype": "dtype"
    }


class ReprData(DataviewDescriptor):
    include = []
    replace = {
        "_dtype": "dtype"
    }

    def __init__(self, *include, **kwargs):
        super().__init__(**kwargs)
        list_include = list(include)
        list_include.extend(self.include)
        self.include = list_include

    def __set_name__(self, owner, name):
        self.name = name


class ItemFormatter:
    _dtype = "ItemFormatter"
    __representation: ReprData
    representation = ReprData()

    @property
    def dtype(self):
        return self._dtype

    @property
    def format_spec(self):
        return self.representation

    def __format__(self, format_spec: dict = None):
        if format_spec is not None:
            self.representation |= format_spec
        return "{}({})".format(self.__class__.__name__,
                               "".join([f"{k}={v}, " for k, v in self.representation.items()])[:-1][:-1])

    def __str__(self):
        """
        Item Format str
        """

        return self.__format__()

    def __repr__(self):
        return f"< {self.__format__()} at {hex(id(self))} >"


from json import JSONEncoder


class ItemEncoder(JSONEncoder):

    def default(self, o):
        try:
            if isinstance(o, pydantic.BaseModel):
                return o.dict()
            else:
                return o.to_dict()

        except:
            raise TypeError(f'Object of type {o.__class__.__name__} '
                            f'is not JSON serializable')


class Item(Identifiable, ItemFormatter):
    metadata = Metadata()
    representation = ReprData("version", "uid", "dtype")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


class GeomConversionMap(DataviewDescriptor):
    include = ["to_rhino", "to_compas"]
    replace = {

    }


class GeometryItem(Item):
    data = GeomConversionMap()

    def to_rhino(self) -> Union[list[float], Generator]:
        ...

    def to_compas(self) -> Union[list[float], Generator]:
        ...


class member_table(dict):
    def __init__(self):
        self.members = []
        self.methods = []

    def __setitem__(self, key, value: list[Any]):
        # if the key is not already defined, add to the
        # list of keys.

        ml = []
        for m, v in zip(self.members, value):
            setattr(m, key, v)

            ml.append(getattr(m, key))
            dict.__setitem__(self, m, {key: ml})

    def __getitem__(self, item):
        for m in self.members:
            yield getattr(m, item)

    def reload(self):
        del self.names_irerator
        self.names_irerator()

    def __setattr__(self, key, value):
        self[next(self.names_irerator)[self]].__setattr__(key, value)
        # print(key, value)

    def __getattr__(self, k):
        return self[next(self.names_irerator)[self]].__getattr__(k)


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


class DictableItem(FieldItem, ItemFormatter):
    fields = []

    representation = ReprData("uid", "version")
    exclude = ('args', 'kw', 'representation', 'aliases', "fields", "uid", "__array__", "_dtype")
    metadata = Metadata(include=["uuid", "dtype", "version", "custom_fields", "base_fields"])

    def __hash__(self):
        st = ""
        for k, v in self.to_dict().items():

            if not ((k in self.exclude) or (k == "metadata")):
                try:
                    iter(v)

                    if not isinstance(v, str):
                        # print(f'hash iter {v}')
                        st.join([hex(int(n)) for n in np.asarray(np.ndarray(v) * 100, _dtype=int)])
                    else:
                        continue
                except:
                    # print(f'hash not iter {v}')
                    if isinstance(v, int) or isinstance(v, float):
                        st += hex(int(v * 100))
                    else:
                        continue

        return st

    def to_dict(self):
        st: dict = {}

        for k, v in self.__dict__.items():
            k = k[1:] if k[0] == "_" else k
            if k in self.exclude:
                continue

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

                if k in self.base_fields:

                    st |= {k: dct}
                else:
                    pass
        st["metadata"] = self.metadata
        return st

    def encode(self, **kwargs):
        return ItemEncoder(**kwargs).encode(self)

    def to_data(self):
        data = self.to_dict()
        data |= {"guid": self.uuid}
        return data

    def to_json(self, **kwargs):
        return self.encode(**kwargs)

    def b64encode(self):
        return base64.b64encode(self.gzip_encode())

    def gzip_encode(self):
        return gzip.compress(self.encode().encode(), compresslevel=9)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    def to_compas(self):
        ...

    def to_occ(self):
        ...


class GeomDataItem(DictableItem, GeometryItem):
    exclude = ["to_rhino", "to_compas", "to_occ"]
    exclude.extend(DictableItem.exclude)

    def to_dict(self):
        dct = super().to_dict()
        dct["data"] = self.data["data"]
        return dct

# New Style Classes
# ----------------------------------------------------------------------------------------------------------------------
