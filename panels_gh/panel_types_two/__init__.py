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
    NicheShortenedWard

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


class PW_1(ArcPanel):

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

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        ArcPanel.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Side(self.edges[1])
        self.side = [HolesSideOne(self.edges[0], True), HolesSideTwo(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

class PW_1_SH(PW_1):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [HolesSideOne(self.edges[0], True), NicheShortenedWard(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

class PW_2_SH(PW_1):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [NicheShortenedWard(self.edges[0], True), HolesSideTwo(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class PW_1_L(PW_1):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [HolesSideOne(self.edges[0], True), NicheShortenedWard(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()


class PW_2_L(PW_1):

    def __init__(self, surf=None, holes=None, pins=None, cogs_bend=None, tag=None, **kwargs):
        PW_1.__dict__['__init__'](self, surf=surf, holes=holes, pins=pins, cogs_bend=cogs_bend, tag=tag, **kwargs)

    def gen_side_types(self):
        self.niche = NicheShortenedBoard(self.edges[3], self.cogs_bend)
        self.bottom = Bottom(self.edges[1])
        self.side = [NicheShortenedWard(self.edges[0], True), HolesSideTwo(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()