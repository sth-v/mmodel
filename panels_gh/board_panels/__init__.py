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
    BoardHolesTwo, BottomBoard, BoardEdgeOne, BoardEdgeTwo, NicheShortenedBoard, HolesSideOneExtra

reload(main_sides)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

main_panels.__init__("main_panels", "generic nodule")
from main_panels import NichePanel, SimplePanel, ArcPanel, MainPanel

reload(main_panels)

def divide_edge(crv, ofs=20, num=2):
    if crv.GetLength() < 45:
        ofs = 10
    else:
        ofs = 20
    st = crv.ClosestPoint(crv.PointAtLength(ofs))[1]
    end = crv.ClosestPoint(crv.PointAtLength(crv.GetLength() - ofs))[1]
    curve = crv.Trim(st, end)

    if curve.GetLength() > 25:
        param = curve.DivideByCount(num, True)
        points = [curve.PointAt(i) for i in param]
    else:
        param = curve.DivideByCount(2, False)
        points = [curve.PointAt(i) for i in param]

    return points



class ArcConePanel(MainPanel):
    top_ofs = 45

    @property
    def bound_plane(self):
        cone = list(self.marks[1][len(self.pins_mark):])[0]

        xaxis = rh.Vector3d(cone.PointAt(cone.Domain[1] - 0.01) - cone.PointAt(cone.Domain[0] + 0.01))
        yaxis = rh.Vector3d(cone.PointAt(cone.Domain[1] - 0.01) - cone.PointAt(cone.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)

        j = rh.Curve.JoinCurves([self.side[0].join, self.niche.join, self.side[1].join, self.bottom.fres])[0]
        b_r = j.GetBoundingBox(rh.Plane.WorldXY)

        bound_plane = rh.Plane(b_r.Min, xaxis, yaxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, rh.Plane.WorldXY)

        return tr

    @property
    def frame_dict(self):

        diag = self.diag_side([self.top_parts[1].PointAtEnd, self.top_parts[0].PointAtStart, self.fres[1].PointAtEnd])
        top = self.fres[2]
        p_niche = self.fres[1]
        p_bend = self.fres[0]
        order = [[p_bend, self.bend_ofs, 'st'], [diag, self.diag, False], [p_niche, self.niche_ofs, 'both'],
                 [top, self.top_ofs, 'e']]
        bridge = [[2, self.top_parts[1], None], [0, self.top_parts[0], None], [3, self.top_parts[2], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    @property
    def pins_marker(self):
        unrol = list(self.marks[1][0:len(self.pins_mark)])
        rec = []
        for i in unrol:
            c = i.DuplicateCurve()
            c.Transform(self.bound_plane)
            rec.append(c)
        return rec

    @property
    def marker_curve(self):
        crv = [self.niche.fres.DuplicateCurve(), self.bottom.fres.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in crv]
        return crv

    @property
    def grav(self):
        if self.marks[2] is not None:
            unrol = list(self.marks[2][0:len(self.pins)])
            circ = []
            for i in unrol:
                c = rh.Circle(i, 3.25)
                c.Transform(self.bound_plane)
                circ.append(c.ToNurbsCurve())
            res = circ + self.pins_marker
            return res
        else:
            pass

    @property
    def grav_cone(self):
        if self.marks[1] is not None:
            unrol = list(self.marks[1][len(self.pins_mark):])
            crv = []
            for i in unrol:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                crv.append(ii)
            return crv
        else:
            pass


    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, pins=None, pins_mark=None, cone_mark=None, **kwargs):
        MainPanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend, holes=holes)

        self.pins = pins
        self.pins_mark = pins_mark
        self.c_mark = cone_mark

        marks = rh.Unroller(brep=self.surf)
        if self.pins is not None:
            p = [self.surf.ClosestPoint(i) for i in self.pins]
            marks.AddFollowingGeometry(points=p)
            marks.AddFollowingGeometry(curves=self.pins_mark)

            marks.AddFollowingGeometry(curves=self.c_mark)

        self.marks = marks.PerformUnroll()

        self.gen_side_types()

    def gen_side_types(self):

        self.niche = Niche(self.edges[0], self.cogs_bend)
        self.bottom = BottomPanel(self.edges[2])
        self.side = [HolesSideOne(self.edges[1], True), HolesSideTwo(self.edges[3], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()










class BendLikePanel(SimplePanel):

    @property
    def bound_plane(self):
        xaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[0] + 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[1] - 0.01))
        yaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[0] + 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[1] - 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)
        bound_plane = rh.Plane(self.bottom.fres.PointAt(self.bottom.fres.Domain[1]), xaxis, yaxis)
        tr = rh.Transform.PlaneToPlane(bound_plane, self.parent_plane)
        return tr

    @property
    def plane_disp(self):
        xaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[0] + 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[1] - 0.01))
        yaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[0] + 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[1] - 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)
        bound_plane = rh.Plane(self.bottom.fres.PointAt(self.bottom.fres.Domain[1]), xaxis, yaxis)
        return bound_plane

    @property
    def top_parts(self):
        top = [self.side[0].top_part.DuplicateCurve(), self.niche.top_part.DuplicateCurve(),
               self.side[1].top_part.DuplicateCurve()]
        [i.Transform(self.bound_plane) for i in top]
        return top

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

    @property
    def grav(self):
        if self.mark_crv is not None:
            unrol = list(self.mark_crv)
            circ = []
            for i in unrol:
                if i.GetLength() >= 150:
                    num =2
                else:
                    num= 1

                c = divide_edge(i, num=num)
                for ii in c:
                    cc = rh.Circle(ii, 3.25)
                    cc.Transform(self.bound_plane)
                    circ.append(cc.ToNurbsCurve())


            return circ
        else:
            pass

    def __init__(self, surf, tag=None, cogs_bend=None, mark_crv=None, **kwargs):
        SimplePanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend)

        self.mark_crv = mark_crv
        self.edges = self.surf.Curves3D

        self.gen_side_types()

    def gen_side_types(self):
        self.niche = Side(self.edges[1])
        self.bottom = BottomBoard(self.edges[3])
        self.side = [HolesSideOneExtra(self.edges[0], True), HolesSideOneExtra(self.edges[2], False)]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()



