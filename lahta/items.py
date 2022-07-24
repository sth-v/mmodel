from __future__ import print_function

import math
import rhino3dm
import numpy as np

from mm.baseitems import Item
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle

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

    def get_third_vector(self, axe):
        side = axe.vector / np.linalg.norm(axe.vector)
        normal = -np.asarray(self.poly_normal())
        return (np.cross(side, normal)) / np.linalg.norm(np.cross(side, normal))

    def sum_of_vectors(self, axe):
        vec = np.sum([np.asarray(self.get_third_vector(axe)), -np.asarray(self.poly_normal())], axis=0)
        return vec / np.linalg.norm(vec)







class FoldElement:
    def __init__(self, base_axe, initial_poly):
        self.base_axe = base_axe  # in the shape of pair of vertices (axe = corner of fold in 3d and )
        self.poly= initial_poly   # initial plane
        #self.fold_position = self.fold_position()
        #self.unwrap = self.unwrap()

    def fold_position_center(self, radius):
        transl_dist = math.sqrt(2 * (radius**2))
        vec = self.poly.sum_of_vectors(self.base_axe) * transl_dist
        return translate_points([self.base_axe[0]], vec)

    def fold_position_circle(self, radius):
        point = Point(*self.fold_position_center(radius)[0])
        pl = Plane(point, self.base_axe.vector / np.linalg.norm(self.base_axe.vector))
        return Circle(pl, radius)




        
























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

c = FoldElement(b.frame.polygon_lines[0], b.frame)
print(c.fold_position_circle(radius = 10))