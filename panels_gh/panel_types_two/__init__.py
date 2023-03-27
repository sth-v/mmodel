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
    RibsSide, HolesSideThree, RibsSideTwo, BoardEdgeOne, BoardEdgeTwo, NicheShortenedBoard, BottomBoard, BottomHeat, \
    NicheShortenedWard, NicheShortenedWardReverse

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



class PC_TW_1(ArcConePanel):
    @property
    def bound_plane(self):
        cone = list(self.marks[1][len(self.pins_mark):])[0]

        xaxis = rh.Vector3d(cone.PointAt(cone.Domain[1] - 0.01) - cone.PointAt(cone.Domain[0] + 0.01))
        yaxis = rh.Vector3d(cone.PointAt(cone.Domain[1] - 0.01) - cone.PointAt(cone.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        bound_plane = rh.Plane(b_r.Max, xaxis, yaxis)
        bpl = rh.Plane(cone.PointAt(cone.Domain[0]), xaxis, yaxis)
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

    @property
    def fres(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve(), self.bottom.fres.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].join, self.niche.join_region, self.side[1].join, self.bottom.join_region])[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)
        return [side]

    @property
    def bot_holes(self):
        cut = []
        reg = self.bottom.region_holes
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
                # p = rh.Circle(v, self.h_r[i]).ToNurbsCurve()
                ii = v.DuplicateCurve()
                ii.Transform(self.bound_plane)
                cut.append(ii)

        return cut + self.niche_holes + self.bot_holes


    def gen_side_types(self):
        self.niche = Niche(self.edges[1], self.cogs_bend)
        self.bottom = Niche(self.edges[3], self.cogs_bend)
        self.side = [HolesSideTwo(self.edges[0]), HolesSideOne(self.edges[2])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class PC_W_1(ArcConePanel):
    @property
    def bound_plane(self):
        cone = list(self.marks[1][len(self.pins_mark):])[0]

        xaxis = rh.Vector3d(cone.PointAt(cone.Domain[1] - 0.01) - cone.PointAt(cone.Domain[0] + 0.01))
        yaxis = rh.Vector3d(cone.PointAt(cone.Domain[1] - 0.01) - cone.PointAt(cone.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        bound_plane = rh.Plane(b_r.Max, xaxis, yaxis)
        bpl = rh.Plane(cone.PointAt(cone.Domain[0]), xaxis, yaxis)
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
        self.niche = Niche(self.edges[1], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[3])
        self.side = [HolesSideTwo(self.edges[0]), HolesSideOne(self.edges[2])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class PC_TW_2(PC_TW_1):
    @property
    def bound_plane(self):
        cone = list(self.marks[1][len(self.pins_mark):])[0]

        xaxis = rh.Vector3d(cone.PointAt(cone.Domain[0] - 0.01) - cone.PointAt(cone.Domain[1] + 0.01))
        yaxis = rh.Vector3d(cone.PointAt(cone.Domain[0] - 0.01) - cone.PointAt(cone.Domain[1] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        bound_plane = rh.Plane(b_r.Min, xaxis, yaxis)
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
        PC_TW_1.__dict__['__init__'](self, surf=surf, tag=tag, pins=pins, cogs_bend=cogs_bend, holes=holes, cone_mark=cone_mark, **kwargs)

    def gen_side_types(self):
        self.niche = Niche(self.edges[3], self.cogs_bend)
        self.bottom = Niche(self.edges[1], self.cogs_bend)
        self.side = [HolesSideTwo(self.edges[2]), HolesSideOne(self.edges[0])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class PC_W_2(PC_W_1):
    @property
    def bound_plane(self):
        cone = list(self.marks[1][len(self.pins_mark):])[0]

        xaxis = rh.Vector3d(cone.PointAt(cone.Domain[0] - 0.01) - cone.PointAt(cone.Domain[1] + 0.01))
        yaxis = rh.Vector3d(cone.PointAt(cone.Domain[0] - 0.01) - cone.PointAt(cone.Domain[1] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        bound_plane = rh.Plane(b_r.Min, xaxis, yaxis)
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
        PC_W_1.__dict__['__init__'](self, surf=surf, tag=tag, pins=pins, cogs_bend=cogs_bend, holes=holes, cone_mark=cone_mark, **kwargs)

    def gen_side_types(self):
        self.niche = Niche(self.edges[3], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[1])
        self.side = [HolesSideTwo(self.edges[2]), HolesSideOne(self.edges[0])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()



class PW_1(ArcPanel):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        ArcPanel.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        fr = self.side[0].fres.FrameAt(self.side[0].fres.Domain[1])[1]
        bound_plane = rh.Plane(b_r.Min, fr.XAxis, fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr

    @property
    def frame_dict(self):
        diag = self.diag_side([self.top_parts[1].PointAtEnd, self.top_parts[0].PointAtStart, self.fres[1].PointAtEnd])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_bend, self.bend_ofs, 'st'], [diag, self.diag, 'both'], [p_niche, self.niche_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[2, self.top_parts[1], None], [0, self.top_parts[0], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    @property
    def fres(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve(), self.bottom.fres.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].join, self.niche.join_region, self.side[1].join, self.bottom.join])[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)
        return [side]

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Side(self.edges[1])
        self.side = [HolesSideOne(self.edges[0]), HolesSideTwo(self.edges[2])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

class PW_1_L(PW_1):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    '''@property
    def frame_dict(self):
        print(self.side)
        diag = self.diag_side([self.top_parts[1].PointAtEnd, self.top_parts[0].PointAtStart, self.fres[1].PointAtEnd])
        top = self.top_side()
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_bend, self.bend_ofs, 'st'], [diag, self.diag, 'both'], [p_niche, self.niche_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[2, self.top_parts[1], None], [0, self.top_parts[0], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}'''

    @property
    def bound_plane(self):
        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]

        b_r = j.GetBoundingBox(rh.Plane.WorldXY)
        fr = self.side[0].fres.FrameAt(self.side[0].fres.Domain[1])[1]
        bound_plane = rh.Plane(b_r.Min, fr.XAxis, fr.YAxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)
        return tr


    '''@property
    def top_parts(self):
        try:
            top = [self.side[0].top_part.DuplicateCurve(), self.niche.top_part.DuplicateCurve(),
                   self.bottom.top_part.DuplicateCurve()]
        except AttributeError:
            top = [self.side[1].top_part.DuplicateCurve(), self.niche.top_part.DuplicateCurve(),
                   self.bottom.top_part.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in top]
        return top'''

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Side(self.edges[1])
        self.side = [ NicheShortenedWardReverse(self.edges[0], False), BottomPanel(self.edges[0])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].fres, self.niche.join_region, self.side[1].join_region, self.bottom.join])[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)
        return [side]

class PW_2_L(PW_1_L):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1_L.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Side(self.edges[1])
        self.side = [BottomPanel(self.edges[0]), NicheShortenedWardReverse(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].fres, self.niche.join_region, self.side[1].join_region, self.bottom.join])[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)
        return [side]


class PW_1_S(PW_1):

    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join_region, self.bottom.join])[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)
        return [side]

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = Side(self.edges[3], True)
        self.bottom = Side(self.edges[1], True)
        self.side = [HolesSideOne(self.edges[0], True), NicheShortenedWard(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

class PW_2_S(PW_1):
    @property
    def cut(self):
        s = rh.Curve.JoinCurves([self.side[0].join_region, self.niche.join, self.side[1].join, self.bottom.join])[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)
        return [side]

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = Side(self.edges[3], False)
        self.bottom = Side(self.edges[1], True)
        self.side = [NicheShortenedWard(self.edges[0], False), HolesSideTwo(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()