from subprocess import Popen

from fastapi import FastAPI
from pydantic import BaseModel
from numpy import ndarray
from typing import Optional
from models import mmodel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
app = FastAPI()

import uvicorn

class SimpleApi(BaseModel):
    kwargs: Optional[dict]

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
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["contextmachine.online", "*.contextmachine.online"]
)

app.add_middleware(HTTPSRedirectMiddleware)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/mmodel_attrs/{name}")
async def get_model(name: str):
    if name == 'help':
        ans = str(dir(mmodel))
    else:
        val = getattr(mmodel, name)
        if isinstance(val, ndarray):
            ans = val.tolist()

        else:
            ans = val
    return {name: ans}


@app.get("/mmodel_method/{name}")
async def mm_method(name: str):
    func = getattr(mmodel, name)

    ans = func()

    return {name: ans}


@app.post("/mmodel_method/{name}")
async def mm_method(name: str, data: Optional[SimpleApi]):
    func = getattr(mmodel, name)
    if data:

        ans = func(**data.kwargs)
    else:
        ans = func()

    return {name: ans}


@app.put("/mmodel_commit/{name}")
async def mm_commit(name: str, data: SimpleApi):
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
@app.get("/mmodel_build_download/{name}")
async def mm_build_download(name):
    pass

if __name__ == '__main__':
    Popen(['python', '-m', 'https_redirect'])  # Add this
    uvicorn.run(
        'main:app', port=8443, host='0.0.0.0',
        reload=False,
        ssl_keyfile='/home/sthv/mmodel_server/privat.key',
        ssl_certfile='ptc_torch/certificate.crt')
