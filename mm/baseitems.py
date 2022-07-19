__all__ = ['Item', 'BaseField', 'ArgsField', 'KeyField', 'RequiredFildItem', 'HashVersion', 'Version']

import copy
import inspect
import json
import warnings
from abc import ABC, ABCMeta
from collections import Mapping, MutableMapping, Awaitable, ChainMap, namedtuple
from typing import Any

import compas

from tools.colors import TemplateBase

import numpy as np

from vcs import Version, HashVersion

from mm.exceptions import MModelException


class NestedStructure(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._dict = kwargs

    def get_dict_data(self):

        return dict(self.items())

    def unzip(self):
        k, v = list(zip(self.items()))
        return k, v

    def sorted_by_lambda(self, var=lambda x: x[1]):
        l = list(self.items())
        l.sort(key=var)
        return l

    def __getitem__(self, keys):
        self.dct_data = self.get_dict_data()
        print(self.dct_data)

        return list(self.item_traversal(self.dct_data, keys))

    def item_traversal(self, vls, keys):
        print("root", keys, vls)
        if isinstance(keys, str):
            v = vls.pop(keys)
            yield keys, v
        else:

            for key in keys:
                yield list(self.item_traversal(vls, key))


from itertools import chain


class PathMapping(dict):
    def __init__(self, kwargs):
        super().__init__(**kwargs)
        self.dct = kwargs
        self.paths = dict()

        self.basepth = ""
        self.generate_path()

    def generate_path(self):

        # yield pth, v

        self.recurse(self.dct, self.basepth)

    def recurse(self, d, pth):

        for x, v in d.items():

            if not isinstance(v, dict):
                ptt = pth + f'_{x}'
                # pth += f'_{x}'

                setattr(self, ptt, v)
                print(list(d.values()).index(v), ptt)
                self.paths[ptt] = v


            else:
                path = f'_{x}'
                # pth += " -> " + x

                self.recurse(v, path)


json.dumps()


class Item(object):
    """
    Base Abstract class
    """

    def __init__(self, *args, **kwargs):
        self._uid = None
        self.uid = id(self)
        self.__call__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.__dict__ |= kwargs
        self._version()

    def _version(self):
        self.version = HashVersion().__hex__()

    def __hash__(self):
        ...

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, val):
        self._uid = hex(val)

class ArgsItem(Item):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        inspect.signature(self.__class__.__init__)
class ItemCollection:
    item = Item

    def __init__(self, item):
        self.next_item = item

    def __next__(self):
        ...

    def __iter__(self):
        return self

    def __call__(self, *args, **kwargs):
        self.__class__.item.__call__(*args, **kwargs)


