"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"
try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

otgib_side = globals()['otgib_side']
otgib_niche = globals()['otgib_niche']
panels = globals()['panels']
import Rhino.Geometry as rh
import ghpythonlib.treehelpers as th
import math


# a = th.tree_to_list(panels)


def angle_ofs(angle, side, met_left):
    ang = math.radians((180 - angle) / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad


def right_angle_ofs(side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad


def trim_with_frame(frame, surf):
    tr = rh.Brep.Trim()


def get_plane(surf, edge, edge_point):
    point_surf = surf.Faces[0].ClosestPoint(edge_point)
    eval_surf = surf.Faces[0].FrameAt(point_surf[1], point_surf[2])[1]
    point_edge = edge.ClosestPoint(edge_point)
    eval_edge = edge.FrameAt(point_edge[1])[1]
    frame = rh.Plane(eval_surf.Origin, eval_edge.XAxis, eval_surf.ZAxis)
    return frame


class BendSide:
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_side

    @property
    def eval_frame(self):
        frame = get_plane(self.base_surf, self.edge, self.edge.PointAtStart)
        self._eval_frame = rh.Plane(frame.Origin, frame.ZAxis, -frame.YAxis)
        return self._eval_frame

    @property
    def surf_otgib(self):
        if self.otgib is not None:
            otg = self.transpose_otgib()
            extr = rh.SweepOneRail()
            extr = extr.PerformSweep(self.edge, [otg])[0]
            self._surf_otgib = extr.CapPlanarHoles(0.1)
        else:
            self._surf_otgib = None
        return self._surf_otgib

    def __init__(self, edge, base_surf):
        self.base_surf = base_surf
        self.edge = self.curve_offset(edge)

    def curve_offset(self, curve):
        crv = curve.OffsetOnSurface(self.base_surf.Faces[0], self.side_offset, 0.01)
        return crv[0]

    def transpose_otgib(self):

        tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, self.eval_frame)
        otg = self.otgib.Duplicate()
        otg.Transform(tr)
        surf_otgib = rh.Brep.CreateContourCurves(otg, self.eval_frame)[0]

        return surf_otgib


class Niche(BendSide):
    angle = 45
    side = 0.3
    met_left = 0.5
    side_offset = right_angle_ofs(side, met_left)
    otgib = otgib_niche

    @property
    def trim_otgib(self):
        frame_one = get_plane(self.base_surf, self.edge, self.edge.PointAtStart)
        frame_one = rh.Plane(frame_one.Origin, frame_one.ZAxis, frame_one.YAxis)
        tr = rh.Transform.Rotation(math.radians(60), frame_one.XAxis, frame_one.Origin)
        frame_one.Transform(tr)
        trim_planes = self.surf_otgib.Trim(frame_one, 0.1)[0]

        frame_two = get_plane(self.base_surf, self.edge, self.edge.PointAtEnd)
        frame_two = rh.Plane(frame_two.Origin, frame_two.ZAxis, frame_two.YAxis)
        tr = rh.Transform.Rotation(math.radians(120), frame_two.XAxis, frame_two.Origin)
        frame_two.Transform(tr)
        trim_otgib = trim_planes.Trim(frame_two, 0.1)[0]
        self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)

        return self._trim_otgib

    def __init__(self, edge, base_surf):
        BendSide.__init__(self, edge, base_surf)


class Schov(BendSide):
    side_offset = 1.25
    otgib = None

    def __init__(self, edge, base_surf):
        BendSide.__init__(self, edge, base_surf)


class Side(BendSide):
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_side

    @property
    def trim_otgib(self):
        if self.reverse is False:
            frame_one = get_plane(self.base_surf, self.edge, self.edge.PointAtStart)
            frame_one = rh.Plane(frame_one.Origin, frame_one.ZAxis, frame_one.YAxis)
            tr = rh.Transform.Rotation(math.radians(60), frame_one.XAxis, frame_one.Origin)
            frame_one.Transform(tr)
            trim_otgib = self.surf_otgib.Trim(frame_one, 0.1)[0]
            self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)
        else:
            frame_two = get_plane(self.base_surf, self.edge, self.edge.PointAtEnd)
            frame_two = rh.Plane(frame_two.Origin, frame_two.ZAxis, frame_two.YAxis)
            tr = rh.Transform.Rotation(math.radians(120), frame_two.XAxis, frame_two.Origin)
            frame_two.Transform(tr)
            trim_otgib = self.surf_otgib.Trim(frame_two, 0.1)[0]
            self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)

        return self._trim_otgib

    def __init__(self, edge, base_surf, reverse):
        BendSide.__init__(self, edge, base_surf)
        self.reverse = reverse


class Panel:

    @property
    def surf_top(self):
        s = rh.Brep.CreateEdgeSurface([self.niche.edge, self.side[0].edge, self.schov.edge, self.side[1].edge])
        self._surf_top = s
        return self._surf_top

    @property
    def surf_otgib(self):
        self._surf_otgib = [self.niche.trim_otgib, self.side[0].trim_otgib, self.side[1].trim_otgib]
        # self._surf_otgib = [self.niche.surf_otgib, self.side[0].surf_otgib, self.side[1].surf_otgib]
        return self._surf_otgib

    def __init__(self, surface, type):
        self.surface = surface
        self.type = type
        self.edges = self.surface.Curves3D
        self.side_types()

    def side_types(self):

        if self.type == 0:
            self.niche = Niche(self.edges[3], self.surface)
            self.schov = Schov(self.edges[1], self.surface)
            self.side = [Side(self.edges[0], self.surface, False), Side(self.edges[2], self.surface, True)]

        else:
            self.niche = Niche(self.edges[1], self.surface)
            self.schov = Schov(self.edges[3], self.surface)
            self.side = [Side(self.edges[0], self.surface, True), Side(self.edges[2], self.surface, False)]

        self.side_types = [self.niche, self.schov, self.side[0], self.side[1]]
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self.side_types):
            param = []
            for ind, val in enumerate(self.side_types):
                if i != ind:
                    inters = rs.CurveCurveIntersection(v.edge, val.edge)
                    if inters is not None:
                        param.append(inters[0][5])
            param = sorted(param)

            trimed = rh.Curve.Trim(v.edge, param[0], param[1])
            v.edge = trimed


o_left = []
s_left = []
o_right = []
s_right = []
a = []

for i in panels[0::2]:
    pan = Panel(i, 0)
    s_left.append(pan.surf_top)
    o_left.append(pan.surf_otgib)
    a.append(pan.niche.eval_frame)

for i in panels[1::2]:
    pan = Panel(i, 1)
    s_right.append(pan.surf_top)
    o_right.append(pan.surf_otgib)
    a.append(pan.niche.eval_frame)

o_left = th.list_to_tree(o_left)
o_right = th.list_to_tree(o_right)
