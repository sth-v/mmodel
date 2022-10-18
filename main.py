#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import os
import sys

# print('Python %s on %s' % (sys.version, sys.platform))

sys.path.extend(
    ['/tmp/mmodel_server_remote/', '/tmp/mmodel_server_remote/', '/tmp/mmodel_server_remote/bucket_watchdog',
     '/tmp/mmodel_server_remote/mm/tests', '/tmp/mmodel_server_remote/tests',
     '/tmp/mmodel_server_remote/bucket_watchdog', '/tmp/mmodel_server_remote/mm/tests',
     '/tmp/mmodel_server_remote/tests', '/Users/andrewastakhov/mmodel', '/Users/andrewastakhov/mmodel/lahta'])

import json
from typing import Iterable, Optional, Any, Type, Union
import pickle
from cxm_remote.sessions import S3Session
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from lahta.items import *
from lahta.extrusions import *

from pydantic import BaseModel


@dataclass
class UpdSchema:
    patch: dict


app = FastAPI(debug=True)

bend = FastAPI(debug=True)




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
def entry_bend():
    return {"api": "bend"}


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
    panel: list[list[float]]
    dtype: str = "Panel"

    @property
    def cxm(self):
        cls = globals()[self.dtype]
        bends = []
        for k in self.bends:
            bends.append(Bend([s.cxm for s in k.segments]))
        return cls(self.panel, bends)


class MmodelGeometryData(BaseModel):
    compas: Any
    rhino: Any


class MmodelMetaData(BaseModel):
    uid: str
    uuid: str
    version: str
    dtype: str


class BindPydantic:
    def __init__(self, model: Type[BaseModel]):
        self.model = model
        self.name = model.__name__

    @property
    def pydantic_type(self) -> Type[BaseModel]:
        return self.model

    def __call__(self, obj) -> BaseModel:
        data = {
            "data": {
                "compas": list(obj.to_compas()),
                "rhino": list(obj.to_rhino())
            },

            "metadata": obj.metadata
        }
        return self.model(**data)


@BindPydantic
class MmodelObjectSchema(BaseModel):
    data: MmodelGeometryData
    metadata: MmodelMetaData


@bend.get("/objects")
def get_bend_stream():
    def stream():
        for k, v in bend_db.items():
            yield MmodelObjectSchema(v)

    return StreamingResponse(stream())

    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)


@bend.get("/objects/{uid}", response_model=MmodelObjectSchema.pydantic_type)
def construct_bend4(uid: str):
    test = bend_db[uid]
    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    return MmodelObjectSchema(test)


@bend.post("/object/create", response_model=MmodelObjectSchema.pydantic_type)
def construct_bend2(data: BendInput):
    print(list(data.segments), data.segments[0])

    test = Bend([s.cxm for s in data.segments])
    bend_db[test.uid] = test
    print(test)
    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    return MmodelObjectSchema(test)


"""
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

    return StreamingResponse(stream())"""


@bend.patch("/object/patch/{uid}", response_model=MmodelObjectSchema.pydantic_type)
def update_bend(uid: str, data: BendPatch):
    print(data)

    test = segments = bend_db[uid]
    # pkl = pickle.dumps(obj=obj)

    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/pkl/{uid}", Body=pkl)

    return MmodelObjectSchema(test)


@bend.post("/panel/create", response_model=MmodelObjectSchema.pydantic_type)
def construct_panel(data: PanelApi):
    print(list(data.panel), data.bends[0])

    test = data.cxm
    bend_db[test.uid] = test
    print(test)
    # bend_sess.s3.put_object(Bucket=bend_sess.bucket, Key=f"cxm/playground/bend/pkl/{test.uid}", Body=pkl)

    return MmodelObjectSchema(test)


app.mount("/bend", bend)
"""
if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8888)
"""
