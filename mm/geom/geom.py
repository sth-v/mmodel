import copy
from abc import ABC
from collections import namedtuple

import compas
import compas.data
import compas.geometry as cg
import numpy as np

from mm.baseitems import DictableItem, Item
from mm.parametric import Circle

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


class Point(DictableItem):
    x = 0.0
    y = 0.0
    z = 0.0

    def to_compas(self):
        return cg.Point(self.x, self.y, self.z)


class Arc(DictableItem, Circle):
    r = 1.0
    x0 = 0.0
    y0 = 0.0
    start_angle = 0.0
    end_angle = np.pi / 2

    def __call__(self, *args, **kwargs):
        super(Arc, self).__call__(*args, **kwargs)

        self.start = self.evaluate(self.start_angle)
        self.end = self.evaluate(self.end_angle)
        self.cc = cg.NurbsCurve.from_circle(cg.Circle(cg.Plane([self.x0, self.y0, 0.0], [0, 0, 1]), self.r))
        s, self.ts = self.cc.closest_point(self.start, return_parameter=True)
        es, self.te = self.cc.closest_point(self.end, return_parameter=True)

    def evaluate(self, t):
        return super(Arc, self).evaluate(t)

    def nurbs(self):
        return self.cc.segmented(self.ts, self.te)

    def to_compas(self):
        return self.nurbs()


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
