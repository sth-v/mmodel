from __future__ import print_function

import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line, intersection_line_line, \
    Translation, Line, Rotation, NurbsSurface

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
    metal_width = 3

    def __init__(self, angle, radius, *args, **kwargs):
        super(FoldElement, self).__init__(*args, **kwargs)
        self.radius = radius  # radius of the fold
        self.angle = angle  # angle between vectors of sides of bend after fillet
        self.plane = Plane.worldXY()

    def circle_center(self):
        circ_s = Circle(self.plane, self.radius)
        circ_l = Circle(self.plane, self.radius + self.metal_width)
        if self.angle > 0:
            return circ_s, circ_l
        else:
            return circ_l, circ_s

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
            tr = Translation.from_vector(Vector.Yaxis() * (-self.radius - self.metal_width))
        c_t = circle.transformed(tr)
        return c_t

    def curved_segment(self, circle):
        transl = self.transl_to_radius(circle)
        if self.angle < 0:
            param = 0.75 - self.circle_param()
            seg = OCCNurbsCurvePanels.segmented(transl, 0.75, param)
            curve = OCCNurbsCurvePanels.reversed_copy(seg)
            return curve
        else:
            param = 0.25 + self.circle_param()
            seg = OCCNurbsCurvePanels.segmented(transl, 0.25, param)
            return seg

    def construct_folds(self):
        folds = []
        for i in self.circle_center():
            circ = OCCNurbsCurvePanels.from_circle_world(i)
            folds.append(self.curved_segment(circ))
        return folds

    def straight_segment_len(self):
        full_len = self.circle_center()[1].circumference
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
    metal_width = 3

    def __init__(self, length=None, *args, **kwargs):
        super(StraightElement, self).__init__(*args, **kwargs)
        self.length = length
        self.plane = Plane.worldXY()

    def translate_y(self, line):
        tr = Translation.from_vector(Vector.Yaxis() * (-self.metal_width))
        l_t = line.transformed(tr)
        return l_t

    def build_line(self):
        start = Point(0, 0, 0)
        end = Point(self.length, 0, 0)
        l_in = OCCNurbsCurve.from_line(Line(start, end))
        l_out = self.translate_y(l_in)
        return l_in, l_out

    @staticmethod
    def cap_elem(c_one, c_two):
        s_one, e_one = c_one.point_at(min(c_one.domain)), c_two.point_at(min(c_two.domain))
        s_two, e_two = c_two.point_at(max(c_two.domain)), c_one.point_at(max(c_one.domain))
        l_one = OCCNurbsCurve.from_line(Line(s_one, e_one))
        l_two = OCCNurbsCurve.from_line(Line(s_two, e_two))
        return l_one, l_two


view = App(width=1600, height=900)
import json
js = {'poly':[], 'seg':[]}

class BendConstructor:
    def __init__(self, *args, start):
        self.steps = args[0]
        self.start = start
        self.curve = start
        self._i = -1
        self.bend_curve = self.close_curve()

    @staticmethod
    def get_local_plane(previous, domain):
        X = previous.tangent_at(domain).unitized()
        ea1 = 0.0, 0.0, np.radians(90)
        R1 = Rotation.from_euler_angles(ea1, False, 'xyz')
        Y = X.transformed(R1).unitized()
        # view.add(Frame(previous.point_at(domain), X, Y), size=5)
        return Frame(previous.point_at(domain), X, Y)

    def translate_segment(self, line_segment, previous, domain):
        goal_frame = self.get_local_plane(previous, domain)
        inner = goal_frame.to_world_coordinates(line_segment[0])
        outer = goal_frame.to_world_coordinates(line_segment[1])
        return inner, outer

    def __iter__(self):
        return self

    # гнем и все остальное относительно внутреннего радиуса
    def __next__(self):
        self._i += 1
        fold = FoldElement(angle=self.steps[self._i][0], radius=self.steps[self._i][1])
        straight = StraightElement(self.steps[self._i][2] - (2 * fold.calc_rightangle_length()))

        get_fold = fold.construct_folds()
        get_line = straight.build_line()

        transl_f = self.translate_segment(get_fold, self.curve, max(self.curve.domain))
        transl_s = self.translate_segment(get_line, transl_f[0], max(transl_f[0].domain))
        join_in, join_out = transl_f[0].joined(transl_s[0]), transl_f[1].joined(transl_s[1])
        self.curve = join_in
        return join_in, join_out

    def bend_(self):
        bend_in, bend_out = next(self)
        while self._i + 1 < len(self.steps):
            b_in, b_out = next(self)
            bend_in = bend_in.joined(b_in)
            bend_out = bend_out.joined(b_out)
        return bend_in, bend_out

    def close_curve(self):
        bends = self.bend_()
        caps = StraightElement()
        caps = caps.cap_elem(bends[0], bends[1])
        return [*bends, *caps]

    def extrusion(self):
        vec = self.get_local_plane(self.start, max(self.start.domain)).zaxis
        surf = []
        for i in self.bend_curve:
            surf.append(OCCNurbsSurface.from_extrusion(i, vec * 50))
        cap = NurbsSurface.from_fill(*self.bend_curve)
        tr = Translation.from_vector(vec * 50)
        surf.append([cap, cap.transformed(tr)])
        return surf


