"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"
try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import ghpythonlib.treehelpers as th
import Rhino.Geometry as rh
import math


def angle_ofs(angle, side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad / math.tan(math.radians(angle / 2))


def right_angle_ofs(side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad


def niche_offset(angle, side, met_left):
    d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    return d * math.tan(math.radians(angle))


# так получается так как нижний отгиб короче
def niche_shorten(angle, side, met_left):
    # d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    # return d / math.cos(math.radians(angle))
    return angle_ofs(angle, side, met_left) - 0.5 + 0.25


class BendSide:
    side_offset = 0.5
    angle = 30
    angle_niche = 45
    side_niche = 0.3
    met_left_niche = 0.5
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
        if self.side_offset is not None:
            crv = rh.Curve.Offset(curve, rh.Plane.WorldXY, -self.side_offset, 0.01,
                                  rh.CurveOffsetCornerStyle.__dict__['None'])
            return crv[0]
        else:
            return curve


class Niche(BendSide):
    angle_niche = 45
    side_niche = 0.3
    met_left_niche = 0.5
    side_offset = niche_offset(angle_niche, side_niche, met_left_niche) + (
                angle_ofs(angle_niche, side_niche, met_left_niche) - right_angle_ofs(side_niche, met_left_niche)) + 0.5
    length = 35 - niche_shorten(angle_niche, side_niche, met_left_niche)

    @property
    def top_part(self):
        p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
        p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
        trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01,
                                         rh.CurveOffsetCornerStyle.__dict__['None'])
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

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01,
                                         rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    def __init__(self, curve, reverse):
        BendSide.__init__(self, curve)
        self.reverse = reverse


class Bottom(BendSide):
    side_offset = None

    def __init__(self, curve):
        BendSide.__init__(self, curve)


class Ribs:
    def __init__(self, surf_list):
        self.surf = surf_list

        self.extend = []
        for i in range(self.__len__()):
            self.i = i
            ext = self.extend_surf()
            self.extend.append(ext)

    def __len__(self):
        return len(self.surf)

    def extend_surf(self):
        surf = self.surf[self.i]
        interv = surf.Domain(1)
        interv = rh.Interval(interv[0] - 50, interv[1] + 50)

        surf.Extend(1, interv)
        extr = rh.Surface.ToBrep(surf)

        return extr


class BackSurface:
    def __init__(self, surf):
        self.surf = surf
        self.extend = self.extend_surf()

        self.unrol_surf = rh.Unroller(self.surf).PerformUnroll()[0][0]

        self.edges = self.unrol_surf.Curves3D
        self.side_types()

    def side_types(self):

        self.top = Niche(self.edges[0])
        self.bottom = Bottom(self.edges[2])
        self.side = [Side(self.edges[1], False), Side(self.edges[3], True)]

        self.side_types = [self.top, self.bottom, self.side[0], self.side[1]]
        #self.intersect()

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

    def extend_surf(self):
        surf = self.surf
        interv = surf.Domain(0)
        interv = rh.Interval(interv[0] - 50, interv[1] + 50)

        surf.Extend(0, interv)
        extr = rh.Surface.ToBrep(surf)

        return extr


class NicheSide:

    @property
    def fres(self):
        self._fres = [self.side[0].fres, self.niche.fres, self.side[1].fres]
        return self._fres

    @property
    def cut(self):
        self._cut = [self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres]
        return self._cut

    @property
    def mark_ribs(self):
        self._mark_ribs = self.ribs_offset()
        return self._mark_ribs

    @property
    def mark_back(self):
        one = self.unrol[1][-1].LengthParameter(1)[1]
        two = self.unrol[1][-1].LengthParameter(self.unrol[1][-1].GetLength() - 1)[1]
        self._mark_back = self.unrol[1][-1].Trim(one, two)

        return self._mark_back


    def __init__(self, surface, tip, rib, back):

        self.surf = surface
        self.type = tip

        self.rebra = Ribs(rib)
        self.back_side = BackSurface(back)

        self.intersections = self.unroll_intersection()

        unrol = rh.Unroller(self.surf)
        unrol.AddFollowingGeometry(curves=self.intersections)
        self.unrol = unrol.PerformUnroll()

        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D
        self.side_types()


    def ribs_offset(self):
        r = self.unrol[1][0:len(self.unrol[1])-1]
        ofset_rebra = []
        for i in r:
            if i.GetLength() > 10:
                ofs_one = i.OffsetOnSurface(self.unrol_surf.Faces[0], 1.5, 0.1)
                ofs_two = i.OffsetOnSurface(self.unrol_surf.Faces[0], -1.5, 0.1)
                ofset_rebra.append([ofs_one[0], ofs_two[0]])
        return ofset_rebra

    def unroll_intersection(self):
        r_inters = self.rebra_intersect()
        b_inters = self.back_intersect()

        r_inters.append(b_inters)
        return r_inters


    def side_types(self):
        if self.type == 0:
            self.niche = Niche(self.edges[2])
            self.bottom = Bottom(self.edges[0])
            self.side = [Side(self.edges[1], False), Side(self.edges[3], True)]
        else:
            self.niche = Niche(self.edges[0])
            self.bottom = Bottom(self.edges[2])
            self.side = [Side(self.edges[1], True), Side(self.edges[3], False)]

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

    def rebra_intersect(self):
        intersect = []
        for i in self.rebra.extend:
            inters = rs.IntersectBreps(self.surf, i, 0.1)
            line = rh.LineCurve(rs.CurveStartPoint(inters[0]), rs.CurveEndPoint(inters[0]))
            intersect.append(line)

        return intersect

    def back_intersect(self):
        inters = rs.IntersectBreps(self.surf, self.back_side.extend, 0.1)
        line = rh.LineCurve(rs.CurveStartPoint(inters[0]), rs.CurveEndPoint(inters[0]))
        return line



panel = []
fres = []
cut = []
b = []
a=[]
for p_r, p_l in zip(panels_right, panels_left):
    pan_r = NicheSide(p_r, 0, rebra, back_side)
    pan_l = NicheSide(p_l, 1, rebra, back_side)
    panel.append(pan_r)
    fres.append(pan_r.fres)
    cut.append(pan_r.cut)
    panel.append(pan_l)
    fres.append(pan_l.fres)
    cut.append(pan_l.cut)
    b.append(pan_r.mark_ribs)
    a.append(pan_r.mark_back)
    # b.append(pan_l.unrol_surf)

fres = th.list_to_tree(fres)
cut = th.list_to_tree(cut)
b = th.list_to_tree(b)
a = th.list_to_tree(a)