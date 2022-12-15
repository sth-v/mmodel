#  Copyright (c)  CONTEXTMACHINE 2022.
#  AEC, computational geometry, digital engineering and Optimizing construction processes.
#
#  Author: Andrew Astakhov <sthv@contextmachine.space>
#
#  Computational Geometry, Digital Engineering and Optimizing your construction processes
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 2 of the License, or (at your
#  option) any later version.  See http://www.gnu.org/copyleft/gpl.html for
#  the full text of the license.
#
#
#
import json
import os

with open("/home/sthv/cxm_remote/env.json") as env_file:
    os.environ |= json.load(env_file)
import typing

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from cxm_remote.sessions import WatchSession
from apps import AppSession
from fastapi.middleware.gzip import GZipMiddleware


class S3Session(WatchSession):
    def __init__(self, bucket=os.environ["BUCKET"]):
        super().__init__(bucket)
        self.s3 = self.session.client(
            service_name='s3',
            endpoint_url=self.storage
        )


sess = AppSession(buck="bucket.contextmachine.online")

app = FastAPI(debug=True)


@app.get("/config")
async def get_config():
    return sess.config


@app.get("/get_keys")
async def get_keys():
    return sess.g3(pref="pridex/")


@app.get("/get_all")
async def get_all():
    return sess.g2(pref="pridex/")


@app.get("/get_parts/{name}")
async def get_parts(name: str):
    def stream():
        with sess.g4(name, pref="pridex/") as body_stream:
            yield from body_stream

    return StreamingResponse(stream())


@app.patch("/patch/{name}")
async def patch(name: str, data: typing.Any):
    sess.patch(name, data, pref="pridex/")
    return {name: f"/get_parts/{name}"}


if __name__ == "__main__":
    uvicorn.run(
        '__main__:app', port=443, host='0.0.0.0',
        ssl_keyfile="/home/sthv/private_key.pem",
        ssl_certfile="/home/sthv/certificate_full_chain.pem"
    )
