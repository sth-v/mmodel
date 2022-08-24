#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
from fastapi import FastAPI
from dataclasses import dataclass
import numpy as np
import plotly.graph_objects as go
app = FastAPI()

@dataclass
class ContentShema:
    area:list[float]
    points: list[list[float]]
    def __init__(self, area, points):
        self.area = np.asrray(area)
        self.points = np.asrray(points)
        self.maxarea=3*1.5*68*12
        self.traces = []
    def ratio(self):
        return 1-(np.sum(self.area)/self.maxarea)
    def percent(self):
        return 100*self.ratio()
    def generate_scatters(self):

        for face in self.points:
            self.traces.append(go.Scatter(x=np.array(face)[:,0], y=np.array(face)[:,1], mode="lines+text",
                                                  line=dict(color='rgb(17,17,17)', width=2), text=np.asarray(self.area)/(3*1.5),
                       textfont=dict(
                                size=12,
                                color="#ffffff")

                            ))

@app.put("content/")
def put_content(data: ContentShema):
    data.generate_scatters()
    data.percent()
    np.sum(data.area)
    fig = go.Figure()
    fig.update_layout(width=3456 ,
                     height=2234, legend=dict(
            orientation="v", font=dict(size=16)), template="plotly_dark")

    fig.update_xaxes(showgrid=True, zeroline=False, griddash="dot", ticks="outside", tickwidth=2,
                     tickcolor='#868686',
                     ticklen=20)
    fig.update_yaxes(scaleanchor="x",
                     scaleratio=1, showgrid=True, zeroline=False, griddash="dot", ticks="outside", tickwidth=2,
                     tickcolor='#868686', ticklen=20)