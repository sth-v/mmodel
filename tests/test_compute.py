import json

import numpy as np
import rhino3dm
from compute_rhino3d import Util
from rhino3dm import _rhino3dm

from plugins.compute import ComputeBinder


class A:
    def __init__(self, pln):
        self.polyline = pln

    @ComputeBinder
    def rhcmp(self, polyline: rhino3dm.Polyline = None, x=None, y=None, z=None):
        import Rhino.Geometry as rg

        rail = rg.NurbsCurve.CreateControlPointCurve \
            ([rg.Point3d(xx, yy, zz) for xx, yy, zz in zip(eval(x), eval(y), eval(z))], 2)
        _, pln = rail.FrameAt(0.0)

        plnn = rg.Plane(pln.Origin, pln.YAxis,
                        pln.ZAxis)
        polyline.Transform(rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plnn))
        swp = rg.SweepOneRail()
        ans = swp.PerformSweep(rail, polyline)
        return ans

    def sweep(self, rail):
        x, y, z = rail
        return self.rhcmp(polyline=self.polyline, x=f'{x}', y=f'{y}', z=f'{z}')["ans"][0]


class SweepRail1:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        return self.blob(instance, instance.profile, *instance.rail)

    @ComputeBinder
    def blob(self, polyline: rhino3dm.Polyline = None, x=None, y=None, z=None):
        import Rhino.Geometry as rg
        rail = rg.NurbsCurve.CreateControlPointCurve \
            ([rg.Point3d(xx, yy, zz) for xx, yy, zz in zip(eval(x), eval(y), eval(z))], 2)
        _, pln = rail.FrameAt(0.0)

        plnn = rg.Plane(pln.Origin, pln.YAxis,
                        pln.ZAxis)
        polyline.Transform(rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plnn))
        swp = rg.SweepOneRail()
        ans = swp.PerformSweep(rail, polyline)
        return ans


def test1():
    profile = {"version": 10000, "archive3dm": 70, "opennurbs": -1879014534,
               "data": "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"}
    rail = [[0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
            [0.0, 10.00, 20.0, 30.0, 50.0, 180.0, 339.0],
            [0.0, 20.0, 50.0, 100.0, 140.0, 255.0, 360.0]]
    a = A(_rhino3dm.CommonObject.Decode(profile))
    print(a)

    brp = a.sweep(rail)
    print(brp)

    model = rhino3dm.File3dm()
    model.Objects.AddBrep(brep=brp)
    model.Write("testcompute.3dm", 7)


from plugins.compute.blobs.l2mask import CalcMaskL2
from mm.baseitems import WithSlots
from mm.collection.getter import CollectionItemGetSetter


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


class SectMask:
    __blob__ = "import Rhino.Geometry as rg\nimport json\ndef check(x, y, eps=50.0):\n    x.Transform(rg.Transform.PlanarProjection(rg.Plane.WorldXY))\n    [yy.Transform(rg.Transform.PlanarProjection(rg.Plane.WorldXY)) for yy in y]\n    ap=rg.AreaMassProperties.Compute(x)\n    dst=list(map(lambda yy: (yy, ap.Centroid.DistanceTo(yy.ClosestPoint(ap.Centroid))),  y))\n    dst.sort(key=lambda xx: xx[1])\n    if dst[0][1]<eps:\n        return all([not rg.Curve.PlanarCurveCollision(x, crv, rg.Plane.WorldXY, 0.1) for crv in list(rg.Curve.JoinCurves(dst[0][0].Edges))])\n    else:\n        return False\ndef main_func(aa,bb,eps=50.0):\n    for aaa in aa:\n        yield check(aaa, bb, eps=eps)\nans=json.dumps(list(main_func(x,y, eps=40)))"

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        def wrap(constrains, eps=40.0):
            return json.loads(
                Util.PythonEvaluate(self.__blob__, {"x": instance.triangles, "y": constrains, "eps": eps},
                                    ["ans"])["ans"])

        wrap.__name__ = self.name
        return wrap


SectMask()
from scipy.spatial.distance import euclidean


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


class TrianglePanel(WithSlots):
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
        self._triangle.SetAllX(self.a_rh.X, self.b_rh.X, self.c_rh.X)
        self._triangle.SetAllY(self.a_rh.Y, self.b_rh.Y, self.c_rh.Y)
        self._triangle.SetAllZ(self.a_rh.Z, self.b_rh.Z, self.c_rh.Z)
        return self._triangle
