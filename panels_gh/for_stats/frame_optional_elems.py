"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

import copy

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import imp
import os

import sys

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    os.environ["MMODEL_DIR"] = "/Users/andrewastakhov/PycharmProjects/mmodel"
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs",
         os.getenv("MMODEL_DIR") + "/panels_gh/tagging"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
cogs = imp.load_module("cogs", cogsfile, PWD, (cogssuffix, cogsmode, cogstype))
# sys.path.extend(["/Users/sofyadobycina/Documents/GitHub/mmodel/panels_gh"])
import cogs

reload(cogs)

# taggingfile, taggingfilename, (taggingsuffix, taggingmode, taggingtype) = imp.find_module("tagging", path=[PWD+"/panels_gh"])
# tagging = imp.load_module("tagging", taggingfile, PWD, (taggingsuffix, taggingmode, taggingtype))
# import tagging
# reload(tagging)
# %start gh-py template


# %start script

import Rhino.Geometry as rh

import rhinoscriptsyntax as rs

import math
import ghpythonlib.treehelpers as th


def offset(crv, ofs_dist, extend=None):
    c = rh.Curve.Offset(crv, rh.Plane.WorldXY, ofs_dist, 0.01, rh.CurveOffsetCornerStyle.Sharp)[0]
    if extend is not None:
        c = rh.Curve.Extend(c, rh.Interval(extend[0], extend[1]))
    return c


def bound_rec(crv):
    join = rh.Curve.JoinCurves(crv)[0]
    bound_rec = rh.PolyCurve.GetBoundingBox(join, rh.Plane.WorldXY)
    return bound_rec


def intersect(values):
    res = []
    for i, v in enumerate(values):
        param = []
        for ind, val in enumerate(values):
            if i != ind:
                inters = rs.CurveCurveIntersection(v, val)
                if inters is not None:
                    param.append(inters[0][5])
        param = sorted(param)
        if len(param) != 1 and i != 0:
            trimed = rh.Curve.Trim(v, param[0], param[1])
        elif i == len(values) - 1:
            trimed = rh.Curve.Trim(v, v.Domain[0], param[0])
        elif i == 0 and len(param) != 1:
            trimed = rh.Curve.Trim(v, param[1], v.Domain[1])
        else:
            trimed = rh.Curve.Trim(v, param[0], v.Domain[1])
        res.append(trimed)
    return res


