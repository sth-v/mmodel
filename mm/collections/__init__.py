#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from __future__ import annotations

import inspect
from collections import defaultdict
from collections.abc import Iterator
from functools import wraps
from typing import Any

import numpy as np

from mm.baseitems import BaseItem, Item


def t(glb):
    for i, kv in enumerate(glb.items()):
        k, v = kv

        yield i, k


def clsmap(seq, item):
    cls = seq[0].__class__
    cls_attr = getattr(cls, item)
    # print(f"Target <{item}> is <{cls.__name__}>'s method or base attribute ...")
    if inspect.ismethod(cls_attr):
        # print("It is method!")

        @wraps(cls_attr)
        def wrp(args, **kwargs):
            for i, slf in enumerate(cls.seq):
                arg = args[i]
                f = getattr(slf, item)
                # print(f"Start yielding ...\nwith seq[{i}] yield {slf.__repr__()}.{item}(args={arg}, kwargs={kwargs})")

                try:
                    kw = dict(arg)
                    kw |= kwargs
                    yield f(**kw)
                finally:
                    yield f(*arg, **kwargs)
            return wrp
    else:
        raise "It is not method"


class BaseCollection(Item, Iterator):
    def __init__(self, seq, *args, **kwargs):
        try:
            iter(seq)
            self.seq = seq
        except:
            self.seq = [seq]
        self.item_dtype = seq[0].__class__
        super().__init__(*args, seq=seq, **kwargs)
        self._i = -1

    def reload(self):
        self._i = -1

    @property
    def state(self):
        return self._i

    def __iter__(self):
        return self

    def __call__(self, *args, **kwargs):
        super(BaseCollection, self).__call__(*args, **kwargs)
        self.item_dtype = self.seq[0].__class__

    def get(self, key):
        return self.seq[key]

    def __getattr__(self, item):
        try:
            cls_attr = getattr(self.item_dtype, item)
            # print(f"Target <{item}> is <{self.item_dtype.__name__}>'s method or base attribute ...")
            if inspect.ismethod(cls_attr):
                # print("It is method!")

                @wraps(cls_attr)
                def wrp(args, **kwargs):
                    for i, slf in enumerate(self.seq):
                        arg = args[i]
                        f = getattr(slf, item)
                        # print(f"Start yielding ...\nwith {self.uid}[{i}] yield {slf.__repr__()}.{item}(args={arg}, kwargs={kwargs})")

                        try:
                            kw = dict(arg)
                            kw |= kwargs
                            yield f(**kw)
                        finally:
                            yield f(*arg, **kwargs)
                    return wrp


            else:
                # print(f"it is base attribute")
                for itm in self.seq:
                    yield getattr(itm, item)
        finally:
            print(
                f"WARN!  Вызываемый аттрибут <{item}> не является обязательным для типа коллекции <{self.item_dtype.__name__}> ."
                "У некоторых элементов он может отсутствовать. В этом случае будет сгенерирован None .")
            for itm in self.seq:
                try:
                    g = getattr(itm, item)
                    yield g
                except:

                    yield None

    def __setattr__(self, k, v):
        for i, itm in enumerate(self):
            setattr(itm, k, v[i])

    def call_item(self, args, **kwargs):
        """Safe call the __call__ method piecewise.
            Pass a list of private arguments to the args, common arguments can be passed as **kwargs."""
        return (item.__call__(args[i], **kwargs) for i, item in enumerate(self.seq))

    def __delitem__(self, key):
        del self.seq[key]

    def __getitem__(self, key):
        return self.seq[key]

    def __setitem__(self, key, value):
        self.seq[key] = value

    def __len__(self):
        return len(self.seq)

    def __next__(self):
        self._i += 1
        if len(self) > self._i:
            return self.seq[self._i]
        else:
            raise StopIteration

    def _fmt(self, prf, pfx, form="({})"):
        bs = "".join([f"{x[0]}={x[1]}" for x in self.__dict__.items()])
        return prf + form.format(bs) + form.format(pfx)

    def __str__(self):
        self._fmt(self.dtype, self.state, form=self.seq)
        return f"{self.dtype}({self.state} in {self.seq})"

    def __repr__(self):
        return f"<{self.dtype}({self.state} in {self.seq}) at {self.uid}>"


class ItemCollection(Iterator):
    def __next__(self):
        pass

    def __init__(self, *args, **kwargs):
        ...


