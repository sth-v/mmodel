import copy
import json
import uuid
import numpy as np

import pandas as pd

import pydantic
from typing import List
class PolyCoords(pydantic.BaseModel):
    kwargs: List[List[float, float, float]]
a=PolyCoords.kwargs[0][2]
def rgb_int2tuple(rgbint):
    return (1 / 256) * np.array((rgbint // 256 // 256 % 256, rgbint // 256 % 256, rgbint % 256, 256))

marks_map={}
def from_treejs_object_to_mmarray(source_path, target_path):
    with open(source_path, 'r') as fp:
        data = json.load(fp)

    l = []

    for i in range(len(data["geometries"])):
        dct = dict()
        metadata = data["metadata"]
        mt = rgb_int2tuple(data['materials'][i]['color']).tolist()
        metadata |= {'material': [mt], 'type': "BufferGeometry"}
        metadata["generator"] = "MmodelCxm"
        d = data["geometries"][i]
        print(metadata)
        del d['data']['boundingSphere']

        d["data"]['attributes']['position']['array'] = np.asarray(d["data"]['attributes']['position']['array']).round(
            5).tolist()

        narr = np.asarray(d['data']['attributes']['normal']['array'])

        d['data']['attributes']['normal']['array'] = np.asarray(narr.round(5)).tolist()
        del d['data']['attributes']['normal']['normalized']
        del d['data']['attributes']['position']['normalized']

        d["uuid"] = uuid.uuid4().hex
        dct |= d
        dct["metadata"] = metadata
        l.append(copy.deepcopy(dct))

    with open(f"{target_path}.json", "w") as fp:
        json.dump(l, fp)


def append_metadata_fields(source_path, target_path):
    with open(source_path + ".json", "r") as fp:
        data = json.load(fp)

    mtr = map(lambda x: x["metadata"]["material"][0], data)
    nu = np.array(list(mtr))
    nm = np.asarray(list(marks_map.items()))

    tags = pd.DataFrame(nm, columns=['name', 'mark'])
    cs = pd.Series(np.unique(np.sum(nu, axis=1)), name='cs')
    result = pd.concat([tags, cs], axis=1)

    for v in data:
        i = list(result.cs).index(float(np.sum(v["metadata"]["material"][0])))
        dct = dict(result.loc[i])
        dct |= {'area': 1.0}
        v["metadata"].update(copy.deepcopy(dct))
    with open(target_path + ".json", "w") as fp:
        json.dump(data, fp)
