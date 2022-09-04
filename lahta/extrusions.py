
from operator import itemgetter
from mm.baseitems import Item
import compas.geometry as cg
from compas_gmsh.models import ShapeModel
from compas_view2.app import App
from lahta.items import Bend, BendSegment
import compas_occ.geometry as cc
from compas_cgal.booleans import boolean_union, boolean_difference, boolean_intersection
from compas_cgal.intersections import intersection_mesh_mesh
from compas_cgal.meshing import remesh
from compas.datastructures import Mesh
from compas_gmsh.models import CSGModel


import compas_occ.conversions as oconv
import compas_occ.brep as cb
from compas_view2.objects import Collection
from typing import MutableMapping
import numpy as np
from compas import json_dumps
from setup_view import view

four = BendSegment(40, 1.8, 90)
one = BendSegment(25, 1.8, 90)
two = BendSegment(45, 1.8, 90)
ttt = Bend([one, four, two])
elem = ttt.outer

class BendExtrusionMap(dict[Bend, list[cg.Transformation, cg.Transformation]]):

    def __init__(self):
        self._geom = []
        self.ordered = []

    def __setitem__(self, key:str,  val: list[Bend, cg.Frame, cg.Vector]):
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


class BendExtrusion(Item):
    extrusion = []

    def __call__(self, extr, *args, **kwargs):
        super().__call__(extr=extr, *args, **kwargs)

        join = extr[0]
        for i in extr[1:]:
            join = i.joined(join)

        surf = cc.OCCNurbsSurface.from_extrusion(join, cg.Vector.Zaxis()*30)
        surf_mesh = surf.to_mesh()

        #view.add(surf.to_mesh())
        view.add(cg.Polyline(join.locus()), linewidth=2, linecolor=(0, 0, 1))

        points = [surf.point_at(0.5, 0.7), surf.point_at(0.7, 0.7), surf.point_at(0.7, 0.2), surf.point_at(0.5, 0.2), surf.point_at(0.5, 0.7)]
        tr = cg.Translation.from_vector(cg.Vector.Xaxis()*10)
        point_tr = points[2].transformed(tr)

        #view.add(Collection(points))
        #view.add(point_tr)

        surf_face = cg.Box.from_corner_corner_height(points[3], point_tr, 10).faces
        surf_point = cg.Box.from_corner_corner_height(points[3], point_tr, 10).points
        polygon = []
        for i in surf_face:
            polygon.append(itemgetter(*i)(surf_point))


        surf_trim = Mesh.from_polygons(polygon)
        tr = cg.Translation.from_vector(cg.Vector.Xaxis()*(-5))
        surf_trim = surf_trim.transformed(tr)
        #view.add(surf_trim)
        A = surf_mesh.to_vertices_and_faces(triangulated=True)
        B = surf_trim.to_vertices_and_faces(triangulated=True)


        pointsets = intersection_mesh_mesh(A, B)
        polylines = []
        for points in pointsets:
            points = [cg.Point(*point) for point in points]
            polyline = cg.Polyline(points)
            polylines.append(polyline)

        view.add(Mesh.from_vertices_and_faces(*A), facecolor=(1, 0, 0), opacity=0.7)
        #view.add(Mesh.from_vertices_and_faces(*B), facecolor=(0, 1, 0), opacity=0.7)
        for polyline in polylines:
            view.add(
                polyline,
                linecolor=(0, 0, 1),
                linewidth=3,
                pointcolor=(1, 0, 0),
                pointsize=10,
                show_points=True
            )

brep = BendExtrusion(elem)

#for i in elem:
    #view.add(cg.Polyline(i.locus()), linewidth=2, linecolor=(0, 0, 1))

view.run()
