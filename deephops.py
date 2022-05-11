from flask import Flask
import ghhops_server as hs
import requests
import json
import urllib3
urllib3.disable_warnings()

app = Flask(__name__)
hops = hs.Hops(app)


@hops.component(
    "/GET",
    name="GET",
    description="GET request",
    inputs=[
        hs.HopsBoolean("run", "run", "run"),
        hs.HopsString("url", "url", "url"),
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
        hs.HopsString("url", "url", "url"),
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
        hs.HopsString("url", "url", "url"),
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
    app.run(
        host='0.0.0.0',
        port='5000'
    )
