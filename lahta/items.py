from __future__ import print_function
import math
from tools.geoms import OCCNurbsCurvePanels
import numpy as np
from functools import wraps
from mm.parametric import Arc
from mm.baseitems import Item
from compas_occ.geometry import OCCNurbsCurve
import compas_occ.geometry as cc
from lahta.setup_view import view
from dataclasses import dataclass, astuple
import compas.geometry as cg

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


# Элемент отгиба

class ParentFrame2D:

    def __init__(self, function):
        self.function = function
        self.name = function.__name__

    def __get__(self, obj, type=None) -> object:
        args = self.function(obj)

        obj.__dict__[self.name] = self.parent_frame(*args)
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        pass

    def parent_frame(self, *args):
        if len(args) > 2:
            X = args[2].tangent_at(args[3]).unitized()
        else:
            X = args[0].tangent_at(args[1]).unitized()
        ea1 = 0.0, 0.0, np.radians(90)
        R1 = cg.Rotation.from_euler_angles(ea1, False, 'xyz')
        Y = X.transformed(R1).unitized()
        parent = cg.Frame(args[0].point_at(args[1]), X, Y)
        return parent


class ParentFrame3D(ParentFrame2D):
    def parent_frame(self, *args):
        y = cg.Vector.from_start_end(args[0].start, args[0].end).unitized()
        x = cg.Vector.cross(y, args[1])
        z = cg.Vector(*args[1]).inverted()
        parent = cg.Frame(args[0].start, xaxis=x, yaxis=z)
        return parent


class ParentFrameUnroll(ParentFrame2D):
    def parent_frame(self, *args):
        y = cg.Vector.from_start_end(args[0].start, args[0].end).unitized()
        x = cg.Vector.cross(y, args[1])
        parent = cg.Frame(args[0].start, xaxis=x, yaxis=y)
        return parent


class TransformableItem(Item):
    zero_frame = cg.Frame.worldXY()

    @property
    def transform_matrix(self):
        try:
            return cg.Transformation.from_frame_to_frame(self.zero_frame, self.parent.parent_frame)
        except:
            return cg.Transformation.from_frame_to_frame(self.zero_frame, self.parent)

    @classmethod
    def obj_transform(cls, f):
        @wraps(f)
        def this_wrapper(this):

            if hasattr(this, 'parent_obj'):
                transformation = cg.Transformation.from_frame_to_frame(this.zero_frame, this.parent_obj)
                this.zero_frame = this.parent_obj
            else:
                transformation = cg.Transformation.from_frame_to_frame(this.zero_frame, this.zero_frame)

            f(this, transformation)

            return this

        return this_wrapper


class FoldElement(TransformableItem):
    inner_parts_trim = 0

    @ParentFrame2D
    def parent_frame(self):
        return self.inner, max(self.inner.domain)

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

    def calc_folds(self):
        folds = []
        for circ in self.circle_center():
            crv_seg = self.curved_segment(circ, self.radius)
            folds.append(crv_seg)
        return folds

    def __call__(self, parent=cg.Frame.worldXY(), *args, **kwargs):
        super().__call__(parent=parent, *args, **kwargs)
        inner = self.calc_folds()[0]
        self.inner = inner.transformed(self.transform_matrix)

        outer = self.calc_folds()[1]
        self.outer = outer.transformed(self.transform_matrix)

    @property
    def straight_len(self):
        self._straight_len = (2 * math.pi * self.radius) * (np.radians(self.angle) / (2 * math.pi))
        return self._straight_len


    # расстояние от точки касания до точки пересечения касательных
    def calc_extra_length(self):
        a = math.tan(np.radians(self.angle))
        return (self.radius + self.metal_width) / a

    # вроде как это всегда будет длина, которая получается от 90 градусов
    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return (self.radius + self.metal_width) / a


class FoldElementFres(FoldElement):

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

    @ParentFrame2D
    def parent_frame(self):

        return self.inner, max(self.inner.domain), self.outer, max(self.outer.domain)

    def circle_center(self):
        circ_s = Arc(r=self.in_rad)
        circ_l = Arc(r=self.radius)
        return circ_s, circ_l

    def outer_parts_l(self):
        ang = np.radians((180 - np.abs(self.angle)) / 2)
        l_out = (self.metal_width - self.met_left) * math.tan(ang)
        return l_out

    def inner_parts_l(self):
        ang = np.radians((180 - np.abs(self.angle)) / 2)
        l_in = (self.metal_width - self.met_left) / math.cos(ang)
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

    def calc_folds(self):
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
        return [inner, outer]

    def calc_rightangle_length(self):
        a = math.tan(math.pi / 4)
        return self.radius / a


