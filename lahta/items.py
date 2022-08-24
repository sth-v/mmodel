from __future__ import print_function

import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
import compas.geometry
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


view = App(width=1600, height=900)


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

    def translate_segments(self, inner, to_transl, outer=None):
        if outer is not None:
            goal_frame = self.get_plane(inner, outer)
        else:
            goal_frame = self.get_plane(inner)

        new_line = goal_frame.to_world_coordinates(to_transl)
        return new_line


class FoldElement(BendMethods, Item):
    metal_width = 1

    def __call__(self, angle=None, radius=None, new_curve=None, inner_curve=None, outer_curve=None, *args, **kwargs):
        if inner_curve is None and outer_curve is None:
            super().__call__(angle=angle, radius=radius, *args, **kwargs)
            self.radius = radius  # radius of the fold
            self.angle = angle  # angle between vectors of sides of bend after fillet
            self.plane = Plane.worldXY()
            self.curve = self.construct_folds()
            self.inner = self.construct_folds()[0]
            self.outer = self.construct_folds()[1]
            self.inner_parts = 0
        else:
            super().__call__(inner_curve=inner_curve, outer_curve=outer_curve, *args, **kwargs)
            self.inner = inner_curve
            self.outer = outer_curve
            self.inner_parts = 0

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


class FoldElementFres(FoldElement, Item):
    metal_width = 1
    coeff = 0.3

    def __call__(self, angle=None, radius=None, fres_len=None, inner_curve=None, outer_curve=None, *args, **kwargs):
        if inner_curve is None and outer_curve is None:
            super().__call__(angle=angle, radius=radius, *args, **kwargs)
            self.angle = angle
            self.radius = radius
            self.fres_len = fres_len
            self.curve = self.construct_folds()
            self.inner = self.construct_folds()[0]
            self.outer = self.construct_folds()[1]
            self.inner_parts = self.inner_parts_l()
        else:
            super().__call__(inner_curve=inner_curve, outer_curve=outer_curve, *args, **kwargs)
            self.inner = inner_curve
            self.outer = outer_curve
            self.inner_parts = self.inner_parts_l()

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
        return OCCNurbsCurvePanels.from_circle_world(circ_s), OCCNurbsCurvePanels.from_circle_world(circ_l)

    def inner_parts_l(self):
        ang = np.radians(np.abs(self.angle) / 2)
        l_out = (self.metal_width / 2) / math.tan(ang)
        return l_out

    def construct_inner(self, curve):
        old_xy_max = curve.point_at(max(curve.domain))
        old_xy_min = curve.point_at(min(curve.domain))
        if self.angle > 0:
            new_x = old_xy_max.x - (self.inner_parts_l())
            new_y = old_xy_max.y + (self.metal_width / 2)
            new_points = [Point(0, 0, 0), Point(new_x, new_y, 0)]
        else:
            new_x_max = old_xy_max.x - (self.inner_parts_l())
            new_y_max = old_xy_max.y - (self.metal_width / 2)
            new_x_min = old_xy_min.x - (self.inner_parts_l())
            new_y_min = old_xy_min.y - (self.metal_width / 2)
            new_points = [Point(new_x_min, new_y_min, 0), Point(new_x_max, new_y_max, 0)]

        min_crv = OCCNurbsCurve.from_line(Line(old_xy_min, new_points[0]))
        max_crv = OCCNurbsCurve.from_line(Line(old_xy_max, new_points[1]))
        view.add(Polyline(max_crv.locus()), linewidth=1, linecolor=(1, 0, 0))
        view.add(Polyline(min_crv.locus()), linewidth=1, linecolor=(1, 0, 0))
        return max_crv.joined(curve.joined(min_crv))

    def construct_folds(self):
        crv_segments = []
        for i, c in enumerate(self.circle_center()):
            crv = self.curved_segment(c, radius=-0.2)
            if self.angle > 0:
                x_tr = Translation.from_vector(Vector.Xaxis() * (self.inner_parts_l()))
                crv_shift = crv.transformed(x_tr)
            else:
                crv_shift = crv
            crv_segments.append(crv_shift)

        inner = self.construct_inner(crv_segments[0])
        outer = crv_segments[1]
        if self.angle>0:
            return [inner, outer]
        else:
            return [outer, inner]

    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return (self.radius / a) + self.inner_parts_l()


