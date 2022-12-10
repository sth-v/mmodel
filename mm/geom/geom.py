#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from __future__ import absolute_import

import compas.geometry as cg
import numpy as np

from baseitems import WithSlots
from ..baseitems import DictableItem
from mm.baseitems import DictableItem, Item


mesh_js_schema = {
    "metadata": dict(),
    "uuid": '',
    "type": "BufferGeometry",
    "data": {"attributes": {"position": {"itemSize": 3,
                                         "type": "Float32Array",
                                         "array": []}
                            }
             },
}
pts_js_schema = {
    "metadata": dict(),
    "uuid": '',
    "type": "BufferGeometry",
    "data": {"attributes": {"position": {"itemSize": 3,
                                         "type": "Float32Array",
                                         "array": None}
                            }
             }
}


class Point(DictableItem):
    x = 0.0
    y = 0.0
    z = 0.0
    exclude = ["version", "uid", "__array__"]

    def to_compas(self):
        return cg.Point(self.x, self.y, self.z)

    def __array__(self, *args):
        return np.asarray([self.x, self.y, self.z])



class MmPoint(WithSlots):
    __match_args__ = "x", "y", "z"
    _i = -1

    @property
    def xyz(self) -> tuple[float, float, float]:
        return self.x, self.y, self.z


    def distance(self, other):
        return euclidean(np.asarray(self.xyz), np.asarray(other))

    def __array__(self, *args):
        return np.asarray([self.a, self.b, self.c])

    def __len__(self):
        return len(self.xyz)

'''class Quad(Vector):
    a: Point
    b: Point
    c: Point
    d: Point'''
