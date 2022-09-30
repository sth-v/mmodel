#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import json
import math

import compas.geometry as cg
import compas_occ.geometry as cc
import numpy as np
import rhino3dm
from more_itertools import pairwise

from lahta.items import ParentFrame3D, StraightElement, TransformableItem, Bend, BendSegment, BendSegmentFres
from lahta.setup_view import view
from mm.conversions.rhino import list_curves_to_polycurves, rhino_crv_from_compas


class Extrusion(TransformableItem):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.inner_extr = []
        self.outer_extr = []
        self.unroll = []

    def occ_extrusion(self, elems, transf=None, line=None):
        if transf is not None:
            inner_extr = cc.OCCNurbsSurface.from_extrusion(elems.inner, self.vector)
            inner_extr = inner_extr.transformed(transf)
            print(transf)
            outer_extr = cc.OCCNurbsSurface.from_extrusion(elems.outer, self.vector)
            outer_extr = outer_extr.transformed(transf)
            setattr(elems, 'extrusion_inner', inner_extr)
            setattr(elems, 'extrusion_outer', outer_extr)
            self.inner_extr.append(inner_extr)
            self.outer_extr.append(outer_extr)

        elif line is not None:
            unroll = cc.OCCNurbsSurface.from_extrusion(line, self.vector).boundary()

            crv = unroll[0].to_polyline(n=2)
            join = cc.OCCNurbsCurve.from_line(cg.Line(crv.points[0], crv.points[1]))
            for i in unroll[1:]:
                crv = i.to_polyline(n=2)
                l = cc.OCCNurbsCurve.from_line(cg.Line(crv.points[0], crv.points[1]))
                join = join.joined(l)

            setattr(elems, 'unroll', join)
            self.unroll.append(join)

        return elems





class BendPanelExtrusion(Extrusion):

    @ParentFrame3D
    def extrusion_parent(self):
        return self.extrusion_line, self.normal

    @property
    def transl_frame(self):
        vec = cg.Vector.from_start_end(self.profile.inner[0].start, self.profile.outer[0].start)
        v = vec.unitized().inverted()*vec.length
        tr = cg.Translation.from_vector(v)
        self._transl_frame = self.extrusion_parent.transformed(tr)
        return self._transl_frame

    @property
    def vector(self):
        vector = cg.Vector.from_start_end(self.extrusion_line.start, self.extrusion_line.end)
        self._vector = vector.unitized() * self.lengths[0]
        return self._vector

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self._i = 0
        self.bend_extr = []

        self.profile, self.extrusion_line, self.normal,self.lengths = args
        self.profile(parent_obj=self.extrusion_parent)

        super().__call__(profile=self.profile, vector=self.vector, *args, **kwargs)
        self.point = self.extrusion_parent.point

        while self._i < self.__len__():
            bend = next(self)
            self.bend_extr.append(bend)

        self.reload()

    def __len__(self):
        return len(self.profile.obj_transform)

    def __next__(self):
        extrusion = self.profile.obj_transform[self._i]
        transl = cg.Translation.from_vector(self.vector.unitized() * (self.lengths[1]))

        extrude_profile = self.occ_extrusion(extrusion, transf=transl)

        self._i += 1
        return extrude_profile

    def reload(self):
        self._i = 0


class StrongBendExtrusion(BendPanelExtrusion):
    def __call__(self, profile: Bend, line: cg.Line, normal: cg.Vector, *args, **kwargs):
        super(StrongBendExtrusion, self).__call__(profile, line, normal, *args, **kwargs)

    @property
    def extrude_transform_rh(self):
        return rhino3dm.Transform.Translation(*np.array(self.vector))

    @property
    def inner_rh(self) -> rhino3dm.PolyCurve:
        return list_curves_to_polycurves(rhino_crv_from_compas(self.profile.inner))

    @property
    def outer_rh(self) -> rhino3dm.PolyCurve:
        return list_curves_to_polycurves(rhino_crv_from_compas(self.profile.outer))

    @property
    def extruded_inner_rh(self) -> rhino3dm.PolyCurve:
        i = self.inner_rh.Duplicate()
        i.Transform(self.extrude_transform_rh)
        return i

    @property
    def extruded_outer_rh(self) -> rhino3dm.PolyCurve:
        o = self.outer_rh.Duplicate()
        o.Transform(self.extrude_transform_rh)
        return o

    @property
    def extruded_cap_start_rh(self) -> rhino3dm.Line:
        return rhino3dm.NurbsCurve.CreateFromLine(
            rhino3dm.Line(self.extruded_inner_rh.PointAtStart, self.extruded_outer_rh.PointAtStart))

    @property
    def extruded_cap_end_rh(self) -> rhino3dm.Line:
        return rhino3dm.NurbsCurve.CreateFromLine(
            rhino3dm.Line(self.extruded_inner_rh.PointAtEnd, self.extruded_outer_rh.PointAtEnd))

    @property
    def cap_start_rh(self) -> rhino3dm.Line:
        return rhino3dm.NurbsCurve.CreateFromLine(rhino3dm.Line(self.inner_rh.PointAtStart, self.outer_rh.PointAtStart))

    @property
    def cap_end_rh(self) -> rhino3dm.Line:
        return rhino3dm.NurbsCurve.CreateFromLine(rhino3dm.Line(self.inner_rh.PointAtEnd, self.outer_rh.PointAtEnd))

    @property
    def extrusion_inner_rh(self):
        return rhino3dm.NurbsSurface.CreateRuledSurface(self.inner_rh, self.extruded_inner_rh)

    @property
    def extrusion_outer_rh(self):
        return rhino3dm.NurbsSurface.CreateRuledSurface(self.outer_rh, self.extruded_outer_rh)

    @property
    def extrusion_cap_start_rh(self):
        return rhino3dm.NurbsSurface.CreateRuledSurface(self.cap_start_rh, self.extruded_cap_start_rh)

    @property
    def extrusion_cap_end_rh(self):
        return rhino3dm.NurbsSurface.CreateRuledSurface(self.cap_end_rh, self.extruded_cap_end_rh)

    @property
    def extrusion_rh(self):
        # polycurve_a = list_curves_to_polycurves([self.outer_rh, self.cap_start_rh, self.inner_rh, self.cap_end_rh])
        # polycurve_b = polycurve_a.Duplicate()
        # polycurve_b.Transform(self.extrude_transform_rh)
        # rhino3dm.NurbsSurface.CreateRuledSurface(polycurve_a, polycurve_b)

        return [self.extrusion_cap_start_rh, self.extrusion_outer_rh, self.extrusion_cap_end_rh,
                self.extrusion_inner_rh]


