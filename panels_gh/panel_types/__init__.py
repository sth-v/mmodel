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
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_panels"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype) = imp.find_module("main_sides", path=[PWD])
main_sides = imp.load_module("main_sides", sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype))

main_sides.__init__("main_sides", "generic nodule")
from main_sides import Niche, Bottom, Side, NicheShortened, HolesSideOne, HolesSideTwo, HeatSchov, BottomPanel

reload(main_sides)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

main_panels.__init__("main_panels", "generic nodule")
from main_panels import NichePanel, SimplePanel, ArcPanel

reload(main_panels)
import main_tagging

reload(main_tagging)


def bound_rec(crv):
    join = rh.Curve.JoinCurves(crv)[0]
    bound_rec = rh.PolyCurve.GetBoundingBox(join, rh.Plane.WorldXY)
    return bound_rec


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


class N_1(NichePanel):

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, **kwargs)


class N_3(NichePanel):
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
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def frame_dict(self):
        diag = self.diag_side([self.top_parts[2].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[2]
        order = [[p_niche, self.niche_ofs, 'st'], [diag, self.diag, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1], None], [2, self.top_parts[2], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, cogs_bend=cogs_bend, tag=tag, holes=holes, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortened(self.edges[1], self.cogs_bend)
        self.bottom = Bottom(self.edges[3])
        self.side = [HolesSideTwo(self.edges[2], True), HolesSideOne(self.edges[0], False)]

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
        fres = [rh.Curve.DuplicateCurve(self.side[0].fres), rh.Curve.DuplicateCurve(self.side[1].fres)]
        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut(self):
        cut = [rh.Curve.JoinCurves([self.side[0].join, self.top.fres, self.side[1].join, self.bottom.fres])[0]]
        [i.Transform(self.bound_plane) for i in cut]
        return cut

    @property
    def grav(self):
        new = self.mark_back
        return new

    @property
    def top_parts(self):
        top = [self.side[0].top_part.DuplicateCurve(), self.side[1].top_part.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in top]
        return top

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

    def __init__(self, surf, holes=None, tag=None, cogs_bend=False,  **kwargs):
        NichePanel.__dict__['__init__'](self, surf=surf, holes=holes, tag=tag, cogs_bend=cogs_bend, **kwargs)

        self.__dict__.update(**kwargs)
        #self.surf_rev = self.surf.Duplicate()
        #self.surf_rev.Flip()
        self.extend = self.extend_surf()

        unrol = rh.Unroller(self.surf)

        if hasattr(self, 'rebra'):
            self.intersections = self.rebra_intersect('b')
            unrol.AddFollowingGeometry(curves=self.intersections)
        else:
            pass

        self.unrol = unrol.PerformUnroll()

        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D
        self.gen_side_types()

    def gen_side_types(self):
        self.top = Bottom(self.edges[0])
        self.bottom = Bottom(self.edges[2])
        self.side = [Side(self.edges[3]), Side(self.edges[1])]

        self.side_types = [self.top, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def extend_surf(self):
        surf = self.surf.Surfaces[0].Duplicate()
        interv = surf.Domain(0)
        interv = rh.Interval(interv[0] - 50, interv[1] + 50)

        surf.Extend(0, interv)
        extr = rh.Surface.ToBrep(surf)

        return extr
