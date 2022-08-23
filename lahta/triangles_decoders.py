#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"
import os
import sys

sys.path.extend(["/Users/andrewastakhov/mmodel_server", "/Users/andrewastakhov/mmodel_server/mm",
                 "/Users/andrewastakhov/mmodel_server/lahta"])
import mm
import numpy as np


def b1_decoder(
        path="/Volumes/GoogleDrive/Shared drives/CONTEXTMACHINE/PROJECTS/2206_Lahta_Triangles/Lahta_Trngls_FILES_WORK/SV/json/triangle_point_coordinates.txt"):
    with open(path, "rb") as fp:
        bytes = eval(fp.read())
    return bytes


def b1_decoderp(path="/Users/andrewastakhov/mmodel_server/tmp/type_map_b1.json"):
    with open(path, "rb") as fp:
        bytes = eval(fp.read())
    return bytes


from mm.baseitems import DictableItem, FieldItem

dat = b1_decoder()

fad = b1_decoderp()
ndat = np.asarray(list(dat.values()))
flndat = ndat.flatten()
a, = flndat.shape
ids = np.arange(a).reshape(ndat.shape)
def cullnls():
    for k, v in fad.items():
        fad[k] = list(map(lambda x: x[1], v))

class Point(DictableItem):
    def __init_(self, **kwargs):

        super().__init__(**kwargs)

    def __call__(self, arr: np.ndarray = None, x=None, y=None, z=None, ):
        if arr is not None:
            dct = dict(zip(["x", "y", "z"], arr.tolist()))
            dct["arr"] = arr.tolist()
        else:
            dct = dict(x=x, y=y, z=z)
            dct["arr"] = np.array([x, y, z])
        super().__call__(**dct)

    def __array__(self):
        return np.array([self.x, self.y, self.z])


class Tri(DictableItem):
    def __init_(self, a: Point, b: Point, c: Point):
        super()


class RefPoint(Point):

    def __call__(self, **kwargs):
        super().__call__(**kwargs)
        self.real_arr = flndat[self.arr]