class BendPanelUnroll(BendPanelExtrusion):


    def translation_vector(self, dist):
        vec = self.extrusion_parent.xaxis * dist
        transl = cg.Translation.from_vector(vec)
        return self.point.transformed(transl)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    def __len__(self):
        return len(self.profile.obj_transform)

    def __next__(self):

        extrusion = self.profile.obj_transform[self._i]

        if isinstance(extrusion, StraightElement):
            n_o = self.profile.obj_transform[self._i - 1].straight_len / 2
            try:
                n_t = self.profile.obj_transform[self._i + 1].straight_len / 2
                transl_point = self.translation_vector(extrusion.length_out + n_o + n_t)
            except IndexError:
                transl_point = self.translation_vector(extrusion.length_out + n_o)

            line = cc.OCCNurbsCurve.from_line(cg.Line(self.point, transl_point))
            transl = cg.Translation.from_vector(self.vector.unitized() * self.lengths[2])

            extrude_profile = self.occ_extrusion(extrusion, line=line.transformed(transl))

            self.point = transl_point
            self._i += 1

            return extrude_profile

        else:
            self._i += 1

    def reload(self):
        self._i = 0
        self.point = self.extrusion_parent.point

    @property
    def rhino_extrusion(self):
        l =[]
        for i in self.unroll:
            crv = rhino_crv_from_compas([i])
            crv = list_curves_to_polycurves(crv)
            l.append(crv)
        self._rhino_extrusion = l
        return self._rhino_extrusion