class BoardPanel(MainPanel):

    @property
    def top_parts(self):
        top = [self.side[0].top_part.DuplicateCurve(), self.niche.top_part.DuplicateCurve(),
               self.side[1].top_part.DuplicateCurve()]
        top += self.extra_panel.top_parts
        [i.Transform(self.bound_plane) for i in top]
        return top

    @property
    def cut(self):
        crv = [self.side[0].join, self.niche.join_region, self.side[1].join]+self.extra_panel.cut
        s = rh.Curve.JoinCurves(crv, 0.2)[0]
        side = s.ToNurbsCurve()
        side.Transform(self.bound_plane)

        return [side]

    @property
    def fres(self):
        s_o = rh.Curve.JoinCurves([self.side[1].fres.DuplicateCurve(), self.extra_panel.fres[0].DuplicateCurve()], 0.2)[0]
        s_t = rh.Curve.JoinCurves([self.side[0].fres.DuplicateCurve(), self.extra_panel.fres[2].DuplicateCurve()], 0.2)[0]
        fres = rh.Curve.JoinCurves([s_o.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                s_t.DuplicateCurve(), self.extra_panel.fres[1].DuplicateCurve()], 0.2)[0]

        tr = rh.Curve.Trim(self.bottom.fres.DuplicateCurve(), self.bottom.fres.Domain[0],  self.bottom.fres.Domain[1]-0.015 )
        fres = [fres, tr]

        [i.Transform(self.bound_plane) for i in fres]
        return fres

    @property
    def fres_for_frame(self):
        fres = [self.side[0].fres.DuplicateCurve(), self.niche.fres.DuplicateCurve(),
                self.side[1].fres.DuplicateCurve(), self.bottom.fres.DuplicateCurve()] \
               + self.extra_panel.fres

        [i.Transform(self.bound_plane) for i in fres]
        return fres


    @property
    def ribs_marker(self):
        pairs=[]
        for n, c in zip(self.mark_name, self.bend_mark[1::2]):

            cent = c.PointAtNormalizedLength(1.0)
            cent.Transform(self.bound_plane)
            pairs.append([n, cent])

        return pairs


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
    def grav(self):
        if self.crv_surf is not None:
            unrol = list(self.crv_surf)
            circ = []
            for i in unrol:
                c = divide_edge(i, num=2)
                for ii in c:
                    cc = rh.Circle(ii, 3.25)
                    cc.Transform(self.bound_plane)
                    circ.append(cc.ToNurbsCurve())

            for i in self.extra_panel.grav:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                circ.append(ii)

            for i in self.bend_mark:
                ii = i.DuplicateCurve()
                ii.Transform(self.bound_plane)
                circ.append(ii)

            return circ
        else:
            pass


    @property
    def parent_plane(self):
        xaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[1] - 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[0] + 0.01))
        yaxis = rh.Vector3d(self.bottom.fres.PointAt(self.bottom.fres.Domain[1] - 0.01) - self.bottom.fres.PointAt(
            self.bottom.fres.Domain[0] + 0.01))
        yaxis.Rotate(math.pi / 2, rh.Plane.WorldXY.ZAxis)
        parent_plane = rh.Plane(self.bottom.fres.PointAt(self.bottom.fres.Domain[0]), xaxis, yaxis)
        return parent_plane

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
        diag = self.diag_side([self.top_parts[0].PointAtEnd, self.top_parts[1].PointAtStart, self.fres_for_frame[1].PointAtStart])
        top = self.top_side()
        p_niche = self.fres_for_frame[1]
        p_bend = self.fres_for_frame[0]
        extra_bend = self.fres_for_frame[6]
        order = [[p_niche, self.niche_ofs, 'st'], [diag, self.diag, False], [p_bend, self.bend_ofs, 'both', 0.3],
                 [extra_bend, self.bend_ofs, 'both'], [top, self.top_ofs, 'e']]
        bridge = [[0, self.top_parts[1], None], [2, self.top_parts[0], None], [3, self.top_parts[5], None]]

        return {'p_niche': p_niche, 'p_bend': p_bend, 'order': order, 'bridge': bridge}

    def __init__(self, surf, tag=None, cogs_bend=None, holes=None, top_surf=None, top_mark=None, surf_mark=None,
                 crv_mark=None, **kwargs):
        MainPanel.__dict__['__init__'](self, surf=surf, tag=tag, cogs_bend=cogs_bend, holes=holes)

        self.mark_name = ['2', '3', '4', '5', '6']

        self.top_surf = top_surf
        tup_unr = rh.Unroller(self.top_surf)
        if top_mark is not None:
            tup_unr.AddFollowingGeometry(curves=top_mark)
        self.top_unrol = tup_unr.PerformUnroll()

        self.crv_surf = surf
        crv_surf = rh.Unroller(self.crv_surf)
        if surf_mark is not None:
            crv_surf.AddFollowingGeometry(curves=surf_mark+crv_mark)
        self.crv_surf = crv_surf.PerformUnroll()[1][0:5]
        self.bend_mark = crv_surf.PerformUnroll()[1][5:]

        self.extra_panel = BendLikePanel(self.top_unrol[0][0], mark_crv=self.top_unrol[1])
        setattr(self.extra_panel, 'parent_plane', self.parent_plane)

    def gen_side_types(self):

        self.niche = NicheShortenedBoard(self.edges[2], self.cogs_bend)
        self.bottom = BottomBoard(self.edges[0])
        self.side = [HolesSideTwo(self.edges[1]), HolesSideOne(self.edges[3])]

        self.side_types = [self.niche, self.bottom, self.side[0], self.side[1]]
        self.intersect()

    def top_side(self):
        join = rh.Curve.JoinCurves(self.fres_for_frame[0:3]+self.fres_for_frame[4:], 0.1)[0]
        bound_rec = rh.PolyCurve.GetBoundingBox(join, rh.Plane.WorldXY)
        top_side = bound_rec.GetEdges()[2]
        return top_side.ToNurbsCurve()