#TEST = FoldElementFres(angle=70, radius=0.8, fres_len=1.4)
#t = TEST.construct_folds()

# view.show()
class StraightElement(BendMethods, Item):
    metal_width = 1

    def __call__(self, length_in=None, length_out=None, inner_curve=None, outer_curve=None, *args, **kwargs):
        if inner_curve is None and outer_curve is None:
            super().__call__(length_in=length_in, length_out=length_out, *args, **kwargs)
            self.length_in = length_in
            self.length_out = length_out
            self.plane = Plane.worldXY()
            self.inner = self.build_line()[0]
            self.outer = self.build_line()[1]
        else:
            super().__call__(inner_curve=inner_curve, outer_curve=outer_curve, *args, **kwargs)
            self.inner = inner_curve
            self.outer = outer_curve

    def build_line(self):
        start = Point(0, 0, 0)
        end = Point(self.length_in, 0, 0)
        l_in = OCCNurbsCurve.from_line(Line(start, end))

        start = Point(-self.length_out[0], -self.metal_width, 0)
        end = Point(self.length_in+self.length_out[1], -self.metal_width, 0)
        l_out = OCCNurbsCurve.from_line(Line(start, end))
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
        self.curve = StraightElement(inner_curve=start, outer_curve=OCCNurbsCurve.from_line(Line(Point(5, 6, 0), Point(-30, 6, 0))))
        self._i = -1
        self.bend_curve = self.close_curve()

    @staticmethod
    def translate_segments(line_segment, previous):

        if isinstance(previous, FoldElementFres):
            goal_frame = previous.get_plane(previous.inner, previous.outer)
        else:
            goal_frame = previous.get_plane(previous.inner)

        inner_crv = goal_frame.to_world_coordinates(line_segment.inner)
        outer_crv = goal_frame.to_world_coordinates(line_segment.outer)
        line_segment(inner_curve=inner_crv, outer_curve=outer_crv)
        return line_segment

    def __iter__(self):
        return self


    # гнем и все остальное относительно внутреннего радиуса
    def __next__(self):
        self._i += 1

        if self.steps[self._i][1] > 1:
            fold = FoldElement(angle=self.steps[self._i][0], radius=self.steps[self._i][1])
        else:
            fold = FoldElementFres(angle=self.steps[self._i][0], radius=self.steps[self._i][1], fres_len=1.4)
        straight = StraightElement(length_in=self.steps[self._i][2] - (2 * fold.calc_rightangle_length()), length_out=[fold.inner_parts, 0])

        transl_f = self.translate_segments(fold, self.curve)
        transl_s = self.translate_segments(straight, transl_f)
        print(compas.geometry.distance_point_line(transl_f.inner.point_at(max(transl_f.inner.domain)), (transl_s.outer.point_at(max(transl_s.outer.domain)),transl_s.outer.point_at(min(transl_s.outer.domain)) )))

        view.add(Polyline(transl_f.outer.locus()), linewidth=1, linecolor=(0, 0, 0))
        view.add(Polyline(transl_s.outer.locus()), linewidth=1, linecolor=(0, 0, 1))
        view.add(Polyline(transl_f.inner.locus()), linewidth=1, linecolor=(0, 0, 0))
        view.add(Polyline(transl_s.inner.locus()), linewidth=1, linecolor=(0, 0, 1))
        view.show()

        join_in, join_out = transl_f.inner.joined(transl_s.inner), transl_f.outer.joined(transl_s.outer)
        self.curve = transl_s
        return join_in, join_out

    def bend_(self):
        bend_in, bend_out = next(self)
        view.add(Polyline(bend_in.locus()), linewidth=1, linecolor=(0, 0, 1))
        view.add(Polyline(bend_out.locus()), linewidth=1, linecolor=(0, 0, 1))
        view.show()
        while self._i + 1 < len(self.steps):
            b_in, b_out = next(self)

            view.add(Polyline(b_in.locus()), linewidth=1, linecolor=(0, 0, 1))
            view.add(Polyline(b_out.locus()), linewidth=1, linecolor=(0, 0, 1))
            view.show()
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
test = BendConstructor(((70, 0.8, 30), (110, 1.3, 9.3), (90, 1.3, 20)), start=line)

bend_ = test.bend_curve
# extr = test.extrusion()
print(bend_)

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
