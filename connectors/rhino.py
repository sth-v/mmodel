import rhino3dm


def get_model_objects(path):
    rr = rhino3dm.File3dm().Read(path)
    return list(rr.Objects)


def get_model_geometry(path):
    rr = rhino3dm.File3dm().Read(path)
    return [o.Geometry for o in rr.Objects]


def get_model_attributes(path):
    rr = rhino3dm.File3dm().Read(path)
    return [o.Geometry for o in rr.Attributes]
