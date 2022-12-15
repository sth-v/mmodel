from flask import Flask
import ghhops_server as hs
import requests
import json
import urllib3
from tools.unused.models import mmodel

urllib3.disable_warnings()

apphs = Flask(__name__)
hops = hs.Hops(apphs)

mmodel_url = f"{mmodel.host}:{mmodel.port}/"


@hops.component(
    "/GET",
    name="GET",
    description="GET request",
    inputs=[
        hs.HopsBoolean("run", "run", "run"),
        hs.HopsString("url", "url", "url", default=mmodel_url),
        hs.HopsString("name", "name", "name"),
    ],
    outputs=[
        hs.HopsString("out", "out", "outputs"),
    ],
)
def req_get(run, url, name):
    if run:
        r = requests.get(url + name, verify=False)
        return json.dumps(r.json())


@hops.component(
    "/POST",
    name="POST",
    description="POST request",
    inputs=[
        hs.HopsBoolean("run", "run", "run"),
        hs.HopsString("url", "url", "url", default=mmodel_url),
        hs.HopsString("name", "name", "name"),
        hs.HopsString("data", "data", "data")
    ],
    outputs=[
        hs.HopsString("out", "out", "outputs"),
    ],
)
def req_post(run, url, name, data):
    if run:
        r = requests.post(url + name, data, verify=False)
        return json.dumps(r.json())


@hops.component(
    "/PUT",
    name="PUT",
    description="PUT request",
    inputs=[
        hs.HopsBoolean("run", "run", "run"),
        hs.HopsString("url", "url", "url", default=mmodel_url),
        hs.HopsString("name", "name", "name"),
        hs.HopsString("data", "data", "data")
    ],
    outputs=[
        hs.HopsString("out", "out", "outputs"),
    ],
)
def req_put(run, url, name, data):
    if run:
        r = requests.put(url + name, data, verify=False)
        return json.dumps(r.json())


if __name__ == "__main__":
    apphs.run(
        host='localhost',
        port=mmodel.hops_port
    )
