#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from __future__ import absolute_import

import compas.geometry as cg
import numpy as np

from ..baseitems import DictableItem, Item
from ..meta import MetaItem

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


class PointT(metaclass=MetaItem):
    x, y, z = 1, 1, 1

    def __array__(self):
        return np.array([self.x, self.y, self.z])

    def to_compas(self):
        return cg.Point(self.x, self.y, self.z)


class Triangle(Item, metaclass=MetaItem):
    a: Point
    b: Point
    c: Point

    def __array__(self, *args):
        return np.asarray([self.a, self.b, self.c])
