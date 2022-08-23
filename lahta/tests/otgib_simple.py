#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from enum import Enum
from typing import Iterator, Iterable
import numpy as np
from math import pi, degrees
from mm.baseitems import Item, DictableItem, FieldItem


def xform_matrix2d(rotation_angle, translate):
    rot = np.array([
        [np.cos(rotation_angle), -np.sin(rotation_angle), translate[0]],
        [np.sin(rotation_angle), np.cos(rotation_angle), translate[1]]


    ])
    return rot


class Point2d(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, x, y, **kwargs):
        super(Point2d, self).__call__(**kwargs)
        self.x = x
        self.y = y

import dataclasses
    def __array__(self):
        return np.array([self.x, self.y, self.z])


class Polyline:
    def __init__(self, seq):
        self._seq = seq

    def __len__(self):
        return len(self._seq)

    def __iter__(self):
        return self

    def __next__(self) -> Point2d:
        return self._seq.__next__()

    def __setitem__(self, key, value: Point2d) -> None:
        self._seq[key] = value

    def __getitem__(self, key) -> Point2d:
        return self._seq[key]

    @property
    def T(self):
        return self.__array__().T

    def __array__(self):
        l=[]
        for i in self._seq:
            l.append([i.x, i.y])
        return np.array(l)
    def __rmatmul__(self, other):
        return other @ np.asarray(self).T

    def append(self, v):
        self._seq.append(v)
    def __delitem__(self, key):
        del self._seq[key]

class TestOtgib(Iterator):
    def __init__(self, spec):
        self._i = -1
        super().__init__()
        self._spec = spec
        self.prg = Polyline(Point2d(0, 0))

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        if self._i < len(self._spec):
            angle, length, radius = self._spec[self._i]
            xf = xform_matrix2d(pi - angle, -1*np.array([1,0])*length)

            xf @ self.prg
            self.prg.append(Point2d(0, 0))
            print(f"Bending event {self._i}({self._spec}), ang: {degrees(angle)}°, len: {length}mm, rad: {radius}")
            return self.prg
        else:
            raise StopIteration