class _AbstractItemCollection(Iterator):
    target = None

    def __init__(self, *args, **kwargs):
        super(_AbstractItemCollection, self).__init__(**kwargs)
        self._i = 0

        self._collection = list(map(lambda x: self.target(**dict(x)), args))

        # map(lambda x: self.target(**dict(x)), args, seq if self._collection is None else self._collection)

    def __len__(self):
        return len(self._collection)

    def __iter__(self):
        return self

    def __call__(self, *args, **kwargs):
        self.collection_keys = dict(args[0])
        self._collection = list(map(lambda x, y: x(**dict(y)), self._collection, args))
        return self

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self._collection[slice(item)]
        else:
            return self._collection[item]

    def __setitem__(self, item, val):
        if isinstance(item, slice):
            self._collection[slice(item)] = val
        else:
            self._collection[item] = val

    def __delitem__(self, item):
        del self._collection[item]

    def __next__(self):
        if self._i < len(self._collection):
            yield self.__getitem__(self._i)
            self._i += 1
        else:
            raise StopIteration


class _AttrHandlerCollection(_AbstractItemCollection):
    attrs_handler: Any

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.attrs_handler.collection = self

    def __getitem__(self, key):
        if isinstance(key, str):

            return list(map(lambda x: getattr(x, key), self._collection))
        elif isinstance(key, int):
            return self._collection[key]
        else:
            return getattr(self[key[1]], key[0])


class AbstractItemCollection(_AttrHandlerCollection):
    """
    >>> ddd = defaultdict()
    >>> ddd["x"]= 1,2,33,8,22,4,51,8
    >>> ddd["y"]= 11,45,3,99,12,2,1,3
    >>> dt=[dict([("x", ddd["x"][i]),("y",ddd["y"][i])]) for i in range(8)]
    >>> dt
    [{'x': 1, 'y': 11},
     {'x': 2, 'y': 45},
     {'x': 33, 'y': 3},
     {'x': 8, 'y': 99},
     {'x': 22, 'y': 12},
     {'x': 4, 'y': 2},
     {'x': 51, 'y': 1},
     {'x': 8, 'y': 3}]
    >>> AbstractItemCollection(*dt)
    Out[3]: <__main__.AbstractItem at 0x15a1e2e20>
    >>> t_collection =

    (*dt)
    >>> t_collection["x"]
    [1, 2, 33, 8, 22, 4, 51, 8]
    >>> t_collection["y"]
    [11, 45, 3, 99, 12, 2, 1, 3]
    >>> t_collection[0,"x"]
    Out[4]: 1
    >>>t_collection[0,"y"]
    Out[5]: 11
    >>>list(next(t_collection))[0].ikw
    Out[7]: {'x': 33, 'y': 3}
    >>>list(next(t_collection))[0].ikw
    Out[8]: {'x': 8, 'y': 99}
    >>>list(next(t_collection))[0].ikw
    Out[9]: {'x': 22, 'y': 12}
    >>>list(next(t_collection))[0].ikw
    Out[10]: {'x': 4, 'y': 2}
    >>>for o in t_collection:
    ....   print(list(o)[0].__dict__)
    {'ikw': {'x': 1, 'y': 11}, 'iar': (), '_uid': '0x12a5ab040', 'x': 1, 'y': 11, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 2, 'y': 45}, 'iar': (), '_uid': '0x12a5ab430', 'x': 2, 'y': 45, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 33, 'y': 3}, 'iar': (), '_uid': '0x12a5ab2b0', 'x': 33, 'y': 3, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 8, 'y': 99}, 'iar': (), '_uid': '0x11fc27eb0', 'x': 8, 'y': 99, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 22, 'y': 12}, 'iar': (), '_uid': '0x11fc27cd0', 'x': 22, 'y': 12, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 4, 'y': 2}, 'iar': (), '_uid': '0x11fc27f40', 'x': 4, 'y': 2, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 51, 'y': 1}, 'iar': (), '_uid': '0x11fc27880', 'x': 51, 'y': 1, 'version': '0x4d0x5b0x600x600x62'}
    {'ikw': {'x': 8, 'y': 3}, 'iar': (), '_uid': '0x11fc27e50', 'x': 8, 'y': 3, 'version': '0x4d0x5b0x600x600x62'}
    """


class NamedNumericCollection(BaseItem):
    def __init__(self, arg, *args, **kwargs):
        self._i = -1
        # print(arg, args)
        try:
            iter(arg)

            arg_ = arg
        except:
            arg_ = (arg,)

        if len(args) == 0:

            args_ = arg_


        else:

            args_ = arg_ + args
        super().__init__(*args_, **kwargs)

    def __setitem__(self, i, v):
        setattr(self, self.__default_keys__[i], v)

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i < len(self.__array__()):
            return self.__array__()[self._i]
        else:
            raise StopIteration

    def __array__(self, *args, **kwargs) -> np.ndarray:
        return np.asarray(list(self.default_fields.values))

    def __getitem__(self, i):
        return self.__array__()[i]


class CollectionDescriptor:
    grid = None

    def __init__(self, function):
        super().__init__()
        self.function = function
        self.name = function.__name__

    def __get__(self, obj, type=None) -> object:
        for i in self.grid.cellgrid:
            for j in i:
                self.function(obj, j)
