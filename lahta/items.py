from __future__ import print_function
import math
# import rhino3dm
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from mm.baseitems import Item
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line
from compas_occ.geometry import OCCNurbsCurve, OCCCurve
from compas_view2.app import App

np.set_printoptions(suppress=True)


class Element(Item):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)


#
#
#
#
#
#
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
        return PointObj(tr).point


#
#
#
#
#
#
# Элемент отгиба
class FoldElement:
    def __init__(self, radius, angle, *args, **kwargs):
        super(FoldElement, self).__init__(*args, **kwargs)
        self.radius = radius  # radius of the fold
        self.angle = angle  # angle between vectors of sides of bend after fillet
        self.plane = Plane.worldXY()

    def circle_center(self):
        circ = Circle(self.plane, self.radius)
        return circ

    def circle_param(self):
        circ_angle = 180 - self.angle
        return circ_angle / 360

    def curved_segment(self):
        circ = OCCNurbsCurvePanels.from_circle_world(self.circle_center())
        return OCCNurbsCurvePanels.segmented(circ, 0.0, self.circle_param())

    def straight_segment_len(self):
        full_len = self.circle_center().circumference
        unfold = full_len * self.circle_param()
        return unfold


class StraightElement:
    def __init__(self, *args, **kwargs):
        # super(StraightElement, self).__init__(*args, **kwargs)
        # self.radius = radius  # radius of the fold
        # self.angle = angle  # angle between vectors of sides of bend after fillet
        self.plane = Plane.worldXY()


#
#
#
#
#
#
# разные типы отгибов
# думаю это будет класс, который генерит профиль на основе паттерна? значений загиб - прямой кусок и тд

class BendProfile(object):
    instances = set()

    def __init__(self, name_, radius_s, angle_s):
        self.name_ = name_
        self.radius_s = radius_s
        self.f_radius = self.radius_s[0]
        self.angle_s = angle_s
        self.f_angle = self.angle_s[0]
        self.direction_s = None
        BendProfile.instances.add(self.name_)

    def calc_fold_start(self):
        a = math.tan(np.radians(self.f_angle))
        return self.f_radius / a


def Bends_Factory(name, radius_s, angle_s, **kwargs):

    def __init__(self, **kwarg):
        for key, value in kwarg.items():
            setattr(self, key, value)
        BendProfile.__init__(self, name, radius_s, angle_s)


    type_class = type('BendType' + name, (BendProfile,),{"__init__": __init__})
    return type_class


bend_types = {}
value = 'A'
bend_types[value] = Bends_Factory(value, [35,67,90], [45,78,56])
profile = bend_types[value]()
print (profile.name_, BendProfile.instances, bend_types[value].instances)

#
#
#
#
#
#
# разные типы панелей
# думаю это будет класс, который генерит профиль на основе паттерна? значений загиб - прямой кусок и тд
class FaceProfile(StraightElement):
    bend_types = {}

    def __init__(self, bend_types, radius_s, angle_s, poly_, *args, **kwargs):
        super(FaceProfile, self).__init__(*args, **kwargs)
        self.bend_types = bend_types
        self.radius_s = radius_s
        self.angle_s = angle_s
        self.poly = poly_
        self.special_args = kwargs

   # @staticmethod
    #def offset_sides():



    def side_offset_from_type(self):
        for key, value in self.bend_types.items():
            if value in BendProfile.instances:
                profile = FaceProfile.bend_types[value](**self.special_args)

            else:
                FaceProfile.bend_types[value] = Bends_Factory(value, self.angle_s, self.radius_s, **self.special_args)
                profile = FaceProfile.bend_types[value](**self.special_args)
        return None


    # dist = self.offset_dist(value)
    # offs = Polygon(offset_polygon(self.poly, dist))
    # return offs.lines[key]


#
#
#
#
#
#
# Сама панель
class Panel(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

        # пишу пока просто для общего понимания, что за тип данных будет передан в класс
        self.grid_hash = kwargs['grid_hash']  # identical for panel and bend
        self.vertices = kwargs['vertices']  # фактическое положение вершин
        self.offset_dist = kwargs['offset_dist']
        self.frame = self.panel_safe_offset()  # офсет до точки с расстоянием между панелями
        self.bend_type = {1: 'A', 2: 'A', 3: 'B'}

    # линия офсета от панели в осях, внешний край загиба (до радиуса)
    def panel_safe_offset(self):
        frame = PolygonObj(self.vertices)
        offset = frame.poly_offset(self.offset_dist)
        return PolygonObj(offset)


b = Panel(grid_hash='123', vertices=[[-1383.220328, 1499.49728, -160.132],
                                     [-882.411001, 2121.091646, 186.82], [-448.874568, 1451.682329, -186.82],
                                     [-1383.220328, 1499.49728, -160.132]], offset_dist=10)

print(b.frame.polygon.to_jsonstring())
c = FoldElement(10, 135)
poly = c.circle_center()
# segment = c.straight_segment()

# view = App(width=1600, height=900)
# view.add(Polyline(poly.locus()), linewidth=1, linecolor=(0, 0, 0))
# view.add(Polyline(segment.locus()), linewidth=4, linecolor=(0, 1, 0))
# view.show()
