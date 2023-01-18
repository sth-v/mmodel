import os

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
import ghpythonlib.components as comp
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
from main_sides import BendSide, Niche, Bottom, Side, NicheShortened, HolesSideOne, HolesSideTwo, BottomPanel, BoardHolesOne, \
    BoardHolesTwo, BottomBoard

reload(main_sides)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

main_panels.__init__("main_panels", "generic nodule")
from main_panels import NichePanel, SimplePanel, ArcPanel, MainPanel

reload(main_panels)


class BendLikePanel(SimplePanel):

    @property
    def bound_plane(self):
        fr = self.bottom.fres.FrameAt(self.bottom.fres.Domain[1])[1]
        bound_plane = rh.Plane(fr.Origin, -fr.XAxis, -fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, self.parent_plane)
        return tr

    @property
    def fres(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve()]
        if hasattr(self, 'parent_plane'):
            [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut_holes(self):
        cut = []
        for v in self.side:
            for i in v.holes_curve:
                ii = i.DuplicateCurve()

                if hasattr(self, 'parent_plane'):
                   ii.Transform(self.bound_plane)

                cut.append(ii)
        return cut

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join])[0]
        side = s.ToNurbsCurve()
        if hasattr(self, 'parent_plane'):
            side.Transform(self.bound_plane)
        return [side]

    def __init__(self, surf, tag=None, cogs_bend=None, **kwargs):
        SimplePanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend)

        self.edges = self.surf.Curves3D

        self.gen_side_types()

    def gen_side_types(self):
        self.niche = Side(self.edges[2])
        self.bottom = BottomBoard(self.edges[0])
        self.side = [HolesSideOne(self.edges[3], False), HolesSideTwo(self.edges[1], True)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()



class BoardPanel(MainPanel):
    bend_panel = 150

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].join, self.niche.join_region, self.side[1].join])[0]
        side = s.ToNurbsCurve()
        side = [side]+self.extra_panel.cut
        [i.Transform(self.bound_plane) for i in side]

        return side

    @property
    def fres(self):
        fres = [self.side[1].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[0].fres.DuplicateCurve(), self.bottom.fres.DuplicateCurve()] \
               + self.extra_panel.fres

        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut_holes(self):
        cut = []
        for v in self.side:
            for i in v.holes_curve:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)

        for i in self.extra_panel.cut_holes:
            ii = i.DuplicateCurve()
            ii.Transform(self.bound_plane)
            cut.append(ii)

        return cut + self.niche_holes

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        fr = self.niche.fres.FrameAt(self.niche.fres.Domain[0])[1]
        bound_plane = rh.Plane(rh.Point3d(b_r.Max[0], b_r.Min[1], 0), fr.XAxis, -fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def frame_dict(self):
        diag = self.diag_side([self.top_parts[2].PointAtEnd, self.top_parts[1].PointAtStart, self.fres[1].PointAtStart])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_niche, self.niche_ofs, 'st'], [diag, self.diag, False], [p_bend, self.bend_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1], None], [2, self.top_parts[2], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, top_surf=None, **kwargs):
        MainPanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend, holes=holes)

        self.top_surf = top_surf
        tup_unr = rh.Unroller(self.top_surf)
        self.top_unrol = tup_unr.PerformUnroll()[0][0]

        self.extra_panel = BendLikePanel(self.top_unrol)
        setattr(self.extra_panel, 'parent_plane', self.bottom.fres.FrameAt(self.bottom.fres.Domain[0])[1])

    def gen_side_types(self):

        self.niche = NicheShortened(self.edges[0], self.cogs_bend)
        self.bottom = BottomBoard(self.edges[2])
        self.side = [HolesSideTwo(self.edges[1]), HolesSideOne(self.edges[3])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def create_panel(self, curve):
        fr = curve.FrameAt(curve.Domain[0])[1]
        panel = rh.Rectangle3d(fr, curve.GetLength(), -self.bend_panel)
        corner = [panel.Corner(i) for i in range(4)]


        surf = rh.NurbsSurface.CreateFromCorners(corner[0], corner[1], corner[2], corner[3])
        surf = surf.ToBrep()
        return BendLikePanel(surf)
