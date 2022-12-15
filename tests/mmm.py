import collections
import json
from abc import ABC
from collections import OrderedDict
from typing import ContextManager

import numpy as np

from collection.masks import Mask

try:
    import Rhino
except:
    pass
import pandas as pd
import rhino3dm
from compute_rhino3d import AreaMassProperties

from baseitems import Base, Matchable
from collection.multi_description import CollectionItemGetSetter, MultiDescriptor

from mm.geom.base import MmPoint
from plugins.compute import Util
from functools import lru_cache


class ComputeMask(Mask):
    __blob__ = "import Rhino.Geometry as rg\ndef check(x, y, eps=50.0):\n    x.Transform(" \
               "rg.Transform.PlanarProjection(rg.Plane.WorldXY))\n    [yy.Transform(rg.Transform.PlanarProjection(" \
               "rg.Plane.WorldXY)) for yy in y]\n    ap=rg.AreaMassProperties.Compute(x)\n    dst=list(map(lambda yy: " \
               "(yy, ap.Centroid.DistanceTo(yy.ClosestPoint(ap.Centroid))),  y))\n    dst.sort(key=lambda xx: xx[" \
               "1])\n    if dst[0][1]<eps:\n        return all([not rg.Curve.PlanarCurveCollision(x, crv, " \
               "rg.Plane.WorldXY, 0.1) for crv in list(rg.Curve.JoinCurves(dst[0][0].Edges))])\n    else:\n        " \
               "return False\ndef main_func(aa,bb,eps=50.0):\n    for aaa in aa:\n        yield check(aaa, bb, " \
               "eps=eps)\nans=\"{}\".format(list(main_func(a,b, eps=40))) "

    @staticmethod
    @lru_cache(maxsize=1024 * 4)
    def wrapper(mask, instance, owner, constrains, **kwargs):
        # print(instance, owner, constrains)
        res = Util.PythonEvaluate(mask.__blob__, {"a": instance["triangle"], "b": constrains}, ["ans"])
        # print(res)
        itr = IterCall(eval(res["ans"])
                       )

        return lambda key: list(filter(itr, instance[key]))


class SubtypeCollection(CollectionItemGetSetter):
    def __init__(self, target="L2.json", firstkey="L2"):
        l = pd.read_json(target)
        centers = []
        for ll in l[firstkey]:
            a, (b,) = ll
            centers.append(MmPoint(*a, subtype=b))
        super().__init__(centers)


# L1Subtypes = SubtypeCollection(target="tests/L1.json", firstkey="L1")
L2Subtypes = SubtypeCollection(target="tests/L2.json", firstkey="L2")


class IterCall:
    def __init__(self, seq):
        self._i = -1
        self._seq = seq

    def __call__(self, val):
        self._i += 1
        return self._seq[self._i % len(self._seq)]


class AreaMassProps(Base):
    Area: float
    Centroid: dict[str, float]


class TrianglePanel(Matchable):
    __match_args__ = "index", "pairtype", "subtype", "cont"
    __repr_ignore__ = "cont"
    _area_mass_props = {}

    @property
    def area_mass_props(self) -> AreaMassProps:
        return AreaMassProps(**self._area_mass_props)

    @area_mass_props.setter
    def area_mass_props(self, value):
        self._area_mass_props = value

    @property
    def triangle(self) -> rhino3dm.PolylineCurve:
        # print(self.cont)
        self.cont['archive3dm'] = 70
        return Util.DecodeToCommonObject(self.cont)

    @triangle.setter
    def triangle(self, value):
        raise AttributeError("Can not set this attribute")

    @property
    def centroid(self) -> MmPoint:
        _cntr = self.area_mass_props.Centroid
        return MmPoint(_cntr["X"], _cntr["Y"], _cntr["Z"])

    @property
    def area(self) -> float:
        return self.area_mass_props.Area * 1e-6

    @property
    def tag(self):
        return self.subtype + "-" + self.pairtype


# --------------------------------------------------------------------------------------------------------------
from connectors.rhino import get_model_geometry


class MDL2(MultiDescriptor):
    main_mask = ComputeMask(constrains=get_model_geometry("tests/L2-cut-mask.3dm"))


class CollectionFieldManager(ContextManager, ABC):
    def __init__(self, clls, fields: collections.OrderedDict):
        super().__init__()
        self._cls = clls
        self.fields = fields

        self.cache_key = hex(id(self))

    def __enter__(self):
        dct = []
        for k, path in self.fields.items():
            with open(path, "rb") as fl:
                dct.append(json.load(fl))
        mm = MDL2([self._cls(*dts) for dts in zip(*dct)])
        mm["area_mass_props"] = AreaMassProperties.Compute(mm["triangle"], multiple=True)
        return mm

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)


with CollectionFieldManager(TrianglePanel,
                            OrderedDict(index="tests/L2-indexing.json",
                                        pairtype="tests/L2-subtype.json",
                                        subtype="tests/L2-subtype.json",
                                        cont="tests/L2-triangles.json")) as items:

    len(items.main_mask("triangle")), len(items["triangle"])
    print(items.main_mask("area"))
    import pandas as pd

    pd.read_json("tests/L1L2summ.json").to_csv("tests/tables/L1L2summ.csv")
