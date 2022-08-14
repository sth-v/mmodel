from __future__ import print_function

import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line, intersection_line_line, \
    Translation, Line, Rotation

from mm.baseitems import Item
from compas_occ.geometry import OCCNurbsCurve, OCCNurbsSurface
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
    def __init__(self, angle, radius, dir, *args, **kwargs):
        super(FoldElement, self).__init__(*args, **kwargs)
        self.radius = radius  # radius of the fold
        self.angle = angle  # angle between vectors of sides of bend after fillet
        self.dir = dir
        self.plane = Plane.worldXY()

    def circle_center(self):
        circ = Circle(self.plane, self.radius)
        return circ

    def circle_param(self):
        if self.angle > 0:
            circ_angle = 180 - self.angle
        else:
            circ_angle = 180 - (-self.angle)
        return circ_angle / 360

    def transl_to_radius(self, circle):
        if self.angle > 0:
            tr = Translation.from_vector(Vector.Yaxis() * self.radius)
        else:
            tr = Translation.from_vector(Vector.Yaxis() * (-self.radius))
        c_t = circle.transformed(tr)
        return c_t


    def curved_segment(self):
        circ = OCCNurbsCurvePanels.from_circle_world(self.circle_center())
        if self.angle < 0:
            transl = self.transl_to_radius(circ)
            param = 0.75 - self.circle_param()
            seg = OCCNurbsCurvePanels.segmented(transl, 0.75, param)
            curve = OCCNurbsCurvePanels.reversed_copy(seg)
            return curve
        else:
            transl = self.transl_to_radius(circ)
            param = 0.25 + self.circle_param()
            seg = OCCNurbsCurvePanels.segmented(transl, 0.25, param)
            return seg

    def straight_segment_len(self):
        full_len = self.circle_center().circumference
        unfold = full_len * self.circle_param()
        return unfold

    # расстояние от точки касания до точки пересечения касательных
    def calc_extra_length(self):
        a = math.tan(np.radians(self.angle))
        return self.radius / a

    # вроде как это всегда будет длина, которая получается от 90 градусов
    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return self.radius / a


class StraightElement:
    def __init__(self, length, *args, **kwargs):
        # super(StraightElement, self).__init__(*args, **kwargs)
        self.length = length
        self.plane = Plane.worldXY()

    def build_line(self):
        start = Point(0, 0, 0)
        end = Point(self.length, 0, 0)
        return OCCNurbsCurve.from_line(Line(start, end))

view = App(width=1600, height=900)
class BendConstructor:
    def __init__(self, angle, radius, dir, straight, start):
        self.angle = angle
        self.radius = radius
        self.dir = dir
        self.straight = straight
        self.start = start
        self.curve = start
        self._i = -1
        self.bend_curve = self.bend_()

    def get_local_plane(self, previous, domain):
        X = previous.tangent_at(domain).unitized()
        ea1 = 0.0, 0.0, np.radians(90)
        R1 = Rotation.from_euler_angles(ea1, False, 'xyz')
        Y = X.transformed(R1).unitized()
        view.add(Frame(previous.point_at(domain), X, Y), size=5)
        return Frame(previous.point_at(domain), X, Y)

    def translate_segment(self, line_segment, previous, domain):
        goal_frame = self.get_local_plane(previous, domain)
        return goal_frame.to_world_coordinates(line_segment)

    def translate_segment_inverse(self, line_segment, previous, domain):
        goal_frame = self.get_local_plane(previous, domain)
        reversed_frame = Frame(goal_frame.point, goal_frame.xaxis, -goal_frame.yaxis)
        return reversed_frame.to_world_coordinates(line_segment)

    def __iter__(self):
        return self

    def __next__(self):
        self._i += 1
        fold = FoldElement(self.angle[self._i], self.radius[self._i], self.dir[self._i])
        straight = StraightElement(self.straight[self._i] - (2 * fold.calc_rightangle_length()))
        get_fold = fold.curved_segment()
        view.add(get_fold.frame_at(min(get_fold.domain)), size=5)

        get_line = straight.build_line()

        transl_f = self.translate_segment(get_fold, self.curve, max(self.curve.domain))
        transl_s = self.translate_segment(get_line, transl_f, max(transl_f.domain))

        join = transl_f.joined(transl_s)
        self.curve = join
        return join

    def bend_(self):
        bend = next(self)
        while self._i + 1 < len(self.angle):
            bend = bend.joined(next(self))
        return bend

    def extrusion(self):
        vec = self.get_local_plane(self.start, max(self.start.domain)).zaxis
        surf = OCCNurbsSurface.from_extrusion(self.bend_curve, vec * 50)
        return surf


c = FoldElement(10, 135, -1)
line = OCCNurbsCurve.from_line(Line(Point(5, 2, 0), Point(-30, 12, 0)))
test = BendConstructor(angle=[90, 60, 120, -70], radius=[2, 2, 2, 2], dir=[1, 1, 1, 1], straight=[35, 15, 15, 15], start=line)
bend_ = test.bend_curve

view.add(Polyline(line.locus()), linewidth=1, linecolor=(0, 0, 1))
view.add(Polyline(bend_.locus()), linewidth=1, linecolor=(1, 0, 0))
view.show()

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



