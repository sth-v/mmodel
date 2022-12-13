import json

import rhino3dm


def DecodeToCommonObject(item):
    if item is None:
        return None
    elif isinstance(item, str):
        return DecodeToCommonObject(json.loads(item))
    elif isinstance(item, list):
        return [DecodeToCommonObject(x) for x in item]
    return rhino3dm.CommonObject.Decode(item)
