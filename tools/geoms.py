from compas_occ.geometry import OCCNurbsCurve
from compas.geometry import Point, Polygon, offset_polyline, Polyline, offset_polygon, normal_polygon, Plane, \
    translate_points, Circle, Frame, Transformation, NurbsCurve, Vector
import math


class OCCNurbsCurvePanels(OCCNurbsCurve):
    def __init__(self, name=None):
        super().__init__(name=name)

    @classmethod
    def from_circle_world(cls, circle):
        """Construct a NURBS curve from a circle.
        Parameters
        ----------
        circle : :class:`~compas.geometry.Circle`
            The circle geometry.
        Returns
        -------
        :class:`OCCNurbsCurve`
        """
        frame = Frame.worldXY()
        w = 0.5 * math.sqrt(2)
        dx = frame.xaxis * circle.radius
        dy = frame.yaxis * circle.radius

        points = [
            frame.point + dx,
            frame.point + dy + dx,
            frame.point + dy,
            frame.point + dy - dx,
            frame.point - dx,
            frame.point - dy - dx,
            frame.point - dy,
            frame.point - dy + dx,
            frame.point + dx
        ]

        knots = [0, 1 / 4, 1 / 2, 3 / 4, 1]
        mults = [3, 2, 2, 2, 3]
        weights = [1, w, 1, w, 1, w, 1, w, 1]
        return cls.from_parameters(
            points=points, weights=weights, knots=knots, multiplicities=mults, degree=2
        )
