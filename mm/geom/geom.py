__all__=["Point", "Arc"]
import copy
from abc import ABC
from collections import namedtuple

import compas
import compas.data
import compas.geometry as cg
import numpy as np
import rhino3dm
from mm.baseitems import DictableItem, Item
from mm.parametric import SimpleCircle

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
    exclude = ["version", "uid"]


    def to_compas(self):
        return cg.Point(self.x, self.y, self.z)


from rhino3dm import CommonObject, GeometryBase


class Arc(SimpleCircle, DictableItem):

    r = 1.0
    x0 = 0.0
    y0 = 0.0
    start_angle = 0.0
    end_angle = np.pi / 2

    def __call__(self, *args, **kwargs):
        super(Arc, self).__call__(*args, **kwargs)

        self.start = self.evaluate(self.start_angle)
        self.end = self.evaluate(self.end_angle)

    def to_compas(self):
        self.cc = cg.NurbsCurve.from_circle(cg.Circle(cg.Plane([self.x0, self.y0, 0.0], [0, 0, 1]), self.r))
        _, self.ts = self.cc.closest_point(self.start.to_compas(), return_parameter=True)
        _, self.te = self.cc.closest_point(self.end.to_compas(), return_parameter=True)
        return self.cc.segmented(self.ts, self.te)

    def evaluate(self, t):
        x, y = super().evaluate(t)
        return Point(x=x, y=y)

    def to_rhino(self):
        rh_arc = rhino3dm.Arc(rhino3dm.Point3d(0.0, 0.0, 0.0), radius=self.r,
                              angleRadians=self.end_angle - self.start_angle)
        return rh_arc

    def to_rhino_json(self):
        return self.to_rhino().ToNurbsCurve().Encode()

    def to_compas_json(self):
        return self.to_compas().to_jsonstring()


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
