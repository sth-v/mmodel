from __future__ import print_function

import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line, intersection_line_line, \
    Translation, Line, Rotation, NurbsSurface
from mm.geom.geom import Arc
from mm.baseitems import Item
from compas_occ.geometry import OCCNurbsCurve, OCCNurbsSurface
from more_itertools import pairwise
import itertools
from compas_view2.app import App

np.set_printoptions(suppress=True)
import json

js = {'poly': []}


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
class BendMethods(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)

    @staticmethod
    def get_plane(inner, outer=None):
        if outer is not None:
            X = outer.tangent_at(max(outer.domain)).unitized()
        else:
            X = inner.tangent_at(max(inner.domain)).unitized()
        ea1 = 0.0, 0.0, np.radians(90)
        R1 = Rotation.from_euler_angles(ea1, False, 'xyz')
        Y = X.transformed(R1).unitized()
        return Frame(inner.point_at(max(inner.domain)), X, Y)


view = App()


class FoldElement(BendMethods, Item):
    metal_width = 1

    def __call__(self, angle=None, radius=None, curve=None, *args, **kwargs):
        if curve is None:
            super().__call__(angle=angle, radius=radius, *args, **kwargs)
            self.radius = radius  # radius of the fold
            self.angle = angle  # angle between vectors of sides of bend after fillet
            self.inner = self.construct_folds()[0]
            self.outer = self.construct_folds()[1]
            self.inner_parts_trim = 0
        else:
            super().__call__(curve=curve, *args, **kwargs)
            self.inner = curve[0]
            self.outer = curve[1]
            self.inner_parts_trim = 0

    def circle_center(self):
        circ_s = Arc(r=self.radius)
        circ_l = Arc(r=self.radius + self.metal_width)
        if self.angle > 0:
            return circ_s, circ_l
        else:
            return circ_l, circ_s

    def circle_param(self):
        if self.angle > 0:
            circ_angle = 180 - self.angle
        else:
            circ_angle = 180 - (-self.angle)
        return np.radians(circ_angle)

    def transl_to_radius(self, circle, radius):
        if self.angle > 0:
            tr = Translation.from_vector(Vector.Yaxis() * radius)
        else:
            tr = Translation.from_vector(Vector.Yaxis() * (-radius - self.metal_width))
        c_t = circle.transformed(tr)
        return c_t

    def curved_segment(self, circle, radius):
        if self.angle < 0:
            circle(start_angle=np.pi / 2, end_angle=(np.pi / 2) - self.circle_param())
            seg = circle.to_compas()
            transl = self.transl_to_radius(seg, radius)
            return transl
        else:
            circle(start_angle=3 * np.pi / 2, end_angle=(3 * np.pi / 2) + self.circle_param())
            seg = OCCNurbsCurvePanels.reversed_copy(circle.to_compas())
            transl = self.transl_to_radius(seg, radius)
            return transl

    def construct_folds(self):
        folds = []
        for circ in self.circle_center():
            crv_seg = self.curved_segment(circ, self.radius)
            folds.append(crv_seg)
        return folds

    def straight_segment_len(self):
        full_len = self.circle_center()[1].circumference
        unfold = full_len * self.circle_param()
        return unfold

    # расстояние от точки касания до точки пересечения касательных
    def calc_extra_length(self):
        a = math.tan(np.radians(self.angle))
        return (self.radius+self.metal_width) / a

    # вроде как это всегда будет длина, которая получается от 90 градусов
    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        print(self.radius+self.metal_width)
        return (self.radius+self.metal_width) / a