class RequiredFildItem(Item):
    """
    Check name

    MModelException: The class name does not match the descriptor signature!
    classname: B, input name: A

    """

    required_fields: set = {}

    def __init__(self, *args, **kwargs):
        super(Item, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        for field in self.__class__.required_fields:
            if field not in self.__dict__.keys():
                self.__field_missing__(field, kwargs)

    @classmethod
    def __field_missing__(cls, key, kws):
        if key in cls.required_fields:
            raise MModelException(
                f"Miss required field: {key} in {cls.__name__}!")


class DictableElement(RequiredFildItem):
    del_keys = ['args', 'kw', 'aliases']

    def __init__(self, *args, **kwargs):
        super(RequiredFildItem, self).__init__(*args, **kwargs)

    def __str__(self):
        return compas.json_dumps(self.element_dict(), pretty=True)

    def __repr__(self):
        _d = self.element_dict()
        reprdict = {'uid': self._uid}
        for r in self.required_fields:
            reprdict[r] = _d[r]

        return compas.json_dumps(reprdict, pretty=True)

    def __hash__(self):
        st = ""
        for k, v in self.element_dict().items():

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

    def element_dict(self):
        st: dict = {'metadata': {}}

        for k, v in self.__dict__.items():
            k = k[1:] if k[0] == "_" else k
            if k in self.del_keys:
                pass
            else:
                try:

                    vdct = v.element_dict()
                except:

                    vdct = v

                if k in self.required_fields:

                    st |= {k: vdct}
                else:
                    st['metadata'] |= {k: vdct}

        return st

    def __call__(self, *args, **kwargs):
        super(DictableElement, self).__call__(*args, **kwargs)
        self.__dict__["hash"] = self.__hash__()


class FieldsMeta(type):
    root = DictableElement
    interfaces: dict = {}
    classname_prefix = "Mmodel"

    def __new__(mcs, classname, bases, attrs, interface=False, **kws):

        main_parent = bases[0]
        if interface:
            o = super().__new__(mcs, classname, bases, attrs, **kws)
            mcs.interfaces[classname] = o
            return o
        else:
            attrs['aliases'] = []
            attrs['main_parent'] = main_parent
            attrs['mro'] = lambda x: list(inspect.getmro(x.main_parent))
            if 'required_fields' in attrs.keys():
                arf = copy.deepcopy(attrs['required_fields'])

                attrs['required_fields'].update(main_parent.required_fields)

            else:
                arf = set()
                attrs['required_fields'] = main_parent.required_fields
            newarf = attrs['required_fields']

            if 'interfaces' in attrs.keys():
                call_plugins = []
                for i in attrs['interfaces']:

                    if (i in mcs.interfaces.keys()) and (not None):

                        call_plugins.append(mcs.interfaces[i])

                    else:

                        raise MModelException(
                            f'\nDeclared interface "{i}" is not defined!\n{mcs.interfaces.keys()}\n')

                    def call_with_fields(self, *args, **kwargs):
                        self.args, self.kw = args, kwargs
                        for plugin in self.call_plugins:
                            print(f'call {plugin.__name__} interface')
                            # print(self.args)
                            # print(self.kw, " ->")
                            plugin.interface_call(self)
                            # print("-> ", self.kw)
                        kws_ = self.kw
                        # print(kws_)
                        super(main_parent, self).__call__(*args, **kws_)

                    attrs['call_plugins'] = call_plugins
                    attrs['__call__'] = call_with_fields

            else:
                pass

            # print(
            #   f'{main_parent.__name__} required_fields ({main_parent.required_fields}) -> {classname} required_fields ({arf}) ->  {classname} required_fields ({newarf})')

            return super().__new__(mcs, classname, bases, attrs, **kws)


class BaseField(RequiredFildItem, metaclass=FieldsMeta, interface=True):
    @classmethod
    def interface_call(cls, other):
        ...


class ArgsField(BaseField, interface=True):

    @classmethod
    def interface_call(cls, other):
        other.kw |= other.__dict__
        if hasattr(other.main_parent, "arg_fields"):
            parents_fields = copy.deepcopy(other.main_parent.arg_fields)
            other.main_parent.arg_fields.extend(other.arg_fields)
            other.arg_fields = other.main_parent.arg_fields

        if len(other.args) > len(other.arg_fields):
            raise MModelException('args count largest count arg fields')
        else:

            for i, a in enumerate(other.args):
                if i < len(other.args):
                    other.kw[other.arg_fields[i]] = a
                else:
                    break

        # print(other.kw)


class KeyField(BaseField, interface=True):
    interphase_key = ...

    @classmethod
    def interface_call(cls, other):
        key = cls.interphase_key

        other.required_fields.add(key)

        other_key = cls.key_handler(other)
        if (key not in other.kw.keys()) or (other.kw[key] == other_key):
            other.kw[cls.interphase_key] = other_key
        else:
            raise MModelException(
                f"The class name does not match the descriptor signature!"
                f"\nclassname: {cls.__class__.__name__}, input name: {key}")

    @classmethod
    def key_handler(cls, other) -> Any:
        pass


class DtypeField(KeyField, interface=True):
    interphase_key = 'dtype'

    @classmethod
    def key_handler(cls, other):
        return other.__class__.__name__


class ZField(KeyField, interface=True):
    interphase_key = 'z'

    @classmethod
    def key_handler(cls, other):
        try:
            return other.kw[cls.interphase_key]
        except:
            return 0.0


class BaseElement(DictableElement, metaclass=FieldsMeta):
    interfaces = ['BaseField']


class Point(BaseElement):
    interfaces = ['ArgsField', 'DtypeField']
    required_fields = {'x', 'y', 'z'}
    arg_fields = ['x', 'y', 'z']

    def __call__(self, *args, **kwargs):

        super().__call__(*args, **kwargs)

    def _version(self):
        # nn=np.round(np.ndarray([self.x, self.y, self.z], dtype=float) * 100, decimals=0)
        # print(nn)
        # s=int("".join([n for n in nn.tolist()]))

        self.version = hex(int(f"{int(self.x * 100)}{int(self.y * 100)}{int(self.z * 100)}"))
        if hasattr(self, 'aliases'):
            for als in self.aliases:
                als._version()

    def __array__(self):
        return np.ndarray([self.x, self.y, self.z])


class Axis(BaseElement):
    interfaces = ['ArgsField', 'DtypeField']
    required_fields = {'start', 'end'}
    arg_fields = list(required_fields)

    def __init__(self, *args, **kwargs):
        super(Axis, self).__init__(*args, **kwargs)

        for t in self.arg_fields:
            pt = self.__dict__[t]
            pt(aliases=[self])

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    def _version(self):
        self.version = self.end.version + self.start.version


from collections import MutableSequence

from tools.temps import AXIS_NAMES


class Structure(tuple):

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, args)
        instance.__dict__ = kwargs

        return instance

    def _structure(self):
        return np.mgrid[[slice(0, i) for i in self]]

    def __array__(self):
        return self._structure()

    def __add__(self, other):
        return self.__class__(*super(Structure, self).__add__(other))


