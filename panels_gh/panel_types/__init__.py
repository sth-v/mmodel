import math
import os

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import Rhino.Geometry as rh
import sys
import imp
import ghpythonlib.components as comp

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_sides",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_panels",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/board_panels"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype) = imp.find_module("main_sides", path=[PWD])
main_sides = imp.load_module("main_sides", sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype))

main_sides.__init__("main_sides", "generic nodule")
from main_sides import Niche, Bottom, Side, NicheShortened, HolesSideOne, HolesSideTwo, HeatSchov, BottomPanel, \
    RibsSide, HolesSideThree, RibsSideTwo, BoardEdgeOne, BoardEdgeTwo, NicheShortenedBoard, BottomBoard, BottomHeat

reload(main_sides)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

main_panels.__init__("main_panels", "generic nodule")
from main_panels import NichePanel, SimplePanel, ArcPanel

reload(main_panels)

boardfile, boardfilename, (boardsuffix, boardmode, boardtype) = imp.find_module("board_panels", path=[PWD])
board_panels = imp.load_module("board_panels", boardfile, boardfilename, (boardsuffix, boardmode, boardtype))

board_panels.__init__("board_panels", "generic nodule")
from board_panels import BoardPanel, BoardEdge, ArcConePanel

reload(board_panels)
import main_tagging

reload(main_tagging)


def bound_rec(crv):
    join = rh.Curve.JoinCurves(crv)[0]
    bound_rec = rh.PolyCurve.GetBoundingBox(join, rh.Plane.WorldXY)
    return bound_rec


class PC_1(ArcConePanel):
    def __init__(self, surf, tag=None, pins=None, cogs_bend=None, holes=None, cone_mark=None, **kwargs):
        ArcConePanel.__dict__['__init__'](self, surf=surf, tag=tag, pins=pins, cogs_bend=cogs_bend, holes=holes, cone_mark=cone_mark, **kwargs)