class Panel(TransformableItem):

    @property
    def tri_offset(self):
        self._tri_offset = self.bend_types[0].tri_offset
        return self._tri_offset

    @property
    def unroll_offset(self):
        self._unroll_offset = self.bend_types[0].unroll_offset
        return self._unroll_offset

    @property
    def coor_offset_extrusion(self):
        offset = cg.offset_polygon(self.coor_axis, self.tri_offset)
        self._coor_offset_extrusion = cg.Polygon(offset)
        return self._coor_offset_extrusion

    @property
    def coor_offset_unroll(self):
        dist = self.bend_types[0].unroll_offset
        offset = cg.offset_polygon(self.coor_axis, self.tri_offset-dist)
        self._coor_offset_unroll = cg.Polygon(offset)
        return self._coor_offset_unroll

    @property
    def angles(self):
        l_one = np.asarray(self.coor_offset_extrusion.lines)
        l_two = np.roll(l_one, 1, axis=0)
        angles = []
        for o, t in zip(l_one, l_two):
            vec_o = cg.Vector.from_start_end(o[1], o[0])
            vec_t = cg.Vector.from_start_end(t[0], t[1])
            angles.append(vec_o.angle(vec_t) / 2)
        angles.append(angles[0])
        self._angles = list(pairwise(angles))
        return self._angles

    @property
    def lengths(self):
        self._lengths =[]

        param = 0.01
        poly = cg.Polygon(self.coor_axis).lines
        for i, v in enumerate(poly):
            dist = (param / 2) / math.sin(self.angles[i][0])
            neigh_one = 1 / math.tan(self.angles[i][0])
            neigh_two = 1 / math.tan(self.angles[i][1])
            bend_l = v.length - neigh_one - neigh_two

            ofs_l = neigh_one * (1 - self.tri_offset)

            unrl_l = neigh_one * (1 - (self.tri_offset - self.unroll_offset))

            self._lengths.append([bend_l, ofs_l, unrl_l])

        return self._lengths

    @property
    def normal(self):
        self._normal = [self.coor_offset_extrusion.normal, self.coor_offset_extrusion.normal,
                        self.coor_offset_extrusion.normal]
        return self._normal

    def __call__(self, coor_axis, bend_types, *args, **kwargs):
        super().__call__(coor_axis=coor_axis, bend_types=bend_types, *args, **kwargs)


        self.bend_types = bend_types
        #self.bends_extrusion = list(
            #map(BendPanelExtrusion, self.bend_types, self.coor_offset_extrusion.lines, self.normal, self.lengths))
        self.bends_unroll = list(map(BendPanelUnroll, self.bend_types, self.coor_offset_unroll.lines, self.normal, self.lengths))


    def to_rhino(self):
        model = rhino3dm.File3dm()

        for unr in self.bends_unroll:
            #for i in ext.rhino_extrusion:
                #model.Objects.Add(i)

            for i in unr.rhino_extrusion:
                model.Objects.Add(i)

        poly = [cc.OCCNurbsCurve.from_line(i) for i in cg.Polygon(self.coor_axis).lines]
        crv_poly = rhino_crv_from_compas(poly)
        crv_poly = list_curves_to_polycurves(crv_poly)
        model.Objects.Add(crv_poly)

        poly_of = [cc.OCCNurbsCurve.from_line(i) for i in self.coor_offset_extrusion.lines]
        crv_poly_of = rhino_crv_from_compas(poly_of)
        crv_poly_of = list_curves_to_polycurves(crv_poly_of)
        model.Objects.Add(crv_poly_of)

        model.Write(f"/Users/sofyadobycina/Desktop/{hex(id(self))}.3dm")


class TypingPanel(Panel):
    unroll_type = BendPanelUnroll
    extrusion_type = BendPanelExtrusion

    def __call__(self, coor_axis, bend_types, *args, **kwargs):
        # Мне пришлось полностью переопределить __call__ для этой реализации,
        # только потому что классы было не достать.
        # Вся идея в том, чтобы объявить классы Unroll и Extrusion в качестве переменных.
        super(TransformableItem, self).__call__(coor_axis=coor_axis, bend_types=bend_types, *args, **kwargs)

        self.bend_types = bend_types
        self.bends_extrusion = list(
            map(self.extrusion_type, self.bend_types, self.coor_offset_extrusion.lines, self.normal, self.lengths))
        #self.bends_unroll = list(map(self.unroll_type, self.bend_types, self.coor_offset_unroll.lines, self.normal, self.lengths))


class RhinoFriendlyPanel(TypingPanel):

    """
    >>> from lahta.items import *
    >>> panel = RhinoFriendlyPanel(coor_axis=[[258.627489, 545.484455, 490.055883],
    ...                         [36.862172, -12.028006, 490.055883],
    ...                         [705.257292, 44.962907, 490.055883]],
    ...              bend_types=[
    ...                  Bend([BendSegmentFres(36, 0.8, 90, in_rad=0.3),
    ...                       BendSegment(18, 1.0, 90),
    ...                       BendSegment(7, 1.0, 90)]),
    ...                  Bend([BendSegmentFres(36, 0.8, 90, in_rad=0.3)]),
    ...                  Bend([BendSegmentFres(36, 0.8, 90, in_rad=0.3)])
    ...              ]
    ...              )
    >>> ext1=panel.bends_extrusion[0]
    >>> model=rhino3dm.File3dm()
    >>> [model.Objects.Add(ext) for ext in ext1.extrusion_rh]
    [UUID('08874b17-c8d0-4236-8c55-de433175eecc'),
     UUID('37e220fe-8f20-4b50-8d5d-15af571240f3'),
     UUID('29c41150-f50d-44e8-875e-68551084ce3d'),
     UUID('04bfec2a-60af-4a32-ba82-5c0014f116b2')]
    >>> [model.Objects.Add(ext) for ext in panel.bends_extrusion[1].extrusion_rh]
    [UUID('ea7c4044-6e79-4f25-b3d8-1875091fac16'),
     UUID('ada9f62c-6fcc-440e-9b31-bde88e6e4958'),
     UUID('affa554a-90fe-4594-bde5-71374ced1fc9'),
     UUID('0318af09-8a5f-4f5e-b5a6-c966c575fa2c')]
    >>> [model.Objects.Add(ext) for ext in panel.bends_extrusion[2].extrusion_rh]
    [UUID('b4df8ce7-2321-4780-96d3-437ce2231e3b'),
     UUID('780a9855-0a8a-472e-85ff-636a544147ba'),
     UUID('7addc705-4b07-4951-bc26-fa6fe63a73e9'),
     UUID('1faf1e87-d446-4b03-9389-68373e540095')]
    >>> model.Write("example.3dm")
    True
    """
    extrusion_type = StrongBendExtrusion
