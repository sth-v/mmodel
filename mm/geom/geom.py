import copy
from abc import ABC
from collections import namedtuple

import compas
import compas.data
import compas.geometry as cg
import numpy as np
from mm.baseitems import DictableItem, Item
from ..collections import NamedNumericCollection
from ..meta import Dct, DefaultFied, MetaItem

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

    def __array__(self):
        return np.ndarray([self.x, self.y])


class Face(DictableItem):
    fields = dict(
        vertices=[]
    )
    schema_js = copy.deepcopy(mesh_js_schema)

    def __call__(self, vertices=(), **kwargs):
        super().__call__(vertices=vertices, **kwargs)
        self.polygon = compas.geometry.Polygon(list(map(lambda x: compas.geometry.Point(x.x, x.y, x.z), vertices)))
        self.area = self.polygon.area

    def encode(self, **kwargs):
        self.schema_js["data"]["attributes"]["position"]["array"] = list \
            (np.asarray(self.vertices, dtype=np.float32).tolist())


class PointTableField(DefaultFied):

    def __get__(self, instance, owner=None):
        return instance.__class__._table[instance.uid][instance.__default_keys__.index(self.name)]

    def __set__(self, instance, value):
        super(PointTableField, self).__set__(instance, value)

        instance.__class__._table[instance.uid][instance.__default_keys__.index(self.name)] = value


class Pt(NamedNumericCollection, default_descriptor=PointTableField, dict_descriptor=Dct):
    x, y, z = 0.0, 0.0, 0.0

    def __init__(self, arg, *args, **kwargs):
        self.__class__._table.update({self.uid: [None, None, None]})
        super().__init__(arg, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        self.__class__._table[self.uid] = self.__array__()
        return self

    def __array__(self, *args, **kwargs):
        return np.asarray([self.x, self.y, self.z])

    def __getitem__(self, i):
        return self.__array__()[i]


class Triangle(NamedNumericCollection, metaclass=MetaItem, dict_descriptor=Dct):
    a: Pt
    b: Pt
    c: Pt

    def __array__(self, *args):
        return np.asarray([self.a, self.b, self.c])


class Quad(NamedNumericCollection):
    a: Pt
    b: Pt
    c: Pt
    d: Pt
