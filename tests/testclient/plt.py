#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import json
from typing import Any

import numpy as np
import plotly.graph_objects as go
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response

app = FastAPI()
import redis_om
import pydantic
import pydantic_numpy

conn = redis_om.get_redis_connection()
PRIMARY_KEY = "tests:mmodel:tests:plt"


class ContentShema(pydantic.BaseModel):
    area: pydantic_numpy.NDArray
    points: pydantic_numpy.NDArray
    # privats
    maxarea: pydantic.PrivateAttr[float] = float(3 * 1.5 * 68 * 12)
    traces: pydantic.PrivateAttr[list[Any]] = []

    def __init__(self, **data: Any):
        super().__init__(**data)
        if data.get("area") > self.__class__.maxarea:
            raise ValueError("Area mastest at maxarea")

    def ratio(self):
        return 1 - (np.sum(self.area) / self.maxarea)

    def percent(self):
        return 100 * self.ratio()

    def generate_scatters(self):

        for face in self.points:
            self.traces.append(go.Scatter(x=np.array(face)[:, 0], y=np.array(face)[:, 1], mode="lines+text",
                                          line=dict(color='rgb(17,17,17)', width=2),
                                          text=np.asarray(self.area) / (3 * 1.5),
                                          textfont=dict(
                                              size=12,
                                              color="#ffffff")

                                          ))


def test_put_content(data: ContentShema = ContentShema(points=np.random.random((8, 3)), area=444)):
    fig = go.Figure()

    data.generate_scatters()
    data.percent()
    fig.add_traces(data=data.traces)

    fig.update_layout(width=3456,
                      height=2234, legend=dict(
            orientation="v", font=dict(size=16)), template="plotly_dark")

    fig.update_xaxes(showgrid=True, zeroline=False, griddash="dot", ticks="outside", tickwidth=2,
                     tickcolor='#868686',
                     ticklen=20)
    fig.update_yaxes(scaleanchor="x",
                     scaleratio=1, showgrid=True, zeroline=False, griddash="dot", ticks="outside", tickwidth=2,
                     tickcolor='#868686', ticklen=20)
    conn.set(PRIMARY_KEY + ":" + "fig", fig.to_plotly_json())


@app.put("content/")
def put_content(data: ContentShema):
    try:
        test_put_content(data=data)
        return Response(status_code=200)
    except Exception as err:
        return Response(repr(err))


@app.get("content/", response_model=HTMLResponse)
def get_content():
    fig = go.Figure(json.loads(conn.get(PRIMARY_KEY + ":" + "fig")))
    return HTMLResponse(fig.to_html())
