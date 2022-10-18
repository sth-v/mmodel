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

import Rhino.Geometry as rh
import math
def get_plane(surf, edge, edge_point):
    point_surf = surf.Faces[0].ClosestPoint(edge_point)
    eval_surf = surf.Faces[0].FrameAt(point_surf[1], point_surf[2])[1]
    point_edge = edge.ClosestPoint(edge_point)
    eval_edge = edge.FrameAt(point_edge[1])[1]
    frame = rh.Plane(eval_surf.Origin, eval_edge.XAxis, eval_surf.ZAxis)
    return frame

def angle_ofs(angle, side, met_left):
    ang = math.radians(90/2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad / math.tan(math.radians(angle/2))


def right_angle_ofs(side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad

def niche_offset(angle, side, met_left):
    d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    return d * math.tan(math.radians(angle))



class BendSide:
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_niche

    @property
    def eval_frame(self):
        point_surf = self.base_surf.Faces[0].ClosestPoint(self.edge.PointAtEnd)
        eval_surf = self.base_surf.Faces[0].FrameAt(point_surf[1], point_surf[2])[1]
        point_edge = self.edge.ClosestPoint(self.edge.PointAtEnd)
        eval_edge = self.edge.FrameAt(point_edge[1])[1]
        frame = rh.Plane(eval_surf.Origin, eval_edge.XAxis, eval_surf.ZAxis)

        if self.type == 0:
            self._eval_frame = rh.Plane(frame.Origin, frame.ZAxis, frame.YAxis)
        else:
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

    def __init__(self, edge, base_surf, type):
        self.base_surf = base_surf
        self.edge = self.curve_offset(edge)
        self.type = type

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


class Niche(BendSide):
    angle = 45
    side = 0.3
    met_left = 0.5
    side_offset = niche_offset(angle, side, met_left) + angle_ofs(angle, side, met_left)
    otgib = otgib_niche

    @property
    def trim_otgib(self):
        frame_one = get_plane(self.base_surf, self.edge, self.edge.PointAtStart)
        frame_one = rh.Plane(frame_one.Origin, frame_one.YAxis, frame_one.XAxis)
        tr = rh.Transform.Rotation(math.radians(60), frame_one.XAxis, frame_one.Origin)
        frame_one.Transform(tr)
        trim_planes = self.surf_otgib.Trim(frame_one, 0.1)[0]

        frame_two = get_plane(self.base_surf, self.edge, self.edge.PointAtEnd)
        frame_two = rh.Plane(frame_two.Origin, frame_two.YAxis, frame_two.XAxis)
        tr = rh.Transform.Rotation(math.radians(120), frame_two.XAxis, frame_two.Origin)
        frame_two.Transform(tr)
        #trim_otgib = trim_planes.Trim(frame_two, 0.1)[0]
        #self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)
        self._trim_otgib=frame_two

        return self._trim_otgib
    def __init__(self, edge, base_surf, type):
        BendSide.__init__(self, edge, base_surf, type)


class Bottom(BendSide):
    side_offset = None
    otgib = None

    def __init__(self, edge, base_surf, type):
        BendSide.__init__(self, edge, base_surf, type)


class Side(BendSide):
    side_offset = 0.5
    otgib = None

    def __init__(self, edge, base_surf, type):
        BendSide.__init__(self, edge, base_surf, type)


class Panel:
    @property
    def niche_otgib(self):
        self._niche_otgib = self.niche.trim_otgib
        return self._niche_otgib

    @property
    def surf_trimed(self):
        s = rh.Brep.CreateEdgeSurface([self.niche.edge, self.side[0].edge, self.bottom.edge, self.side[1].edge])
        self._surf_trimed = s
        return self._surf_trimed

    def __init__(self, surface, type):
        self.surface = surface
        self.type = type
        self.edges = self.surface.Curves3D
        self.side_types()

    def side_types(self):

        self.niche = Niche(self.edges[3], self.surface, self.type)
        self.bottom = Bottom(self.edges[1], self.surface, self.type)
        self.side = [Side(self.edges[0], self.surface, self.type), Side(self.edges[2], self.surface, self.type)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
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


n_left=[]
s_left=[]
n_right = []
s_right = []
b=[]
a=[]

for i in niche_left[0:3]:
    pan = Panel(i, 0)
    s_left.append(pan.surf_trimed)
    n_left.append(pan.niche_otgib)
    b.append(pan.niche.eval_frame)
    a.append(pan.niche.edge)

for i in niche_right[0:3]:
    pan = Panel(i, 1)
    s_right.append(pan.surf_trimed)
    n_right.append(pan.niche_otgib)
    b.append(pan.niche.eval_frame)
    a.append(pan.niche.edge)