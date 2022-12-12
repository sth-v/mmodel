import json

from fastapi import FastAPI

from baseitems import Matchable
from collection.multi_description import MultiDescriptor
from plugins.compute.encoding import DecodeToCommonObject
from plugins.compute.gh import do_request


class L1L2(Matchable):
    __match_args__ = "table", "summary", "mesh"

    def reload(self, path="example.json", **kwargs):
        v = do_request(path=path, **kwargs)["values"]
        table = json.loads(json.loads(list(v[0]['InnerTree'].values())[0]["data"]))
        summary = json.loads(json.loads(list(v[1]['InnerTree'].values())[0][0]["data"]))
        mesh = DecodeToCommonObject(MultiDescriptor(list(v[2]['InnerTree'].values())[0])["data"])
        return self(table, summary, mesh)


app = FastAPI()
m_model = L1L2()
m_model.reload("")


def get_summary():
    return m_model.summary


def get_mesh():
    return m_model.mesh


def get_table():
    return m_model.table


def set_overrides():
    m_model.table
    return m_model.table


def append_mask():
    return m_model.table


def with_mask():
    return m_model.table
