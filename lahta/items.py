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
    metal_width = 1

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


view = App(width=1600, height=900)


class FoldElementFres(FoldElement):
    metal_width = 1
    coeff = 0.3

    def __init__(self, angle, radius, fres_len, *args, **kwargs):
        super().__init__(angle, radius, *args, **kwargs)
        self.fres_len = fres_len

    @staticmethod
    def get_local_plane(previous, domain):
        X = previous.tangent_at(domain).unitized()
        ea1 = 0.0, 0.0, np.radians(90)
        R1 = Rotation.from_euler_angles(ea1, False, 'xyz')
        Y = X.transformed(R1).unitized()
        return Frame(previous.point_at(domain), X, Y)

    # вычисление внутреннего радиуса
    def calc_inner_rad(self):
        part = (180 - np.abs(self.angle)) / 360
        # goal_fl = self.fres_len * self.coeff
        goal_fl = self.fres_len * (self.radius - (self.metal_width / 2))
        return goal_fl / (2 * math.pi * part)

    def circle_center(self):
        circ_l = Circle(self.plane, self.radius)
        circ_s = Circle(self.plane, self.calc_inner_rad())
        return OCCNurbsCurvePanels.from_circle_world(circ_l), OCCNurbsCurvePanels.from_circle_world(circ_s)

    def straight_parts_l(self):
        ang = np.radians(self.angle / 2)
        l_out = (self.metal_width / 2) / math.tan(ang)
        l_in = l_out / math.cos(ang)
        start = Point(0, 0, 0)
        return OCCNurbsCurve.from_line(Line(start, Point(l_out, 0, 0))), OCCNurbsCurve.from_line(
            Line(start, Point(l_in, 0, 0)))

    def crv_str_in(self, curve, straight):
        join = curve
        for c, s in zip(curve.domain, straight.domain[-1::-1]):
            if self.angle > 0:
                ea1 = 0, 0, np.radians(-self.angle / 2)
            else:
                ea1 = 0, 0, np.radians(self.angle / 2)
            args = False, 'xyz'
            R1 = Rotation.from_euler_angles(ea1, *args)
            s_rot = straight.transformed(R1)

            c_fr = self.get_local_plane(curve, c)

            tr = Translation.from_vector(Vector.from_start_end(s_rot.point_at(max(s_rot.domain)), c_fr.point))
            st = s_rot.transformed(tr)

            join = join.joined(st)

            view.add(Polyline(join.locus()), linewidth=1, linecolor=(0, 0, 0))

        return join

    def crv_str_out(self, curve, straight):
        join = curve
        for c, s in zip(curve.domain, straight.domain[-1::-1]):
            str_fr = self.get_local_plane(straight, s)
            c_fr = self.get_local_plane(curve, c)
            tr = Transformation.from_frame_to_frame(str_fr, c_fr)
            st = straight.transformed(tr)
            join = join.joined(st)

            view.add(Polyline(st.locus()), linewidth=1, linecolor=(1, 0, 0))
            view.add(Polyline(curve.locus()), linewidth=1, linecolor=(0, 0, 1))
        return join

    def construct_folds(self):
        folds = []
        crv_segments = []
        for c in self.circle_center():
            crv = self.curved_segment(c)
            ang = np.radians(self.angle / 2)
            x_tr = Translation.from_vector(Vector.Xaxis() * ((self.metal_width / 2) / math.tan(ang)))
            crv_shift = crv.transformed(x_tr)
            crv_segments.append(crv_shift)

        outer = self.crv_str_out(crv_segments[0], self.straight_parts_l()[0])
        inner = self.crv_str_in(crv_segments[1], self.straight_parts_l()[1])

        return folds

    '''def translate_inner(self, curve, domain):

        ea1 = 0, 0, np.radians(-self.angle / 2)
        args = False, 'xyz'
        R1 = Rotation.from_euler_angles(ea1, *args)
        ang = np.radians(self.angle / 2)
        l = (self.metal_width / 2) / math.sin(ang)
        vec = Vector(l, 0, 0).transformed(R1)

        pl_one = self.get_local_plane(curve, domain)
        y_tr = Translation.from_vector(pl_one.yaxis * (self.metal_width))
        l_one = curve.point_at(domain)
        l_one = l_one.transformed(y_tr)
        vec_tr = Translation.from_vector(vec)
        l_two = l_one.transformed(vec_tr)
        line_one = OCCNurbsCurve.from_line(Line(l_one, l_two))
        return line_one

    def construct_inner_fold(self):
        outer = self.construct_folds()
        seg_one =self.translate_inner(outer, max(outer.domain))
        seg_two = self.translate_inner(outer, min(outer.domain))
        join = OCCNurbsCurve.from_line(Line(seg_one.point_at(max(seg_one.domain)), seg_two.point_at(max(seg_two.domain))))
        return seg_two.joined(seg_one.joined(join))

    def inner_fold(self):
        if self.angle > 0:
            return self.construct_inner_fold(), self.construct_folds()
        else:
            return self.construct_folds(), self.construct_inner_fold()'''