class StraightElement(TransformableItem):

    @ParentFrame2D
    def parent_frame(self):
        return self.inner, max(self.inner.domain)

    def __call__(self, parent=cg.Frame.worldXY(), *args, **kwargs):
        super().__call__(parent=parent, *args, **kwargs)
        start = cg.Point(-self.length_in[0], -self.metal_width, 0)
        end = cg.Point(self.length_out - self.length_in[0], -self.metal_width, 0)
        outer = OCCNurbsCurve.from_line(cg.Line(start, end))
        self.outer = outer.transformed(self.transform_matrix)

        start = cg.Point(0, 0, 0)
        end = cg.Point(self.length_out - self.length_in[0] - self.length_in[1], 0, 0)
        inner = OCCNurbsCurve.from_line(cg.Line(start, end))
        self.inner = inner.transformed(self.transform_matrix)


@dataclass
class Segment(Item, list):
    length: float

    def __getitem__(self, item):
        l = astuple(self)
        return l[item]

    def __init__(self, length, *args, **kwargs):
        super().__init__(length=length, *args, **kwargs)


@dataclass
class BendSegment(Segment, TransformableItem):
    length: float
    radius: float
    angle: float
    metal_width = 1.0

    def __init__(self, length, radius, angle, *args, **kwargs):
        super().__init__(length=length, radius=radius, angle=angle, *args, **kwargs)

    def __call__(self, parent=cg.Frame.worldXY(), end=None, *args, **kwargs):
        super().__call__(parent=parent, end=end, *args, **kwargs)
        if 'parent_obj' in kwargs.keys():
            pass
        elif hasattr(self, 'fold'):
            self.fold(parent=self.parent, **kwargs)
            if self.end is not None:
                self.straight(parent=self.fold, length_in=[self.fold.inner_parts_trim, self.end.inner_parts_trim],
                              length_out=self.length - (self.fold.calc_rightangle_length() +
                                                        self.end.calc_rightangle_length()), **kwargs)
            else:
                self.straight(length_in=[self.fold.inner_parts_trim, 0],
                              length_out=self.length - (self.fold.calc_rightangle_length()),
                              metal_width=self.metal_width, parent=self.fold)

            self.parent_frame = self.straight.parent_frame

        else:
            self.fold = self.bending_fold()
            self.straight = self.bending_straight(self.fold)

            self.parent_frame = self.straight.parent_frame

    def bending_fold(self):
        fold = FoldElement(angle=self.angle, radius=self.radius, metal_width=self.metal_width, parent=self.parent)
        return fold

    def bending_straight(self, fold):
        straight = StraightElement(metal_width=self.metal_width, parent=fold, length_in=[self.fold.inner_parts_trim, 0],
                                   length_out=self.length - (self.fold.calc_rightangle_length()), length = self.length)
        return straight



    @TransformableItem.obj_transform
    def transform_data(self, transformation):
        self.fold.inner = self.fold.inner.transformed(transformation)
        self.fold.outer = self.fold.outer.transformed(transformation)
        self.straight.inner = self.straight.inner.transformed(transformation)
        self.straight.outer = self.straight.outer.transformed(transformation)

    def to_compas(self):
        return (self.fold.inner,
                self.straight.inner,
                self.fold.outer,
                self.straight.outer)

    def viewer(self, v):
        v.add(cg.Polyline(self.fold.inner.locus()), linewidth=2, linecolor=(1, 0, 0))
        v.add(cg.Polyline(self.fold.outer.locus()), linewidth=2, linecolor=(0, 0, 1))
        v.add(cg.Polyline(self.straight.inner.locus()), linewidth=2, linecolor=(1, 0, 0))
        v.add(cg.Polyline(self.straight.outer.locus()), linewidth=2, linecolor=(0, 0, 1))
        return v


@dataclass
class BendSegmentFres(BendSegment):
    length: float
    radius: float
    angle: float
    in_rad: float = None
    met_left: float = None
    metal_width = 1.0

    def __init__(self, length, radius, angle, in_rad=None, met_left=None, *args, **kwargs):
        super().__init__(length=length, radius=radius, angle=angle, in_rad=in_rad, met_left=met_left, *args, **kwargs)

    def __call__(self, parent=cg.Frame.worldXY(), end=None, *args, **kwargs):
        super().__call__(parent=parent, end=end, *args, **kwargs)

    def bending_fold(self):
        if self.met_left is not None:
            self.in_rad = self.radius - self.met_left
        elif self.in_rad is not None:
            self.met_left = self.radius - self.in_rad
        else:
            raise ValueError
        fold = FoldElementFres(angle=self.angle, radius=self.radius, in_rad=self.in_rad, met_left=self.met_left,
                               metal_width=self.metal_width, parent=self.parent)
        return fold


