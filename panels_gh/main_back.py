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
        if self.side_offset is not None:
            crv = curve.OffsetOnSurface(self.base_surf.Faces[0], self.side_offset, 0.01)
            return crv[0]
        else:
            return curve

    def transpose_otgib(self):

        tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, self.eval_frame)
        otg = self.otgib.Duplicate()
        otg.Transform(tr)
        surf_otgib = rh.Brep.CreateContourCurves(otg, self.eval_frame)[0]

        return surf_otgib


class Side(BendSide):
    side_offset = None
    otgib = None

    def __init__(self, edge, base_surf):
        BendSide.__init__(self, edge, base_surf)


class OtgSide(BendSide):
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_side

    @property
    def trim_otgib(self):
        frame_one = get_plane(self.base_surf, self.edge, self.edge.PointAtStart)
        frame_one = rh.Plane(frame_one.Origin, frame_one.ZAxis, frame_one.YAxis)
        tr = rh.Transform.Rotation(math.radians(60), frame_one.XAxis, frame_one.Origin)
        frame_one.Transform(tr)
        trim_otgib = self.surf_otgib.Trim(frame_one, 0.1)[0]

        frame_two = get_plane(self.base_surf, self.edge, self.edge.PointAtEnd)
        frame_two = rh.Plane(frame_two.Origin, frame_two.ZAxis, frame_two.YAxis)
        tr = rh.Transform.Rotation(math.radians(120), frame_two.XAxis, frame_two.Origin)
        frame_two.Transform(tr)
        trim_otgib = trim_otgib.Trim(frame_two, 0.1)[0]
        self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)

        return self._trim_otgib

    def __init__(self, edge, base_surf, reverse):
        BendSide.__init__(self, edge, base_surf)
        self.reverse = reverse


class Panel:

    @property
    def surf_top(self):
        s = rh.Brep.CreateEdgeSurface(
            [self.otg_side[0].edge, self.side[0].edge, self.otg_side[1].edge, self.side[1].edge])
        self._surf_top = s
        return self._surf_top

    @property
    def surf_otgib(self):
        self._surf_otgib = [self.otg_side[0].trim_otgib, self.otg_side[1].trim_otgib]
        return self._surf_otgib

    def __init__(self, surface):
        self.surface = surface
        self.edges = self.surface.Curves3D
        self.gen_side_types()

    def gen_side_types(self):

        self.side = [Side(self.edges[1], self.surface), Side(self.edges[3], self.surface)]
        self.otg_side = [OtgSide(self.edges[0], self.surface, False), OtgSide(self.edges[2], self.surface, True)]

        self.side_types = [self.otg_side[0], self.otg_side[1], self.side[0], self.side[1]]
        self.intersect()

    def intersect(self):
        for i, v in enumerate(self.side_types):
            old = v.edge.Domain
            v.edge = v.edge.Extend(rh.Interval(old[0] - 15, old[1] + 15))
            param = []
            for ind, val in enumerate(self.side_types):
                if i != ind:
                    old = val.edge.Domain
                    new = val.edge.Extend(rh.Interval(old[0] - 15, old[1] + 15))
                    inters = rs.CurveCurveIntersection(v.edge, new)
                    if inters is not None:
                        param.append(inters[0][5])
            param = sorted(param)

            trimed = rh.Curve.Trim(v.edge, param[0], param[1])
            v.edge = trimed


otgib = []
surf = []

for i in panels:
    pan = Panel(i)
    surf.append(pan.surf_top)
    otgib.append([pan.otg_side[0].trim_otgib, pan.otg_side[1].trim_otgib])

otgib = th.list_to_tree(otgib)
surf = th.list_to_tree(surf)
