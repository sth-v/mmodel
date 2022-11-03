"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

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
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
cogs = imp.load_module("cogs", cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype))
from functools import wraps

cogs.__init__("cogs", "generic module")
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
    return angle_ofs(angle, side, met_left) - 0.5 + 0.25


def niche_shift(angle_niche, side_niche, met_left_niche):
    res = niche_offset(angle_niche, side_niche, met_left_niche) + (angle_ofs(angle_niche, side_niche, met_left_niche)
                                                                   - right_angle_ofs(side_niche, met_left_niche)) + 0.5
    return res


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
    side_offset = 0.5
    length = 35
    cogs_shift = -1.466

    @property
    def top_part(self):
        p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
        p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
        trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01,
                                         rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    def __init__(self, curve):
        BendSide.__dict__['__init__'](self, curve)

        self.hls = None
        self._cogs = None
        self._join_brep = None

    @property
    def bend_axis(self):
        return rh.Line(self.join.PointAtStart, self.join.PointAtEnd)

    @property
    def join_cp(self):
        crv = self.bend_surf
        return crv

    @property
    def bend_surf(self):
        return rh.NurbsSurface.CreateRuledSurface(self.top_part, self.bend_axis.ToNurbsCurve())

    @property
    def cogs(self):
        return self._cogs

    def generate_cogs(self):
        _cogs = []
        cu = self.cogs_unit
        br = self.join_cp.ToBrep()
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
        return Pattern(self._cg, 23, self.bend_axis.Length)

    @property
    def otgib_morph(self):
        self._morph = rh.Morphs.FlowSpaceMorph(
            rh.Line(rh.Point3d(0.0, 0.0, 0.0), rh.Point3d(self.bend_axis.Length, self.cogs_shift, 0.0)).ToNurbsCurve(),
            self.bend_axis.ToNurbsCurve(), True, False, True
        )
        return self._morph

    @morph_decore
    def choles(self, geoms):
        return geoms.hole

    @morph_decore
    def ccontour(self, geoms):
        return geoms.contour

    @property
    def join_region(self):

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


class NicheShortened(Niche):
    angle_niche = 45
    side_offset = niche_shift(angle_niche, BendSide.side_niche, BendSide.met_left_niche)
    length = 35 - niche_shorten(angle_niche, BendSide.side_niche, BendSide.met_left_niche)
    cogs_shift = 0

    def __init__(self, curve):
        Niche.__dict__['__init__'](self, curve)


class Side(BendSide):
    side_offset = 1.0

    @property
    def top_part(self):
        if self.reverse is not None:
            if self.reverse is False:
                p_one = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
                trimed = rh.Curve.Trim(self.fres, self.fres.Domain[0], p_one[1])
            else:
                p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
                trimed = rh.Curve.Trim(self.fres, p_one[1], self.fres.Domain[1])
        else:
            p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
            p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
            trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01,
                                         rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    def __init__(self, curve, reverse=None):
        BendSide.__dict__['__init__'](self, curve)
        self.reverse = reverse


class Bottom(BendSide):
    side_offset = None

    def __init__(self, curve):
        BendSide.__dict__['__init__'](self, curve)