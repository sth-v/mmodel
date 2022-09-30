#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import json
import math

import compas.geometry as cg
import compas_occ.geometry as cc
import numpy as np
import rhino3dm
from more_itertools import pairwise
from mm.conversions.rhino import rhino_crv_from_compas, list_curves_to_polycurves
from lahta.items import ParentFrame3D, StraightElement, TransformableItem
from lahta.setup_view import view


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
        tr = cg.Translation.from_vector(vec.inverted())
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

        self.profile, self.extrusion_line, self.normal, self.tri_offset, self.lengths = args
        self.profile(parent_obj=self.extrusion_parent)
        self.profile(parent_obj=self.transl_frame)

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
        # self.to_json(extrusion)
        return extrude_profile

    def reload(self):
        self._i = 0

    @property
    def rhino_extrusion(self):
        crv_in = rhino_crv_from_compas(self.profile.inner)
        crv_in = list_curves_to_polycurves(crv_in)

        ext_in = rhino3dm.Extrusion()
        extr_in = ext_in.Create(crv_in, self.vector.length, False)

        crv_out = rhino_crv_from_compas(self.profile.inner)
        crv_out = list_curves_to_polycurves(crv_out)

        ext_out = rhino3dm.Extrusion()
        extr_out = ext_out.Create(crv_out, self.vector.length, False)
        self._rhino_extrusion = [extr_in, extr_out]
        return self._rhino_extrusion





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

            rel_ofs = 1 / (1 - self.tri_offset)
            ofs_l = neigh_one * (1 - self.tri_offset)

            rel_unr = 1 / (1 - self.unroll_offset)
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
        self.bends_extrusion = list(
            map(BendPanelExtrusion, self.bend_types, self.coor_offset_extrusion.lines, self.normal,
                np.repeat(self.tri_offset, 3), self.lengths))
        self.bends_unroll = list(map(BendPanelUnroll, self.bend_types, self.coor_offset_unroll.lines, self.normal,
                                     np.repeat(self.tri_offset, 3), self.lengths))


    def to_rhino(self):
        model = rhino3dm.File3dm()

        for ext, unr in zip(self.bends_extrusion, self.bends_unroll):
            for i in ext.rhino_extrusion:
                model.Objects.Add(i)

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
