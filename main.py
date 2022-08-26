#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import os, sys
import sys

from compas.geometry import Line, Point

print('Python %s on %s' % (sys.version, sys.platform))

sys.path.extend(
    ['/tmp/mmodel_server_remote/', '/tmp/mmodel_server_remote/', '/tmp/mmodel_server_remote/bucket_watchdog',
     '/tmp/mmodel_server_remote/mm/tests', '/tmp/mmodel_server_remote/tests',
     '/tmp/mmodel_server_remote/bucket_watchdog', '/tmp/mmodel_server_remote/mm/tests',
     '/tmp/mmodel_server_remote/tests', '/Users/andrewastakhov/mmodel_server'])

import json
from typing import Iterable, Optional, Any
import pickle
import mm.parametric as prm
from dataclasses import dataclass
import importlib
from cxm_s3.sessions import S3Session
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, FileResponse
import uvicorn
from lahta.items import OCCNurbsCurve, BendConstructorFres
from pydantic import BaseModel
with open("/tmp/mmodel_server_remote/mm/parametric/localconfig.json", "rb") as fp:
    local_configs = json.load(fp)
    S3Session.storage = local_configs["storage"]
    sess = S3Session(bucket=local_configs["bucket"])
    pref = local_configs["prefix"]
    parent = local_configs["parent"]
    remote_configs = local_configs["remote"]
    obj_list = sess.s3.list_objects(Bucket=sess.bucket, Prefix="dev/")
    print(f"S3 Session {sess.bucket} success!\n\n"
          f"----------------------------------------------------------------------------------------------------------\n"
          f"List objects from prefix - ({parent}/{pref}/)\n{obj_list} ")
    CONFIGS = json.loads(sess.s3.get_object(Bucket=sess.bucket, Key='dev/mm/parametric/cxmmodule.json')["Body"].read())
    print(f"Get remote configs {sess.bucket,} success!\n\n"
          f"----------------------------------------------------------------------------------------------------------\n"
          f"Configs = ({CONFIGS}")


@dataclass
class CreateSchema:
    a: Optional[float] = 0.0
    b: Optional[float] = 1.0
    r: Optional[float] = 1.0
    x0: float = 0.0
    y0: float = 0.0


@dataclass
class UpdSchema:
    patch: dict


app = FastAPI(debug=True)

bend = FastAPI(debug=True)


@app.get("/")
def home():
    return {"api": "playground"}


@app.get("/all")
def get_all():
    return json.loads(sess.s3.get_object(Bucket=sess.bucket, Key='dev/mm/parametric/cxmmodule.json')["Body"].read())[
        "all"]


@app.put("/create/{name}")
def create_object(name: str, data: CreateSchema = CreateSchema()):
    cls_ = eval("prm.{}".format(name))
    globals()[name] = [cls_]

    obj = cls_(**data.__dict__)
    pkl = pickle.dumps(obj=obj)
    sess.s3.put_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/pkl/{name}/{hex(id(obj))}", Body=pkl)
    sess.s3.put_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/dump/{hex(id(obj))}", Body=pkl)

    return hex(id(obj))


"""
@app.get("/objects/{name}/{item_id}")
def get_object_item(name: str, item_id: str):
    return StreamingResponse(
        sess.s3.get_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/pkl/{name}/{item_id}")["Body"])
"""


@app.get("/objects/{item_id}")
def get_objects_by_id(item_id: str):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    return {
        "type": obj.__class__.__name__,
        "id": item_id,
        "repr": obj.__repr__(),
        "attrs": obj.__dict__
    }


@app.get("/eval/{item_id}")
def eval_object_by_id(item_id: str, start: float = -1.0, stop: float = 1.0, step: float = 0.1):
    obj_type = get_objects_by_id(item_id)["type"]
    obj = pickle.loads(
        sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/pkl/{obj_type}/{item_id}')["Body"].read())
    return list(obj[start:stop:step])


@app.get("/eval_single/{item_id}")
def eval_object_single_parametr(item_id: str, t: float = 0.3):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    return obj.evaluate(t)


@app.post("/objects_patch/{item_id}")
def eval_object_single_parametr(item_id: str, data: UpdSchema):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    obj(**data.patch)
    pkl = pickle.dumps(obj=obj)
    sess.s3.put_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/pkl/{obj.__class__.__name__}/{item_id}", Body=pkl)
    sess.s3.put_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/dump/{item_id}", Body=pkl)
    print(obj)

    return {
        "type": obj.__class__.__name__,
        "id": item_id,
        "repr": obj.__repr__(),
        "attrs": obj.__dict__
    }


@dataclass
class Segment(tuple):
    angle: float
    radius: float
    length: float

    def __new__(cls, angle, radius, length) -> tuple[float, float, float]:
        return super().__new__(cls, (angle, radius, length))

    def __getitem__(self, item):
        l = [self.angle, self.radius, self.length]
        return l[item]


@dataclass
class Bending(Iterable):
    segments: Iterable[Segment]

    def __init__(self, segments: Iterable[Segment] = ()):
        super().__init__()
        self.segments = segments

    def __iter__(self):
        return iter(self.segments)



class FuckingShema(BaseModel):
    segments:list[Any]
@bend.post("/construct")
def construct_bend(data: FuckingShema):
    line = OCCNurbsCurve.from_line(Line(Point(-30, 0, 0), Point(0, 0, 0)))
    print(data, data.segments)
    test = BendConstructorFres(data.segments, start=line)
    js = {'poly': []}

    bend_ = test.bend_()

    for i, v in enumerate(bend_):
        js['poly'].append(v.data)

    return js


app.mount("/bend", bend)
if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8888)
