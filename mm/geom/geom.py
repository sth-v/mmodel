import copy
from abc import ABC
from collections import namedtuple

import compas
import compas.data
import compas.geometry as cg
import numpy as np
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





