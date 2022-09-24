#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import numpy as np

from ..collections import Vector
from ..meta import Dct, MetaItem

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

from mm.baseitems import Item


class Point(Item, metaclass=MetaItem):
    x, y, z = 1, 1, 1

    def __array__(self):
        return np.array([self.x, self.y, self.z])


class Triangle(Vector, metaclass=MetaItem, dict_descriptor=Dct):
    a: Pt
    b: Pt
    c: Pt

    def __array__(self, *args):
        return np.asarray([self.a, self.b, self.c])


class Quad(Vector):
    a: Pt
    b: Pt
    c: Pt
    d: Pt
