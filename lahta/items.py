from __future__ import print_function

import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line, intersection_line_line, \
    Translation, Line, Rotation, NurbsSurface

from mmodel_server.mm.mm.baseitems import Item
from compas_occ.geometry import OCCNurbsCurve, OCCNurbsSurface

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
        return PointObj(tr).point


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

    def transl_to_radius(self, circle, radius):
        if self.angle > 0:
            tr = Translation.from_vector(Vector.Yaxis() * radius)
        else:
            tr = Translation.from_vector(Vector.Yaxis() * (-radius - self.metal_width))
        c_t = circle.transformed(tr)
        return c_t

    def curved_segment(self, circle, radius):
        transl = self.transl_to_radius(circle, radius)
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
            folds.append(self.curved_segment(circ, self.radius))
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
        # goal_fl = self.fres_len * (self.radius - (self.metal_width / 2))
        # return goal_fl / (2 * math.pi * part)
        return 0.3

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
        return join

    def crv_str_out(self, curve, straight):
        join = curve
        for c, s in zip(curve.domain, straight.domain[-1::-1]):
            str_fr = self.get_local_plane(straight, s)
            c_fr = self.get_local_plane(curve, c)
            tr = Transformation.from_frame_to_frame(str_fr, c_fr)
            st = straight.transformed(tr)
            join = join.joined(st)
        return join

    def construct_folds(self):
        crv_segments = []
        for c in self.circle_center():
            crv = self.curved_segment(c, radius=-0.2)
            ang = np.radians(self.angle / 2)
            x_tr = Translation.from_vector(Vector.Xaxis() * ((self.metal_width / 2) / math.tan(ang)))
            crv_shift = crv.transformed(x_tr)
            crv_segments.append(crv_shift)

        outer = self.crv_str_out(crv_segments[0], self.straight_parts_l()[0])
        inner = self.crv_str_in(crv_segments[1], self.straight_parts_l()[1])

        if self.angle > 0:
            return [outer, inner]
        else:
            return [inner, outer]


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
        return l_out, l_in

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
            fold = FoldElementFres(angle=self.steps[self._i][0], radius=self.steps[self._i][1], fres_len=1.4)
            get_fold = fold.construct_folds()
            straight = StraightElement(self.steps[self._i][2] - (2 * fold.calc_rightangle_length()))
            get_line = straight.build_line_fres()

        transl_f = self.translate_segment(get_fold, self.curve, max(self.curve.domain))

        if self.steps[self._i][1] > 1:
            transl_s = self.translate_segment(get_line, transl_f[0], max(transl_f[0].domain))
        else:
            transl_s = self.translate_segment(get_line, transl_f[0], max(transl_f[0].domain))

        line = OCCNurbsCurve.from_line(Line(Point(5, 5, 0), Point(-30, 5, 0)))

        join_in, join_out = transl_f[0].joined(transl_s[0]), transl_f[1].joined(transl_s[1])
        self.curve = join_in
        return join_in, join_out

    def bend_(self):
        bend_in, bend_out = next(self)
        while self._i + 1 < len(self.steps):
            try:
                b_in, b_out = next(self)
            except:
                pass
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