class FoldElementFres(FoldElement, Item):
    metal_width = 1
    coeff = 0.3

    def __call__(self, angle=None, radius=None, fres_len=None, curve=None, *args, **kwargs):
        if curve is None:
            super().__call__(angle=angle, radius=radius, *args, **kwargs)
            self.angle = angle
            self.radius = radius
            self.fres_len = fres_len
            self.inner = self.construct_folds()[0]
            self.outer = self.construct_folds()[1]
            self.inner_parts_trim = self.outer_parts_l()
        else:
            super().__call__(curve=curve, *args, **kwargs)
            self.inner = curve[0]
            self.outer = curve[1]
            self.inner_parts_trim = self.outer_parts_l()

    # вычисление внутреннего радиуса
    def calc_inner_rad(self):
        part = (180 - np.abs(self.angle)) / 360
        # goal_fl = self.fres_len * self.coeff
        # goal_fl = self.fres_len * (self.radius - (self.metal_width / 2))
        # return goal_fl / (2 * math.pi * part)
        return 0.3

    def circle_center(self):
        circ_s = Arc(r=self.calc_inner_rad())
        circ_l = Arc(r=self.radius)
        return circ_s, circ_l

    def outer_parts_l(self):
        ang = np.radians((180 - np.abs(self.angle)) / 2)
        l_out = (self.metal_width / 2) * math.tan(ang)
        return l_out

    def inner_parts_l(self):
        ang = np.radians((180 - np.abs(self.angle)) / 2)
        l_in = (self.metal_width / 2) / math.cos(ang)
        return l_in

    def construct_inner(self, curve):
        ang = np.radians(np.abs(self.angle) / 2)
        old_xy_max = curve.point_at(max(curve.domain))
        old_xy_min = curve.point_at(min(curve.domain))
        if self.angle > 0:
            vec = Vector(-math.cos(ang), math.sin(ang))
            tr = Translation.from_vector(vec * self.inner_parts_l())
            new_points = [old_xy_min.transformed(tr), old_xy_max.transformed(tr)]
        else:
            vec = Vector(-math.cos(ang), -math.sin(ang))
            tr = Translation.from_vector(vec * self.inner_parts_l())
            new_points = [old_xy_min.transformed(tr), old_xy_max.transformed(tr)]

        min_crv = OCCNurbsCurve.from_line(Line(old_xy_min, new_points[0]))
        max_crv = OCCNurbsCurve.from_line(Line(old_xy_max, new_points[1]))
        return max_crv.joined(curve.joined(min_crv))

    def construct_folds(self):
        crv_segments = []
        for i, c in enumerate(self.circle_center()):
            crv = self.curved_segment(c, radius=-(self.metal_width - self.radius))
            if self.angle > 0:
                x_tr = Translation.from_vector(Vector.Xaxis() * (self.outer_parts_l()))
                crv_shift = crv.transformed(x_tr)
            else:
                crv_shift = crv
            crv_segments.append(crv_shift)

        inner = self.construct_inner(crv_segments[0])
        outer = crv_segments[1]
        if self.angle > 0:
            return [inner, outer]
        else:
            return [outer, inner]

    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return self.radius / a


class StraightElement(BendMethods):
    metal_width = 1

    @property
    def inner(self):

        if hasattr(self,"curve"):
            self._inner = self.curve[0]
            return self._inner
        elif hasattr(self,"length_out") and hasattr(self,"length_in"):
            self._inner = self.build_line()[0]
            return self._inner
        else:
            raise Exception

    @inner.setter
    def inner(self, v):
        self._inner = v

    @property
    def outer(self):
        if hasattr(self,"curve"):
            self._outer = self.curve[1]
            return self._outer
        elif hasattr(self,"length_out") and hasattr(self,"length_in"):
            self._outer = self.build_line()[1]
            return self._outer
        else:
            raise Exception

    @outer.setter
    def outer(self, v):
        self._outer = v



    def build_line(self):
        start = Point(-self.length_in[0], -self.metal_width, 0)
        #print(self.length_out, self.length_in)
        end = Point(self.length_out - self.length_in[0], -self.metal_width, 0)
        l_out = OCCNurbsCurve.from_line(Line(start, end))

        start = Point(0, 0, 0)
        end = Point(self.length_out - self.length_in[0] - self.length_in[1], 0, 0)
        l_in = OCCNurbsCurve.from_line(Line(start, end))
        return l_in, l_out

    @staticmethod
    def cap_elem(c_one, c_two):
        s_one, e_one = c_one.point_at(min(c_one.domain)), c_two.point_at(min(c_two.domain))
        s_two, e_two = c_two.point_at(max(c_two.domain)), c_one.point_at(max(c_one.domain))
        l_one = OCCNurbsCurve.from_line(Line(s_one, e_one))
        l_two = OCCNurbsCurve.from_line(Line(s_two, e_two))
        return l_one, l_two


