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

import imp
import math
import os
import sys

import Rhino.Geometry as rh

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
# print cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype)
cogs = imp.load_module("cogs", cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype))
from functools import wraps

cogs.__init__("cogs", "generic nodule")

from cogs import Pattern, TT

reload(cogs)


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
        object.__init__(self)
        self.fres = self.curve_offset(curve)

    def curve_offset(self, curve):
        crv = rh.Curve.Offset(curve, rh.Plane.WorldXY, -self.side_offset, 0.01, rh.CurveOffsetCornerStyle.
                              None)
        return crv[0]


class Niche(BendSide):
    side_offset = 0.5
    cogs_shift = -1.466

    @property
    def top_part(self):
        p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
        p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
        trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01, rh.CurveOffsetCornerStyle.
                                         None)
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

            if bb == aa == rh.RegionContainment.BInsideA:
                self.hls.extend(h)
                cnt.append(ii.contour)

            else:
                pass

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
            rh.Line(rh.Point3d(0.0, self.cogs_shift, 0.0),
                    rh.Point3d(self.bend_axis.Length, self.cogs_shift, 0.0)).ToNurbsCurve(),
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

        p_one = trg.ClosestPoint(self.fres.PointAtStart)[1]
        p_two = trg.ClosestPoint(self.fres.PointAtEnd)[1]
        trim = trg.Trim(p_one, p_two)

        tt = []

        tt.append(trim)
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

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01, rh.CurveOffsetCornerStyle.
                                         None)
        return self._top_part[0]

    def __init__(self, curve, reverse):
        BendSide.__init__(self, curve)
        self.reverse = reverse


class Bottom(BendSide):
    side_offset = 1.25

    def __init__(self, curve):
        BendSide.__init__(self, curve)


class Panel:

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        if self.type == 0:
            fr = self.side[0].fres.FrameAt(self.side[0].fres.Domain[1])[1]
            bound_plane = rh.Plane(b_r.Min, fr.XAxis, fr.YAxis)
        else:
            fr = self.side[1].fres.FrameAt(self.side[1].fres.Domain[0])[1]
            bound_plane = rh.Plane(b_r.Max, fr.XAxis, fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def top_parts(self):
        top = [self.side[0].top_part.DuplicateCurve(), self.niche.top_part.DuplicateCurve(),
               self.side[1].top_part.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in top]
        return top

    @property
    def fres(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut(self):
        if self.cogs_bend is True:
            side = \
                rh.Curve.JoinCurves(
                    [self.side[0].join, self.niche.join_region[0], self.side[1].join, self.bottom.fres])[0]
            side.Transform(self.bound_plane)

            cut = [side]

            reg = self.niche.join_region[1:]

            for i in reg:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)
        else:
            side = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
            side.Transform(self.bound_plane)
            cut = [side]
        return cut

    @property
    def unroll_dict(self):
        _unroll_dict = {'tag': self.tag, 'unroll': self.unrol_surf, 'frame': {'bb': 0}}
        return _unroll_dict

    def __init__(self, surface, type, cogs_bend, tag):

        self.type = type
        self.cogs_bend = cogs_bend
        self.tag = tag

        self.surf = surface

        self.unrol_surf = rh.Unroller(self.surf).PerformUnroll()[0][0]
        self.edges = self.unrol_surf.Curves3D

        self.gen_side_types()

    def gen_side_types(self):

        if self.type == 0:
            self.niche = Niche(self.edges[0])
            self.bottom = Bottom(self.edges[2])
            self.side = [Side(self.edges[1], True), Side(self.edges[3], False)]

        else:
            self.niche = Niche(self.edges[2])
            self.bottom = Bottom(self.edges[0])
            self.side = [Side(self.edges[1], False), Side(self.edges[3], True)]

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


panel = Panel
