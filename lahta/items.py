from __future__ import print_function
import math
# import rhino3dm
import numpy as np
from mm.baseitems import Item
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation
from compas_occ.geometry import OCCNurbsCurve

np.set_printoptions(suppress=True)


class Element(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


# геометрические примитивы
class PolygonObj(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        try:
            self.vertices = args[0].tolist()
            if self.vertices[0] == self.vertices[-1]:
                del self.vertices[-1]
        except AttributeError:
            self.vertices = args[0]
            if self.vertices[0] == self.vertices[-1]:
                del self.vertices[-1]

        self.polygon = self.get_poly()
        self.polygon_lines = self.get_lines()

    def get_poly(self):
        return Polygon(self.vertices)

    def get_lines(self):
        return self.polygon.lines

    def poly_offset(self, dist):
        return offset_polygon(self.vertices, dist)

    def poly_normal(self):
        return normal_polygon(self.get_poly())


class PointObj(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.point = args[0]
        self.compas_point = self.compas_point

    def compas_point(self):
        return Point(*self.point)

    def translate_points(self, vector):
        tr = translate_points([self.point], vector)[0]
        return PointObj(tr)


#
#
#
#
#
#
#

class FoldElement():
    def __init__(self, radius, angle, base_axe, fold_dir, normal, *args, **kwargs):
        super(FoldElement, self).__init__(*args, **kwargs)

        self.radius = radius  # radius of the fold
        self.angle = angle  # part of the circle required for fold
        self.base_axe = base_axe  # compas line
        self.fold_dir = fold_dir  # fold_dir - whether radius to inside ot to outside (- or + sign)
        self.normal = normal  # poly normal
        self.point = PointObj(self.base_axe[0])

    # Возможно нужно засунуть в класс векторов
    def get_third_vector(self):
        side_vec = self.base_axe.vector / np.linalg.norm(self.base_axe.vector)
        normal_vec = self.fold_dir * np.asarray(self.normal)
        return (np.cross(side_vec, normal_vec)) / np.linalg.norm(np.cross(side_vec, normal_vec))

    def circle_center(self):
        vec = np.sum([np.asarray(self.get_third_vector()), self.fold_dir * np.asarray(self.normal)], axis=0)
        vec = vec / np.linalg.norm(vec)
        transl_dist = math.sqrt(2 * (self.radius ** 2))
        transl_vec = vec * transl_dist
        return self.point.translate_points(transl_vec).point

    def fold_position_circle(self):
        #pl = Plane.from_point_and_two_vectors(self.circle_center(), self.get_third_vector(), self.fold_dir * np.asarray(self.normal))
        pl = Plane(self.circle_center(), self.base_axe.vector / np.linalg.norm(self.base_axe.vector))
        pl_frame = Frame.from_plane(pl)
        rotation_frame = Frame(self.circle_center(), self.get_third_vector(), self.fold_dir * np.asarray(self.normal))
        tr = Transformation.from_frame_to_frame(pl_frame, rotation_frame)
        circ = Circle(pl, self.radius)
        return OCCNurbsCurve.from_circle(circ).transformed(tr)

    def split_circ_at_param(self):
        return OCCNurbsCurve.segmented(self.fold_position_circle(), 0.25, 0.5)















# разные типы отгибов
class BendProfile_A(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.profile = self.profile_geometry()

    def profile_geometry(self):
        return self


class BendProfile_B(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.profile = self.profile_geometry()

    def profile_geometry(self):
        return self


# Отгиб панели - профиль получается в зависимости от типа
class PanelBend(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        # пишу пока просто для общего понимания, что за тип данных будет передан в класс
        self.grid_hash = kwargs['grid_hash']  # identical for panel and bend
        self.side = kwargs['side']  # integer
        self.type = kwargs['type']  # bend type name str

        # получение профиля отгиба в зависимости от типа
        if self.type == 'A':
            self.profile = BendProfile_A().profile
        elif self.type == 'B':
            self.profile = BendProfile_B().profile


# Сама панель
class Panel(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        # пишу пока просто для общего понимания, что за тип данных будет передан в класс
        self.grid_hash = kwargs['grid_hash']  # identical for panel and bend
        self.vertices = kwargs['vertices']  # фактическое положение вершин
        self.frame = PolygonObj(self.vertices)

        # self.perforation = kwargs['perforation']

    # линия офсета от панели в осях, внешний край загиба (до радиуса)
    def panel_outer_bend_line(self):
        dist = 7.5  # may be changed
        frame = PolygonObj(self.vertices)
        return frame.poly_offset(dist)


b = Panel(grid_hash='1234', vertices=[[-1383.220328, 1499.49728, -160.132],
                                      [-882.411001, 2121.091646, 186.82], [-448.874568, 1451.682329, -186.82],
                                      [-1383.220328, 1499.49728, -160.132]])

c = FoldElement(10, 45, b.frame.polygon_lines[0], -1, b.frame.poly_normal())
print(c.split_circ_at_param())
