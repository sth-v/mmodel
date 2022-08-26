#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import json
from typing import Optional
import pickle
import mm.parametric
from dataclasses import dataclass
import importlib
from cxm_s3.sessions import S3Session
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, FileResponse
import uvicorn

with open("localconfig.json", "rb") as fp:
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


@app.get("/")
def home():
    return {"api": "playground"}


@app.get("/all")
def get_all():
    return json.loads(sess.s3.get_object(Bucket=sess.bucket, Key='dev/mm/parametric/cxmmodule.json')["Body"].read())[
        "all"]


@app.put("/create/{name}")
def create_object(name: str, data: CreateSchema = CreateSchema()):
    cls_ = __import__(f"mm.parametric.{name}")
    globals()[name]=[cls_]
    obj = cls_(**data.__dict__)
    pkl = pickle.dumps(obj=obj)
    sess.s3.put_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/pkl/{name}/{hex(id(obj))}", Body=pkl)
    sess.s3.put_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/dump/{hex(id(obj))}", Body=pkl)

    return f"/objects/{name}/{hex(id(obj))}"


@app.get("/objects/{name}/{item_id}")
def get_object_item(name: str, item_id: str):
    return StreamingResponse(
        sess.s3.get_object(Bucket=sess.bucket, Key=f"dev/{parent}/{pref}/pkl/{name}/{item_id}")["Body"])


@app.get("/objects/{item_id}")
def get_objects_by_id(item_id: str):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    return {
        "type": obj.__class__.__name__,
        "id": item_id,
        "repr": obj.__repr__(),
        "attrs": obj.__dict__
    }


@app.get("/objects/{item_id}/eval")
def eval_object_by_id(item_id: str, start: float = -1.0, stop: float = 1.0, step: float = 0.1):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    return list(obj[start:stop:step])


@app.get("/objects/{item_id}/single_eval")
def eval_object_single_parametr(item_id: str, t: float = 0.3):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    return obj.evaluate(t)


@app.patch("/objects/{item_id}/patch")
def eval_object_single_parametr(item_id: str, data: UpdSchema):
    obj = pickle.loads(sess.s3.get_object(Bucket=sess.bucket, Key=f'dev/{parent}/{pref}/dump/{item_id}')["Body"].read())
    obj(data.patch)
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


if __name__ == "__main__":
    uvicorn.run("main:playground", host=CONFIGS["host"], port=CONFIGS["host"])
