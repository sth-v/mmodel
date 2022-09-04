import uuid

import uvicorn
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import RedirectResponse

app = FastAPI()

with open("/gg") as fp:
    a=fp.readable()
@app.route('/{_:path}')
async def https_redirect(request: Request):
    return RedirectResponse(request.url.replace(scheme='https'))
str.find()
if __name__ == '__main__':
    uvicorn.run('https_redirect:app', port=8080, host='0.0.0.0')