class PC_2(ArcConePanel):
    @property
    def bound_plane(self):
        cone = list(self.marks[1][len(self.pins_mark):])[0]

        xaxis = rh.Vector3d(cone.PointAt(cone.Domain[0] - 0.01) - cone.PointAt(cone.Domain[1] + 0.01))
        yaxis = rh.Vector3d(cone.PointAt(cone.Domain[0] - 0.01) - cone.PointAt(cone.Domain[1] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        bound_plane = rh.Plane(b_r.Max, xaxis, yaxis)
        bpl = rh.Plane(cone.PointAt(cone.Domain[1]), xaxis, yaxis)
        setattr(self, 'bpl', bpl)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)

        return tr

    @property
    def frame_dict(self):
        diag = self.diag_side([self.top_parts[1].PointAtEnd, self.top_parts[2].PointAtStart, self.fres[1].PointAtEnd])
        top = self.fres[0]
        p_niche = self.fres[1]
        p_bend = self.fres[2]
        order = [[p_bend, self.bend_ofs, 'st'], [diag, self.diag, False], [p_niche, self.niche_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[2, self.top_parts[1], None], [0, self.top_parts[2], None], [3, self.top_parts[0], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, tag=None, pins=None, cogs_bend=None, holes=None, cone_mark=None, **kwargs):
        ArcConePanel.__dict__['__init__'](self, surf=surf, tag=tag, pins=pins, cogs_bend=cogs_bend, holes=holes, cone_mark=cone_mark, **kwargs)

    def gen_side_types(self):
        self.niche = Niche(self.edges[2], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[0])
        self.side = [HolesSideOne(self.edges[1], False), HolesSideTwo(self.edges[3], True)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()



class P_1(ArcPanel):

    def __init__(self, surf, tag=None, pins=None, cogs_bend=None, holes=None, **kwargs):
        ArcPanel.__dict__['__init__'](self, surf=surf, tag=tag, pins=pins, cogs_bend=cogs_bend, holes=holes, **kwargs)


class P_2(ArcPanel):

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        fr = self.side[1].fres.FrameAt(self.side[1].fres.Domain[0])[1]
        bound_plane = rh.Plane(b_r.Max, fr.XAxis, fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def frame_dict(self):
        diag = self.diag_side([self.top_parts[1].PointAtEnd, self.top_parts[2].PointAtStart, self.fres[1].PointAtEnd])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[2]
        order = [[p_bend, self.bend_ofs, 'st'], [diag, self.diag, False], [p_niche, self.niche_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[2, self.top_parts[1], None], [0, self.top_parts[2], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        ArcPanel.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = Niche(self.edges[2], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[0])
        self.side = [HolesSideOne(self.edges[1], False), HolesSideTwo(self.edges[3], True)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class P_3(SimplePanel):
    @property
    def fres(self):
        fres = [self.side[0].fres_shift.DuplicateCurve(), self.side[1].fres_shift.DuplicateCurve(),
                self.side[2].fres_shift.DuplicateCurve(), self.side[3].fres_shift.DuplicateCurve()]
        return fres

    @property
    def cut(self):
        side = rh.Curve.JoinCurves([self.side[0].fres, self.side[1].join, self.side[2].fres, self.side[3].join])[0]
        return [side]

    @property
    def bound_frame(self):
        return self._bound_rect

    @property
    def cut_holes(self):
        unrol = self.unrol[2]
        h = []
        for i in unrol[0:len(self.pins) / 2]:
            c = rh.Circle(i, 5.25)
            h.append(c.ToNurbsCurve())

        for i in unrol[len(self.pins) / 2:]:
            vec = rh.Vector3d(i)
            tr = rh.Transform.Translation(vec)
            n = self.hls.DuplicateCurve()
            n.Transform(tr)
            h.append(n)
        return h

    @property
    def hole_one(self):
        unroll = self.unrol[2]
        cent = unroll[0:len(self.pins) / 2]
        cent = cent[int((4 * len(cent)) / 5)]
        return cent

    @property
    def hole_two(self):
        unroll = self.unrol[2]
        cent = unroll[len(self.pins) / 2:]
        cent = cent[int(len(cent) / 5)]
        return cent

    @property
    def all_elems(self):
        return self.cut + self.cut_holes

    def __init__(self, surf=None, pins=None, cogs_bend=None, tag=None):
        SimplePanel.__dict__['__init__'](self, surf, pins, cogs_bend, tag)
        unrol = rh.Unroller(self.surf)

        if self.pins is not None:
            unrol.AddFollowingGeometry(points=self.pins[0:len(self.pins) / 2])
            unrol.AddFollowingGeometry(points=self.pins[len(self.pins) / 2:])

        self.unrol = unrol.PerformUnroll()
        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D
        self.gen_side_types()
        edge1_vector = rh.Vector3d(self.edges[0].PointAtEnd - self.edges[0].PointAtStart)
        edge0_pt = self.edges[0].PointAt(self.edges[0].GetLength() / 2)
        edge3_pt = self.edges[3].PointAt(self.edges[3].GetLength() / 2)
        # edge2_vector = rh.Vector3d(self._cls.panel.edges[3].PointAtEnd - self._cls.panel.edges[3].PointAtStart)

        self._bound_rect, _ = comp.Bubalus_GH2.CurveMinBoundingBox(self.cut)

    edge2_vector = property(fget=lambda self: rh.Vector3d.CrossProduct(self.edge1_vector, rh.Vector3d(0, 0, 1)))
    edge1_vector = property(fget=lambda self: rh.Vector3d(self.edges[0].PointAtEnd - self.edges[0].PointAtStart))

    @property
    def plane(self):
        return rh.Plane(self._bound_rect.Center, self.edge1_vector, self.edge2_vector)

    # edge2_vector.Unitize()
    def gen_side_types(self):
        self.side = [Bottom(self.edges[0]), HeatSchov(self.edges[1]), Bottom(self.edges[2]),
                     HeatSchov(self.edges[3])]
        self.side_types = self.side
        self.intersect()

class PC_4(P_3):

    @property
    def plane(self):
        return rh.Plane(self.edges[1].PointAtNormalizedLength(0.5), self.edge1_vector, self.edge2_vector)
    @property
    def cut(self):
        side = rh.Curve.JoinCurves([self.side[0].fres, self.side[1].fres, self.side[2].fres, self.side[3].fres])[0]
        return [side]
    def __init__(self, surf=None, pins=None, cogs_bend=None, tag=None):
        P_3.__dict__['__init__'](self, surf, pins, cogs_bend, tag)

    edge2_vector = property(fget=lambda self: rh.Vector3d.CrossProduct(self.edge1_vector, rh.Vector3d(0, 0, 1)))
    edge1_vector = property(fget=lambda self: rh.Vector3d(self.edges[1].PointAtEnd - self.edges[1].PointAtStart))

    @property
    def all_elems(self):
        _all_elems = [[], [], [], [], [], []]

        _all_elems[0].extend(self.cut)
        return _all_elems

    def gen_side_types(self):
        self.side = [Bottom(self.edges[0]), Bottom(self.edges[1]), Bottom(self.edges[2]),
                     Bottom(self.edges[3])]
        self.side_types = self.side
        self.intersect()


class PC_3(P_3):

    @property
    def cut(self):
        side = rh.Curve.JoinCurves([self.side[0].fres, self.side[1].fres, self.side[2].fres, self.side[3].fres])[0]
        return [side]

    @property
    def all_elems(self):

        _all_elems = [[], [], [], [], [], []]


        _all_elems[0].extend(self.cut + self.cut_holes)
        _all_elems[4].extend(self.rib_mark)
        # _all_elems[2].extend([self.panel.fres[0], self.panel.fres[2]])

        return _all_elems


    def __init__(self, surf=None, pins=None, cogs_bend=None, tag=None, rib_mark=None):
        P_3.__dict__['__init__'](self, surf, pins, cogs_bend, tag)

        unrol = rh.Unroller(self.surf)

        if self.pins is not None:
            unrol.AddFollowingGeometry(points=self.pins)
            unrol.AddFollowingGeometry(curves=rib_mark)

        self.unrol = unrol.PerformUnroll()
        self.unrol_surf = self.unrol[0][0]
        self.rib_mark = self.unrol[1]
        self.edges = self.unrol_surf.Curves3D
        self.gen_side_types()
        edge1_vector = rh.Vector3d(self.edges[0].PointAtEnd - self.edges[0].PointAtStart)
        edge0_pt = self.edges[0].PointAt(self.edges[0].GetLength() / 2)
        edge3_pt = self.edges[3].PointAt(self.edges[3].GetLength() / 2)
        # edge2_vector = rh.Vector3d(self._cls.panel.edges[3].PointAtEnd - self._cls.panel.edges[3].PointAtStart)

        self._bound_rect, _ = comp.Bubalus_GH2.CurveMinBoundingBox(self.cut)

    edge2_vector = property(fget=lambda self: rh.Vector3d.CrossProduct(self.edge1_vector, rh.Vector3d(0, 0, 1)))
    edge1_vector = property(fget=lambda self: rh.Vector3d(self.edges[1].PointAtEnd - self.edges[1].PointAtStart))

    def gen_side_types(self):
        self.side = [BottomHeat(self.edges[0]), Bottom(self.edges[1]), BottomHeat(self.edges[2]),
                     Bottom(self.edges[3])]
        self.side_types = self.side
        self.intersect()



class N_1(NichePanel):

    @property
    def grav_laser(self):
        g = []
        if self.unrol_grav[1] is not None:
            for i, v in enumerate(self.unrol_grav[1]):
                if v.GetLength() > 5:
                    ii = v.DuplicateCurve()
                    ii.Transform(self.bound_plane)
                    if v.GetLength() < 500:
                        g.append(ii)
                    else:
                        p_one = ii.ClosestPoint(ii.PointAtLength(1.0))[1]
                        p_two = ii.ClosestPoint(ii.PointAtLength(ii.GetLength() - 1.0))[1]
                        tr = ii.Trim(p_one, p_two)
                        g.append(tr)
            return g
        else:
            raise ValueError

    @property
    def cut_podves(self):
        cut = []
        try:

            ofs = self.grav_laser[0].Offset(rh.Plane.WorldXY, 40, 0.01,
                                            rh.CurveOffsetCornerStyle.__dict__['None'])[0]
            p = ofs.PointAtLength(12)
            h_one = rh.Circle(p, 4)

            ofs = self.grav_laser[1].Offset(rh.Plane.WorldXY, -40, 0.01,
                                            rh.CurveOffsetCornerStyle.__dict__['None'])[0]
            p = ofs.PointAtLength(12)
            h_two = rh.Circle(p, 4)
            return [h_one.ToNurbsCurve(), h_two.ToNurbsCurve()]
        except:
            return [rh.Circle(rh.Plane.WorldXY.Origin, 4)]


    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, mark_crv=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, mark_crv=mark_crv,
                                        **kwargs)


class N_3(NichePanel):

    @property
    def grav_laser(self):
        g = []
        if self.unrol_grav[1] is not None:
            for i, v in enumerate(self.unrol_grav[1]):
                if v.GetLength() > 5:
                    ii = v.DuplicateCurve()
                    ii.Transform(self.bound_plane)
                    if v.GetLength() < 500:
                        g.append(ii)
                    else:
                        p_one = ii.ClosestPoint(ii.PointAtLength(1.0))[1]
                        p_two = ii.ClosestPoint(ii.PointAtLength(ii.GetLength() - 1.0))[1]
                        tr = ii.Trim(p_one, p_two)
                        g.append(tr)
            return g
        else:
            raise ValueError

    @property
    def cut_podves(self):
        cut = []

        ofs = self.grav_laser[0].Offset(rh.Plane.WorldXY, 40, 0.01,
                                        rh.CurveOffsetCornerStyle.__dict__['None'])[0]
        p = ofs.PointAtLength(ofs.GetLength() - 12)
        h_one = rh.Circle(p, 4)

        ofs = self.grav_laser[1].Offset(rh.Plane.WorldXY, -40, 0.01,
                                        rh.CurveOffsetCornerStyle.__dict__['None'])[0]

        p = ofs.PointAtLength(ofs.GetLength() - 12)
        h_two = rh.Circle(p, 4)
        return [h_one.ToNurbsCurve(), h_two.ToNurbsCurve()]

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, mark_crv=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, mark_crv=mark_crv,
                                        **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortened(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [HolesSideTwo(self.edges[2], False), HolesSideOne(self.edges[0], True)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class N_2(NichePanel):
    bend_ofs = 45
    top_ofs = 0
    niche_ofs = 10

    bottom_rec = 30
    side_rec = 30

    @property
    def bound_plane(self):
        vec = rh.Vector3d(self.top.fres.PointAtEnd - self.top.fres.PointAtStart)
        rot = rh.Vector3d(self.top.fres.PointAtEnd - self.top.fres.PointAtStart)

        rot.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        bound_plane = rh.Plane(self.top.fres.PointAtStart, vec, rot)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def fres(self):
        fres = [rh.Curve.DuplicateCurve(self.side[0].fres.ToNurbsCurve()),
                rh.Curve.DuplicateCurve(self.side[1].fres.ToNurbsCurve())]
        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut(self):
        cut = [rh.Curve.JoinCurves([self.side[0].join, self.top.fres, self.side[1].join, self.bottom.fres])[
                   0].ToNurbsCurve()]
        [i.Transform(self.bound_plane) for i in cut]
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
                ii = v.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)

        return cut

    @property
    def top_parts(self):
        top = [self.side[0].top_part.DuplicateCurve(), self.side[1].top_part.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in top]
        return top

    @property
    def ribs_marker(self):
        pairs = []
        gr = self.grav
        for n, c in zip(self.mark_name, gr[0::2]):
            cent = c.PointAtNormalizedLength(0.5)
            pairs.append([n, cent])
        return pairs

    @property
    def grav(self):
        g = []
        if self.unrol_grav[1] is not None:
            for i, v in enumerate(self.unrol_grav[1]):
                if v.GetLength() > 5:
                    ii = v.DuplicateCurve()
                    ii.Transform(self.bound_plane)
                    g.append(ii)
            return g
        else:
            raise ValueError

    @property
    def frame_dict(self):

        bf = self.top.fres.DuplicateCurve()
        bf.Transform(self.bound_plane)
        p_niche = bf
        p_bend = self.fres[0]

        ll = self.fres
        ll.append(p_niche)
        bound = bound_rec(ll)
        top = bound.GetEdges()[2].ToNurbsCurve()

        order = [[p_niche, self.niche_ofs, 'st'], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, p_niche, None], [1, self.top_parts[0], True]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, holes=None, tag=None, cogs_bend=False, mark_crv=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, holes=holes, tag=tag, cogs_bend=cogs_bend, mark_crv=mark_crv,
                                        **kwargs)

        self.gen_side_types()

    def gen_side_types(self):
        self.top = Bottom(self.edges[0])
        self.bottom = Bottom(self.edges[2])
        self.side = [HolesSideOne(self.edges[3], spec_dist=250), HolesSideThree(self.edges[1], spec_dist=250)]

        self.side_types = [self.top, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class N_4(SimplePanel):

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].fres, self.side[1].fres, self.side[2].fres, self.top.join])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        if self.orient[0] == '2':
            fr = self.side[1].fres.FrameAt(self.side[1].fres.Domain[0])[1]
            if fr.YAxis[0] > 0:
                bound_plane = rh.Plane(rh.Point3d(b_r.Max[0], b_r.Min[1], 0), fr.XAxis, -fr.YAxis)
            else:
                bound_plane = rh.Plane(rh.Point3d(b_r.Max[0], b_r.Min[1], 0), fr.XAxis, fr.YAxis)
        else:
            fr = self.side[1].fres.FrameAt(self.side[1].fres.Domain[1])[1]
            if fr.YAxis[0] > 0:
                bound_plane = rh.Plane(rh.Point3d(b_r.Max[0], b_r.Min[1], 0), -fr.XAxis, -fr.YAxis)
            else:
                bound_plane = rh.Plane(rh.Point3d(b_r.Max[0], b_r.Min[1], 0), -fr.XAxis, fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def cut(self):
        side = rh.Curve.JoinCurves([self.side[0].fres, self.side[1].fres, self.side[2].fres, self.top.join])[0]
        side.Transform(self.bound_plane)
        return [side]

    @property
    def bound_frame(self):
        o = self.cut[0].GetBoundingBox(True).Corner(True, True, True)
        t = self.cut[0].GetBoundingBox(True).Corner(True, False, True)
        l_one = rh.Line(o, t).ToNurbsCurve()
        l_one = l_one.PointAtNormalizedLength(0.5)

        o = self.cut[0].GetBoundingBox(True).Corner(False, True, True)
        t = self.cut[0].GetBoundingBox(True).Corner(False, False, True)
        l_t = rh.Line(o, t).ToNurbsCurve()
        l_t = l_t.PointAtNormalizedLength(0.5)

        a = [l_one, l_t]
        return a

    @property
    def all_elems(self):
        if self.unrol[1] is not None:
            crvs = []
            for i in self.unrol[1]:
                new = i.DuplicateCurve()
                new.Transform(self.bound_plane)
                crvs.append(new)
            return self.cut + crvs
        else:
            return self.cut

    def __init__(self, surf, pins=None, cogs_bend=None, tag=None, orient=None, rib_cut=None, **kwargs):
        SimplePanel.__dict__['__init__'](self, surf, pins, cogs_bend, tag)

        if orient[0] == "2":
            self.surf = surf
        else:
            a = surf.DuplicateBrep()
            a.Flip()
            self.surf = a
            # print(self.surf)

        unrol = rh.Unroller(self.surf)

        if rib_cut[0] is not None:
            unrol.AddFollowingGeometry(curves=rib_cut)

        self.unrol = unrol.PerformUnroll()
        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D
        self.orient = orient
        self.gen_side_types()

        self._bound_rect = self.cut[0].GetBoundingBox(True)

    def gen_side_types(self):
        if self.orient[0] == '2':
            self.top = RibsSide(self.edges[3])
            self.side = [Bottom(self.edges[0]), Bottom(self.edges[1]), Bottom(self.edges[2])]

        else:
            self.top = RibsSideTwo(self.edges[3])
            self.side = [Bottom(self.edges[0]), Bottom(self.edges[1]), Bottom(self.edges[2])]

        self.side_types = [self.side[0], self.side[1], self.side[2], self.top]
        self.intersect()

    @property
    def plane(self):
        return rh.Plane(self._bound_rect.Center, rh.Plane.WorldXY.XAxis, rh.Plane.WorldXY.YAxis)


class B_1(BoardPanel):
    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, **kwargs):
        BoardPanel.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, **kwargs)

class B_1_T(BoardPanel):
    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, **kwargs):
        BoardPanel.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, **kwargs)
        self.mark_name = ['2', '5', '4', '3', '6']
    @property
    def parent_plane(self):
        xaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[1] - 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[0] + 0.01))
        yaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[1] - 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)
        parent_plane = rh.Plane(self.bottom.fres.PointAt(self.bottom.fres.Domain[0]), xaxis, yaxis)
        return parent_plane

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

    def gen_side_types(self):

        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = BottomBoard(self.edges[1])
        self.side = [HolesSideTwo(self.edges[2]), HolesSideOne(self.edges[0])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()





class B_2(BoardEdge):
    def __init__(self, surf=None, holes=None, cogs_bend=None, tag=None, params=None, **kwargs):
        BoardEdge.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, params=params, **kwargs)