class Bend(Item):
    def __init__(self, segments: list[BendSegment], parent=cg.Frame.worldXY(), *args, **kwargs):
        self._i = 0
        self.bend_stage = []
        super().__init__(segments=segments, parent=parent, *args, **kwargs)

    def __call__(self, parent=cg.Frame.worldXY(), *args, **kwargs):
        super().__call__(parent=parent, *args, **kwargs)

        if 'parent_obj' in kwargs.keys():
            pass
        else:
            self._data = []
            while self._i < self.__len__():
                bend = next(self)
                self.bend_stage.append(bend)

            self.reload()

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.segments)

    def to_compas(self):
        for d in self._data:
            yield d.to_data()

    def reload(self):
        self._i = 0

    # гнем и все остальное относительно внутреннего радиуса
    def __next__(self):

        bend_segment = self.segments[self._i]

        if self._i != len(self.segments) - 1:
            neigh = self.segments[self._i + 1].fold
        else:
            neigh = None

        bend_segment(parent=self.parent, end=neigh)

        self.parent = bend_segment.parent_frame
        self._i += 1
        # self._data.extend(bend_segment.to_compas())
        return bend_segment

    @property
    def obj_transform(self):
        self._obj_transform = []
        for i in self.bend_stage:
            i(parent_obj=self.parent_obj)
            i.transform_data()
            self._obj_transform.append(i.fold)
            self._obj_transform.append(i.straight)
        return self._obj_transform

    @property
    def tri_offset(self):
        fold = self.bend_stage[0].fold
        a = math.tan(np.radians(fold.angle/2))
        if isinstance(fold, FoldElementFres):
            self._tri_offset = (fold.in_rad + fold.metal_width) / a
        else:
            self._tri_offset = (fold.radius + fold.metal_width) / a
        return self._tri_offset

    @tri_offset.setter
    def tri_offset(self, v):
        self._tri_offset = v

    @property
    def inner(self):
        self._inner = []
        for i in self.obj_transform:
            self._inner.append(i.fold.inner)
            self._inner.append(i.straight.inner)
        return self._inner

    @inner.setter
    def inner(self, r):
        self._inner = r

    @property
    def outer(self):
        self._outer = []
        for i in self.obj_transform:
            self._outer.append(i.fold.outer)
            self._outer.append(i.straight.outer)
        return self._outer

    @outer.setter
    def outer(self, r):
        self._outer = r

    @property
    def lengths(self):
        self._lengths = []
        for i in self.bend_stage:
            self._lengths.append(i.fold.straight_len)
            self._lengths.append(i.straight.length_out)
        return self._lengths



class Panel(Item):
    def __call__(self, panel, bends, *args, **kwargs):
        super().__call__(panel=panel, bends=bends, *args, **kwargs)
        self.offset_panel = cg.Polygon(cg.offset_polygon(self.panel, self.bends[0].tri_offset))
        self.normal = self.offset_panel.normal
        self.panel_lines = self.offset_panel.lines

    @property
    def parent_frames(self):
        self._parent_frames = []
        for i in self.panel_lines:
            y = cg.Vector.from_start_end(i.start, i.end).unitized()
            x = cg.Vector.cross(y, self.normal)
            z = cg.Vector(*self.normal).inverted()
            parent = cg.Frame(i.start, xaxis=x, yaxis=z)
            self._parent_frames.append(parent)
        return self._parent_frames

    @parent_frames.setter
    def parent_frames(self, v):
        self._parent_frames = v


class PanelUnroll(Panel):
    def __call__(self, panel, bends, *args, **kwargs):
        super().__call__(panel=panel, bends=bends, *args, **kwargs)

    @property
    def parent_frames(self):
        self._parent_frames = []
        for i in self.panel_lines:
            y = cg.Vector.from_start_end(i.start, i.end).unitized()
            x = cg.Vector.cross(y, self.normal)
            parent = cg.Frame(i.start, xaxis=x, yaxis=y)
            self._parent_frames.append(parent)
        return self._parent_frames

    @parent_frames.setter
    def parent_frames(self, v):
        self._parent_frames = v

    @property
    def unroll(self):
        self._unroll = []
        for num, bend in enumerate(self.bends):
            bend_list = []
            start = self.parent_frames[num].point

            for i in bend.lengths:
                start_ps = start
                tr_x = cg.Translation.from_vector(self.parent_frames[num].xaxis * i)
                end_ps = start_ps.transformed(tr_x)
                tr_y = cg.Translation.from_vector(
                    cg.Vector.from_start_end(self.panel_lines[num].start, self.panel_lines[num].end))
                start_pe = start_ps.transformed(tr_y)
                end_pe = end_ps.transformed(tr_y)
                bend_list.append(cg.Polygon([start_ps, end_ps, end_pe, start_pe]))

                start = end_ps
            self._unroll.append(bend_list)
        return self._unroll

    @unroll.setter
    def unroll(self, r):
        self._unroll = r
