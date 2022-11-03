import os

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import Rhino.Geometry as rh
import sys
import imp


if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_sides"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype) = imp.find_module("main_sides", path=[PWD])
main_sides = imp.load_module("main_sides", sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype))

main_sides.__init__("main_sides", "generic nodule")
from main_sides import BendSide, Niche, Bottom, Side
reload(main_sides)


def bound_rec(crv):
    join = rh.Curve.JoinCurves(crv)[0]
    bound_rec = rh.PolyCurve.GetBoundingBox(join, rh.Plane.WorldXY)
    return bound_rec


class MainPanel:
    bend_ofs = 45
    top_ofs = 0
    niche_ofs = 43.53
    diag_ofs = 20

    bottom_rec = 30
    side_rec = 100

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        fr = self.niche.fres.FrameAt(self.niche.fres.Domain[0])[1]
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
            side = rh.Curve.JoinCurves([self.side[0].join, self.niche.join_region[0], self.side[1].join, self.bottom.fres])[0]
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
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[0].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_niche, self.niche_ofs, 'st'], [diag, self.diag_ofs, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1]], [2, self.top_parts[0]]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surface, cogs_bend=None, tag=None):
        object.__init__(self)

        self.surf = surface
        self.tag = tag

        if cogs_bend is None:
            self.cogs_bend = False
        else:
            self.cogs_bend = cogs_bend

        unrol = rh.Unroller(self.surf)
        self.unrol = unrol.PerformUnroll()

        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D
        self.gen_side_types()


    def gen_side_types(self):

        self.niche = Niche(self.edges[0])
        self.bottom = Bottom(self.edges[2])
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

    def top_side(self):
        bound = bound_rec(self.fres)
        top_side = bound.GetEdges()[2]
        return top_side.ToNurbsCurve()

    def diag_side(self, i):

        crv = rh.Line.ToNurbsCurve(rh.Line(*i[0:2]))

        crv_d = crv.PointAtLength(rh.Curve.DivideByCount(crv, 2, False)[0])
        self.diag = rh.Point3d.DistanceTo(i[2], crv_d) + 10
        return crv



class NicheSide(MainPanel):
    bend_ofs = 45
    top_ofs = 0
    niche_ofs = 43.53
    diag_ofs = 20

    bottom_rec = 30
    side_rec = 100

    @property
    def mark_ribs(self):
        mark_ribs = self.ribs_offset()
        for i, v in enumerate(mark_ribs):
            v[0].Transform(self.bound_plane)
            v[1].Transform(self.bound_plane)
        return mark_ribs

    @property
    def mark_back(self):
        one = self.unrol[1][-1].LengthParameter(1)[1]
        two = self.unrol[1][-1].LengthParameter(self.unrol[1][-1].GetLength() - 1)[1]
        mark_back = self.unrol[1][-1].Trim(one, two)
        mark_back.Transform(self.bound_plane)
        return mark_back

    @property
    def grav(self):
        new =[]
        for i in self.mark_ribs:
            for ii in i:
                new.append(ii)

        new.append(self.mark_back)
        return new

    @property
    def unroll_dict(self):
        unroll_dict = {'tag': self.tag, 'unroll': self.unrol_surf, 'axis': {'curve': self.unrol[1][0:len(self.unrol[1]) - 1],
                        'tag': [self.tag[0:-1]+str(4+i) for i in range(len(self.unrol[1]) - 1)]}, 'frame':{'bb': 0}}
        return unroll_dict

    @property
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[0].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_niche, self.niche_ofs, 'st'], [diag, self.diag_ofs, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1]], [2, self.top_parts[0]]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surface, rib=None, back=None, cogs_bend=None, tag=None):
        MainPanel.__init__(self, surface, cogs_bend, tag)

        unrol = rh.Unroller(self.surf)

        if rib is not None:
            self.rebra = rib
            self.back_side = back
            self.intersections = self.unroll_intersection()
            unrol.AddFollowingGeometry(curves=self.intersections)
        else:
            pass

        self.unrol = unrol.PerformUnroll()

        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Edges
        self.gen_side_types()


    def ribs_offset(self):
        r = self.unrol[1][0:len(self.unrol[1]) - 1]
        ofset_rebra = []
        for i in r:
            if i.GetLength() > 3:
                ofs_one = i.OffsetOnSurface(self.unrol_surf.Faces[0], 1.5, 0.1)
                ofs_two = i.OffsetOnSurface(self.unrol_surf.Faces[0], -1.5, 0.1)
                ofset_rebra.append([ofs_one[0], ofs_two[0]])
        return ofset_rebra

    def unroll_intersection(self):
        r_inters = self.rebra_intersect()
        [i.PullToBrepFace(self.surf.Faces[0], 0.01) for i in r_inters]

        b_inters = self.back_intersect()
        b_inters =rh.Intersect.Intersection.CurveBrepFace(b_inters, self.surf.Faces[0], 0.1)[1][0]

        r_inters.append(b_inters)
        return r_inters

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

