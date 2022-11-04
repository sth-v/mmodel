__author__ = "sofyadobycina"

import copy

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import imp
import os

import sys

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/cogs",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_tagging"])
else:
    os.environ["MMODEL_DIR"] = "/Users/andrewastakhov/PycharmProjects/mmodel"
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs",
         os.getenv("MMODEL_DIR") + "/panels_gh/tagging"])


taggingfile, taggingfilename, (taggingsuffix, taggingmode, taggingtype) = imp.find_module("main_tagging", path=[PWD])
main_tagging = imp.load_module("main_tagging", taggingfile, taggingfilename, (taggingsuffix, taggingmode, taggingtype))

main_tagging.__init__("main_tagging", "generic nodule")

import main_tagging
reload(main_tagging)
#%start script

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
cogs = imp.load_module("cogs", cogsfile, PWD, (cogssuffix, cogsmode, cogstype))
# sys.path.extend(["/Users/sofyadobycina/Documents/GitHub/mmodel/panels_gh"])
import cogs
reload(cogs)



import Rhino.Geometry as rh

import rhinoscriptsyntax as rs

import math
import ghpythonlib.treehelpers as th


def offset(crv, ofs_dist, extend=None):
    if ofs_dist != 0:
        c = rh.Curve.Offset(crv, rh.Plane.WorldXY, ofs_dist, 0.01, rh.CurveOffsetCornerStyle.Sharp)[0]
    else:
        c = crv
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

def offset_side(elem, dist, extend='st'):
    if extend == 'st':
        det = offset(elem, dist, extend=[elem.Domain[0] - 200, elem.Domain[1]])
    elif extend == 'e':
        det = offset(elem, dist, extend=[elem.Domain[0], elem.Domain[1]+200])
    elif extend == 'both':
        det = offset(elem, dist, extend=[elem.Domain[0] + 200, elem.Domain[1] - 200])
        if det is None:
            det = offset(elem, dist, extend=[elem.Domain[0] - 200, elem.Domain[1] + 200])
    else:
        det = offset(elem, dist)
    return det

@main_tagging.Framer
@main_tagging.Tagger
class MainFrame:

    rect = rh.Rectangle3d(rh.Plane.WorldXY, rh.Point3d(-2.5, -15, 0), rh.Point3d(2.5, 15, 0)).ToNurbsCurve()

    @property
    def frame_offset(self):
        fr_one = self.frame_inner()[0]
        p_o = self.bound_frame.ClosestPoint(fr_one.PointAtStart)[1]
        p_t = self.bound_frame.ClosestPoint(fr_one.PointAtEnd)[1]
        inters = self.bound_frame.Trim(p_o, p_t)
        self._frame_offset = rh.Curve.JoinCurves([inters, fr_one])[0]
        return self._frame_offset

    @property
    def bound_frame(self):
        rec = bound_rec(self.frame_all())
        min_transl = rh.Point3d(rec.Min[0] - self.side_rec, rec.Min[1] - self.bottom_rec, 0)
        bound_frame = rh.Rectangle3d(rh.Plane.WorldXY, min_transl, rec.Max)
        self._bound_frame = bound_frame.ToNurbsCurve()
        return self._bound_frame

    @property
    def bound_stats(self):
        rec = bound_rec(self.frame_all())
        min_transl = rh.Point3d(rec.Min[0] - self.side_rec, rec.Min[1] - self.bottom_rec, 0)

        return rh.Rectangle3d(rh.Plane.WorldXY, min_transl, rec.Max)

    @property
    def region(self):
        ofs_sides = self.all_offset()
        o, t = ofs_sides[self.bridge[0][0]], ofs_sides[self.bridge[1][0]]
        spec = self.bridge[0][2]

        if self.cogs is True:
            elems = self.cogs_points(o) + self.simple_points(t, self.bridge[1][1])
        else:
            elems = self.simple_points(o, self.bridge[0][1], spec) + self.simple_points(t, self.bridge[1][1], spec)

        elems.append(self.frame_offset)
        elems.append(self.panel.cut[0])
        new = list(rh.Curve.CreateBooleanUnion(elems, 0.1))
        new.extend(self.panel.cut[1:])
        return new

    @property
    def all_elems(self):
        a = [self.region, self.panel.fres]
        if hasattr(self.panel, 'grav'):
            a.append(self.panel.grav)
        else:
            pass
        return a

    def __init__(self, panel):

        self.panel = panel
        self.cogs = self.panel.cogs_bend

        self.__dict__.update(self.panel.frame_dict)

        self.bottom_rec = self.panel.bottom_rec
        self.bend = self.panel.bend_ofs
        self.top = self.panel.top_ofs
        self.niche = self.panel.niche_ofs
        self.side_rec = self.panel.side_rec



    @property
    def unroll_dict_f(self):
        return {"data": copy.deepcopy(self.panel.unroll_dict), "frame": self.bound_frame.ToNurbsCurve()}

    def frame_all(self):
        frame_all = rh.Curve.JoinCurves(self.all_offset())
        return frame_all

    def tr_rect(self, p, crv, spec=None):
        frame = crv.FrameAt(crv.ClosestPoint(p)[1])[1]
        if frame.YAxis[0] < 0 and spec is None:
            frame = rh.Plane(frame.Origin, frame.XAxis, -frame.YAxis)
        else:
            frame = rh.Plane(frame.Origin, frame.XAxis, frame.YAxis)
        tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, frame)
        rect = self.rect.DuplicateCurve()
        rect.Transform(tr)
        return rect

    def cogs_points(self, crv):
        rectang = []
        for i in self.panel.cut[2:-1:8]:
            b = i.TryGetCircle(0.1)[1].Center
            rect = self.tr_rect(b, crv)
            rectang.append(rect)

        b = self.panel.cut[-1].TryGetCircle(0.1)[1].Center
        rect = self.tr_rect(b, crv)
        rectang.append(rect)
        return rectang

    def divide_points(self, crv):
        st = crv.ClosestPoint(crv.PointAtLength(7.5))[1]
        end = crv.ClosestPoint(crv.PointAtLength(crv.GetLength() - 7.5))[1]
        n_crv = crv.Trim(st, end)

        num = math.ceil(n_crv.GetLength() / 100)
        param = n_crv.DivideByCount(num, True)
        points = [n_crv.PointAt(i) for i in param]
        return points

    def simple_points(self, side, goal, spec):
        points = self.divide_points(goal)
        rectang = [self.tr_rect(i, side, spec) for i in points]
        return rectang

    def all_offset(self):

        all_offset = []
        for i in self.order:
            e = offset_side(*i)
            all_offset.append(e)

        all_offset = intersect(all_offset)
        return all_offset

    def frame_inner(self):
        offset = rh.Curve.JoinCurves(self.all_offset()[0:-1])[0]
        crv = rh.Line(offset.PointAtEnd, rh.Point3d(offset.PointAtEnd[0], offset.PointAtEnd[1] - self.bend + 15,
                                                    offset.PointAtEnd[2])).ToNurbsCurve()
        frame_offset = rh.Curve.JoinCurves([offset, crv])
        return frame_offset