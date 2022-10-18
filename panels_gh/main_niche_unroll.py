
"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"
try:
    rs=__import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import ghpythonlib.treehelpers as th
import Rhino.Geometry as rh
import math

def angle_ofs(angle, side, met_left):
    ang = math.radians(90/2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad / math.tan(math.radians(angle/2))


def right_angle_ofs(side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad

def niche_offset(angle, side, met_left):
    d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    return d * math.tan(math.radians(angle))

def niche_shorten(angle, side, met_left):
    d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    return d / math.cos(math.radians(angle))


class BendSide:
    side_offset = 0.5
    angle = 30
    angle_niche = 45
    side_niche = 0.3
    met_left_niche = 0.5
    length = 35 - niche_shorten(angle_niche, side_niche, met_left_niche)

    @property
    def top_offset(self):
        self._top_offset = self.length / math.tan(math.radians(self.angle))
        return self._top_offset

    @property
    def top_part(self):
        return self._top_part

    @property
    def join(self):
        one = rh.Line(self.fres.PointAtStart, self.top_part.PointAtStart).ToNurbsCurve()
        two = rh.Line(self.fres.PointAtEnd, self.top_part.PointAtEnd).ToNurbsCurve()
        self._join = rh.Curve.JoinCurves([one, self.top_part, two])
        return self._join[0]

    def __init__(self, curve):
        self.fres = self.curve_offset(curve)

    def curve_offset(self, curve):
        if self.side_offset is not None:
            crv = rh.Curve.Offset(curve, rh.Plane.WorldXY, -self.side_offset, 0.01, rh.CurveOffsetCornerStyle.__dict__['None'])
            return crv[0]
        else:
            return curve


class Niche(BendSide):
    angle_niche = 45
    side_niche = 0.3
    met_left_niche = 0.5
    side_offset = niche_offset(angle_niche, side_niche, met_left_niche) + (angle_ofs(angle_niche, side_niche, met_left_niche)-right_angle_ofs(side_niche, met_left_niche)) + 0.5

    @property
    def top_part(self):
        p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
        p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
        trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01, rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    def __init__(self, curve):
        BendSide.__init__(self, curve)


class Side(BendSide):
    side_offset = 0.5

    @property
    def top_part(self):
        if self.reverse is False:
            p_one = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
            trimed = rh.Curve.Trim(self.fres, self.fres.Domain[0], p_one[1])
        else:
            p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
            trimed = rh.Curve.Trim(self.fres, p_one[1], self.fres.Domain[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01, rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    def __init__(self, curve, reverse):
        BendSide.__init__(self, curve)
        self.reverse = reverse


class Bottom(BendSide):
    side_offset = None

    def __init__(self, curve):
        BendSide.__init__(self, curve)


class Panel:

    @property
    def fres(self):
        self._fres = self.niche.fres
        return self._fres

    @property
    def cut(self):
        self._cut = [self.side[0].fres, self.niche.join, self.side[1].fres, self.bottom.fres]
        return self._cut

    def __init__(self, surface):


        self.surf = surface

        self.unrol_surf = rh.Unroller(self.surf).PerformUnroll()[0][0]
        self.edges = self.unrol_surf.Curves3D

        self.side_types()

    def side_types(self):
        self.niche = Niche(self.edges[3])
        self.bottom = Bottom(self.edges[1])
        self.side = [Side(self.edges[0], True), Side(self.edges[2], False)]


        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self.side_types):
            param = []
            for ind, val in enumerate(self.side_types):
                if i != ind:
                    inters = rs.CurveCurveIntersection(v.fres, val.fres)
                    if inters is not None:
                        param.append(inters[0][5])
            param = sorted(param)

            trimed = rh.Curve.Trim(v.fres, param[0], param[1])
            v.fres = trimed




panel = []
fres = []
cut = []

for p  in panels:
    pan = Panel(p)
    panel.append(pan)
    fres.append(pan.fres)
    cut.append(pan.cut)




fres = th.list_to_tree(fres)
cut = th.list_to_tree(cut)