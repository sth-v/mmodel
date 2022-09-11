from __future__ import annotations

import numpy as np

from .geom import *
from ..collections import NamedNumericCollection
from ..meta import Dct, DefaultFied


class PointTableField(DefaultFied):

    def __get__(self, instance, owner=None):
        return instance.__class__._table[instance.uid][instance.__default_keys__.index(self.name)]

    def __set__(self, instance, value):
        super(PointTableField, self).__set__(instance, value)

        instance.__class__._table[instance.uid][instance.__default_keys__.index(self.name)] = value


class Pt(NamedNumericCollection, default_descriptor=PointTableField, dict_descriptor=Dct):
    x, y, z = 0.0, 0.0, 0.0
    def __init__(self, arg, *args, **kwargs):
        self.__class__._table.update({self.uid:[None,None,None]})
        super().__init__(arg, *args, **kwargs)

    def __call__(self, *args, **kwargs):

        super().__call__(*args, **kwargs)

        self.__class__._table[self.uid] = self.__array__()
        return self

    def __array__(self, *args, **kwargs):
        return np.asarray([self.x, self.y, self.z])

    def __getitem__(self, i):
        return self.__array__()[i]


class Triangle(NamedNumericCollection, dict_descriptor=Dct):
    a: Pt
    b: Pt
    c: Pt

    def __array__(self, *args):
        return np.asarray([self.a, self.b, self.c])