class B_3(BoardEdge):
    @property
    def all_elems(self):
        return self.cut + [self.cut_hole]

    @property
    def cut_hole(self):
        if self.tag[2] == 'R':
            ofs = self.side[2].fres.Offset(rh.Plane.WorldXY, -10, 0.01,
                                  rh.CurveOffsetCornerStyle.__dict__['None'])[0]

        else:
            ofs = self.side[2].fres.Offset(rh.Plane.WorldXY, 10, 0.01,
                                           rh.CurveOffsetCornerStyle.__dict__['None'])[0]

        p = ofs.PointAtLength(ofs.GetLength()-25.0)
        circ = rh.Circle(p, 2.5)
        cc = circ.ToNurbsCurve()

        return cc

    @property
    def fres(self):
        fres = [self.side[0].fres_shift.DuplicateCurve(), self.side[-1].fres_shift.DuplicateCurve()]
        return fres

    @property
    def cut(self):

        ss = [i.fres for i in self.side[1:-1]]

        side = rh.Curve.JoinCurves([self.side[0].join] + ss + [self.side[-1].join])[0]
        hls = self.side[0].holes_curve + self.side[-1].holes_curve

        for i in hls:
            side = rh.Curve.CreateBooleanDifference(side, i)[0]
        fillet = rh.Curve.CreateFilletCornersCurve(side, 2, 0.1, 0.1)
        if len(self.unrol[1]) >= 1:
            return [fillet] + list(self.unrol[1])
        else:
            return [fillet]
    def __init__(self, surf=None, holes=None, cogs_bend=None, tag=None, params=None, **kwargs):
        BoardEdge.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, params=params, **kwargs)

    def gen_side_types(self):
        if list(self.edges)[-1].GetLength() >= 150:
            num = 2
        else:
            num = 1

        ss = [Bottom(i.ToNurbsCurve()) for i in list(self.edges)[1:-1]]
        self.side = [BoardEdgeOne(list(self.edges)[0].ToNurbsCurve(), params=self.trim_params.top, rev=True, tag=self.tag)] + ss + [BoardEdgeTwo(list(self.edges)[-1].ToNurbsCurve(), params=self.trim_params.side, spec_dist=num, tag=self.tag)]
        self.side_types = self.side
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self.side_types):
            old = v.fres.Domain
            if old[1]-old[0] > 2:
                v.fres = v.fres.Extend(rh.Interval(old[0] - 7, old[1] + 7))
            else:
                v.fres = v.fres.Extend(rh.Interval(old[0] - 0.025, old[1] + 0.025))
            param = []
            for ind, val in enumerate(self.side_types):
                if i != ind:
                    old = val.fres.Domain
                    if old[1] - old[0] > 2:
                        new = val.fres.Extend(rh.Interval(old[0] - 7, old[1] + 7))
                    else:
                        new = val.fres.Extend(rh.Interval(old[0] - 0.025, old[1] + 0.025))
                    inters = rs.CurveCurveIntersection(v.fres, new)
                    if inters is not None:
                        param.append(inters[0][5])
            param = sorted(param)

            trimed = rh.Curve.Trim(v.fres, param[0], param[1])
            v.fres = trimed



