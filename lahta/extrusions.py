from mm.geom.geom import Arc
from mm.baseitems import Item
import compas.geometry as cg
from compas_view2.app import App
from lahta.items import Bend, BendSegment
import compas_occ.geometry as cc
import compas_occ.brep as cb
from compas_view2.objects import Collection

view = App()

four = BendSegment(40, 1.8, 65)
one = BendSegment(25, 1.8, -70)
two = BendSegment(45, 1.3, 90)
ttt = Bend([one, four, two])


class BendExtrusion(Item):
    extrusion = []

    def __call__(self, extr, *args, **kwargs):
        super().__call__(extr=extr, *args, **kwargs)

        for i in extr:
            surf = cc.OCCNurbsSurface.from_extrusion(i, cg.Vector.Zaxis() * 35)

            points = [surf.point_at(0.5, 0.7), surf.point_at(0.7, 0.7), surf.point_at(0.7, 0.2),
                      surf.point_at(0.5, 0.2), surf.point_at(0.5, 0.7)]

            loop = cb.BRep.from_polygons([cg.Polygon(points)])
            brep = cb.BRep.from_mesh(surf.to_mesh(nu=2, nv=2))

            C = brep - loop
            print(C)

            mesh = C.to_meshes(u=25, v=25)
            self.brep = C

            # self.extrusion.append(surf_)
            view.add(mesh[0])
            # view.add(Collection(points))
            # view.add(cg.Polyline(curve.locus()), linewidth=3)

    # def to_local_plane(self, extr):


test = BendExtrusion([ttt.inner[1]])

# seg_list = ttt.bend_stage
# for i in seg_list:
# i.viewer(view)

view.run()
