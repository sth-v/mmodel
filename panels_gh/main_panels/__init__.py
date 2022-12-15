import os

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import Rhino.Geometry as rh
import sys
import imp
import math

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
from main_sides import BendSide, Niche, Bottom, Side, NicheShortened, HolesSideOne, HolesSideTwo, BottomPanel

reload(main_sides)


def bound_rec(crv):
    join = rh.Curve.JoinCurves(crv)[0]
    bound_rec = rh.PolyCurve.GetBoundingBox(join, rh.Plane.WorldXY)
    return bound_rec

def divide(crv, dist):
    st = crv.ClosestPoint(crv.PointAtLength(dist))[1]
    end = crv.ClosestPoint(crv.PointAtLength(crv.GetLength() - dist))[1]
    curve = crv.Trim(st, end)

    num = math.ceil(curve.GetLength() / 100)
    param = curve.DivideByCount(num, True)
    points = [curve.PointAt(i) for i in param]
    return points


def translate(point, crv):
    frame = crv.FrameAt(crv.ClosestPoint(point)[1])[1]
    tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, frame)
    return tr

class SimplePanel:
    @property
    def unroll_dict(self):
        _unroll_dict = {'tag': self.tag, 'unroll': self.unrol_surf}
        return _unroll_dict

    def __init__(self, surf=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        object.__init__(self)

        self.surf = surf
        self.tag = tag
        self.pins = pins

        if cogs_bend is None:
            self.cogs_bend = False
        else:
            self.cogs_bend = cogs_bend

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



class MainPanel(SimplePanel):
    bend_ofs = 45
    top_ofs = 35
    niche_ofs = 45
    grav_holes = 23.75
    bottom_rec = 30
    side_rec = 30

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        fr = self.side[0].fres.FrameAt(self.side[0].fres.Domain[1])[1]
        bound_plane = rh.Plane(b_r.Min, fr.XAxis, fr.YAxis)
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
        side = rh.Curve.JoinCurves([self.side[0].join, self.niche.join_region, self.side[1].join, self.bottom.fres])[0]
        side.Transform(self.bound_plane)
        return [side]

    @property
    def marker_curve(self):
        crv = [self.bottom.fres.DuplicateCurve(), self.niche.fres.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in crv]
        return crv

    @property
    def niche_holes(self):
        cut = []
        reg = self.niche.region_holes
        for i in reg:
            ii = i.DuplicateCurve()
            ii.Transform(self.bound_plane)
            cut.append(ii)

        return cut

    @property
    def cut_holes(self):
        cut = []
        for v in self.side:
            for i in v.holes_curve:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)

        if self.unrol[1] is not None:
            for i, v in enumerate(self.unrol[1]):
                #p = rh.Circle(v, self.h_r[i]).ToNurbsCurve()
                ii = v.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)

        return cut + self.niche_holes


    @property
    def unroll_dict(self):
        return {'tag': self.tag, 'unroll': self.unrol_surf}

    @property
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[1].PointAtEnd, self.top_parts[0].PointAtStart, self.fres[1].PointAtEnd])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_bend, self.bend_ofs, 'st'], [diag, self.diag, False], [p_niche, self.niche_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[2, self.top_parts[1], None], [0, self.top_parts[0], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, **kwargs):
        SimplePanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend)
        self.holes = holes
        self.h_p = self.holes['point']
        self.h_r = self.holes['r']

        unrol = rh.Unroller(self.surf)
        if self.h_p[0] is not None:
            a = self.h_p
            #a = [self.surf.ClosestPoint(i) for i in self.h_p]
            unrol.AddFollowingGeometry(curves=a)

        self.unrol = unrol.PerformUnroll()
        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D

        self.gen_side_types()
    def gen_side_types(self):

        self.niche = Niche(self.edges[0], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[2])
        self.side = [HolesSideOne(self.edges[1], True), HolesSideTwo(self.edges[3], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def top_side(self):
        bound = bound_rec(self.fres)
        top_side = bound.GetEdges()[2]
        return top_side.ToNurbsCurve()

    def diag_side(self, i):

        crv = rh.Line.ToNurbsCurve(rh.Line(*i[0:2]))

        crv_d = crv.PointAtLength(rh.Curve.DivideByCount(crv, 2, False)[0])
        self.diag = rh.Point3d.DistanceTo(i[2], crv_d) + 10
        return crv

class ArcPanel(MainPanel):

    @property
    def pins_marker(self):
        unrol = list(self.u_p_m[2])
        circ = []
        for i in unrol:
            c = rh.Circle(i, 5.0)
            c.Transform(self.bound_plane)
            circ.append(c.ToNurbsCurve())

            c = rh.Circle(i, 8.25)
            c.Transform(self.bound_plane)
            p = rh.Polyline.CreateCircumscribedPolygon(c, 3).ToNurbsCurve()
            circ.append(p)
        return circ
    @property
    def grav(self):
        unrol = list(self.u_p[2])
        circ = []
        for i in unrol:
            c = rh.Circle(i, 3.25)
            c.Transform(self.bound_plane)
            circ.append(c.ToNurbsCurve())
        res = circ + self.pins_marker

        return res

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None,  pins=None, pins_mark=None, **kwargs):
        MainPanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend, holes=holes)

        self.pins = pins
        self.pins_mark = pins_mark

        u_pins = rh.Unroller(self.surf)
        if self.pins is not None:
            a = [self.surf.ClosestPoint(i) for i in self.pins]
            u_pins.AddFollowingGeometry(points=a)

        self.u_p = u_pins.PerformUnroll()

        u_pins_mark = rh.Unroller(self.surf)
        if self.pins is not None:
            a = [self.surf.ClosestPoint(i) for i in self.pins_mark]
            u_pins_mark.AddFollowingGeometry(points=a)

        self.u_p_m = u_pins_mark.PerformUnroll()
        self.gen_side_types()

    def gen_side_types(self):

        self.niche = Niche(self.edges[0], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[2])
        self.side = [HolesSideOne(self.edges[1], True), HolesSideTwo(self.edges[3], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()




class NichePanel(MainPanel):
    bend_ofs = 45
    top_ofs = 0
    niche_ofs = 43.53

    bottom_rec = 30
    side_rec = 30

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        xaxis = rh.Vector3d(self.niche.fres.PointAt(self.niche.fres.Domain[1] - 0.01) - self.niche.fres.PointAt(
            self.niche.fres.Domain[0] + 0.01))
        yaxis = rh.Vector3d(self.niche.fres.PointAt(self.niche.fres.Domain[1] - 0.01) - self.niche.fres.PointAt(
            self.niche.fres.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)
        bound_plane = rh.Plane(rh.Point3d(b_r.Min[0], b_r.Max[1], 0), xaxis, yaxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def fres(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve()]

        fr =[]

        for i in fres:
            i.Transform(self.bound_plane)
            if i.IsValid is False:
                print(False)
                a = i.Rebuild(25, i.Degree, True)
                fr.append(a)
            else:
                fr.append(i)
        return fr

    '''@property
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
        new = []
        for i in self.mark_ribs:
            for ii in i:
                new.append(ii)

        new.append(self.mark_back)
        return new'''

    @property
    def unroll_dict(self):
        unroll_dict = {'tag': self.tag, 'unroll': self.unrol_surf,
                       'axis': {'curve': self.unrol[1][0:len(self.unrol[1]) - 1],
                                'tag': [self.tag[0:-1] + str(4 + i) for i in range(len(self.unrol[1]) - 1)]}}
        return unroll_dict

    @property
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[0].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_niche, self.niche_ofs, 'st'], [diag, self.diag, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1], None], [2, self.top_parts[0], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, **kwargs):
        MainPanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend, holes=holes)
        self.__dict__.update(**kwargs)

        unrol = rh.Unroller(self.surf)

        if hasattr(self, 'rebra') and hasattr(self, 'back_side'):
            self.intersections = self.unroll_intersection()
            unrol.AddFollowingGeometry(curves=self.intersections)
        else:
            pass

        self.unrol = unrol.PerformUnroll()

        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Edges
        self.gen_side_types()

    def __add__(self, other):

        if other.__class__.__name__ == 'N_4':
            if hasattr(self, 'back_side'):
                return NichePanel(self.surf, self.cogs_bend, self.tag, back_side=self.back_side, rebra=other)
            else:
                return NichePanel(self.surf, self.cogs_bend, self.tag, rebra=other)

        elif other.__class__.__name__ == 'N_2':
            if hasattr(self, 'rebra'):
                return NichePanel(self.surf, self.cogs_bend, self.tag, back_side=other, rebra=self.rebra)
            else:
                return NichePanel(self.surf, self.cogs_bend, self.tag, back_side=other)
        else:
            pass

    def gen_side_types(self):

        self.niche = NicheShortened(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [HolesSideTwo(self.edges[2], False), HolesSideOne(self.edges[0], True)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

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
        r_inters = self.rebra_intersect('s')
        [i.PullToBrepFace(self.surf.Faces[0], 0.01) for i in r_inters]

        b_inters = self.back_intersect()
        b_inters = rh.Intersect.Intersection.CurveBrepFace(b_inters, self.surf.Faces[0], 0.1)[1][0]

        r_inters.append(b_inters)
        return r_inters

    def rebra_intersect(self, name):
        intersect = []
        if name == 's':
            ext = self.rebra.extend
        else:
            ext = self.rebra.extend_bottom
        for i in ext:
            inters = rs.IntersectBreps(self.surf, i, 0.1)
            line = rh.LineCurve(rs.CurveStartPoint(inters[0]), rs.CurveEndPoint(inters[0]))
            intersect.append(line)

        return intersect

    def back_intersect(self):
        inters = rs.IntersectBreps(self.surf, self.back_side.extend, 0.1)
        line = rh.LineCurve(rs.CurveStartPoint(inters[0]), rs.CurveEndPoint(inters[0]))
        return line



class N_4:
    def __init__(self, surf=None):
        self.cogs_bend = False
        self.surf = surf

        self.extend = []
        ext_surf = [rh.Surface.Duplicate(i) for i in self.surf]

        self.edges = []
        for i in self.surf:
            unrol = rh.Unroller(i).PerformUnroll()[0][0]
            edge = rh.Curve.JoinCurves(list(unrol.Curves3D))[0]
            self.edges.append(edge)


        for i in range(self.__len__()):
            self.i = i
            ext = self.extend_surf(ext_surf)
            self.extend.append(ext)

        self.extend_bottom = []
        ext_b = [rh.Surface.Duplicate(i) for i in self.surf]

        for i in range(self.__len__()):
            self.i = i
            ext = self.extend_bot(ext_b)
            self.extend_bottom.append(ext)


    def __len__(self):
        return len(self.surf)

    def extend_surf(self, ext_surf):
        surf = ext_surf[self.i]
        interv = surf.Domain(1)
        interv = rh.Interval(interv[0] - 50, interv[1] + 50)

        surf.Extend(1, interv)
        extr = rh.Surface.ToBrep(surf)

        return extr

    def extend_bot(self, ext_bott):
        surf = ext_bott[self.i]
        interv = surf.Domain(0)
        interv = rh.Interval(interv[0] - 50, interv[1] + 50)

        surf.Extend(0, interv)
        extr = rh.Surface.ToBrep(surf)

        return extr