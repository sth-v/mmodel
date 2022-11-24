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
import copy
import os
import sys

import Rhino.Geometry as rh
import math

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    os.environ["MMODEL_DIR"] = "/Users/andrewastakhov/PycharmProjects/mmodel"
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs",
         os.getenv("MMODEL_DIR") + "/panels_gh/tagging"])


def plane(edge, target, param, param_val):
    ptt2 = edge.PointAt(edge.ClosestPoint(param)[1])
    vec = rh.Vector3d(ptt2.X - param.X, ptt2.Y - param.Y, ptt2.Z - param.Z)

    xvec = rh.Vector3d.CrossProduct(target.TangentAt(target.NormalizedLengthParameter(param_val)[1]), vec)
    frame = rh.Plane(param, vec, xvec)
    return frame


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
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_niche

    def __init__(self, edge, base_surf, type):
        object.__init__(self)
        self.base_surf = base_surf  # type: rh.Brep
        self.edge = self.curve_offset(edge)
        self.type = type

    @property
    def eval_frame(self):

        t = 0.0001
        ptt = self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1])

        if self.type == 0:
            r2 = self.base_surf.Edges[0].ToNurbsCurve()
        else:
            r2 = self.base_surf.Edges[2].ToNurbsCurve()

        ptt2 = r2.PointAt(r2.ClosestPoint(ptt)[1])
        vec = rh.Vector3d(ptt2.X - ptt.X, ptt2.Y - ptt.Y, ptt2.Z - ptt.Z)
        xvec = rh.Vector3d.CrossProduct(self.edge.TangentAt(self.edge.NormalizedLengthParameter(t)[1]), vec)

        if self.type == 0:
            frame = rh.Plane(self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1]), -vec, -xvec)
            fr = copy.deepcopy(frame)
            fr.Flip()
            fr.Rotate(math.pi * 0.5, frame.Normal)
        else:
            frame = rh.Plane(self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1]), -vec, -xvec)
            fr = copy.deepcopy(frame)
            #fr.Flip()
            #fr.Rotate(math.pi * 0.5, frame.Normal)



        self._eval_frame = fr

        return self._eval_frame

    @property
    def surf_otgib(self):
        if self.otgib is not None:
            otg = self.transpose_otgib()

            swp = rh.SweepOneRail()
            #self.edge.Reverse()
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
            nrbc = crv[0].ToNurbsCurve()

            return nrbc
        else:
            nrb = curve.ToNurbsCurve()
            nrb.Reparameterize(1.0)
            return nrb

    def transpose_otgib(self):

        tr = rh.Transform.PlaneToPlane(rh.Plane.WorldXY, self.eval_frame)
        otg = copy.deepcopy(self.otgib)
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
        param_st = self.edge.PointAt(self.edge.NormalizedLengthParameter(0.0001)[1])
        param_e = self.edge.PointAt(self.edge.NormalizedLengthParameter(0.9999)[1])

        if self.type == 0:
            r2 = self.base_surf.Edges[0].ToNurbsCurve()
        else:
            r2 = self.base_surf.Edges[2].ToNurbsCurve()

        one = rh.Curve.DuplicateCurve(self.edge)
        frame_one = plane(r2, one, param_st, 0.0001)
        frame_two = plane(r2, one, param_e, 0.9999)

        tr = rh.Transform.Rotation(math.radians(120), frame_one.XAxis, frame_one.Origin)
        frame_one.Transform(tr)
        tr = rh.Transform.Rotation(math.radians(60), frame_two.XAxis, frame_two.Origin)
        frame_two.Transform(tr)

        trim_planes = self.surf_otgib.Trim(frame_one, 0.1)[0]
        trim_otgib = trim_planes.Trim(frame_two, 0.1)[0]
        self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)

        return self._trim_otgib

    def __init__(self, edge, base_surf, type):
        BendSide.__init__(self, edge, base_surf, type)


class Bottom(BendSide):
    side_offset = None
    otgib = None

    def __init__(self, edge, base_surf, type):
        BendSide.__init__(self, edge, base_surf, type)


