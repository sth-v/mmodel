from fastapi import FastAPI
from pydantic import BaseModel
from numpy import ndarray
from typing import Optional
from models import mmodel




class SimpleApi(BaseModel):
    other_dict: Optional[dict]
app = FastAPI()

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
        elif hasattr(val, '__dict__') and not isinstance(val, ndarray):
            ans = val.__dict__
        else:
            ans = val
    return {name: ans}


@app.get("/mmodel_method/{name}")
async def mm_method(name: str):
    func = getattr(mmodel, name)

    ans = func()
    return {name: ans}


@app.post("/mmodel_method/{name}")
async def mm_method(name: str, data: SimpleApi):
    func = getattr(mmodel, name)
    ans = func(**data.other_dict)
    return {name: ans}


@app.put("/mmodel_commit/{name}")
async def mm_commit(name: str, data: SimpleApi):
    print(data.dict())
    mmodel.change_history(name, data.other_dict)
    return {name: 0}
