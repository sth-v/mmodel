#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import os, sys
import sys

from compas.geometry import Line, Point

from lahta.extrusions import NaivePanel

# print('Python %s on %s' % (sys.version, sys.platform))

sys.path.extend(
    ['/tmp/mmodel_server_remote/', '/tmp/mmodel_server_remote/', '/tmp/mmodel_server_remote/bucket_watchdog',
     '/tmp/mmodel_server_remote/mm/tests', '/tmp/mmodel_server_remote/tests',
     '/tmp/mmodel_server_remote/bucket_watchdog', '/tmp/mmodel_server_remote/mm/tests',
     '/tmp/mmodel_server_remote/tests', '/Users/andrewastakhov/mmodel', '/Users/andrewastakhov/mmodel/lahta'])

import json
from typing import Iterable, Optional, Any, Union
import pickle
import mm.parametric as prm
from dataclasses import dataclass
import importlib
from cxm_remote.sessions import S3Session
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, FileResponse
import uvicorn
from lahta.items import OCCNurbsCurve, BendSegment, Bend, BendSegmentFres, Panel
from pydantic import BaseModel

with open("/tmp/mmodel_server_remote/mm/parametric/localconfig.json", "rb") as fp:
    local_configs = json.load(fp)
    S3Session.storage = local_configs["storage"]
    sess = S3Session(bucket=local_configs["bucket"])
    pref = local_configs["prefix"]
    parent = local_configs["parent"]
    remote_configs = local_configs["remote"]
    obj_list = sess.s3.list_objects(Bucket=sess.bucket, Prefix="dev/")
    # print(f"S3 Session {sess.bucket} success!\n\n"
          f"----------------------------------------------------------------------------------------------------------\n"
          f"List objects from prefix - ({parent}/{pref}/)\n{obj_list} ")
    CONFIGS = json.loads(sess.s3.get_object(Bucket=sess.bucket, Key='dev/mm/parametric/cxmmodule.json')["Body"].read())
    # print(f"Get remote configs {sess.bucket,} success!\n\n"
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
    segments: list[Any]


bend_sess = S3Session(bucket="lahta.contextmachine.online")


@bend.get("/")
def construct_bend():
    return {"api": "bend"}


@bend.get("/objects")
def construct_bend(uid: str):
    bend_sess.s3.list_objects(Bucket=bend_sess.bucket, Prefix="cxm/playground/bend/pkl/")
    obj = pickle.loads(
        bend_sess.s3.get_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{uid}")["Body"].read())
    return {
        "data": obj.to_compas(),
        "metadata": {
            "uid": obj.uid,
            "version": obj.version,
            "dtype": "Bend"

        }
    }


@bend.get("/objects/{uid}")
def construct_bend(uid: str):
    obj = pickle.loads(
        bend_sess.s3.get_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{uid}")["Body"].read())
    return {
        "data": obj.to_compas(),
        "metadata": {
            "uid": obj.uid,
            "version": obj.version,
            "dtype": "Bend"

        }
    }


bend_db = dict()


class SimpleSegment(BaseModel):
    length: float
    radius: float
    angle: float
    dtype: str = "BendSegment"


class MillingSegment(SimpleSegment):
    length: float
    radius: float
    angle: float
    in_rad: float = 0.5
    dtype: str = "BendSegmentFres"


class BendingSegment(SimpleSegment):
    length: float
    radius: float
    angle: float
    dtype: str
    in_rad: Optional[float] = None

    @property
    def cxm(self):
        cls = globals()[self.dtype]
        return cls(**self.dict())


class BendInput(BaseModel):
    segments: list[BendingSegment]


class Insert(BaseModel):
    index: int
    item: Any


class BendInsert(Insert):
    index: int
    item: list[Union[SimpleSegment, MillingSegment, BendingSegment]]


class BendDelete(Insert):
    index: int


class BendPatch(BaseModel):
    uid: Optional[str] = None
    extend: Optional[BendInput] = None
    insert: Optional[BendInsert] = None
    delete: Optional[list[int]] = None

    kwargs: Optional[dict[str, Any]]


class BendMulti(BaseModel):
    bends: list[BendInput]
class PanelApi(BaseModel):
    bends: list[BendInput]
    panel:list[list[float]]
    dtype: str="Panel"


    @property
    def cxm(self):
        cls = globals()[self.dtype]
        bends=[]
        for k in self.bends:
            bends.append(Bend([s.cxm for s in k.segments]))
        return cls(self.panel, bends)


@bend.get("/objects")
def construct_bend():
    def stream():
        for k, v in bend_db.items():
            yield {
                "data": v.to_compas(),

                "metadata": {
                    "uid": v.uid,
                    "version": v.version,
                    "dtype": "Bend"
                }
            }

    return StreamingResponse(stream())

    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)


@bend.get("/objects/{uid}")
def construct_bend4(uid: str):
    test = bend_db[uid]
    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    return {
        "data": test.to_compas(),

        "metadata": {
            "uid": test.uid,
            "version": test.version,
            "dtype": "Bend"
        }
    }


@bend.post("/objects/create")
def construct_bend2(data: BendInput):
    print(list(data.segments), data.segments[0])

    test = Bend([s.cxm for s in data.segments])
    bend_db[test.uid] = test
    print(test)
    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    return {
        "data": test.to_compas(),

        "metadata": {
            "uid": test.uid,
            "version": test.version,
            "dtype": "Bend"
        }
    }


@bend.post("/objects/create_multi")
def construct_bends(data: BendMulti):
    print(list(data.bends), data.bends[0])
    test = NaivePanel()
    for bm in data.bends:
        bnd = Bend([BendSegment(s.length, s.radius, s.angle, in_rad=s.in_rad) for s in bm.segments])
        bend_db[bnd.uid] = bnd
        test.bends = bnd
    print(test.bends)

    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    def stream():
        yield from test.to_compas()

    return StreamingResponse(stream())


@bend.patch("/objects/patch/{uid}")
def update_bend(uid: str, data: BendPatch):
    print(data)

    obj = segments = bend_db[uid]
    # pkl = pickle.dumps(obj=obj)

    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/pkl/{uid}", Body=pkl)

    return {
        "data": obj.to_compas(),
        "metadata": {
            "uid": obj.uid,
            "version": obj.version,
            "dtype": "Bend"

        }
    }


@bend.post("/panel/create")
def construct_panel(data: PanelApi):
    print(list(data.panel), data.bends[0])

    test = data.cxm
    bend_db[test.uid] = test
    print(test)
    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    return {
        "data": test.to_compas(),

        "metadata": {
            "uid": test.uid,
            "version": test.version,
            "dtype": "Panel"
        }
    }


app.mount("/bend", bend)
if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8888)
