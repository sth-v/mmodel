from __future__ import print_function
from typing import Iterable
import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np

from mm.geom.geom import Arc
from mm.baseitems import Item
from compas_occ.geometry import OCCNurbsCurve, OCCNurbsSurface
from more_itertools import pairwise
from compas_view2.app import App
from dataclasses import dataclass, astuple, asdict
import compas.geometry as cg

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
        return cg.Polygon(self.vertices)

    def get_lines(self):
        return self.polygon.lines

    def poly_offset(self, dist):
        return cg.offset_polygon(self.vertices, dist)

    def poly_normal(self):
        return cg.normal_polygon(self.get_poly())


class PointObj(Item):
    def __call__(self, *args, **kwargs):
        super().__call__(*args, **kwargs)
        self.point = args[0]
        self.compas_point = self.compas_point

    def compas_point(self):
        return cg.Point(*self.point)

    def translate_points(self, vector):
        tr = cg.translate_points([self.point], vector)[0]
        return PointObj(tr).point

view = App()
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
        R1 = cg.Rotation.from_euler_angles(ea1, False, 'xyz')
        Y = X.transformed(R1).unitized()
        return cg.Frame(inner.point_at(max(inner.domain)), X, Y)

    @staticmethod
    def translate_segments(line_segment, previous):
        if isinstance(previous, FoldElementFres):
            goal_frame = previous.get_plane(previous.inner, previous.outer)
        elif isinstance(previous, cg.Frame):
            goal_frame = previous
        else:
            goal_frame = previous.get_plane(previous.inner)

        inner_crv = goal_frame.to_world_coordinates(line_segment.inner)
        outer_crv = goal_frame.to_world_coordinates(line_segment.outer)
        line_segment(curve=[inner_crv, outer_crv])
        return line_segment





class FoldElement(BendMethods):
    metal_width = 1
    inner_parts_trim = 0

    @property
    def inner(self):

        if hasattr(self, "curve"):
            self._inner = self.curve[0]
            return self._inner
        elif hasattr(self, "radius") and hasattr(self, "angle"):
            self._inner = self.construct_folds()[0]
            return self._inner
        else:
            raise Exception

    @inner.setter
    def inner(self, v):
        self._inner = v

    @property
    def outer(self):

        if hasattr(self, "curve"):
            self._outer = self.curve[1]
            return self._outer
        elif hasattr(self, "radius") and hasattr(self, "angle"):
            self._outer = self.construct_folds()[1]
            return self._outer
        else:
            raise Exception

    @outer.setter
    def outer(self, v):
        self._outer = v

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
            tr = cg.Translation.from_vector(cg.Vector.Yaxis() * radius)
        else:
            tr = cg.Translation.from_vector(cg.Vector.Yaxis() * (-radius - self.metal_width))
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
        return (self.radius + self.metal_width) / a

    # вроде как это всегда будет длина, которая получается от 90 градусов
    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return (self.radius + self.metal_width) / a


class FoldElementFres(FoldElement, Item):
    metal_width = 1

    def __call__(self, met_left=None, in_rad=None, **kwargs):
        super().__call__(met_left=met_left, in_rad=in_rad, **kwargs)

        if met_left is not None:
            self.in_rad = self.radius - self.met_left
        if in_rad is not None:
            self.met_left = self.radius - self.in_rad

    @property
    def inner_parts_trim(self):

        if hasattr(self, "angle"):
            self._inner_parts_trim = self.outer_parts_l()
            return self._inner_parts_trim
        else:
            raise Exception

    @inner_parts_trim.setter
    def inner_parts_trim(self, v):
        self._inner_parts_trim = v

    def circle_center(self):
        circ_s = Arc(r=self.in_rad)
        circ_l = Arc(r=self.radius)
        return circ_s, circ_l

    def outer_parts_l(self):
        ang = np.radians((180 - np.abs(self.angle)) / 2)
        l_out = self.met_left * math.tan(ang)
        return l_out

    def inner_parts_l(self):
        ang = np.radians((180 - np.abs(self.angle)) / 2)
        l_in = self.met_left / math.cos(ang)
        return l_in

    def construct_inner(self, curve):
        ang = np.radians(np.abs(self.angle) / 2)
        old_xy_max = curve.point_at(max(curve.domain))
        old_xy_min = curve.point_at(min(curve.domain))
        if self.angle > 0:
            vec = cg.Vector(-math.cos(ang), math.sin(ang))
            tr = cg.Translation.from_vector(vec * self.inner_parts_l())
            new_points = [old_xy_min.transformed(tr), old_xy_max.transformed(tr)]
        else:
            vec = cg.Vector(-math.cos(ang), -math.sin(ang))
            tr = cg.Translation.from_vector(vec * self.inner_parts_l())
            new_points = [old_xy_min.transformed(tr), old_xy_max.transformed(tr)]

        min_crv = OCCNurbsCurve.from_line(cg.Line(old_xy_min, new_points[0]))
        max_crv = OCCNurbsCurve.from_line(cg.Line(old_xy_max, new_points[1]))
        return max_crv.joined(curve.joined(min_crv))

    def construct_folds(self):
        crv_segments = []
        for i, c in enumerate(self.circle_center()):
            crv = self.curved_segment(c, radius=-(self.metal_width - self.radius))
            if self.angle > 0:
                x_tr = cg.Translation.from_vector(cg.Vector.Xaxis() * (self.outer_parts_l()))
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
        if hasattr(self, "curve"):
            self._inner = self.curve[0]
            return self._inner
        elif hasattr(self, "length_out") and hasattr(self, "length_in"):
            self._inner = self.build_line()[0]
            return self._inner
        else:
            raise Exception

    @inner.setter
    def inner(self, v):
        self._inner = v

    @property
    def outer(self):
        if hasattr(self, "curve"):
            self._outer = self.curve[1]
            return self._outer
        elif hasattr(self, "length_out") and hasattr(self, "length_in"):
            self._outer = self.build_line()[1]
            return self._outer
        else:
            raise Exception

    @outer.setter
    def outer(self, v):
        self._outer = v

    def build_line(self):
        start = cg.Point(-self.length_in[0], -self.metal_width, 0)
        end = cg.Point(self.length_out - self.length_in[0], -self.metal_width, 0)
        l_out = OCCNurbsCurve.from_line(cg.Line(start, end))

        start = cg.Point(0, 0, 0)
        end = cg.Point(self.length_out - self.length_in[0] - self.length_in[1], 0, 0)
        l_in = OCCNurbsCurve.from_line(cg.Line(start, end))
        return l_in, l_out

    @staticmethod
    def cap_elem(c_one, c_two):
        s_one, e_one = c_one.point_at(min(c_one.domain)), c_two.point_at(min(c_two.domain))
        s_two, e_two = c_two.point_at(max(c_two.domain)), c_one.point_at(max(c_one.domain))
        l_one = OCCNurbsCurve.from_line(cg.Line(s_one, e_one))
        l_two = OCCNurbsCurve.from_line(cg.Line(s_two, e_two))
        return l_one, l_two


