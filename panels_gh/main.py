
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


import Rhino.Geometry as rh
import math


class BendSide:
    side_offset = 0.5
    angle = 30
    length = 35

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
        crv = rh.Curve.Offset(curve, rh.Plane.WorldXY, -self.side_offset, 0.01, rh.CurveOffsetCornerStyle.None)
        return crv[0]


class Niche(BendSide):
    side_offset = 0.5

    @property
    def top_part(self):
        p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
        p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
        trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01, rh.CurveOffsetCornerStyle.None)
        return self._top_part[0]

    def __init__(self, curve):
        BendSide.__init__(self, curve)


class Side(BendSide):
    side_offset = 1.0

    @property
    def top_part(self):
        if self.reverse is False:
            p_one = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
            trimed = rh.Curve.Trim(self.fres, self.fres.Domain[0], p_one[1])
        else:
            p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
            trimed = rh.Curve.Trim(self.fres, p_one[1], self.fres.Domain[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01, rh.CurveOffsetCornerStyle.None)
        return self._top_part[0]

    def __init__(self, curve, reverse):
        BendSide.__init__(self, curve)
        self.reverse = reverse


class Schov(BendSide):
    side_offset = 1.25

    def __init__(self, curve):
        BendSide.__init__(self, curve)


class Panel:

    @property
    def fres(self):
        self._fres = [self.side[0].fres, self.niche.fres, self.side[1].fres]
        return self._fres

    @property
    def cut(self):
        self._cut = [self.side[0].join, self.niche.join, self.side[1].join, self.schov.fres]
        return self._cut

    def __init__(self, surface, type):

        self.type = type

        self.surf = surface
        self.unrol_surf = rh.Unroller(self.surf).PerformUnroll()[0][0]
        self.edges = self.unrol_surf.Curves3D

        self.side_types()

    def side_types(self):

        if self.type == 0:
            self.niche = Niche(self.edges[0])
            self.schov = Schov(self.edges[2])
            self.side = [Side(self.edges[1], True), Side(self.edges[3], False)]

        else:
            self.niche = Niche(self.edges[2])
            self.schov = Schov(self.edges[0])
            self.side = [Side(self.edges[1], False), Side(self.edges[3], True)]

        self.side_types = [self.niche, self.schov, self.side[0], self.side[1]]
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


class FramePanel:

    @property
    def frame_offset(self):
        ofs = []
        for i, v in enumerate(self.panel.fres):
            if i !=2:
                c = rh.Curve.Offset(v, rh.Plane.WorldXY, 45, 0.01, rh.CurveOffsetCornerStyle.Sharp)[0]
            else:
                c = rh.Curve.Offset(v, rh.Plane.WorldXY, 40, 0.01, rh.CurveOffsetCornerStyle.Sharp)[0]
            if i == 1:
                ofs.append(rh.Curve.Extend(c, rh.Interval(c.Domain[0] - 200, c.Domain[1] + 200)))
            elif i==0:
                ofs.append(rh.Curve.Extend(c, rh.Interval(c.Domain[0] - 200, c.Domain[1])))
            else:
                ofs.append(rh.Curve.Extend(c, rh.Interval(c.Domain[0], c.Domain[1] + 200)))
        self._frame_offset = rh.Curve.JoinCurves(self.intersect(ofs))[0]
        return self._frame_offset

    def __init__(self, panel):
        self.panel = panel

    def cut(self):
        st = self.panel.niche.top_part.PointAtEnd
        en = self.panel.side[0].top_part.PointAtStart
        crv = rh.Line.ToNurbsCurve(rh.Line(st, en))
        p = self.panel.niche.fres.PointAtEnd
        crv_d = crv.PointAtLength(rh.Curve.DivideByCount(crv, 2, False)[0])
        dist = rh.Point3d.DistanceTo(p, crv_d) + 10
        line = crv.Offset(rh.Plane.WorldXY, dist, 0.01, rh.CurveOffsetCornerStyle.Sharp)[0]
        return line


    def bound_rec(self):
        param = 30
        rec_max = rh.PolyCurve.GetBoundingBox(self.frame_offset, rh.Plane.WorldXY).Max
        rec_min = rh.PolyCurve.GetBoundingBox(self.frame_offset, rh.Plane.WorldXY).Min
        rect = rh.Rectangle3d(rh.Plane.WorldXY, rh.Point3d(rec_min[0]-param, rec_min[1]-param, 0), rh.Point3d(rec_max)).ToNurbsCurve()
        inters = rs.CurveCurveIntersection(rect, self.frame_offset)
        trimed = rh.Curve.Trim(rect, inters[1][5], inters[0][5])
        return rh.Curve.JoinCurves([trimed, self.frame_offset])

    def intersect(self, vals):
        res = []
        for i, v in enumerate(vals):
            if i == 2:
                pass
            else:
                param = []
                for ind, val in enumerate(vals):
                    if i != ind:
                        inters = rs.CurveCurveIntersection(v, val)
                        if inters is not None:
                            param.append(inters[0][5])
                param = sorted(param)
                if len(param) != 1:
                    trimed = rh.Curve.Trim(v, param[0], param[1])
                else:
                    trimed = rh.Curve.Trim(v, param[0], v.Domain[1])
                res.append(trimed)
        return res


try:
    p_left = Panel(surf_left, 1)
    left_fres = p_left.fres
    left_cut = p_left.cut

    p_right = Panel(surf_right, 0)
    right_fres = p_right.fres
    right_cut = p_right.cut

    fr = FramePanel(p_right)
    frame = fr.frame_offset
    perp = fr.cut()
    rec = fr.bound_rec()
except AttributeError:
    try:
        p_left = Panel(surf_left, 1)
        left_fres = p_left.fres
        left_cut = p_left.cut
    except AttributeError:
        try:
            p_right = Panel(surf_right, 0)
            right_fres = p_right.fres
            right_cut = p_right.cut
        except:
            pass


