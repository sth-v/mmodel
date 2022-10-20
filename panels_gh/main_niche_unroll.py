"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import os
import types

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import Rhino.Geometry as rh
import math
import sys
import imp

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    PWD = os.getenv("HOME") + "/mmodel/panels_gh"
    sys.path.extend(
        [os.getenv("HOME") + "/mmodel/panels_gh", os.getenv("HOME") + "/mmodel/panels_gh/cogs"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
# print cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype)
cogs = imp.load_module("cogs", cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype))
from functools import wraps

cogs.__init__("cogs", "generic nodule")
print cogs
from cogs import Pattern, TT

reload(cogs)


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


def niche_shorten(angle, side, met_left):
    # d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    # return d / math.cos(math.radians(angle))
    return angle_ofs(angle, side, met_left) - 0.5 + 0.25


def morph_decore(fun):
    @wraps(fun)
    def wrp(slf, *args, **kwargs):
        geom = fun(*args, **kwargs)
        try:
            for g in geom:
                if slf.otgib_morph.Morph(g):
                    continue
        except:
            slf.otgib_morph.Morph(geom)
            return

        return geom

    return wrp


class BendSide(object):
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
        # type: () -> rh.Curve
        one = rh.Line(self.fres.PointAtStart, self.top_part.PointAtStart).ToNurbsCurve()
        two = rh.Line(self.fres.PointAtEnd, self.top_part.PointAtEnd).ToNurbsCurve()
        self._join = rh.Curve.JoinCurves([one, self.top_part, two])
        return self._join[0]

    def __init__(self, curve):
        object.__init__(self)
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
        self.hls = None
        self._cogs = None
        self._join_brep = None

    @property
    def bend_axis(self):
        # type: () -> rh.Line
        return rh.Line(self.join.PointAtStart, self.join.PointAtEnd)

    @property
    def join_cp(self):
        crv = self.bend_surf
        return crv

    @property
    def bend_surf(self):
        # type: () -> rh.NurbsSurface

        return rh.NurbsSurface.CreateRuledSurface(self.top_part, self.bend_axis.ToNurbsCurve())

    @property
    def cogs(self):
        return self._cogs

    def generate_cogs(self):
        _cogs = []
        cu = self.cogs_unit
        br = self.join_cp.ToBrep()
        cr3d = list(br.Curves3D)
        self.hls = []
        cnt = []
        for ii in cu:

            h = self.choles(self, ii)
            aa = rh.Curve.PlanarClosedCurveRelationship(rh.Curve.JoinCurves(br.Curves3D)[0], h[0], rh.Plane.WorldXY,
                                                        0.01)
            bb = rh.Curve.PlanarClosedCurveRelationship(rh.Curve.JoinCurves(br.Curves3D)[0], h[1], rh.Plane.WorldXY,
                                                        0.01)
            print aa, bb
            if bb == aa == rh.RegionContainment.BInsideA:
                self.hls.extend(h)
                cnt.append(ii.contour)
                print "cul"
            else:
                print "аагсл"
        _cogs.extend(self.hls[2:-2])
        ccnt = cnt[0:-1]
        for cc in ccnt:
            self.otgib_morph.Morph(cc)

        self._join_brep = br.Faces[0].Split(ccnt, 0.01).GetRegions()[0]

        _cogs.extend(list(self._join_brep.Brep.Faces)[-1].Brep.Edges)
        self._cogs = _cogs

    @property
    def cogs_unit(self):
        # type: () -> Pattern

        return Pattern(self._cg, 23, self.bend_axis.Length)

    @property
    def otgib_morph(self):
        # type: () -> rh.SpaceMorph
        self._morph = rh.Morphs.FlowSpaceMorph(
            rh.Line(rh.Point3d(0.0, 0.0, 0.0), rh.Point3d(self.bend_axis.Length, 0.0, 0.0)).ToNurbsCurve(),
            self.bend_axis.ToNurbsCurve(), True, False, True
        )
        return self._morph

    @morph_decore
    def choles(self, geoms):
        # type: (TT) -> types.ListType[ rh.Curve]
        return geoms.hole

    @morph_decore
    def ccontour(self, geoms):
        return geoms.contour

    @property
    def join_region(self):
        # type: () -> rh.CurveBooleanRegions

        # j = rh.Brep.JoinBreps(rh.Brep.CreatePlanarBreps(cg, 0.1), 0.1)

        # brps = self.join_cp.Split(j, 0.1)

        # brep_regions = brps
        l = list(self._join_brep.Brep.Faces)
        l.sort(key=lambda t: rh.AreaMassProperties.Compute(t).Area, reverse=True)
        trg = l[0].OuterLoop.To3dCurve().Simplify(rh.CurveSimplifyOptions.All, 0.1, 0.01)

        tt = []

        tt.append(trg)
        tt.extend(self.hls[2:-2])

        return tt

    @property
    def cg(self):
        return self._cg

    @cg.setter
    def cg(self, v):
        self._cg = v


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


class SideBackNiche(BendSide):
    side_offset = 1.0

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


class BackNiche:
    @property
    def fres(self):
        self._fres = [self.side[0].fres, self.side[1].fres]
        return self._fres

    @property
    def cut(self):
        self._cut = [self.side[0].join, self.top.fres, self.side[1].join, self.bottom.fres]
        return self._cut

    def __init__(self, surf):
        self.surf = surf
        self.extend = self.extend_surf()

        self.unrol_surf = rh.Unroller(self.surf).PerformUnroll()[0][0]

        self.edges = self.unrol_surf.Curves3D
        self.side_types()

    def side_types(self):

        self.top = Bottom(self.edges[1])
        self.bottom = Bottom(self.edges[3])
        self.side = [SideBackNiche(self.edges[0]), SideBackNiche(self.edges[2])]

        self.side_types = [self.top, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self.side_types):
            old = v.fres.Domain
            v.fres = v.fres.Extend(rh.Interval(old[0] - 15, old[1] + 15))
            param = []
            for ind, val in enumerate(self.side_types):
                if i != ind:
                    old = val.fres.Domain
                    new = val.fres.Extend(rh.Interval(old[0] - 15, old[1] + 15))
                    inters = rs.CurveCurveIntersection(v.fres, new)
                    if inters is not None:
                        param.append(inters[0][5])
            param = sorted(param)

            trimed = rh.Curve.Trim(v.fres, param[0], param[1])
            v.fres = trimed

    def extend_surf(self):
        surf = rh.Surface.Duplicate(self.surf)
        interv = surf.Domain(0)
        interv = rh.Interval(interv[0] - 50, interv[1] + 50)

        surf.Extend(0, interv)
        extr = rh.Surface.ToBrep(surf)

        return extr


class NicheSide(object):

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

    @property
    def fres(self):
        self._fres = [self.side[0].fres, self.niche.fres, self.side[1].fres]
        return self._fres

    @property
    def cut(self):
        self._cut = [self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres]
        return self._cut

    @property
    def grav(self):
        d = self.mark_ribs
        d.append(self.mark_back)
        self._grav = d
        return self._grav

    def __init__(self, surface, tip, rib, back):
        object.__init__(self)

        self.surf = surface
        self.type = tip

        self.rebra = Ribs(rib)
        self.back_side = BackNiche(back)

        self.intersections = self.unroll_intersection()

        unrol = rh.Unroller(self.surf)
        unrol.AddFollowingGeometry(curves=self.intersections)
        self.unrol = unrol.PerformUnroll()

        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Edges
        self.gen_side_types()

    def ribs_offset(self):
        r = self.unrol[1][0:len(self.unrol[1]) - 1]
        ofset_rebra = []
        for i in r:
            if i.GetLength() > 10:
                ofs_one = i.OffsetOnSurface(self.unrol_surf.Faces[0], 1.5, 0.1)
                ofs_two = i.OffsetOnSurface(self.unrol_surf.Faces[0], -1.5, 0.1)
                ofset_rebra.append(ofs_one[0])
                ofset_rebra.append(ofs_two[0])
        return ofset_rebra

    def unroll_intersection(self):
        r_inters = self.rebra_intersect()
        b_inters = self.back_intersect()

        r_inters.append(b_inters)
        return r_inters

    def gen_side_types(self):
        if self.type == 0 or self.type == 1:
            self.niche = Niche(self.edges[0])
            self.bottom = Bottom(self.edges[2])
            self.side = [Side(self.edges[1], True), Side(self.edges[3], False)]
        else:
            self.niche = Niche(self.edges[2])
            self.bottom = Bottom(self.edges[0])
            self.side = [Side(self.edges[1], True), Side(self.edges[3], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self.side_types):
            old = v.fres.Domain
            v.fres = v.fres.Extend(rh.Interval(old[0] - 15, old[1] + 15))
            param = []
            for ind, val in enumerate(self.side_types):
                if i != ind:
                    old = val.fres.Domain
                    new = val.fres.Extend(rh.Interval(old[0] - 15, old[1] + 15))
                    inters = rs.CurveCurveIntersection(v.fres, new)
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


# ptr = TT(globals()['x'], globals()['y'], globals()['circle'])

niche_side = NicheSide
back_niche = BackNiche
ribs = Ribs