class Side(BendSide):
    angle = 90
    side = 0.3
    met_left = 0.5
    side_offset = 0.5 + right_angle_ofs(side, met_left)
    otgib = otgib_side

    @property
    def eval_frame(self):

        t = 0.0001
        ptt = self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1])
        if self.side == 'right':
            r2 = self.base_surf.Edges[3].ToNurbsCurve()
        else:
            r2 = self.base_surf.Edges[1].ToNurbsCurve()

        ptt2 = r2.PointAt(r2.ClosestPoint(ptt)[1])
        vec = rh.Vector3d(ptt2.X - ptt.X, ptt2.Y - ptt.Y, ptt2.Z - ptt.Z)

        xvec = rh.Vector3d.CrossProduct(self.edge.TangentAt(self.edge.NormalizedLengthParameter(t)[1]), vec)
        if self.type == 0:
            frame = rh.Plane(self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1]), -vec, -xvec)
            fr = copy.deepcopy(frame)

            fr.Flip()
            fr.Rotate(math.pi * 0.5, frame.Normal)
        else:
            frame = rh.Plane(self.edge.PointAt(self.edge.NormalizedLengthParameter(t)[1]), -vec, -xvec)
            fr = copy.deepcopy(frame)

            #fr.Flip()
            #fr.Rotate(math.pi * 0.5, frame.Normal)


        self._eval_frame = fr

        return self._eval_frame

    @property
    def trim_otgib(self):
        param_st = self.edge.PointAt(self.edge.NormalizedLengthParameter(0.0001)[1])
        param_e = self.edge.PointAt(self.edge.NormalizedLengthParameter(0.9999)[1])

        if self.side == 'right':
            r2 = self.base_surf.Edges[3].ToNurbsCurve()
        else:
            r2 = self.base_surf.Edges[1].ToNurbsCurve()

        frame_one = plane(r2, self.edge, param_st, 0.0001)
        frame_two = plane(r2, self.edge, param_e, 0.9999)


        tr = rh.Transform.Rotation(math.radians(120), frame_one.XAxis, frame_one.Origin)
        frame_one.Transform(tr)

        tr = rh.Transform.Rotation(math.radians(60), frame_two.XAxis, frame_two.Origin)
        frame_two.Transform(tr)



        trim_otgib = self.surf_otgib.Trim(frame_one, 0.1)[0]
        trim_otgib = trim_otgib.Trim(frame_two, 0.1)[0]
        self._trim_otgib = trim_otgib.CapPlanarHoles(0.1)

        return self._trim_otgib

    @property
    def surf_otgib(self):
        if self.otgib is not None:
            otg = self.transpose_otgib()

            swp = rh.SweepOneRail()

            extr, = swp.PerformSweep(self.edge, otg)

            self._surf_otgib = extr.CapPlanarHoles(0.1)
        else:
            self._surf_otgib = None
        return self._surf_otgib

    def __init__(self, edge, base_surf, type, side):
        BendSide.__init__(self, edge, base_surf, type)
        self.side = side


class Panel:

    @property
    def surf_trimed(self):
        s = rh.Brep.CreateEdgeSurface([self.niche.edge, self.side[0].edge, self.bottom.edge, self.side[1].edge])
        self._surf_trimed = s
        return self._surf_trimed

    def __init__(self, surface, type):
        self.surface = surface
        self.type = type
        self.edges = self.surface.Edges
        self.gen_side_types()

        self.niche_otgib = self.niche.trim_otgib
        self.right_side_otgib = self.side[0].trim_otgib
        self.left_side_otgib = self.side[1].trim_otgib

    def gen_side_types(self):
        if self.type == 0:
            self.niche = Niche(self.edges[0], self.surface, self.type)
            self.bottom = Bottom(self.edges[2], self.surface, self.type)
            self.side = [Side(self.edges[3], self.surface, self.type, 'right'),
                         Side(self.edges[1], self.surface, self.type, 'left')]
        else:
            self.niche = Niche(self.edges[0], self.surface, self.type)
            self.bottom = Bottom(self.edges[2], self.surface, self.type)
            self.side = [Side(self.edges[1], self.surface, self.type, 'right'),
                         Side(self.edges[3], self.surface, self.type, 'left')]

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

import ghpythonlib.treehelpers as th
n_left = []
s_left = []
n_right = []
s_right = []
n_left_side = []
n_right_side = []
for i in niche_left:
    pan = Panel(i, 0)
    s_left.append(pan.surf_trimed)
    n_left.append(pan.niche_otgib)
    n_left_side.append([pan.right_side_otgib, pan.left_side_otgib])


for i in niche_right:
    pan = Panel(i, 1)
    s_right.append(pan.surf_trimed)
    n_right.append(pan.niche_otgib)
    n_right_side.append([pan.right_side_otgib, pan.left_side_otgib])

n_right_side = th.list_to_tree(n_right_side)
n_left_side = th.list_to_tree(n_left_side)