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
import copy

def angle_ofs(angle, side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad / math.tan(math.radians(angle / 2))


def right_angle_ofs(side, met_left):
    ang = math.radians(90 / 2)
    rad = ((side / 2) / math.cos(ang)) + met_left
    return rad


def niche_offset(angle, side, met_left):
    d = angle_ofs(angle, side, met_left) - right_angle_ofs(side, met_left)
    return d * math.tan(math.radians(angle))


class BendSide(object):


    angle = 90
    side = 0.3
    met_left = 0.5
    _eval_frame = None  # type: rh.Plane
    otgib = otgib_niche

    def __init__(self, edge, base_surf, type):
        object.__init__(self)
        self.base_surf = base_surf # type: rh.Brep
        self.edge = self.curve_offset(edge)
        self.type = type

    @property
    def eval_frame(self):
        t=0.0001
        ptt=self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1])

        r2=self.base_surf.Edges[1].ToNurbsCurve()
        ptt2=r2.PointAt(r2.ClosestPoint(ptt)[1])
        print ptt2
        vec=rh.Vector3d(ptt2.X-ptt.X,ptt2.Y-ptt.Y,ptt2.Z-ptt.Z)

        xvec=rh.Vector3d.CrossProduct(self.edge.TangentAt(self.edge.NormalizedLengthParameter(t)[1]),vec)

        frame = rh.Plane(self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1]), vec, xvec )

        if self.type == 0:

            fr = copy.deepcopy(frame)
            fr.Flip()
            fr.Rotate(math.pi * 0.5, frame.Normal)
            self._eval_frame = fr
        else:
            fr = copy.deepcopy(frame)

            fr.Rotate(math.pi * 1, frame.Normal)
            self._eval_frame = fr

        return self._eval_frame

    @property
    def surf_otgib(self):
        if self.otgib is not None:
            otg = self.transpose_otgib()

            swp=rh.SweepOneRail()
            extr, = swp.PerformSweep(self.edge, otg)

            self._surf_otgib = extr.CapPlanarHoles(0.1)
        else:
            self._surf_otgib = None
        return self._surf_otgib

    def curve_offset(self, curve):
        # type: (rh.Curve) -> rh.NurbsCurve
        if self.side_offset is not None:
            nrb = curve.ToNurbsCurve()
            nrb.Reparameterize(1.0)
            crv = nrb.OffsetOnSurface(self.base_surf.Faces[0], self.side_offset, 0.01)
            nrbc=crv[0].ToNurbsCurve()


            return nrbc
        else:
            nrb=curve.ToNurbsCurve()
            nrb.Reparameterize(1.0)
            return nrb

    def transpose_otgib(self):

        tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, self.eval_frame)
        otg = copy.deepcopy(self.otgib)
        otg.Transform(tr)
        surf_otgib = rh.Brep.CreateContourCurves(otg, self.eval_frame)[0]

        return surf_otgib
    @property
    def side_offset(self):
        return  0.5 + right_angle_ofs(self.side, self.met_left)
class Niche(BendSide):
    angle = 45
    side = 0.3
    met_left = 0.5

    otgib = otgib_niche

    def __init__(self, edge, base_surf, type):
        BendSide.__init__(self, edge, base_surf, type)
    @property
    def side_offset(self):
        return  niche_offset(self.angle, self.side, self.met_left) + angle_ofs(self.angle, self.side, self.met_left)
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
        self._niche_otgib = self.niche.surf_otgib
        return self._niche_otgib

    @property
    def surf_trimed(self):
        s = rh.Brep.CreateEdgeSurface([self.niche.edge, self.side[0].edge, self.bottom.edge, self.side[1].edge])
        self._surf_trimed = s
        return self._surf_trimed

    def __init__(self, surface, type):
        self.surface = surface
        self.type = type
        self.edges = self.surface.Edges
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


class Pnl(Panel):
    def __init__(self, surface, type):
        Panel.__init__(self, surface, type)


n_left = []
s_left = []
n_right = []
s_right = []
n_left_edge=[]
n_right_edge=[]
for i in niche_left[0:3]:
    pan = Panel(i, 0)
    s_left.append(pan.surf_trimed)
    n_left.append(pan.niche_otgib)
    n_left_edge.append(pan.niche.eval_frame)
for i in niche_right[0:3]:
    pan = Panel(i, 1)
    s_right.append(pan.surf_trimed)
    n_right.append(pan.niche_otgib)
    n_right_edge.append(pan.niche.edge)