class FramePanel:
    bottom = 45
    top = 35
    diag = 20

    bottom_rec = 30
    side_rec = 30

    p_niche = p_niche
    n_niche = n_niche
    b_niche = b_niche

    rect = rh.Rectangle3d(rh.Plane.WorldXY, rh.Point3d(-2.5, -2, 0), rh.Point3d(2.5, 12, 0)).ToNurbsCurve()

    @property
    def frame_offset(self):
        fr_one = self.frame_inner()[0]
        p_o = self.bound_frame.ClosestPoint(fr_one.PointAtStart)[1]
        p_t = self.bound_frame.ClosestPoint(fr_one.PointAtEnd)[1]
        inters = self.bound_frame.Trim(p_o, p_t)
        self._frame_offset = rh.Curve.JoinCurves([inters, fr_one])[0]
        return self._frame_offset

    @property
    def frame_all(self):
        self._frame_all = rh.Curve.JoinCurves(self.all_offset())
        return self._frame_all

    @property
    def bound_frame(self):
        rec = bound_rec(self.frame_all)
        min_transl = rh.Point3d(rec.Min[0] - self.side_rec, rec.Min[1] - self.bottom_rec, 0)
        bound_frame = rh.Rectangle3d(rh.Plane.WorldXY, min_transl, rec.Max)
        self._bound_frame = bound_frame.ToNurbsCurve()
        return self._bound_frame

    @property
    def bound_frame_r(self):
        rec = bound_rec(self.frame_all)
        min_transl = rh.Point3d(rec.Min[0] - self.side_rec, rec.Min[1] - self.bottom_rec, 0)

        return rh.Rectangle3d(rh.Plane.WorldXY, min_transl, rec.Max)

    @property
    def rec(self):
        rec = bound_rec(self.frame_all)
        return rec

    '''@property
    def region(self):
        if self.panel.__class__.__name__ != 'BackNiche':
            if self.cogs is True:
                elems = self.cogs_points(2) + self.simple_points(0)
            else:
                elems = self.simple_points(2, niche=1) + self.simple_points(0)
        else:
            elems = self.simple_points(1, niche=1) + self.simple_points(0)

        elems.append(self.frame_offset)
        elems.append(self.panel.cut[0])
        new = list(rh.Curve.CreateBooleanUnion(elems, 0.1))
        new.extend(self.panel.cut[1:])
        return new'''

    @property
    def all_elems(self):

        #a = [self.region, self.panel.fres]
        a = [self.frame_offset, self.panel.cut[0], rh.Curve.JoinCurves(self.panel.fres)[0]]
        '''try:
            g = []
            for i in self.panel.grav[0]:
                for j in i:
                    g.append(j)
            try:
                g.append(self.panel.grav[1])
            except:
                pass
            a.append(g)

        except AttributeError:
            pass'''

        return a

    def __init__(self, panel, nich_ofs):
        self.niche = nich_ofs
        self.panel = panel

        try:
            self.cogs = self.panel.cogs_bend
            self.type = self.panel.type

            self.p_niche = self.panel.fres[1]

            if self.type == 1:
                self.p_bottom = self.panel.fres[2]
            else:
                self.p_bottom = self.panel.fres[0]

        except AttributeError:
            self.p_niche = self.panel.bottom.fres
            self.p_bottom = self.panel.fres[0]

    @property
    def unroll_dict_f(self):
        return {
            "data": copy.deepcopy(self.panel.unroll_dict),
            "frame": self.bound_frame.ToNurbsCurve()

        }

    def tr_rect(self, p, ind, spec=None):
        crv = self.all_offset()[ind]
        frame = crv.FrameAt(crv.ClosestPoint(p)[1])[1]
        if frame.YAxis[0] < 0 and spec is None:
            frame = rh.Plane(frame.Origin, frame.XAxis, -frame.YAxis)
        else:
            frame = rh.Plane(frame.Origin, frame.XAxis, frame.YAxis)
        tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, frame)
        rect = self.rect.DuplicateCurve()
        rect.Transform(tr)
        return rect

    def cogs_points(self, side):
        rectang = []
        for i in self.panel.cut[2:-1:8]:
            b = i.TryGetCircle(0.1)[1].Center
            rect = self.tr_rect(b, side)
            rectang.append(rect)

        b = self.panel.cut[-1].TryGetCircle(0.1)[1].Center
        rect = self.tr_rect(b, side)
        rectang.append(rect)
        return rectang

    def simple_points(self, side, niche=None):
        if self.panel.__class__.__name__ != 'BackNiche':
            if niche is not None:
                crv = self.panel.top_parts[1]
            elif self.type == 0:
                crv = self.panel.top_parts[0]
            else:
                crv = self.panel.top_parts[2]
        else:
            if niche is not None:
                crv = self.panel.bottom.fres
            else:
                crv = self.panel.top_parts

        st = crv.ClosestPoint(crv.PointAtLength(7.5))[1]
        end = crv.ClosestPoint(crv.PointAtLength(crv.GetLength() - 7.5))[1]
        n_crv = crv.Trim(st, end)

        num = math.ceil(n_crv.GetLength() / 100)
        param = n_crv.DivideByCount(num, True)
        points = [n_crv.PointAt(i) for i in param]

        if self.panel.__class__.__name__ != 'BackNiche':
            if self.type == 1 and niche is None:
                rectang = [self.tr_rect(i, side, spec=True) for i in points]
            else:
                rectang = [self.tr_rect(i, side) for i in points]
        else:
            rectang = [self.tr_rect(i, side) for i in points]
        return rectang

    def all_offset(self):
        niche = offset(self.p_niche, self.niche,
                       extend=[self.p_niche.Domain[0] + 200, self.p_niche.Domain[1] - 200])
        if niche is None:
            niche = offset(self.p_niche, self.niche,
                           extend=[self.p_niche.Domain[0] - 200, self.p_niche.Domain[1] + 200])

        bottom = offset(self.p_bottom, self.bottom,
                        extend=[self.p_bottom.Domain[0] - 200, self.p_bottom.Domain[1]])
        top_s = self.top_side()
        top = offset(self.top_side(), self.top, extend=[top_s.Domain[0], top_s.Domain[1] + 200])

        try:
            diag = offset(self.diag_side(), self.diag)
            all_offset = [bottom, diag, niche, top]
        except AttributeError:
            all_offset = [bottom, niche, top]

        all_offset = intersect(all_offset)
        return all_offset

    def top_side(self):
        if self.panel.__class__.__name__ != 'BackNiche':
            bound = bound_rec(self.panel.fres)
        else:
            l = self.panel.fres
            l.append(self.p_niche)
            bound = bound_rec(l)

        top_side = bound.GetEdges()[2]
        return top_side.ToNurbsCurve()

    def diag_side(self):

        if self.type == 0:
            st = self.panel.top_parts[1].PointAtEnd
            en = self.panel.top_parts[0].PointAtStart
            p = self.p_niche.PointAtEnd
        else:
            st = self.panel.top_parts[1].PointAtEnd
            en = self.panel.top_parts[2].PointAtStart
            p = self.p_niche.PointAtEnd

        crv = rh.Line.ToNurbsCurve(rh.Line(st, en))

        crv_d = crv.PointAtLength(rh.Curve.DivideByCount(crv, 2, False)[0])
        self.diag = rh.Point3d.DistanceTo(p, crv_d) + 10
        return crv

    def frame_inner(self):
        offset = rh.Curve.JoinCurves(self.all_offset()[0:-1])[0]
        crv = rh.Line(offset.PointAtEnd, rh.Point3d(offset.PointAtEnd[0], offset.PointAtEnd[1] - self.bottom + 15,
                                                    offset.PointAtEnd[2])).ToNurbsCurve()
        frame_offset = rh.Curve.JoinCurves([offset, crv])
        return frame_offset


class MarkerDict:
    def __init__(self, input_dict):
        self.__dict__.update(input_dict)

    def GetString(self):
        return self.__dict__.__str__()



frame = FramePanel