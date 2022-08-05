from __future__ import print_function
import math
# import rhino3dm
from collections import defaultdict
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from mm.baseitems import Item
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector, offset_line, intersection_line_line, \
    Translation, Line, Rotation
from compas_occ.geometry import OCCNurbsCurve, OCCNurbsSurface

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
        circ_angle = 180 - self.angle
        return circ_angle / 360

    '''@staticmethod
    def transl_to_zero(init_point, goal_point):
        vec = goal_point - init_point
        transl = Translation.from_vector(vec)
        return transl'''

    def transl_to_zero(self, curve):
        get_frame = curve.frame_at(min(curve.domain))
        tr = Transformation.from_frame_to_frame(get_frame, Frame.worldXY())
        return tr

    def curved_segment(self):
        circ = OCCNurbsCurvePanels.from_circle_world(self.circle_center())
        origin = Point(0.0, 0.0, 0.0)
        if self.dir > 0:
            seg = OCCNurbsCurvePanels.segmented(circ, 0.0, self.circle_param())
            transl = self.transl_to_zero(seg)
            transf = seg.transformed(transl)
            curve = OCCNurbsCurvePanels.reversed_copy(transf)
            return transf
        else:
            seg = OCCNurbsCurvePanels.segmented(circ, 1 - self.circle_param(), 1.0)
            transl = self.transl_to_zero(seg)
            return seg.transformed(transl)

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
        try:
            frame = previous.frame_at(domain)
            return frame
        #
        except:
            X = previous.tangent_at(domain).unitized()
            ea1 = 0.0, 0.0, np.radians(90)
            R1 = Rotation.from_euler_angles(ea1, False, 'xyz')
            Y = X.transformed(R1).unitized()
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
        get_line = straight.build_line()

        if self.dir[self._i - 1] < 0 or self._i == 0:
            transl_f = self.translate_segment(get_fold, self.curve, max(self.curve.domain))
        else:
            transl_f = self.translate_segment_inverse(get_fold, self.curve, max(self.curve.domain))

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
test = BendConstructor(angle=[90, 60], radius=[2, 2], dir=[1, 1], straight=[35, 45], start=line)
bend_ = test.bend_curve

extra_test = FoldElement(60, 2, 1)
get_fold = extra_test.curved_segment()


