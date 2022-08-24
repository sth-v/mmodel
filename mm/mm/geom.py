import copy
from abc import ABC
from collections import namedtuple
import compas.geometry
import compas.data

import compas
import numpy as np

from mm.mm.baseitems import DictableItem, Item, JsItem

RootParents = namedtuple("RootParents", ["main_parent", "FramrworkParent"])

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
                                         "array": []}
                            }
             },
}


class Point(Item):
    x = 0.0
    y = 0.0

    def __array__(self):
        return np.array([self.x, self.y])


class Point2d(Point):
    x = 0.0
    y = 0.0

    def __array__(self):
        return np.array([self.x, self.y])


class Point3d(Point):
    x = 0.0
    y = 0.0
    z = 0.0

    def __array__(self):
        return np.array([self.x, self.y, self.z])


class Point4d(Point):
    x = 0.0
    y = 0.0
    z = 0.0
    w = 0.0

    def __array__(self):
        return np.array([self.x, self.y, self.z, self.w])


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
        self.schema_js["data"]["attributes"]["position"]["array"] = np.asarray(self.vertices, dtype=np.float32)


class GeometryMeta(type):
    target_framework = compas
    mapping_framework = dict(

    )


class GeometryItem(Item, compas.data.Data, ABC):
    """
    geometry item
    """

    def __init__(self, *args, **kwargs):
        compas.data.Data.__init__()
        super(GeometryItem, self).__init__(*args, **kwargs)
        # super(GeometryItem, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(GeometryItem, self).__call__(*args, **kwargs)
