from collections import namedtuple

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import ghpythonlib.treehelpers as th
import Rhino.Geometry as rg
import math
import copy
import ghpythonlib.components as ghc

R1 = 1.5
W = 11.5
Pat = namedtuple("Pat", ["contour", "hole"])


class TT:

    def __init__(self, pt, pt2, circle, w=15, hole=3.5):
        self.name = "arcpattern"
        self.w = w
        self.fh = 9.872
        self._n = 0
        self._pt = pt
        self._pt2 = pt2
        self.circle = circle
        self.hole = hole
        self.ptk = rg.Point3d(0, 0, 0)
        self.pt2k = rg.Point3d(0, 0, 0)

        self.ln

    @property
    def pt(self):
        return self._pt + self.ptk

    @property
    def pt2(self):
        return self._pt2 + self.pt2k

    @property
    def n(self):
        return self._n

    @n.setter
    def n(self, v):
        self._n = v

    @property
    def tan(self):
        t1, t2 = ghc.TangentLines(self.pt, self.circle)
        return t1, t2

    @property
    def mr(self):
        return rg.Transform.Mirror(self.circle.Center, rg.Vector3d.XAxis)

    @property
    def ln(self):
        plcrv = rg.PolyCurve()
        ln1 = self.tan[self.n]
        ln2 = copy.deepcopy(self.tan[self.n])
        ln0 = rg.Line(self.pt2, ln1.From)
        pt3 = copy.deepcopy(self.pt2)
        pt3.Transform(self.mr)
        pt6 = self.pt2 + rg.Point3d(0, -self.w, 0)
        pt4 = self.pt2 + rg.Point3d(0, -self.w - self.fh, 0)
        pt5 = pt4 + rg.Point3d(0, -16 - self.w + self.fh, 0)
        pt41 = pt4 + rg.Point3d(-self.hole / 2, 0, 0)
        pt42 = pt4 + rg.Point3d(self.hole / 2, 0, 0)
        pt51 = pt5 + rg.Point3d(-self.hole / 2, 0, 0)
        pt52 = pt5 + rg.Point3d(self.hole / 2, 0, 0)
        print pt5

        crv = [
            rg.Circle(pt4, self.hole / 2).ToNurbsCurve(),
            rg.Circle(pt6, self.hole / 2).ToNurbsCurve(),
            rg.Circle(pt5, self.hole / 2).ToNurbsCurve(),
            rg.Polyline([pt41, pt51, pt52, pt42, pt41]).ToPolylineCurve()]
        ln3 = copy.deepcopy(ln0)
        ln2.Transform(self.mr)
        ln3.Transform(self.mr)
        # crvu = list(rg.Curve.CreateBooleanUnion(crv,0.01))
        self.holes = copy.deepcopy(crv)
        self.contour = [ln0.ToNurbsCurve(), ln1.ToNurbsCurve(),
                        rg.Arc(ln1.To, self.circle.PointAt(-0.5), endPoint=ln2.To).ToNurbsCurve(),
                        ln2.ToNurbsCurve(), ln3.ToNurbsCurve()]

        return self.holes


class Ptrn:
    def __init__(self, itr):
        self.itr = itr

    def __getitem__(self, itm):
        return self.itr.__getitem__(itm)

    def __setitem__(self, itm, v):
        self.itr.__setitem__(itm, v)

    def __len__(self):
        return len(self.itr)


class Pattern:
    def __init__(self, unit, modl=23, l=1000):
        self.__unit = unit
        self.name = "pattern_arc"
        self.unit = copy.deepcopy(unit)

        self.u = self.unit.ln
        self.modl = modl
        self.__l = l
        self.ln = l // modl
        print(self.ln)
        self.hole = []
        self.contour = []

    def __iter__(self):
        return self

    @property
    def trsf(self):
        return rg.Transform.Translation(self.modl, 0, 0)

    def mtr(self):
        contour=[]
        hole=[]
        contour.append(self.u.contour)
        hole.append(self.u.hole)
        for i in self.u.contour:
            i.Transform(self.trsf)

        for j in self.u.hole:
            j.Transform(self.trsf)

        return self.u.hole

    def next(self):
        if self.constrain():
            self.ln -= 1
            print(self.u)
            self.mtr()
            return self.u
        else:
            raise StopIteration

    def constrain(self):

        return self.ln > 0

    def reload(self):
        self.hole = []
        self.contour = []
        self.unit = copy.deepcopy(self.__unit)
        self.u = self.unit.ln
        self.ln = self.__l // self.modl
        print(self.ln)
