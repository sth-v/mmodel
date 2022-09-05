#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from numpy import ndarray

from mm.parametric import Arc, Cone3d
import compas.geometry as cg
import bezier

from mm.xforms import mirror
import numpy as np

from mm.baseitems import Item, DictableItem
class ArcForArc(Arc):
    evalute_param = np.pi / 2
    origin = [0, 0, 0]
    normal = [0, 0, 1]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.evalute_point = self.evaluate(self.evalute_param)

    def to_compas_vector(self):
        self.cc = cg.NurbsCurve.from_circle(cg.Circle(cg.Plane([self.x0, self.y0, 0.0], [0, 0, 1]), self.r))
        point, ts = self.cc.closest_point(self.evalute_point.to_compas(), return_parameter=True)
        vec = self.cc.tangent_at(ts)

        vec_pl = cg.Vector.from_start_end(self.origin, self.normal)
        toframe = cg.Frame.from_plane(cg.Plane(self.origin, vec_pl.unitized()))
        tr = cg.Transformation.from_frame(toframe)
        self.point = point.transformed(tr)
        self.ts = vec.transformed(tr).unitized()
        # cg.Circle(cg.Plane([self.x0, self.y0, 0.0], [0, 0, 1]), self.r)
        return self.ts


import json


def tri(right_line):
    left_line = mirror(right_line)

    return np.asarray([right_line[0], cg.intersection_line_line(right_line, left_line)[0], left_line[0]])


"""## Inputs"""

# точка плоскости конуса
a = np.array(
    [5.542538, 35.977149, -12.14216]
)

# точка **задающая ось конуса вершина конуса
b = np.array(
    [25.076713, 39.180588, -25.656795]
)

# t начала окружности
start = np.pi / 2

# t сопряжения на конуса и поверхности
stop = 4.4  # @param {type:"slider", min:0, max:7, step:0.1}

# шаг интерполяции для отображения
step = (stop - start) / 64

# радиус конуса в точке a
ra = 2.6  # @param {type:"slider", min:0, max:10, step:0.1}

# радиус конуса в точке b
rb = 1.3  # @param {type:"slider", min:0, max:10, step:0.1}

"""Script"""

class Cone(Cone3d):
    z0 = 1.0
    target = np.ndarray([0.0, 0.0, 0.0])
    def __call__(self, *args, **kwargs):


def pipeline():
    # @title
    ca = Cone3d(r=ra)

    ca.x0, ca.y0, ca.z0 = a
    ca.target_pt = b
    ca.target_pt = b

    ptr = np.asarray(ca.evaluate(stop))
    line_vec = ca.tan_vec(stop, ray_k=1e+4)

    ptv2 = tri(line_vec)

    cpts_a = np.array(list(ca[start:stop:step]))
    cpts_a_m = mirror(cpts_a)
    # @title
    curve_a = bezier.Curve(ptv2.T, 2)
    # @title
    evl_a = curve_a.evaluate_multi(np.linspace(0, 1, 64))

    import plotly.graph_objects as go

    # @title First test
    aaa = go.Scatter3d(x=evl_a[0, ...], y=evl_a[1, ...], z=evl_a[2, ...],
                       mode="lines",
                       line=dict(
                           width=3,
                           color="rgb(17,111,200)"
                       )
                       )
    paaa = go.Scatter3d(x=ptv2.T[0, ...], y=ptv2.T[1, ...], z=ptv2.T[2, ...],
                        mode="markers+lines",
                        line=dict(
                            width=1,
                            color="rgb(255,0,0)"
                        ),
                        marker=dict(
                            size=2,
                            color="rgb(254,0,0)"
                        )
                        )
    crcl1 = go.Scatter3d(x=cpts_a.T[0, ...], y=cpts_a.T[1, ...], z=cpts_a.T[2, ...],
                         mode="lines",
                         line=dict(
                             width=3,
                             color="rgb(17,111,200)"
                         )
                         )
    crcl2 = go.Scatter3d(x=cpts_a_m.T[0, ...], y=cpts_a_m.T[1, ...], z=cpts_a_m.T[2, ...],
                         mode="lines",
                         line=dict(
                             width=3,
                             color="rgb(17,111,200)"
                         )
                         )
    figaa = go.Figure([aaa, paaa, crcl1, crcl2])
    figaa.update_xaxes(visible=False)
    figaa.update_yaxes(visible=False)

    figaa.update_layout(
        showlegend=False,
        plot_bgcolor="white",
        scene=dict(aspectmode="data", xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)))

    return figaa