class BendConstructorFres:

    def __init__(self, *args, start):
        # super().__init__(*args, start=start)
        self.steps = args[0]
        self.start = start
        self.curve = StraightElement(curve=[start, OCCNurbsCurve.from_line(Line(Point(-30, -1, 0), Point(0, -1, 0)))])
        self._i = 0

        self.folds = []
        self.straights = []
        for i in self.steps:
            if i[1] < 1:
                fold = FoldElementFres(angle=i[0], radius=i[1], fres_len=1.4)
            else:
                fold = FoldElement(angle=i[0], radius=i[1])
            self.folds.append(fold)

            straight = StraightElement(length_out=i[2])
            self.straights.append(straight)

        self.folds.append(FoldElement(angle=10, radius=10))
        self.folds = list(pairwise(self.folds))

    @staticmethod
    def translate_segments(line_segment, previous):
        if isinstance(previous, FoldElementFres):
            goal_frame = previous.get_plane(previous.inner, previous.outer)
        else:
            goal_frame = previous.get_plane(previous.inner)

        inner_crv = goal_frame.to_world_coordinates(line_segment.inner)
        outer_crv = goal_frame.to_world_coordinates(line_segment.outer)
        line_segment(curve=[inner_crv, outer_crv])
        return line_segment

    def __iter__(self):
        return self

    # гнем и все остальное относительно внутреннего радиуса
    def __next__(self):

        fold_start = self.folds[self._i][0]
        fold_end = self.folds[self._i][1]


        straight = self.straights[self._i]
        if self._i != len(self.steps)-1:
            straight(length_in=[fold_start.inner_parts_trim, fold_end.inner_parts_trim], length_out=straight.length_out - (fold_start.calc_rightangle_length()+fold_end.calc_rightangle_length()))
        else:
            straight(length_in=[fold_start.inner_parts_trim, 0], length_out=straight.length_out - fold_start.calc_rightangle_length())

        transl_f = self.translate_segments(fold_start, self.curve)
        transl_s = self.translate_segments(straight, transl_f)
        join_in, join_out = transl_f.inner.joined(transl_s.inner), transl_f.outer.joined(transl_s.outer)

        self.curve = transl_s
        self._i += 1
        return join_in, join_out

    def bend_(self):
        bend_in, bend_out = next(self)
        while self._i < len(self.steps):
            b_in, b_out = next(self)
            bend_in = bend_in.joined(b_in)
            bend_out = bend_out.joined(b_out)
        return bend_in, bend_out

    def close_curve(self):
        bends = self.bend_()
        caps = StraightElement()
        caps = caps.cap_elem(bends[0], bends[1])
        return [*bends, *caps]




line = OCCNurbsCurve.from_line(Line(Point(-30, 0, 0), Point(0, 0, 0)))
test = BendConstructorFres(((70, 0.8, 30), (10, 0.8, 29.3), (90, 1.3, 20)), start=line)

bend_ = test.bend_()
view.add(Polyline(bend_[0].locus()), linewidth=1, linecolor=(1, 0, 0))
view.add(Polyline(bend_[1].locus()), linewidth=1, linecolor=(1, 0, 0))


for i, v in enumerate(bend_):
    js['poly'].append(v.to_jsonstring())

with open("/Users/sofyadobycina/Documents/GitHub/mmodel/tests/triangl.json", "w") as outfile:
    json.dump(js, outfile)

#view.run()