class BoardEdge(SimplePanel):
    @property
    def fres(self):
        #fres = [self.side[0].fres_shift.DuplicateCurve(), self.side[-1].fres_shift.DuplicateCurve()]
        fres = [self.side[4].fres_shift.DuplicateCurve(), self.side[5].fres_shift.DuplicateCurve()]
        return fres

    @property
    def cut(self):

        '''ss = [i.fres for i in self.side[1:-1]]

        side = rh.Curve.JoinCurves([self.side[0].join]+ss+[self.side[-1].join])[0]
        hls = self.side[0].holes_curve+self.side[-1].holes_curve'''
        ss = [i.fres for i in self.side[0:4]]

        side = rh.Curve.JoinCurves(ss+[self.side[4].join] + [self.side[5].join])[0]
        hls = self.side[4].holes_curve + self.side[5].holes_curve

        for i in hls:
            side = rh.Curve.CreateBooleanDifference(side,i)[0]

        fillet = rh.Curve.CreateFilletCornersCurve(side, 2, 0.1, 0.1)

        if len(self.unrol[1]) >=1:
            return [fillet] + list(self.unrol[1])
        else:
            return [fillet]


    @property
    def bound_frame(self):
        return self._bound_rect

    @property
    def all_elems(self):
        return self.cut

    def __init__(self, surf=None, holes=None, cogs_bend=None, tag=None, params=None):
        SimplePanel.__dict__['__init__'](self, surf, holes, cogs_bend, tag)

        self.trim_params = params

        unrol = rh.Unroller(self.surf)

        self.holes = holes
        if self.holes['point'] is not None:
            unrol.AddFollowingGeometry(curves=self.holes['point'])

        self.unrol = unrol.PerformUnroll()
        self.unrol_surf = self.unrol[0][0]
        self.edges = self.unrol_surf.Curves3D


        self.gen_side_types()
        edge1_vector = rh.Vector3d(self.edges[5].PointAtEnd - self.edges[5].PointAtStart)
        '''edge0_pt = self.edges[0].PointAt(self.edges[0].GetLength() / 2)
        edge3_pt = self.edges[3].PointAt(self.edges[3].GetLength() / 2)'''
        edge0_pt = self.edges[4].PointAt(self.edges[0].GetLength() / 2)
        edge3_pt = self.edges[5].PointAt(self.edges[3].GetLength() / 2)
        # edge2_vector = rh.Vector3d(self._cls.panel.edges[3].PointAtEnd - self._cls.panel.edges[3].PointAtStart)

        self._bound_rect, _ = comp.Bubalus_GH2.CurveMinBoundingBox(self.cut[0])


    edge2_vector = property(fget=lambda self: rh.Vector3d.CrossProduct(self.edge1_vector, rh.Vector3d(0, 0, 1)))
    edge1_vector = property(fget=lambda self: rh.Vector3d(self.edges[5].PointAtEnd - self.edges[5].PointAtStart))


    @property
    def plane(self):
        return rh.Plane(self._bound_rect.Center, self.edge1_vector, self.edge2_vector)

    # edge2_vector.Unitize()
    def gen_side_types(self):

        '''if list(self.edges)[-1].GetLength() >= 150:
            num = 2
        else:
            num = 1

        ss = [Bottom(i) for i in list(self.edges)[1:-1]]
        self.side = [BoardEdgeOne(list(self.edges)[0], params=self.trim_params.side, rev=True, spec_dist=2, tag=self.tag)] + ss + [BoardEdgeTwo(list(self.edges)[-1], params=self.trim_params.top, spec_dist=num, tag=self.tag)]
        self.side_types = self.side
        self.intersect()'''

        if list(self.edges)[4].GetLength() >= 150:
            num = 2
        else:
            num = 1

        ss = [Bottom(i) for i in list(self.edges)[0:4]]
        self.side = ss + [BoardEdgeTwo(list(self.edges)[4], params=self.trim_params.top, spec_dist=num, tag=self.tag)] + \
                    [BoardEdgeOne(list(self.edges)[5], params=self.trim_params.side, rev=True, spec_dist=2, tag=self.tag)]
        self.side_types = self.side
        self.intersect()

