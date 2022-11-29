"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

import os

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
from cogs import Pattern, PatternSimple, ReversiblePattern

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


def divide(crv, dist=100, ofs=15):
    st = crv.ClosestPoint(crv.PointAtLength(ofs))[1]
    end = crv.ClosestPoint(crv.PointAtLength(crv.GetLength() - ofs))[1]
    curve = crv.Trim(st, end)

    num = math.ceil(curve.GetLength() / dist)
    param = curve.DivideByCount(num, True)
    points = [curve.PointAt(i) for i in param]
    return points


def translate(point, crv):
    frame = crv.FrameAt(crv.ClosestPoint(point)[1])[1]
    tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, frame)
    return tr


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
    angle = 30
    length = 35
    cogs_shift = -1.466
    pattern = Pattern
    @property
    def top_part(self):
        p_one = rh.Curve.LengthParameter(self.fres, self.top_offset)
        p_two = rh.Curve.LengthParameter(self.fres, self.fres.GetLength() - self.top_offset)
        trimed = rh.Curve.Trim(self.fres, p_one[1], p_two[1])

        self._top_part = rh.Curve.Offset(trimed, rh.Plane.WorldXY, self.length, 0.01,
                                         rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    def __init__(self, curve, init_cogs=False):
        BendSide.__dict__['__init__'](self, curve)

        self.init_cogs = init_cogs

        self.hls = None
        self._cogs = None
        self._join_brep = None
        self.cog_hole = None

    @property
    def bend_axis(self):
        return self.fres

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
            try:
                bb = rh.Curve.PlanarClosedCurveRelationship(rh.Curve.JoinCurves(br.Curves3D)[0], h[1], rh.Plane.WorldXY,
                                                            0.01)
                if bb == aa == rh.RegionContainment.BInsideA:
                    self.hls.extend(ii.hole)
                    cnt.append(ii.contour)

            except IndexError:
                if aa == rh.RegionContainment.BInsideA:
                    self.hls.extend(ii.hole)
                    cnt.append(ii.contour)

        _cogs.extend(self.hls[2:-2])

        try:
            ccnt = cnt[0:-1]

            for cc in ccnt:
                self.otgib_morph.Morph(cc)
            _cogs.extend(ccnt)
            self._join_brep = br.Faces[0].Split(ccnt, 0.01).GetRegions()[0]
            _cogs.extend(list(self._join_brep.Brep.Faces)[-1].Brep.Edges)


        except TypeError:
            pass
        self._cogs = _cogs

    @property
    def cogs_unit(self):
        if self.init_cogs:
            return self.__class__.pattern(self._cg, 23, self.bend_axis.GetLength())
        else:
            return PatternSimple(self._cg, 46, self.bend_axis.GetLength())

    @property
    def otgib_morph(self):
        self._morph = rh.Morphs.FlowSpaceMorph(
            rh.Line(rh.Point3d(0.0, self.cogs_shift, 0.0),
                    rh.Point3d(self.bend_axis.GetLength(), self.cogs_shift, 0.0)).ToNurbsCurve(),
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
        if self.init_cogs:
            l = list(self._join_brep.Brep.Faces)
            l.sort(key=lambda t: rh.AreaMassProperties.Compute(t).Area, reverse=True)
            trg = l[0].OuterLoop.To3dCurve().Simplify(rh.CurveSimplifyOptions.All, 0.1, 0.01)

            p_one = trg.ClosestPoint(self.fres.PointAtStart)[1]
            p_two = trg.ClosestPoint(self.fres.PointAtEnd)[1]
            trim = trg.Trim(p_one, p_two)
            if trim is None:
                trg.MakeClosed(0.1)
                trim = trg.Trim(p_one, p_two)
            print(p_two, p_one, trim)
        else:
            trim = self.join

        return trim

    @property
    def region_holes(self):
        if self.init_cogs:
            return self.hls[2:-2]
        else:
            return self.hls

    @property
    def cg(self):
        return self._cg

    @cg.setter
    def cg(self, v):
        self._cg = v


class NicheShortened(Niche):
    angle_niche = 45
    angle = 30
    side_offset = niche_shift(angle_niche, BendSide.side_niche, BendSide.met_left_niche)
    length = 35 - niche_shorten(angle_niche, BendSide.side_niche, BendSide.met_left_niche)
    cogs_shift = 0
    pattern = ReversiblePattern

    def __init__(self, curve, init_cogs=False):
        Niche.__dict__['__init__'](self, curve, init_cogs=init_cogs)

    @property
    def region_holes(self):
        if self.init_cogs:
            return self.hls[2:-2]
        else:
            return self.hls


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
            try:
                bb = rh.Curve.PlanarClosedCurveRelationship(rh.Curve.JoinCurves(br.Curves3D)[0], h[1], rh.Plane.WorldXY,
                                                            0.01)
                if bb == aa == rh.RegionContainment.BInsideA:
                    self.hls.extend(ii.hole)
                    cnt.append(ii.contour)

            except IndexError:
                if aa == rh.RegionContainment.BInsideA:
                    self.hls.extend(ii.hole)
                    cnt.append(ii.contour)

        _cogs.extend(self.hls[2:-2])

        try:
            ccnt = cnt[1:-1]

            for cc in ccnt:
                self.otgib_morph.Morph(cc)
            _cogs.extend(ccnt)
            self._join_brep = br.Faces[0].Split(ccnt, 0.01).GetRegions()[0]
            _cogs.extend(list(self._join_brep.Brep.Faces)[-1].Brep.Edges)


        except TypeError:
            pass
        self._cogs = _cogs
class Side(BendSide):
    side_offset = 1.0
    angle = 30

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


class HolesSideOne(Side):

    @property
    def hls(self):
        return self._hls

    @hls.setter
    def hls(self, v):
        self._hls = v

    @property
    def holes_curve(self):
        line = self.top_part.Offset(rh.Plane.WorldXY, -self.length / 2, 0.01,
                                    rh.CurveOffsetCornerStyle.__dict__['None'])[0]
        points = divide(line)

        circ = []
        for i in points:
            p = translate(i, line)
            c = rh.Circle(2.25)
            c.Transform(p)
            circ.append(c.ToNurbsCurve())
        return circ

    def __init__(self, curve, reverse=None, holes=True):
        Side.__dict__['__init__'](self, curve)
        self.reverse = reverse
        self.holes = holes


class HolesSideTwo(Side):

    @property
    def hls(self):
        return self._hls

    @hls.setter
    def hls(self, v):
        self._hls = v

    @property
    def holes_curve(self):
        line = self.top_part.Offset(rh.Plane.WorldXY, -self.length / 2, 0.01,
                                    rh.CurveOffsetCornerStyle.__dict__['None'])[0]
        points = divide(line)

        circ = []
        for i, v in enumerate(points):
            p = translate(v, line)
            if i % 2 == 0:
                c = self.hls.DuplicateCurve()
                c.Transform(p)
                circ.append(c)
            else:
                c = rh.Circle(2.25)
                c.Transform(p)
                circ.append(c.ToNurbsCurve())

        return circ

    def __init__(self, curve, reverse=None):
        Side.__dict__['__init__'](self, curve)
        self.reverse = reverse
        self.holes = None


class Bottom(BendSide):
    side_offset = None

    def __init__(self, curve):
        BendSide.__dict__['__init__'](self, curve)


class BottomPanel(BendSide):
    side_offset = 1.25

    def __init__(self, curve):
        BendSide.__dict__['__init__'](self, curve)


class HeatSchov(BendSide):
    side_offset = 6.3
    fres_offset = 4.0
    length = 23.24
    fres_trim_dist = 7

    @property
    def join(self):
        crv = self.fres_trim()
        sm_tr = self.small_trim()
        one = rh.Line(crv.PointAtStart, self.top_part.PointAtStart).ToNurbsCurve()
        two = rh.Line(crv.PointAtEnd, self.top_part.PointAtEnd).ToNurbsCurve()

        join = rh.Curve.JoinCurves([one, self.top_part, two])[0]
        fillet = rh.Curve.CreateFilletCornersCurve(join, 5.0, 0.1, 0.1)

        self._join = rh.Curve.JoinCurves([sm_tr[0], fillet, sm_tr[1]])
        return self._join[0]

    @property
    def top_part(self):
        crv = self.fres_trim()
        self._top_part = crv.Offset(rh.Plane.WorldXY, self.length, 0.01,
                                          rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._top_part[0]

    @property
    def fres_shift(self):
        self._fres_shift = self.fres.Offset(rh.Plane.WorldXY, self.fres_offset, 0.01,
                                            rh.CurveOffsetCornerStyle.__dict__['None'])
        return self._fres_shift[0]

    def __init__(self, curve):
        BendSide.__dict__['__init__'](self, curve)


    def fres_trim(self):
        p_one = self.fres.LengthParameter(self.fres_trim_dist)[1]
        p_two = self.fres.LengthParameter(self.fres.GetLength() - self.fres_trim_dist)[1]
        tr = self.fres.Trim(p_one, p_two)
        return tr

    def small_trim(self):
        p_one = self.fres.LengthParameter(self.fres_trim_dist)[1]
        p_two = self.fres.LengthParameter(self.fres.GetLength() - self.fres_trim_dist)[1]
        tr_o = self.fres.Trim(self.fres.Domain[0], p_one)
        tr_t = self.fres.Trim(p_two, self.fres.Domain[1])
        return [tr_o, tr_t]


