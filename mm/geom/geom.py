#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from __future__ import absolute_import

import compas.geometry as cg
import numpy as np
from scipy.spatial.distance import euclidean

from baseitems import WithSlots
from ..baseitems import DictableItem

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

    def __array__(self, *args, **kwargs) -> np.ndarray[(1, 3), np.dtype[float]]:
        return np.ndarray.__array__(np.ndarray(self.xyz), *args, **kwargs)

    def distance(self, other):
        return euclidean(np.asarray(self.xyz), np.asarray(other))

    def transform(self, trfm):
        self.x, self.y, self.z, _ = trfm @ np.array(self.xyz + (1,)).T

    def __len__(self):
        return len(self.xyz)

    def __getitem__(self, item):
        return self.xyz[item]
