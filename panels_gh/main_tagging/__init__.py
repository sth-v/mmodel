__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import ast
import copy
import os
from pprint import pprint

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
# import main_framing


# reload(main_framing)
MMODEL_DIR = os.getenv("MMODEL_DIR")
HOME = os.getenv("HOME")
BOTTOM = 45
TOP = 35
N_NICHE = 45
P_NICHE = 43.53

import Rhino
import Rhino.Geometry as rh
import os

import sys

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    os.environ["MMODEL_DIR"] = "/Users/andrewastakhov/PycharmProjects/mmodel"
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs",
         os.getenv("MMODEL_DIR") + "/panels_gh/tagging"])


def encode(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            return {k: encode(v)}
    elif isinstance(obj, list):
        for k in obj:
            return encode(k)
    else:
        try:
            return ast.literal_eval(obj.ToJSON(None))
        except:
            return obj


class RhIterArgParser(dict):

    def __init__(self, **kwargs):

        dict.__init__(self, **kwargs)

        for k, v in dict.items(self):
            try:
                dict.__setitem__(self, k, encode(v))
            except:
                if isinstance(v, dict):
                    dict.__setitem__(self, k, RhIterArgParser(**v))
                else:
                    data = []
                    for vv in v:
                        dict.__setitem__(self, k, encode(v))
                        data.append(RhIterArgParser(**vv))
                    dict.__setitem__(self, k, data)


class Vectorizer:

    def __init__(self, cls):
        self._cls = cls

    def __set_name__(self, own, name):
        self.name = name

    def __get__(self, instance, owner):
        self._cls.__getattr__(instance, self.name)


class Extender:
    def __init__(self, cls):
        self._cls = cls

        print
        "INIT Extender", self._cls

    def __call__(self, *args, **kwargs):
        print
        "call Extender"
        self.itemargs = []
        instance = self._cls(*args, **kwargs)
        print
        "call Extender", instance

        return instance


class Framer:
    def __init__(self, cls):
        self._cls = cls

        print
        "init Framer", self._cls

    def __call__(self, u, v, s, *args, **kwargs):
        print
        "call Framer",
        xxx = self._cls(*args, **kwargs)
        print
        "call Framer", xxx, xxx.unroll_dict, xxx.unroll_dict["frame"]
        f, = xxx.unroll_dict["frame"]
        _, vv = f.TryGetPolyline()
        r = rh.Rectangle3d.CreateFromPolyline(vv)
        rH = 1 / r.Height
        rW = 1 / r.Width

        print
        u, v, s
        self.c = r.PointAt(u * rW, v * rH)
        self.pln = rh.Plane(self.c, r.Plane.YAxis, r.Plane.XAxis)
        # self.bb=rh.Rectangle3d.CreateFromPolyline(self.c)

        r = Rhino.DocObjects.DimensionStyle()

        r.Font = r.Font.__class__("GOSTTypeA-Italic")

        ee = rh.TextEntity()

        self.tag = xxx.unroll_dict["tag"]

        ee.Text = xxx.unroll_dict["tag"]
        ee.TextHeight = 16

        ee.Plane = self.pln

        t = rh.Transform.Scale(ee.Plane, s, s, 1.0)
        self.text = ee
        eee = self.text.CreateCurves(r, False, 1.0, 0.01)
        eeee = []
        for crv in eee:
            crv.Transform(t)
            eeee.append(crv)
        xxx._layers[3].objects.extend(eeee)

        xxx.text_g = copy.deepcopy(eeee)

        return xxx


class Tagger:

    def __init__(self, cls):
        self._cls = cls
        self._cls.top = TOP
        self._cls.bottom = BOTTOM

        print
        "init Tagger", self._cls

    def set_attr_cls(self, key, value):
        setattr(self._cls, key, value)

    def __call__(self, *args, **kwargs):
        print
        "call Tagger", args, kwargs
        self.instance = self._cls(*args, **kwargs)
        print
        "call Tagger", self.instance
        # self.panels = FramePanel(self.inst.panel_r, 0, P_NICHE), FramePanel(self.inst.panel_l, 1, P_NICHE)
        # self.niches = FramePanel(self.inst.niche_r, 0, N_NICHE), FramePanel(self.inst.niche_l, 1, N_NICHE)

        # with open("Picklefile","w") as pklf:
        #    pklf.writelines(["PROTOCOL={}".format(pickle.HIGHEST_PROTOCOL)])
        #    pickle.dump(self, pklf, pickle.HIGHEST_PROTOCOL)

        pprint(self.instance.unroll_dict)
        return self.instance
