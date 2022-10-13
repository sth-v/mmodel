"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"
try:
    rs=__import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs


import ghpythonlib.treehelpers as th
import Rhino.Geometry as rh
import math

#a = th.tree_to_list(panels)


def angle_ofs(angle, side, met_left):
    ang = math.radians((180-angle)/2)
    rad = ((side/2)/math.cos(ang)) + met_left
    return rad

def right_angle_ofs(side, met_left):
    ang = math.radians(90/2)
    rad = ((side/2)/math.cos(ang)) + met_left
    return rad

class BendSide:
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_side

    @property
    def eval_frame(self):
        point_surf = self.base_surf.Faces[0].ClosestPoint(self.edge.PointAtStart)
        eval_surf = self.base_surf.Faces[0].FrameAt( point_surf[1],  point_surf[2])[1]
        point_edge = self.edge.ClosestPoint(self.edge.PointAtStart)
        eval_edge = self.edge.FrameAt(point_edge[1])[1]
        frame = rh.Plane(eval_surf.Origin, eval_edge.XAxis, eval_surf.ZAxis)
        self._eval_frame =rh.Plane(eval_surf.Origin, frame.ZAxis, -frame.YAxis)
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

    def __init__(self, edge, base_surf):
        BendSide.__init__(self, edge, base_surf)

class Schov(BendSide):
    side_offset = 1.25
    otgib = None

    def __init__(self, edge, base_surf):
        BendSide.__init__(self,edge, base_surf)

class Side(BendSide):
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_side

    def __init__(self, edge, base_surf):
        BendSide.__init__(self, edge, base_surf)


class Panel:

    @property
    def surf_top(self):
        s = rh.Brep.CreateEdgeSurface([self.niche.edge, self.side[0].edge, self.schov.edge, self.side[1].edge])
        self._surf_top = s
        print(s)
        return self._surf_top

    def __init__(self, surface, type):
        self.surface = surface
        self.type = type
        self.edges = self.surface.Curves3D
        self.side_types()

    def side_types(self):

        if self.type == 0:
            self.niche = Niche(self.edges[3], self.surface)
            self.schov = Schov(self.edges[1], self.surface)
            self.side = [Side(self.edges[0], self.surface), Side(self.edges[2], self.surface)]

        else:
            self.niche = Niche(self.edges[1], self.surface)
            self.schov = Schov(self.edges[3], self.surface)
            self.side = [Side(self.edges[0], self.surface), Side(self.edges[2], self.surface)]

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

bbb=[]
ccc=[]
ddd=[]
e=[]


a = panels[0::2]
for i in a:
    pan = Panel(i, 0)
    bbb.append([pan.niche.edge, pan.schov.edge, pan.side[0].edge, pan.side[1].edge])
    ccc.append([pan.niche.eval_frame, pan.schov.eval_frame, pan.side[0].eval_frame, pan.side[1].eval_frame])
    ddd.append([pan.niche.surf_otgib, pan.schov.surf_otgib, pan.side[0].surf_otgib, pan.side[1].surf_otgib])
    e.append(pan.surf_top)

b=[]
c=[]
d=[]
for bb,cc,dd in zip(bbb,ccc,ddd):
    for i in bb:
        b.append(i)
    for i in cc:
        c.append(i)
    for i in dd:
        d.append(i)
