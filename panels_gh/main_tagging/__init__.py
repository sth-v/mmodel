__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import ast
import copy
import os

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

encode = Rhino.Geometry.GeometryBase.ToJSON


class RhIterArgParser(dict):

    def __init__(self, kwargs):
        dict.__init__(self, **kwargs)

        for k, v in dict.items(self):
            if hasattr(v, "ToJSON"):

                dict.__setitem__(self, k, RhIterArgParser(ast.literal_eval(v.ToJSON(None))))

                continue
            else:
                try:
                    iter(v)
                    datas = []

                    if isinstance(v, dict):
                        dict.__setitem__(self, k, RhIterArgParser(v))


                    else:

                        for vv in v:
                            datas.append(RhIterArgParser(vv))

                    dict.__setitem__(self, k, datas)

                except TypeError:

                    dict.__setitem__(self, k, v)


class Vectorizer:

    def __init__(self, cls):
        self._cls = cls

    def __set_name__(self, own, name):
        self.name = name

    def __get__(self, instance, owner):
        self._cls.__getattr__(instance, self.name)


def trsf(items, transform):
    for i in items:
        anu = copy.deepcopy(i)
        anu.Transform(transform)
        yield anu


class Extender:
    def __init__(self, cls):
        self._cls = cls
        self.name = cls.__name__

    def __call__(self, *items):
        self.itemargs = []
        for xx in enumerate(items):
            self.itemargs.append(self._cls(xx))
        return self

    def __get__(self, inst, own):
        def wrp(*args):
            dd = []
            for i, xx in enumerate(self.itemargs):
                dd.append(xx(*args[i]))
            return dd

        return wrp


class Framer:
    def __init__(self, cls):
        self._cls = cls

    def __call__(self, u, v, s, layer,  *args, **kwargs):
        xxx = self._cls
        _, vv = xxx.unroll_dict_f["frame"].TryGetPolyline()
        r = rh.Rectangle3d.CreateFromPolyline(vv)
        rH = 1 / r.Height
        rW = 1 / r.Width

        self.c = r.PointAt(u * rW, v * rH)
        self.pln = rh.Plane(self.c, r.Plane.YAxis, r.Plane.XAxis)

        mw = r.Width / 4.0
        mh = r.Height / 4.0
        mark_a, mark_b = rh.Plane(rh.Point3d(400, mh * 3, 0.0), rh.Vector3d(0, 0, 1)), rh.Plane(
            rh.Point3d(mw * 3, mh, 0.0), rh.Vector3d(0, 0, 1))
        r = Rhino.DocObjects.DimensionStyle()
        r.TextHeight = 20

        ee = rh.TextEntity()

        self.tag = xxx.unroll_dict_f["tag"]

        ee.Text = xxx.unroll_dict_f["tag"]

        ee.TextHeight = 20
        ee1 = rh.TextEntity()
        ee1.Text = xxx.unroll_dict_f["tag"]
        ee2 = rh.TextEntity()
        ee2.Text = xxx.unroll_dict_f["tag"]
        ee2.TextHeight = 20
        ee1.TextHeight = 20
        ee1.Plane = mark_a
        ee2.Plane = mark_b
        ee.Plane = self.pln
        ee.Font = Rhino.DocObjects.Font("TC_LaserSans")
        ee1.Font = Rhino.DocObjects.Font("JetBrains Mono")
        ee2.Font = Rhino.DocObjects.Font("JetBrains Mono")

        t = rh.Transform.Scale(ee.Plane, 1, 1, 1.0)
        self.text = ee
        te2 = rh.Transform.Scale(ee2.Plane, 20, 20, 1.0)
        te1 = rh.Transform.Scale(ee1.Plane, 20, 20, 1.0)
        mxf = Rhino.Geometry.Transform.Mirror(
            Rhino.Geometry.Plane(self.text.Plane.Origin, self.text.Plane.YAxis, self.text.Plane.ZAxis))
        m2 = Rhino.Geometry.Transform.Mirror(Rhino.Geometry.Plane.WorldXY)
        ds = Rhino.DocObjects.DimensionStyle()
        eee = list(self.text.CreateCurves(r, False, 1.0, 0.01))
        eee1 = list(ee1.CreateCurves(ds, False, 1.0, 0.01))
        eee2 = list(ee2.CreateCurves(ds, False, 1.0, 0.01))

        xxx.panel.grav.extend(list(trsf(eee1, te1)) + list(trsf(eee2, te2)))

        eeee = []
        for ee in eee:
            arcs = ee.ToArcsAndLines(tolerance=0.1, angleTolerance=0.01, minimumLength=3.0,
                                     maximumLength=999999)

            arcs.Transform(t)
            arcs1 = copy.deepcopy(arcs)
            arcs.Transform(mxf)

            arcs1.Transform(m2)
            arcs.Transform(m2)
            eeee.append(arcs1)
            eeee.append(arcs)

        xxx.text_geometry[layer].extend(eeee)

        return xxx


class Tagger:
    _cls = None
    inst = None
    ap = None

    def __init__(self, cls):
        self._cls = cls
        self._cls.top = TOP
        self._cls.bottom = BOTTOM

    def set_attr_cls(self, key, value):
        setattr(self._cls, key, value)

    def __call__(self, *args):
        inst = self._cls(*args)

        dct = inst.unroll_dict_f

        inst.stable_dct = dct
        ap = RhIterArgParser(inst.unroll_dict_f)
        # self.panels = FramePanel(self.inst.panel_r, 0, P_NICHE), FramePanel(self.inst.panel_l, 1, P_NICHE)
        # self.niches = FramePanel(self.inst.niche_r, 0, N_NICHE), FramePanel(self.inst.niche_l, 1, N_NICHE)
        # with open("{}/dump{}.json".format(PWD, id(self)), "w") as pkl:
        # json.dump(ap, pkl, indent=3)
        # with open("Picklefile","w") as pklf:
        #    pklf.writelines(["PROTOCOL={}".format(pickle.HIGHEST_PROTOCOL)])
        #    pickle.dump(self, pklf, pickle.HIGHEST_PROTOCOL)

        # pprint(dict(ap))

        return inst
