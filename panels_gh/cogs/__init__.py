from collections import namedtuple

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import Rhino.Geometry as rg
import copy
import ghpythonlib.components as ghc

R1 = 1.5
W = 11.5

Pat = namedtuple("Pat", ["contour", "hole"])


class TT:

    def __init__(self, pt, pt2, circle, w=6.672, hole=3.5):
        self.contour = None
        self.name = "arcpattern"
        self.w = w
        self.fh = 5.872
        self._n = 0
        self._pt = pt
        self._pt2 = pt2
        self.circle = circle
        self.hole = hole
        self.ptk = rg.Point3d(0, 0, 0)
        self.pt2k = rg.Point3d(0, 0, 0)

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
        print(self.n)
        ln0 = rg.Line(self.pt2, ln1.From)
        pt3 = copy.deepcopy(self.pt2)
        pt3.Transform(self.mr)
        pt6 = self.pt2 + rg.Point3d(0, -self.w, 0)
        pt4 = self.pt2 + rg.Point3d(0, -self.w - self.fh, 0)
        pt5 = pt4 + rg.Point3d(0, -19.067 - (7 - 6.672) + self.fh, 0)
        pt41 = pt4 + rg.Point3d(-self.hole / 2, 0, 0)
        pt42 = pt4 + rg.Point3d(self.hole / 2, 0, 0)
        pt51 = pt5 + rg.Point3d(-self.hole / 2, 0, 0)
        pt52 = pt5 + rg.Point3d(self.hole / 2, 0, 0)

        crv = [

            rg.Circle(pt4, self.hole / 2).ToNurbsCurve(),
            rg.Circle(pt5, self.hole / 2).ToNurbsCurve(),
            rg.Polyline([pt41, pt51, pt52, pt42, pt41]).ToPolylineCurve()]
        ln3 = copy.deepcopy(ln0)
        ln2.Transform(self.mr)
        ln3.Transform(self.mr)
        self.holes = [rg.Curve.CreateBooleanUnion(crv, 0.01)[0].ToNurbsCurve()]
        self.holes.append(rg.Circle(pt6, self.hole / 2).ToNurbsCurve())
        self.contour = rg.Curve.JoinCurves([ln0.ToNurbsCurve(), ln1.ToNurbsCurve(),
                                            rg.Arc(ln1.To, self.circle.PointAt(-0.5), endPoint=ln2.To).ToNurbsCurve(),
                                            ln2.ToNurbsCurve(), ln3.ToNurbsCurve()])[0]

        return Pat(self.contour, self.holes)


class Ptrn:
    def __init__(self, itr):
        self.itr = itr

    def __getitem__(self, itm):
        return self.itr.__getitem__(itm)

    def __setitem__(self, itm, v):
        self.itr.__setitem__(itm, v)

    def __len__(self):
        return len(self.itr)


class PatternSimple:
    def __init__(self, unit, module_length=46, length=1000):
        self.__unit = unit
        self.unit = copy.deepcopy(unit)
        self.u = self.unit.ln
        self.__c = rg.Circle(rg.Point3d(-11.5, 16.9, 0), 1.75).ToNurbsCurve()
        self.circ = copy.deepcopy(self.__c)
        self.module_length = module_length
        self.length = length
        self._len = self.length
        self._hole = self.u.hole
        self._contour = self.u.contour

        self.i = 1

    def __iter__(self):
        return self

    def constrain(self):
        return self._len > 0

    @property
    def transform(self):
        return rg.Transform.Translation(self.module_length, 0, 0)

    def next_transform(self):

        _circ = copy.deepcopy(self.circ)
        _hole = copy.deepcopy(self._hole)

        self.circ.Transform(self.transform)
        for j in self._hole:
            j.Transform(self.transform)

        if self.i % 2 != 0:
            p = Pat(0, [_circ])
            self.i += 1
            return p
        else:
            p = Pat(0, _hole)
            self.i += 1
            return p

    def next(self):
        if self.constrain():
            self._len -= self.module_length
            return self.next_transform()
        else:
            raise StopIteration

    def reload(self):

        self._len = self.length
        self.i = 0

        self.hole = []
        self.contour = []
        self.unit = copy.deepcopy(self.__unit)
        self.u = self.unit.ln
        self._hole = self.u.hole
        self._contour = self.u.contour


from collections import Iterator


class Pattern(Iterator):
    def __init__(self, unit, modl=23, l=1000):
        super(Iterator, self).__init__()
        self.__unit = unit
        self.name = "pattern_arc"
        self.unit = copy.deepcopy(unit)

        self.u = self.unit.ln
        self.modl = modl
        self.__l = l
        self.ln = abs(l // modl)

        self._hole = self.u.hole
        self._contour = self.u.contour

    def __iter__(self):
        return self

    @property
    def trsf(self):
        return rg.Transform.Translation(self.modl, 0, 0)

    def mtr(self):

        p = Pat(copy.deepcopy(self._contour), copy.deepcopy(self._hole))
        self._contour.Transform(self.trsf)

        for j in self._hole:
            j.Transform(self.trsf)

        return p

    def next(self):
        if self.constrain():
            self.ln -= 1
            return self.mtr()
        else:
            raise StopIteration

    def constrain(self):

        return self.ln > 0

    def reload(self):
        self.hole = []
        self.contour = []
        self.unit = copy.deepcopy(self.__unit)
        self.u = self.unit.ln
        self.ln = abs(self.__l // self.modl)
        self._hole = self.u.hole
        self._contour = self.u.contour


class ReversiblePattern(Pattern):
    def __init__(self, unit, modl=23, l=1000):

        Pattern.__dict__["__init__"](self, unit, modl=modl, l=l)

        # Pattern.__init__(self,unit, modl=modl, l=l)
        self._contour.Transform(rg.Transform.Translation(l, 0, 0))

        print self._contour

        for j in self._hole:
            j.Transform(rg.Transform.Translation(l, 0, 0))

        print self._hole

    def next(self):
        if self.constrain():
            self.ln -= 1
            return self.mtr()
        else:
            raise StopIteration

    def constrain(self):
        return self.ln >= -23

    @property
    def trsf(self):
        return rg.Transform.Translation(-self.modl, 0, 0)

    def reload(self):
        Pattern.reload(self)
        self._contour.Transform(rg.Transform.Translation(self.__l, 0, 0))
        print self._contour
        for j in self._hole:
            j.Transform(rg.Transform.Translation(self.__l, 0, 0))


'''def main():
    global x, y, circle

    cog = TT(x, y, circle)
    cu = PatternSimple(cog, 46, 1000)
    cnt = []
    for ii in cu:
        print(ii)
        h = ii[0]
        cnt.append(h)
        try:
            v = ii[1]
            cnt.append(v)
        except:
            pass
    return cnt

if __name__ == "__main__":
    a = main()'''
