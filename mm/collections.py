from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from typing import Any, Mapping, Tuple

from mm.baseitems import ArgsItem
from functools import singledispatchmethod
import types, typing, weakref


def t(glb):
    for i, kv in enumerate(glb.items()):
        k, v = kv

        yield i, k


class ItemCollection(Iterator):
    target = ArgsItem

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
    target = ArgsItem
