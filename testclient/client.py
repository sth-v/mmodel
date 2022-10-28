from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from dataclasses import dataclass
from mm.baseitems import Item
from typing import TypeVar
import pickle, json
import compas
from lahta.items import Bend
import uvicorn
IT = TypeVar("IT", bound=Item)
app = FastAPI(debug=True)


class AbstractTestApi(object):
    mainapp = app
    prefix = None

    def __init__(self):
        self.prefix = self.__class__.prefix
        super().__init__()


@dataclass
class Prot:
    jsn = lambda x: json.dumps(x, ensure_ascii=False, indent=3)
    compas_json = lambda x: compas.json_dumps(x, pretty=True)
    pkl = lambda x: pickle.dumps(x)

    def __new__(cls, v):

        if v == "jsn":

            return cls.jsn

        elif v == "compas_json":
            return cls.compas_json

        elif v == "pkl":
            return cls.pkl


class ItemApiGenerator(AbstractTestApi, Item):
    prefix = None

    def __init__(self, **kwargs):

        super().__init__()
        self.__dict__ |= kwargs
        self._is_post_init_call = False

    def __post_init__(self, *args, **kwargs):
        super(IT, self).__init__(*args, **kwargs)
        self._is_post_init_call = True

    def response(self, response_headers, prot: Prot):
        for h in response_headers:
            yield {h: getattr(self, h)}

    def __call__(self, response_headers, *args, prot: Prot = Prot.pkl, **kwargs):

        if not self._is_post_init_call:
            self.__post_init__(*args, **kwargs)

        else:
            super(Item, self).__call__(*args, **kwargs)
        return StreamingResponse(self.response(response_headers, prot=prot))


class BendConstructorBind(Item, Bend):
    prefix = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prefix = self.__class__.prefix

    def __call__(self, *args, start=None, **kwargs):
        super(BendConstructorBind, self).__init__(*args, start=start)


class BendConstructorApi(ItemApiGenerator, BendConstructorBind):
    mainapp = app
    prefix = "/bc"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._prot = None
        self._is_post_init_call = False

    def __call__(self, response_headers, *args, prot=None, **kwargs):
        if not self._is_post_init_call:
            self.__post_init__(*args, **kwargs)

        else:
            BendConstructorBind.__call__(self, *args, **kwargs)
        return StreamingResponse(self.response(response_headers, prot=prot))


bc = BendConstructorBind()


@app.get(bc.prefix + "/{name}")
def bind_bc(name: str, prot: str = "jsn"):
    return bc(name)