class StructMeta(type):
    __template__ = TemplateBase

    def __new__(cls, classname, bases, attrs, target_element=None, structure=None, **kws):
        attrs['structure'] = structure
        attrs['target_element'] = target_element
        attrs["__call__"] = lambda x, *args, **kw: x.target_element.__call__(x, *args, **kw)

        def __init__(self, *args, **kwargs):
            self._dt = dict()
            self.target_element = target_element
            self.structure = structure

        attrs["__init__"] = __init__

        return super().__new__(cls, classname, bases, attrs)


class BiStructure(Structure):

    def _structure(self):
        return np.mgrid[[slice(a, b) for a, b in self]]


class VectorizeStructure(metaclass=StructMeta, target_element=Axis, structure=BiStructure):

    def __getitem__(self, item):
        return self._dt[item]

    def __setitem__(self, key, value):
        self._dt[key] = value

    def structinit(self, *args):
        grd = self.structure(*args)
        return grd

    def vectorize(self):
        def wrp(*args, **kwargs):

            grd = np.asarray(self.structinit(*args))

            for i in range(grd.shape[1]):
                for j in range(grd.shape[2]):
                    self._dt[i, j] = self.target_element(start=Point(*grd[:, i, 0], z=0),
                                                         end=Point(*grd[:, i, grd.shape[2] - 2], z=0))
                    self._dt[j, i] = self.target_element(start=Point(*grd[:, 0, j], z=0),
                                                         end=Point(*grd[:, grd.shape[1] - 1, j], z=0))
            return self

        return wrp


class BaseStructure(Item, MutableSequence, ABC):
    _ax_names = AXIS_NAMES
    numpy_dtype = float

    def __init__(self, *args, **kwargs):

        super(BaseStructure).__init__(*args, **kwargs)
        super(MutableSequence, self).__init__()

    def _dims(self):
        return len(self.args)

    def _shape(self):
        return tuple([int(arg) for arg in self.args])

    def __getitem__(self, i):
        if len(self.shape) - len(i) == 0:
            return self.__array__()[i]
        else:
            return self.__array__()[i, ...]

    def __delitem__(self, i):
        return self[i]

    def __len__(self):
        return len(self.__array__())

    def __setitem__(self, i, v):
        self[i] = v

    def index_grid(self):
        return np.mgrid[0:[i for i in self.shape]]

    def __array__(self):
        return np.asarray(self, dtype=self.numpy_dtype)

    def __call__(self, *args, **kwargs):
        super(BaseStructure, self).__call__(*args, **kwargs)
        assert len(args)
        self.args = args
        self.shape = self._shape()
        self.dims = self._dims()


class MeshGrid2dStructure(BaseStructure, ABC):

    def __init__(self, x_axes, y_axes, **kwargs):
        super().__init__(x_axes, y_axes, **kwargs)
        self.x_axes = x_axes
        self.y_axes = y_axes

    def __call__(self, x_axes, y_axes, **kwargs):
        kwargs |= dict(x_axes=x_axes, y_axes=y_axes)
        super(MeshGrid2dStructure, self).__call__(**kwargs)
        self.x_axes


from dataclasses import dataclass

"""

class NamedElement(BaseFieldsInterface):
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


class VNElement(NamedElement):
    
    """
