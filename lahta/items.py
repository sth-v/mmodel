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
        #try:
            #view.add(Frame(outer.point_at(max(outer.domain)), X, Y), size=1)
            #view.add(outer.frame_at(min(outer.domain)), size=1)
            #view.add(outer.frame_at(max(outer.domain)), size=1)
        #except:
            #pass
        return Frame(inner.point_at(max(inner.domain)), X, Y)



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
            self.inner_parts_trim = 0
        else:
            super().__call__(inner_curve=inner_curve, outer_curve=outer_curve, *args, **kwargs)
            self.inner = inner_curve
            self.outer = outer_curve
            self.inner_parts_trim = 0

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
            print (circ_angle, 'angle')
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
            print(seg)
            f_one = seg.frame_at(min(seg.domain)).yaxis
            f_two = seg.frame_at(max(seg.domain)).yaxis
            print(0.720, 'parammy', param*90/0.25, 'param_alg')
            view.add(Polyline(seg.locus()), linewidth=1, linecolor=(0, 0, 0))
            view.add(transl.point_at(0.25), pointcolor=(1, 0, 0))
            view.add(transl.point_at(param), pointcolor=(1, 0, 0))
            print(np.degrees(f_one.angles(f_two)[0]), np.degrees(f_one.angles(f_two)[1]), 'vectors')

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
            self.inner_parts_trim = self.outer_parts_l()
        else:
            super().__call__(inner_curve=inner_curve, outer_curve=outer_curve, *args, **kwargs)
            self.inner = inner_curve
            self.outer = outer_curve
            self.inner_parts_trim = self.outer_parts_l()

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
            tr = Translation.from_vector(vec*self.inner_parts_l())
            #view.add(old_xy_min.transformed(tr), pointcolor=(0, 0, 1))
            #view.add(old_xy_max.transformed(tr), pointcolor=(0, 0, 1))
            #view.add(old_xy_min, pointcolor=(1, 0, 0))
            #view.add(old_xy_max, pointcolor=(1, 0, 0))
            new_points = [old_xy_min.transformed(tr), old_xy_max.transformed(tr)]
        else:
            vec = Vector(-math.cos(ang), -math.sin(ang))
            tr = Translation.from_vector(vec * self.inner_parts_l())
            #view.add(old_xy_min.transformed(tr), pointcolor=(0, 0, 1))
            #view.add(old_xy_max.transformed(tr), pointcolor=(0, 0, 1))
            #view.add(old_xy_min, pointcolor=(1, 0, 0))
            #view.add(old_xy_max, pointcolor=(1, 0, 0))
            new_points = [old_xy_min.transformed(tr), old_xy_max.transformed(tr)]

        min_crv = OCCNurbsCurve.from_line(Line(old_xy_min, new_points[0]))
        max_crv = OCCNurbsCurve.from_line(Line(old_xy_max, new_points[1]))
        view.add(Polyline(max_crv.locus()), linewidth=1, linecolor=(0, 0, 0))
        view.add(Polyline(min_crv.locus()), linewidth=1, linecolor=(0, 0, 0))
        return max_crv.joined(curve.joined(min_crv))

    def construct_folds(self):
        crv_segments = []
        for i, c in enumerate(self.circle_center()):
            crv = self.curved_segment(c, radius=-0.2)
            if self.angle > 0:
                x_tr = Translation.from_vector(Vector.Xaxis() * (self.outer_parts_l()))
                crv_shift = crv.transformed(x_tr)
                view.add(Polyline(crv_shift.locus()), linewidth=1, linecolor=(0, 0, 0))
            else:
                crv_shift = crv
                view.add(Polyline(crv_shift.locus()), linewidth=1, linecolor=(0, 0, 0))
            crv_segments.append(crv_shift)

        inner = self.construct_inner(crv_segments[0])
        #print(compas.geometry.distance_point_point(crv_segments[0].point_at(max(crv_segments[0].domain)),crv_segments[1].point_at(max(crv_segments[1].domain))))

        outer = crv_segments[1]
        if self.angle>0:
            return [inner, outer]
        else:
            return [outer, inner]

    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return (self.radius / a) + self.outer_parts_l()


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
        start = Point(-self.length_in[0], -self.metal_width, 0)
        end = Point(self.length_out-self.length_in[0], -self.metal_width, 0)
        l_out = OCCNurbsCurve.from_line(Line(start, end))

        start = Point(0, 0, 0)
        end = Point(self.length_out-self.length_in[0]-self.length_in[1], 0, 0)
        l_in = OCCNurbsCurve.from_line(Line(start, end))
        return l_in, l_out

    @staticmethod
    def cap_elem(c_one, c_two):
        s_one, e_one = c_one.point_at(min(c_one.domain)), c_two.point_at(min(c_two.domain))
        s_two, e_two = c_two.point_at(max(c_two.domain)), c_one.point_at(max(c_one.domain))
        l_one = OCCNurbsCurve.from_line(Line(s_one, e_one))
        l_two = OCCNurbsCurve.from_line(Line(s_two, e_two))
        return l_one, l_two


import json

js = {'poly': []}


class BendConstructor:
    def __init__(self, *args, start):
        self.steps = args[0]
        self.start = start
        self.curve = StraightElement(inner_curve=start, outer_curve=OCCNurbsCurve.from_line(Line(Point(-30, -1, 0), Point(0, -1, 0))))
        self._i = -1
        self.bend_curve = self.close_curve()

    @staticmethod
    def translate_segments(line_segment, previous):

        if isinstance(previous, FoldElementFres):
            goal_frame = previous.get_plane(previous.inner, previous.outer)
            view.add(goal_frame, size=1)
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
        straight = StraightElement(length_in=[fold.inner_parts_trim, 0], length_out=self.steps[self._i][2] - (2 * fold.calc_rightangle_length()))

        transl_f = self.translate_segments(fold, self.curve)
        transl_s = self.translate_segments(straight, transl_f)
        view.add(Polyline(transl_f.outer.locus()), linewidth=1, linecolor=(0, 0, 0))
        view.add(Polyline(transl_s.outer.locus()), linewidth=1, linecolor=(0, 0, 1))
        view.add(Polyline(transl_f.inner.locus()), linewidth=1, linecolor=(0, 0, 0))
        view.add(Polyline(transl_s.inner.locus()), linewidth=1, linecolor=(0, 0, 1))
        view.show()

        js['poly'].append(transl_f.outer.to_jsonstring())
        js['poly'].append(transl_s.outer.to_jsonstring())
        js['poly'].append(transl_f.inner.to_jsonstring())
        js['poly'].append(transl_s.inner.to_jsonstring())

        with open("/Users/sofyadobycina/Documents/GitHub/mmodel/tests/triangl.json", "w") as outfile:
            json.dump(js, outfile)

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


line = OCCNurbsCurve.from_line(Line(Point(-30, 0, 0), Point(0, 0, 0)))
test = BendConstructor(((10, 1.8, 30), (110, 1.3, 9.3), (90, 1.3, 20)), start=line)

bend_ = test.bend_curve
# extr = test.extrusion()
print(bend_)

for i, v in enumerate(bend_):

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
