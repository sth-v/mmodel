
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


view = App()

four = BendSegment(40, 1.8, 90)
one = BendSegment(25, 1.8, 90)
two = BendSegment(45, 1.8, 90)
ttt = Bend([one, four, two])
elem = ttt.outer

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
