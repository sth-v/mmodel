from subprocess import Popen
import inspect
from fastapi import FastAPI
from pydantic import BaseModel
from numpy import ndarray
from typing import Optional
from models import mmodel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()
mmodelapi = FastAPI()


class SimpleApi(BaseModel):
    kwargs: Optional[dict]


"""
origins = [
    "http://localhost:3000",
    "https://cxmapp.vercel.app",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""


# app.add_middleware(HTTPSRedirectMiddleware)


@app.get("/")
async def root():
    return {"available": {
        "mmodel api": "/mmodelapi/"
    }
    }


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@mmodelapi.get("/")
async def root():
    return {"message": "mmodel api"}


@mmodelapi.get("/attrs/help")
async def get_attrs():
    inspect.getmembers(mmodel, inspect.ismethod)

    ans = dir(mmodel)

    return {'help': ans}


@mmodelapi.get("/attrs/{name}")
async def get_attrs(name: str):
    if name == 'help':
        ans = str(dir(mmodel))
    else:
        val = getattr(mmodel, name)
        if isinstance(val, ndarray):
            ans = val.tolist()

        else:
            ans = val
    return {name: ans}


@mmodelapi.get("/methods/{name}")
async def get_method(name: str):
    func = getattr(mmodel, name)

    ans = func()

    return {name: ans}


@mmodelapi.post("/methods/{name}")
async def post_method(name: str, data: Optional[SimpleApi]):
    func = getattr(mmodel, name)
    if data:

        ans = func(**data.kwargs)
    else:
        ans = func()

    return {name: ans}


@mmodelapi.put("/commit/{name}")
async def commit(name: str, data: SimpleApi):
    print(data.kwargs)
    if hasattr(mmodel, name):
        attr = getattr(mmodel, name)
        if not isinstance(attr, dict):
            attr.__dict__ |= data.kwargs
        else:
            attr |= data.kwargs

    else:
        attr = data.kwargs
    setattr(mmodel, name, attr)
    v = mmodel.change_history(name, data.kwargs)
    return {name: v}


app.mount("/mmodelapi", mmodelapi)

if __name__ == '__main__':
    Popen(['python', '-m', 'hops'])  # Add this
    uvicorn.run(
        'main:app', port=mmodel.port, host=mmodel.host,
        reload=True)
((70, 0.8, 30), (10, 0.8, 29.3), (90, 1.3, 20)), start=line