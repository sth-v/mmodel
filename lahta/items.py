from __future__ import print_function
import math
# import rhino3dm
from collections import defaultdict
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from mm.baseitems import Item
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line, intersection_line_line, Translation
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
    def __init__(self, radius, angle, dir, *args, **kwargs):
        super(FoldElement, self).__init__(*args, **kwargs)
        self.radius = radius  # radius of the fold
        self.angle = angle  # angle between vectors of sides of bend after fillet
        self.dir = dir
        self.plane = Plane.worldXY()

    def circle_center(self):
        circ = Circle(self.plane, self.radius)
        return circ

    def circle_param(self):
        circ_angle = 180 - self.angle
        return circ_angle / 360

    @staticmethod
    def transl_to_zero(init_point, goal_point):
        vec = goal_point - init_point
        transl = Translation.from_vector(vec)
        return transl


    def curved_segment(self):
        circ = OCCNurbsCurvePanels.from_circle_world(self.circle_center())
        origin = Point(0.0, 0.0, 0.0)
        if self.dir >0:
            seg = OCCNurbsCurvePanels.segmented(circ, 0.0, self.circle_param())
            transl = self.transl_to_zero(seg.points[2], origin)
            return seg.transformed(transl)
        else:
            seg = OCCNurbsCurvePanels.segmented(circ, 1-self.circle_param(), 1.0)
            transl = self.transl_to_zero(seg.points[0], origin)
            return seg.transformed(transl)


    def straight_segment_len(self):
        full_len = self.circle_center().circumference
        unfold = full_len * self.circle_param()
        return unfold





class BendConstructor:
    def __init__(self, angle, radius, dir, straight):
        self.angle = angle
        self.radius = radius
        self.dir = dir
        self.straight = straight




c = FoldElement(10, 135, -1)

test = BendConstructor(angle = [90, 90, 90], radius = [2, 2, 2], dir = [-1, -1, -1], straight = [35, 15, 7])

poly = c.curved_segment()

cc = FoldElement(10, 135, 1)
poly_ = cc.curved_segment()
frame=poly.frame_at(0.875)
frame_=poly.frame_at(1.0)

view = App(width=1600, height=900)

view.add(Polyline(poly.locus()), linewidth=1, linecolor=(0, 0, 0))
view.add(Polyline(poly_.locus()), linewidth=1, linecolor=(0, 1, 0))
view.add(frame, size=5)
view.add(frame_, size=5)
view.show()




'''class StraightElement:
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

    def __init__(self, name_, radius_s, angle_s, direction_s):
        self.name_ = name_
        self.radius_s = radius_s
        self.f_radius = self.radius_s[0]
        self.angle_s = angle_s
        self.f_angle = self.angle_s[0]
        self.direction_s = direction_s
        BendProfile.instances.add(self)


def Bends_Factory(name, radius_s, angle_s, direction_s, **kwargs):
    def __init__(self, **kwarg):
        for key, value in kwarg.items():
            setattr(self, key, value)
        BendProfile.__init__(self, name, radius_s, angle_s, direction_s)

    def calc_fold_start(self):
        a = math.tan(np.radians(self.f_angle))
        return self.f_radius / a

    type_class = type('BendType' + name, (BendProfile,), {"__init__": __init__, "calc_fold_start": calc_fold_start})
    return type_class


#
#
#
#
#
#
# разные типы панелей
# думаю это будет класс, который генерит профиль на основе паттерна? значений загиб - прямой кусок и тд
class FaceProfile(StraightElement):
    bend_types = defaultdict(list)

    def __init__(self, bend_type, radius_s, angle_s, poly_, directions_s,*args, **kwargs):
        super(FaceProfile, self).__init__(*args, **kwargs)
        self.bend_types = bend_type
        self.radius_s = radius_s
        self.angle_s = angle_s
        self.directions_s = directions_s
        self.poly = poly_
        self.special_args = kwargs
        self.panel_offset = self.panel_offset()

    def panel_offset(self):
        offset_poly=[]
        for index, bend in enumerate(self.bend_types):
            bend_type = Bends_Factory(bend, self.radius_s[index], self.angle_s[index], self.directions_s[index])
            bend_elem = bend_type()
            FaceProfile.bend_types[bend].append(bend_elem)
            offset_dist = bend_elem.calc_fold_start()
            offset_poly.append(PolygonObj(self.poly.poly_offset(offset_dist)).polygon_lines[index])

        return PolygonObj([intersection_line_line(offset_poly[0], offset_poly[1])[0],
                           intersection_line_line(offset_poly[1], offset_poly[2])[0], intersection_line_line(offset_poly[2], offset_poly[0])[0]])








    # @staticmethod
    # def offset_sides():



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
        self.bend_type = ['A', 'A', 'B']

    # линия офсета от панели в осях, внешний край загиба (до радиуса)
    def panel_safe_offset(self):
        frame = PolygonObj(self.vertices)
        offset = frame.poly_offset(self.offset_dist)
        return PolygonObj(offset)


b = Panel(grid_hash='123', vertices=[[-1383.220328, 1499.49728, -160.132],
                                     [-882.411001, 2121.091646, 186.82], [-448.874568, 1451.682329, -186.82],
                                     [-1383.220328, 1499.49728, -160.132]], offset_dist=10)


test = FaceProfile(['A', 'A', 'B'], [[2, 2, 2], [2, 2, 2], [2, 2, 2]], [[90, 90, 90], [90, 90, 90], [90, 90, 90]], b.frame, [[-1,-1,-1], [-1,-1,-1],[-1,1]])

before_offset = b.frame.polygon
start_poly = test.panel_offset.polygon




#segment = c.straight_segment()


#from compas_plotters import Plotter
#plotter = Plotter()

#plotter.add(before_offset, linewidth=3)
#plotter.zoom_extents()
#plotter.show()
view = App(width=1600, height=900)
#view.add(before_offset, linewidth=1, linecolor=(0, 0, 0))

view.add(Polyline(poly.locus()), linewidth=1, linecolor=(0, 0, 0))
view.add(Polyline(poly_.locus()), linewidth=1, linecolor=(0, 1, 0))
view.add(frame, size=5)
view.add(frame_, size=5)
#view.add(Polyline(segment.locus()), linewidth=4, linecolor=(0, 1, 0))
view.show()'''



