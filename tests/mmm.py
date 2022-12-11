import collections
import json
from abc import ABC
from typing import ContextManager

try:
    import Rhino
except:
    pass
import pandas as pd
import rhino3dm
from compute_rhino3d import AreaMassProperties, Util

from baseitems import Base, Matchable, WithSlots
from collection.multi_description import CollectionItemGetSetter

from plugins.compute.blobs.l2mask import CalcMaskL2
from mm.geom.base import MmPoint


class Triangle(WithSlots):
    __match_args__ = "a", "b", "c"
    _polycurve = None

    @property
    def polycurve(self):
        return rhino3dm.Polyline(self.a, self.b, self.c, self.a)


class TriangleCelling(CollectionItemGetSetter[list, Triangle]):
    mask = CalcMaskL2()
    _interior = None

    @property
    def interior(self):
        return self._interior

    @interior.setter
    def interior(self, value):
        self._interior = value

    _exterior = None

    @property
    def exterior(self):
        return self._exterior

    @exterior.setter
    def exterior(self, value):
        self._exterior = value


class DynamicMask:
    __blob__ = "import Rhino.Geometry as rg\nimport json\ndef check(x, y, eps=50.0):\n    x.Transform(" \
               "rg.Transform.PlanarProjection(rg.Plane.WorldXY))\n    [yy.Transform(rg.Transform.PlanarProjection(" \
               "rg.Plane.WorldXY)) for yy in y]\n    ap=rg.AreaMassProperties.Compute(x)\n    dst=list(map(lambda yy: " \
               "(yy, ap.Centroid.DistanceTo(yy.ClosestPoint(ap.Centroid))),  y))\n    dst.sort(key=lambda xx: xx[" \
               "1])\n    if dst[0][1]<eps:\n        return all([not rg.Curve.PlanarCurveCollision(x, crv, " \
               "rg.Plane.WorldXY, 0.1) for crv in list(rg.Curve.JoinCurves(dst[0][0].Edges))])\n    else:\n        " \
               "return False\ndef main_func(aa,bb,eps=50.0):\n    for aaa in aa:\n        yield check(aaa, bb, " \
               "eps=eps)\nans=json.dumps(list(main_func(x,y, eps=40))) "

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        def wrap(constrains, eps=40.0):
            return json.loads(
                Util.PythonEvaluate(self.__blob__, {"x": instance["triangle"], "y": constrains, "eps": eps},
                                    ["ans"])["ans"])

        wrap.__name__ = self.name

        return wrap


class Mask(DynamicMask):
    def __init__(self, constrains=None):
        super().__init__()
        self._constrains = constrains

    def __get__(self, instance, owner):
        return super().__get__(instance, owner) if self._constrains is None else super().__get__(instance, owner)(
            self._constrains)

    def __set__(self, instance, value):
        self._constrains = value


class _TrianglePanel(WithSlots):
    __match_args__ = "a", "b", "c", "subtype", "extratype", "flatindex", "gridindex"
    mask = SectMask()

    _triangle: rhino3dm.Polyline = rhino3dm.Polyline(3)

    @property
    def c_rh(self): return rhino3dm.Point3d(*self.c)

    @property
    def b_rh(self): return rhino3dm.Point3d(*self.b)

    @property
    def a_rh(self): return rhino3dm.Point3d(*self.a)

    @property
    def triangle(self) -> rhino3dm.Polyline:
        self._triangle.Add(*self.a), self._triangle.Add(*self.b), self._triangle.Add(*self.c)
        return self._triangle


class Rhino3dmDecoder(json.JSONDecoder):
    def decode(self, s, *args, **kwargs):
        o = super().decode(s, *args, **kwargs)
        if isinstance(o, dict):
            match list(o.keys()):
                case ["X", "Y", "Z"]:
                    return Util.DecodeToPoint3d(o)
                case ["From", "To"]:
                    return Util.DecodeToLine(o)
                case ['Min', 'Max']:
                    return Util.DecodeToBoundingBox(o)

                case ['version', 'archive3dm', 'opennurbs', 'data']:
                    return Util.DecodeToCommonObject(o)
                case [_]:
                    return o
        elif isinstance(o, list):
            return [self.decode(obj, *args, **kwargs) for obj in o]
        else:
            return o


class SubtypeCollection(CollectionItemGetSetter):
    def __init__(self, target="L2.json", firstkey="L2"):
        l = pd.read_json(target)
        centers = []
        for ll in l[firstkey]:
            a, (b,) = ll
            centers.append(MmPoint(*a, subtype=b))
        super().__init__(centers)


class MaskCollection(CollectionItemGetSetter):
    def __init__(self, target="L2.json", firstkey="L2"):
        l = pd.read_json(target)
        centers = []
        for ll in l[firstkey]:
            a, (b,) = ll
            centers.append(MmPoint(*a, subtype=b))
        super().__init__(centers)


# L1Subtypes = SubtypeCollection(target="tests/L1.json", firstkey="L1")
L2Subtypes = SubtypeCollection(target="tests/L2.json", firstkey="L2")


class AreaMassProps(Base):
    Area: float
    Centroid: dict[str, float]


class TrianglePanel(Matchable):
    __match_args__ = "index", "pairtype", "cont"
    __repr_ignore__ = "cont"
    _area_mass_props = None

    def recompute_props(self):
        self._area_mass_props = AreaMassProps(**AreaMassProperties.Compute1(self.triangle, 0.1))

    @property
    def area_mass_props(self) -> AreaMassProps:
        return self._area_mass_props

    @area_mass_props.setter
    def area_mass_props(self, value):
        self._area_mass_props = value

    @property
    def triangle(self) -> rhino3dm.PolylineCurve:
        # print(self.cont)

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
        return self.area_mass_props.Area


class CollectionFieldManager(ContextManager, ABC):
    def __init__(self, clls, fields: collections.OrderedDict):
        super().__init__()
        self._cls = clls
        self.fields = fields
        print(fields)

        self.cache_key = hex(id(self))

    def __enter__(self):
        dct = []
        for k, path in self.fields.items():
            with open(path, "rb") as fl:
                dct.append(json.load(fl))
        return CollectionItemGetSetter([self._cls(*dts) for dts in zip(*dct)])

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)


with CollectionFieldManager(TrianglePanel, collections.OrderedDict(index="tests/L2-indexing.json",
                                                                   pairtype="tests/L2-subtype.json",
                                                                   cont="tests/L2-triangles.json")) as items:
    items['area_mass_props'] = [AreaMassProps(**i) for i in
                                AreaMassProperties.Compute(items["triangle"], multiple=True)]