@dataclass
class Segment(Item, list):
    length: float

    def __getitem__(self, item):
        l = astuple(self)
        return l[item]

    def __init__(self, length, *args, **kwargs):
        super().__init__(length=length, *args, **kwargs)


@dataclass
class BendSegment(Segment, BendMethods):
    length: float
    radius: float
    angle: float
    in_rad: float = None
    met_left: float = None
    metal_width = 1

    def __init__(self, length, radius, angle, in_rad=None, met_left=None, *args, **kwargs):
        super().__init__(length=length, radius=radius, angle=angle, in_rad=in_rad, met_left=met_left, *args, **kwargs)
        self.init_state = self.real_state

    def __call__(self, start=cg.Frame.worldXY(), end=None, *args, **kwargs):
        super().__call__(start=start, end=end, *args, **kwargs)

        if self.radius < self.metal_width:
            self.fold = FoldElementFres(angle=self.angle, radius=self.radius, in_rad=self.in_rad, met_left=self.met_left)
        else:
            self.fold = FoldElement(angle=self.angle, radius=self.radius)

        if self.end is not None:
            self.straight = StraightElement(length_in=[self.fold.inner_parts_trim, self.end.inner_parts_trim],
                                            length_out=self.length - (self.fold.calc_rightangle_length() + self.end.calc_rightangle_length()))
        else:
            self.straight = StraightElement(length_in=[self.fold.inner_parts_trim, 0],
                                            length_out=self.length - (self.fold.calc_rightangle_length()))

        self.real_state = self.get_segment()

    def get_segment(self):
        self.fold = self.translate_segments(self.fold, self.start)
        self.straight = self.translate_segments(self.straight, self.fold)
        return [self.fold, self.straight]

    def compas_view(self):
        view.add(cg.Polyline(self.real_state[0].inner.locus()), linewidth=1, linecolor=(1, 0, 0))
        view.add(cg.Polyline(self.real_state[1].inner.locus()), linewidth=1, linecolor=(1, 0, 0))
        view.add(cg.Polyline(self.real_state[0].outer.locus()), linewidth=1, linecolor=(1, 0, 0))
        view.add(cg.Polyline(self.real_state[1].outer.locus()), linewidth=1, linecolor=(1, 0, 0))



class Bend(Item):
    _i = 0
    metal_width = 1


    def __init__(self, segments, start=cg.Frame.worldXY(), *args, **kwargs):
        self.bend_stage = []
        self.start_stage = []
        super().__init__(segments=segments, start=start, *args, **kwargs)


    def __call__(self, segments, start=cg.Frame.worldXY(), *args, **kwargs):
        super().__call__(segments=segments, start=start, *args, **kwargs)

        while self._i < len(self.segments):
            bend = next(self)
            self.bend_stage.append(bend)
        self._i = 0
        view.run()

    def __iter__(self):
        return self

    # гнем и все остальное относительно внутреннего радиуса
    def __next__(self):

        if isinstance(self.start, StraightElement):
            self.start_stage.append(self.start.get_plane(self.start.inner))
            view.add(self.start.get_plane(self.start.inner), size=2)

        else:
            self.start_stage.append(self.start)

        bend_segment = self.segments[self._i]

        if self._i != len(self.segments)-1:
            neigh = self.segments[self._i + 1].fold
        else:
            neigh = None

        bend_segment(start=self.start, end=neigh)
        bend_segment.compas_view()
        self.start = bend_segment.straight
        self._i += 1
        return bend_segment





line = OCCNurbsCurve.from_line(cg.Line(cg.Point(-30, 0, 0), cg.Point(0, 0, 0)))

# bend_ = test.bend_()
# view.add(Polyline(bend_[0].locus()), linewidth=1, linecolor=(1, 0, 0))
# view.add(Polyline(bend_[1].locus()), linewidth=1, linecolor=(1, 0, 0))


# for i, v in enumerate(bend_):
# js['poly'].append(v.to_jsonstring())

# with open("/Users/sofyadobycina/Documents/GitHub/mmodel/tests/triangl.json", "w") as outfile:
# json.dump(js, outfile)

# view.run()