test = FoldElementFres(angle=70, radius=0.8, fres_len=1.4)
tt = test.construct_folds()
# view.add(Polyline(test.construct_folds().locus()), linewidth=1, linecolor=(0, 0, 1))
# view.add(Polyline(test.construct_inner_fold().locus()), linewidth=1, linecolor=(0, 0, 0))
view.show()


class StraightElement:
    metal_width = 1

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

    def build_line_fres(self):
        start = Point(0, 0, 0)
        end = Point(self.length, 0, 0)
        l_in = OCCNurbsCurve.from_line(Line(start, end))

        tr = Translation.from_vector(Vector.Yaxis() * (self.metal_width))
        l_out = l_in.transformed(tr)
        return l_in, l_out

    @staticmethod
    def cap_elem(c_one, c_two):
        s_one, e_one = c_one.point_at(min(c_one.domain)), c_two.point_at(min(c_two.domain))
        s_two, e_two = c_two.point_at(max(c_two.domain)), c_one.point_at(max(c_one.domain))
        l_one = OCCNurbsCurve.from_line(Line(s_one, e_one))
        l_two = OCCNurbsCurve.from_line(Line(s_two, e_two))
        return l_one, l_two


import json

js = {'poly': [], 'seg': []}


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

        if self.steps[self._i][1] > 1:
            fold = FoldElement(angle=self.steps[self._i][0], radius=self.steps[self._i][1])
            get_fold = fold.construct_folds()
            straight = StraightElement(self.steps[self._i][2] - (2 * fold.calc_rightangle_length()))
            get_line = straight.build_line()
        else:
            fold = FoldElementFres(angle=self.steps[self._i][0], radius=self.steps[self._i][1])
            # get_fold = fold.inner_fold()
            # straight = StraightElement(self.steps[self._i][2] - (2 * fold.calc_rightangle_length()))
            # get_line = straight.build_line_fres()

        transl_f = self.translate_segment(get_fold, self.curve, max(self.curve.domain))

        if self.steps[self._i][1] > 1:
            transl_s = self.translate_segment(get_line, transl_f[0], max(transl_f[0].domain))
        else:
            transl_s = self.translate_segment(get_line, transl_f[1], max(transl_f[1].domain))
        join_in, join_out = transl_f[0].joined(transl_s[0]), transl_f[1].joined(transl_s[1])
        self.curve = join_in
        return join_in, join_out

    def bend_(self):
        bend_in, bend_out = next(self)
        # view.add(Polyline(bend_in.locus()), linewidth=1, linecolor=(0, 0, 1))
        # view.add(Polyline(bend_out.locus()), linewidth=1, linecolor=(0, 0, 1))
        while self._i + 1 < len(self.steps):
            try:
                b_in, b_out = next(self)
            except:
                pass
            # view.add(Polyline(b_in.locus()), linewidth=1, linecolor=(0, 0, 1))
            # view.add(Polyline(b_out.locus()), linewidth=1, linecolor=(0, 0, 1))
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
test = BendConstructor(((70, 1.8, 30), (-160, 1.3, 9.3), (-90, 1.3, 20)), start=line)

bend_ = test.bend_curve
extr = test.extrusion()
# print(bend_)


for i, v in enumerate(bend_):
    b = v.to_polyline(n=45)
    js['poly'].append(v.to_jsonstring())

with open("/Users/sofyadobycina/Documents/GitHub/mmodel/tests/triangl.json", "w") as outfile:
    json.dump(js, outfile)


# view.add(Polyline(line.locus()), linewidth=1, linecolor=(0, 0, 1))
# for i in bend_:
# view.add(Polyline(i.locus()), linewidth=1, linecolor=(1, 0, 0))

# for i in extr:
#    try:
#        view.add(i.to_mesh())
#    except:
#        for ii in i:
#            view.add(ii.to_mesh())


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
