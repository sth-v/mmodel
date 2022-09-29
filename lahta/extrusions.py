#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import json
import math

import compas.geometry as cg
import compas_occ.geometry as cc
import numpy as np
import rhino3dm
from more_itertools import pairwise

from lahta.items import Bend, ParentFrame3D, ParentFrame3D_end, StraightElement, TransformableItem
from lahta.setup_view import view
from mm.conversions.rhino import list_curves_to_polycurves, rhino_crv_from_compas


class Extrusion(TransformableItem):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    def occ_extrusion(self, elems, transf=None, line=None):
        if transf is not None:
            inner_extr = cc.OCCNurbsSurface.from_extrusion(elems.inner, self.vector)
            inner_extr = inner_extr.transformed(transf)
            outer_extr = cc.OCCNurbsSurface.from_extrusion(elems.outer, self.vector)
            outer_extr = outer_extr.transformed(transf)
            setattr(elems, 'extrusion_inner', inner_extr)
            setattr(elems, 'extrusion_outer', outer_extr)
        elif line is not None:
            unroll = cc.OCCNurbsSurface.from_extrusion(line, self.vector)
            setattr(elems, 'unroll', unroll)

        return elems

    def viewer(self, v, elems):
        v.add(elems.extrusion_inner.to_mesh())
        v.add(elems.extrusion_outer.to_mesh())
        return v

    def to_json(self, elems):
        with open('/Users/sofyadobycina/Documents/GitHub/mmodel/lahta/tests/triangle.json', mode='r') as j:
            my_data = json.load(j)
            i = elems.extrusion_inner.to_mesh(nu=15, nv=15).to_data()
            o = elems.extrusion_outer.to_mesh(nu=15, nv=15).to_data()
            my_data['triangle'].append(i)
            my_data['triangle'].append(o)

        with open('/Users/sofyadobycina/Documents/GitHub/mmodel/lahta/tests/triangle.json', mode='w') as jp:
            json.dump(my_data, jp)


class BendPanelExtrusion(Extrusion):
    param = 0.1

    @ParentFrame3D
    def extrusion_parent(self):
        return self.extrusion_line, self.normal

    @ParentFrame3D_end
    def extrusion_parent_end(self):
        return self.extrusion_line, self.normal

    @property
    def neigh_one(self):
        dist = self.param / (2 * math.cos((math.pi - (2 * self.angles[0])) / 2))
        self._neigh_one = (self.tri_offset - 1) / math.tan(self.angles[0]) - dist
        return self._neigh_one

    @property
    def neigh_two(self):
        dist = self.param / (2 * math.cos((math.pi - (2 * self.angles[1])) / 2))
        self._neigh_two = (self.tri_offset - 1) / math.tan(self.angles[1]) - dist
        return self._neigh_two

    @property
    def vector(self):
        vector = cg.Vector.from_start_end(self.extrusion_line.start, self.extrusion_line.end)
        self._vector = vector.unitized() * (vector.length + self.neigh_one + self.neigh_two)
        return self._vector

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        self._i = 0
        self.bend_extr = []

        self.profile, self.extrusion_line, self.normal, self.tri_offset, self.angles = args
        self.profile, self.extrusion_line, self.normal, self.tri_offset, self.angles = args

        self.profile(parent_obj=self.extrusion_parent_end)
        self.curve_one = [self.profile.inner, self.profile.outer]
        for i, v in zip(self.profile.inner, self.profile.outer):
            view.add(cg.Polyline(i.locus()), linewidth=2, linecolor=(1, 0, 0))
            view.add(cg.Polyline(v.locus()), linewidth=2, linecolor=(0, 1, 0))
        self.profile(parent_obj=self.extrusion_parent)
        self.curve_two = [self.profile.inner, self.profile.outer]
        for i, v in zip(self.profile.inner, self.profile.outer):
            view.add(cg.Polyline(i.locus()), linewidth=2, linecolor=(1, 0, 0))
            view.add(cg.Polyline(v.locus()), linewidth=2, linecolor=(0, 1, 0))

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
        transl = cg.Translation.from_vector(self.vector.unitized().inverted() * (self.neigh_one))

        extrude_profile = self.occ_extrusion(extrusion, transf=transl)

        self._i += 1
        # self.to_json(extrusion)
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
    @property
    def vector(self):
        vector = cg.Vector.from_start_end(self.extrusion_line.start, self.extrusion_line.end)
        self._vector = vector.unitized() * (vector.length - self.neigh_one - self.neigh_two)
        return self._vector

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
                transl_point = self.translation_vector(extrusion.length - n_o - n_t)
            except IndexError:
                transl_point = self.translation_vector(extrusion.length - n_o)

            line = cc.OCCNurbsCurve.from_line(cg.Line(self.point, transl_point))
            transl = cg.Translation.from_vector(self.vector.unitized() * (self.neigh_one))

            extrude_profile = self.occ_extrusion(extrusion, line=line.transformed(transl))

            self.point = transl_point
            self._i += 1

            # with open('/Users/sofyadobycina/Documents/GitHub/mmodel/lahta/tests/triangle.json', mode='r') as j:
            #   my_data = json.load(j)
            #  i = [v.to_polyline(n=2).to_data() for v in extrude_profile.unroll]
            # my_data['triangle'].append(i)

            # with open('/Users/sofyadobycina/Documents/GitHub/mmodel/lahta/tests/triangle.json', mode='w') as jp:
            # json.dump(my_data, jp)

            return extrude_profile

        else:
            self._i += 1

    def reload(self):
        self._i = 0
        self.point = self.extrusion_parent.point


class Panel(TransformableItem):

    @property
    def tri_offset(self):
        self._tri_offset = self.bend_types[0].tri_offset
        return self._tri_offset

    @property
    def coor_offset_extrusion(self):
        offset = cg.offset_polygon(self.coor_axis, self.tri_offset)
        self._coor_offset_extrusion = cg.Polygon(offset)
        return self._coor_offset_extrusion

    @property
    def coor_offset_unroll(self):
        offset = cg.offset_polygon(self.coor_axis, self.tri_offset / 2)
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
    def normal(self):
        self._normal = [self.coor_offset_extrusion.normal, self.coor_offset_extrusion.normal,
                        self.coor_offset_extrusion.normal]
        return self._normal

    def __call__(self, coor_axis, bend_types, *args, **kwargs):
        super().__call__(coor_axis=coor_axis, bend_types=bend_types, *args, **kwargs)

        self.bend_types = bend_types
        self.bends_extrusion = list(
            map(BendPanelExtrusion, self.bend_types, self.coor_offset_extrusion.lines, self.normal,
                np.repeat(self.tri_offset, 3), self.angles))
        self.bends_unroll = list(map(BendPanelUnroll, self.bend_types, self.coor_offset_unroll.lines, self.normal,
                                     np.repeat(self.tri_offset, 3), self.angles))


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
            map(self.extrusion_type, self.bend_types, self.coor_offset_extrusion.lines, self.normal,
                np.repeat(self.tri_offset, 3), self.angles))
        self.bends_unroll = list(map(self.unroll_type, self.bend_types, self.coor_offset_unroll.lines, self.normal,
                                     np.repeat(self.tri_offset, 3), self.angles))


class RhinoFriendlyPanel(TypingPanel):
    extrusion_type = StrongBendExtrusion
