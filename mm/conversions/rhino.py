import numpy as np
import rhino3dm
from mm.baseitems import Item, BaseItem


class RhinoBind(Item):
    source_cls = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.source = self.source_cls(*args, **kwargs)


class RhDesc:
    def __set_name__(self, own, name):
        self.name = name

    def __get__(self, inst, ow=None):
        return getattr(inst.source, self.name)

    def __set__(self, inst, v):
        setattr(inst.source, self.name, v)


class RhinoPoint(RhinoBind):
    source_cls = rhino3dm.Point3d
    X = RhDesc()
    Y = RhDesc()
    Z = RhDesc()
    DistanceTo = RhDesc()

    @property
    def xyz(self):
        return self.X, self.Y, self.Z

    def __str__(self):
        return f"RhinoPoint({self.__array__()})"

    def __repr__(self):
        return f"RhinoPoint({self.__array__()})"

    def __list__(self):
        return list(self.xyz)

    def __array__(self):
        return np.array(self.xyz)


class RhinoAxis(RhinoBind):
    """
    >>> ax = RhinoAxis(RhinoPoint(1, 2, 3), RhinoPoint(12, 2, 3))
    >>> ax.end
    RhinoPoint([12.  2.  3.])
    >>> ax.end.DistanceTo(ax.start.source)
    11.0

    """
    source_cls = rhino3dm.Line
    From = RhDesc()
    To = RhDesc()

    def __init__(self, start, end, **kwargs):
        super().__init__(start.source, end.source, **kwargs)

    @property
    def start(self):
        return RhinoPoint(self.From.X, self.From.Y, self.From.Z)

    @property
    def end(self):
        return RhinoPoint(self.To.X, self.To.Y, self.To.Z)


class RhinoCircle(RhinoBind):
    source_cls = rhino3dm.Circle
    radius = 1.0
    Center = RhDesc()
    Plane = RhDesc()


class RhinoRuledSurf(RhinoBind):
    source_cls = rhino3dm.NurbsSurface
    curve_a = None
    curve_b = None

    def __init__(self, curve_a, curve_b, **kwargs):
        super().__init__(curve_a.source, curve_b.source, **kwargs)


class BiCone(RhinoAxis):
    radius_start = 1.0
    radius_end = 0.5
