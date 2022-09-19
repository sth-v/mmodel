import compas.geometry as cg
import math
from lahta.setup_view import view
from lahta.items import Bend, BendSegment, TransformableItem, ParentFrame3D, ParentFrameUnroll
import compas_occ.geometry as cc
import numpy as np

class Extrusion(TransformableItem):
    def __call__(self, *args, **kwargs):
        super().__call__( *args, **kwargs)


    def occ_extrusion(self, elems):
        try:
            inner_extr = cc.OCCNurbsSurface.from_extrusion(elems.inner, self.vector)
            outer_extr = cc.OCCNurbsSurface.from_extrusion(elems.outer, self.vector)
            setattr(elems, 'extrusion_inner', inner_extr)
            setattr(elems, 'extrusion_outer', outer_extr)
        except:
            unroll = cc.OCCNurbsSurface.from_extrusion(elems, self.vector)
            setattr(elems, 'unroll', unroll)

        return elems




class BendPanel(Extrusion):
    @ParentFrame3D
    def parent(self):
        return self.extrusion_line, self.normal

    @ParentFrameUnroll
    def unroll_parent(self):
        return self.extrusion_line, self.normal

    def __call__(self, *args, **kwargs):
        self._i = 0

        self.profile, self.extrusion_line, self.normal = args
        self.vector = cg.Vector.from_start_end(self.extrusion_line.start, self.extrusion_line.end)
        self.profile(parent_obj=self.parent)

        super().__call__(profile=self.profile, vector=self.vector, *args, **kwargs)
        while self._i < self.__len__():
            bend = next(self)
            self.bend_extr.append(bend)

    def __len__(self):
        return len(self.profile.obj_transform)

    def __next__(self):
        extrusion = self.profile.obj_transform[self._i]
        extrude_profile = self.occ_extrusion(extrusion)
        self._i += 1
        return extrude_profile






class Panel(TransformableItem):

    @property
    def tri_offset(self):
        self._tri_offset = self.bend_types[0].tri_offset
        return self._tri_offset

    @property
    def coor_offset(self):
        offset = cg.offset_polygon(self.coor_axis, self.tri_offset)
        self._coor_offset = cg.Polygon(offset)
        return self._coor_offset

    @property
    def normal(self):
        self._normal = [self.coor_offset.normal, self.coor_offset.normal, self.coor_offset.normal]
        return self._normal


    def __call__(self, coor_axis, bend_types, *args, **kwargs):
        super().__call__(coor_axis=coor_axis, bend_types=bend_types, *args, **kwargs)

        self.bend_types = bend_types
        self.bends = list(map(BendPanel, self.bend_types, self.coor_offset.lines, self.normal))



