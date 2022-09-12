from operator import itemgetter
from mm.baseitems import Item
import compas.geometry as cg

from lahta.setup_view import view
from lahta.items import Bend, BendSegment, TransformableItem, ParentFrame3D
import compas_occ.geometry as cc
import numpy as np
from compas import json_dumps


# from setup_view import view

# four = BendSegment(40, 1.8, 90)
# one = BendSegment(25, 1.8, 90)
# two = BendSegment(45, 1.8, 90)
# ttt = Bend([one, four, two])
# elem = ttt.outer


class Panel(TransformableItem):
    sides = [cc.OCCNurbsCurve.from_line(cg.Line([31.459455, -3.246879, 23.642172], [-10.688287, 30.550345, 18.114868])),
             cc.OCCNurbsCurve.from_line(
                 cg.Line([-10.688287, 30.550345, 18.114868], [-16.909711, -22.469931, 8.145925])),
             cc.OCCNurbsCurve.from_line(cg.Line([-16.909711, -22.469931, 8.145925], [31.459455, -3.246879, 23.642172]))]
    polyg = cg.normal_polygon(cg.Polygon(
        [[31.459455, -3.246879, 23.642172], [-10.688287, 30.550345, 18.114868], [-16.909711, -22.469931, 8.145925]]))
    polyg_vec = cg.Vector(*polyg).inverted()

    # @ParentFrame3D
    @property
    def parent_frame(self):
        y = cg.Vector.from_start_end([31.459455, -3.246879, 23.642172], [-10.688287, 30.550345, 18.114868]).unitized()
        x = cg.Vector.cross(y, self.polyg)
        self._parent_frame = cg.Frame([-10.688287, 30.550345, 18.114868], xaxis=x, yaxis=self.polyg_vec)
        return self._parent_frame

    def __call__(self, bend, *args, **kwargs):
        super().__call__(bend=bend, *args, **kwargs)

        for i in self.bend.bend_stage:
            i.fold(parent=self.parent_frame)
            i.straight(parent=self.parent_frame)
            i.viewer(view)

        for i in self.sides:
            view.add(cg.Polyline(i.locus()), linewidth=2, linecolor=(1, 0, 0))

        view.add(self.parent_frame, size=2)
        view.run()


class BendExtrusionMap(dict[Bend, list[cg.Transformation, cg.Transformation]]):

    def __init__(self):
        self._geom = []
        self.ordered = []

    def __setitem__(self, key: str, val: list[Bend, cg.Frame, cg.Vector]):
        if key not in self:
            len(self.ordered)
            self.ordered.append(key)
        fr, trans = val

        self.first = cg.Transformation.from_frame(fr)
        self.second = cg.Transformation(cg.transformations.matrix_from_translation(list(trans)))
        dict.__setitem__(self, key, [Bend, self.first, self.second])

    def to_compas(self):
        for k, v in self.items():
            f, s = v

            for g in k.to_compas():
                crv = cc.OCCCurve.from_data(g)
                crv.transform(f)

                extrusion = cc.surfaces.OCCExtrusionSurface(crv, s.translation_vector)
                crv2 = cc.OCCNurbsCurve.from_data(g)
                crv2.transform(f)
                crv2.transform(g)
                self._geom.append(dict(curves=(crv.data, crv2.data,), extrusion=extrusion.data))
        return self._geom


class NaivePanel(Item):
    vertices = np.array([[-16.848399354, -32.463546097, -1.400279116],
                         [-16.548399354, -31.863546097, -1.400279116],
                         [-17.148399354, -31.863546097, -1.400279116]])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bend = BendExtrusionMap()

    @property
    def transforms(self):
        for fr in np.stack(
                [np.roll(self.vertices, 1) - self.vertices,
                 np.roll(self.vertices, -1) - self.vertices]):
            ff, fs = cg.Frame(self.vertices[0], fr[1], np.array([0, 0, 1])), fr[1]
            print(ff)
            yield [ff, fs]

    @property
    def bends(self):
        return self._bend

    @bends.setter
    def bends(self, val):

        self._bend[val] = next(self.transforms)

    def to_compas(self):
        for b in self.bends:
            yield json_dumps(b.to_compas())
