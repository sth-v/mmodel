#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import ast
from collections import Iterator

import rhino3dm

from mm.baseitems import Item
from mm.meta import RemoteType


class L2(metaclass=RemoteType, bucket="lahta.contextmachine.online", prefix="cxm/internal/L2/",
         suffix=""):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True

    def __gethook__(self, hook):
        # print(f"{self} get hook")
        return list(map(rhino3dm.GeometryBase.Decode, ast.literal_eval(hook["Body"].read().decode())["rhino"]))

    def __sethook__(self, hook):
        # print(f"{self} set hook")
        return {"rhino": map(rhino3dm.GeometryBase.Encode, hook)}


class CollectionMethod:

    def __init__(self, f):
        self._f = f

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __get__(self, instance, owner):
        # print("call method")

        try:
            return self.__call__
        except:
            raise

    def __call__(self, *args, **kwargs):
        return self._f(self.owner, *args, **kwargs)


class RhItemCollection(Iterator):

    def __init__(self, cls):
        super().__init__()
        self._i = -1
        self._cls = cls
        self._children = []

    def __iter__(self):
        return self

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, v):
        self.children.append(v)

    @children.deleter
    def children(self):
        del self._children

    def reload(self):
        self._i = -1

    def __next__(self):
        self._i += 1
        if self._i < len(self.children):
            return self.children[self._i]
        else:
            self.reload()
            raise StopIteration

    def __call__(self, *args, **kwargs):
        self.children = self._cls(*args, **kwargs)
        return self

    def __getitem__(self, item):
        return self.children[item]

    def __setitem__(self, item, v):
        self.children[item] = v

    def __call_child(self, name):
        cc = next(self)
        f = self._cls.__dict__[name]

        def wrp(*args, **kwargs):

            return f(cc, *args, **kwargs)

        while True:
            try:
                return wrp
            except:
                break


@RhItemCollection
class RhItem(Item):
    def __init__(self, *args, json_string=None, **kwargs):
        self._rhino = None
        super().__init__(**kwargs)
        if json_string is not None:
            self.decode(json_string)

    def __get__(self, instance, ctx=True):
        if ctx:
            return self.rhino
        else:
            return self._rhino

    @property
    def rhino(self):
        return rhino3dm.GeometryBase.Decode(self._rhino)

    @rhino.setter
    def rhino(self, v):
        self._rhino = v

    def decode(self, string):
        if isinstance(string, str):
            self.rhino = ast.literal_eval(string)
        else:
            self.rhino = string
        return self

    def encode(self):
        return self._rhino


with L2() as l2:
    RhItemCollection()