line = OCCNurbsCurve.from_line(Line(Point(5, 5, 0), Point(-30, 5, 0)))
line_ = OCCNurbsCurve.from_line(Line(Point(5, 8, 0), Point(-30, 8, 0)))
test = BendConstructor(((90, 2, 35), (60, 2, 15), (-120, 2, 15)), start=line)

bend_ = test.bend_curve
extr = test.extrusion()
#print(bend_)


for i, v in enumerate(bend_):
    b = v.to_polyline(n=45)
    js['poly'].append(v.to_jsonstring())

with open("/Users/sofyadobycina/Documents/GitHub/mmodel/tests/triangl.json", "w") as outfile:
    json.dump(js, outfile)

view.add(Polyline(line.locus()), linewidth=1, linecolor=(0, 0, 1))
for i in bend_:
    view.add(Polyline(i.locus()), linewidth=1, linecolor=(1, 0, 0))

for i in extr:
    try:
        view.add(i.to_mesh())
    except:
        for ii in i:
            view.add(ii.to_mesh())

#view.show()


#
#
#
#
#
#
# разные типы панелей
# думаю это будет класс, который генерит профиль на основе паттерна? значений загиб - прямой кусок и тд
class FaceProfile(StraightElement):
    # bend_types = defaultdict(list)

    def __init__(self, bend_type, radius_s, angle_s, poly_, directions_s, *args, **kwargs):
        super(FaceProfile, self).__init__(*args, **kwargs)
        self.bend_types = bend_type
        self.radius_s = radius_s
        self.angle_s = angle_s
        self.directions_s = directions_s
        self.poly = poly_
        self.special_args = kwargs
        self.panel_offset = self.panel_offset()

    def panel_offset(self):
        offset_poly = []
        for index, bend in enumerate(self.bend_types):
            bend_type = Bends_Factory(bend, self.radius_s[index], self.angle_s[index], self.directions_s[index])
            bend_elem = bend_type()
            FaceProfile.bend_types[bend].append(bend_elem)
            offset_dist = bend_elem.calc_fold_start()
            offset_poly.append(PolygonObj(self.poly.poly_offset(offset_dist)).polygon_lines[index])

        return PolygonObj([intersection_line_line(offset_poly[0], offset_poly[1])[0],
                           intersection_line_line(offset_poly[1], offset_poly[2])[0],
                           intersection_line_line(offset_poly[2], offset_poly[0])[0]])


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

test = FaceProfile(['A', 'A', 'B'], [[2, 2, 2], [2, 2, 2], [2, 2, 2]], [[90, 90, 90], [90, 90, 90], [90, 90, 90]],
                   b.frame, [[-1, -1, -1], [-1, -1, -1], [-1, 1]])

before_offset = b.frame.polygon
start_poly = test.panel_offset.polygon