class NC_1(N_1):

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, mark_crv=None, **kwargs):
        N_1.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, mark_crv=mark_crv,
                                        **kwargs)

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
        setattr(self, 'bpl', bound_plane)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[0].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        diag = diag.Extend(rh.Interval(diag.Domain[0]-30, diag.Domain[1]+30))
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_niche, self.niche_ofs, 's'], [diag, self.diag, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1], None], [2, self.top_parts[0], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}


    def gen_side_types(self):
        self.niche = NicheShortened(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [HolesSideTwo(self.edges[2], False), HolesSideOne(self.edges[0], True)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class NC_2(NC_1):

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, mark_crv=None, **kwargs):
        NC_1.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, mark_crv=mark_crv,
                                     **kwargs)

class NC_R_1(N_1):

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, mark_crv=None, **kwargs):
        N_1.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, mark_crv=mark_crv,
                                        **kwargs)

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        xaxis = rh.Vector3d(self.niche.fres.PointAt(self.niche.fres.Domain[1] - 0.01) - self.niche.fres.PointAt(
            self.niche.fres.Domain[0] + 0.01))
        yaxis = rh.Vector3d(self.niche.fres.PointAt(self.niche.fres.Domain[1] - 0.01) - self.niche.fres.PointAt(
            self.niche.fres.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)
        bound_plane = rh.Plane(rh.Point3d(b_r.Max[0], b_r.Min[1], 0), xaxis, yaxis)
        setattr(self, 'bpl', bound_plane)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[2].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        diag = diag.Extend(rh.Interval(diag.Domain[0]-30, diag.Domain[1]+30))
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[2]
        order = [[p_niche, self.niche_ofs, 's'], [diag, self.diag, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1], None], [2, self.top_parts[2], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}


    def gen_side_types(self):
        self.niche = NicheShortened(self.edges[0], self.cogs_bend)
        self.bottom = Bottom(self.edges[2])
        self.side = [HolesSideTwo(self.edges[1], True), HolesSideOne(self.edges[3], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

class NC_R_2(NC_R_1):

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, mark_crv=None, **kwargs):
        NC_R_1.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, mark_crv=mark_crv,
                                        **kwargs)

class NC_3(N_2):

    @property
    def frame_dict(self):

        bf = self.top.fres.DuplicateCurve()
        bf.Transform(self.bound_plane)
        p_niche = bf
        p_bend = self.fres[1]

        ll = self.fres
        ll.append(p_niche)
        bound = bound_rec(ll)
        top = bound.GetEdges()[2].ToNurbsCurve()

        order = [[p_niche, self.niche_ofs, 'st'], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, p_niche, None], [1, self.top_parts[1], True]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, holes=None, tag=None, cogs_bend=False, mark_crv=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, holes=holes, tag=tag, cogs_bend=cogs_bend, mark_crv=mark_crv,
                                        **kwargs)

        self.gen_side_types()

    def gen_side_types(self):
        self.top = Bottom(self.edges[3])
        self.bottom = Bottom(self.edges[1])
        self.side = [HolesSideOne(self.edges[0], spec_dist=250), HolesSideThree(self.edges[2], spec_dist=250)]

        self.side_types = [self.top, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    @property
    def bound_plane(self):
        vec = rh.Vector3d(self.top.fres.PointAtEnd - self.top.fres.PointAtStart)
        rot = rh.Vector3d(self.top.fres.PointAtEnd - self.top.fres.PointAtStart)

        rot.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        bound_plane = rh.Plane(self.top.fres.PointAtStart, vec, rot)
        setattr(self, 'bpl', bound_plane)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr


class NC_R_3(N_2):

    @property
    def frame_dict(self):

        bf = self.top.fres.DuplicateCurve()
        bf.Transform(self.bound_plane)
        p_niche = bf
        p_bend = self.fres[1]

        ll = self.fres
        ll.append(p_niche)
        bound = bound_rec(ll)
        top = bound.GetEdges()[2].ToNurbsCurve()

        order = [[p_niche, self.niche_ofs, 'st'], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, p_niche, None], [1, self.top_parts[1], True]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, holes=None, tag=None, cogs_bend=False, mark_crv=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, holes=holes, tag=tag, cogs_bend=cogs_bend, mark_crv=mark_crv,
                                        **kwargs)

        self.gen_side_types()

    def gen_side_types(self):
        self.top = Bottom(self.edges[0])
        self.bottom = Bottom(self.edges[2])
        self.side = [HolesSideOne(self.edges[3], spec_dist=250), HolesSideThree(self.edges[1], spec_dist=250)]

        self.side_types = [self.top, self.bottom, self.side[0], self.side[1]]
        self.intersect()

