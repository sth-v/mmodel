__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import ast
import copy
import itertools
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


def not_inplace_transform(obj, transform):
    copyobj = copy.deepcopy(obj)
    copyobj.Transform(transform)
    return copyobj


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


class Tag(object):
    _transform = rh.Transform.ZeroTransformation
    # transform = property(fget=lambda self: self._transform)
    entity = None

    def __init__(self, hight, font, text="foo", **kwargs):
        object.__init__(self)

        self.hight = hight
        self.font = font
        self.text = text
        self.__dict__.update(kwargs)

    def compute_entity(self):
        self.entity = rh.TextEntity()
        self.entity.Text = self.text
        self.entity.Font = Rhino.DocObjects.Font(self.font)
        self.entity.TextHeight = self.hight
        self.entity.Plane = self.plane

        self.entity.Justification = rh.TextJustification.Center

    def generate_curves(self):
        self.compute_entity()
        curves = list(self.entity.CreateCurves(Rhino.DocObjects.DimensionStyle(), False, 1.0, 0.01))

        if self.transform != rh.Transform.ZeroTransformation:
            res = []
            for curve in curves:
                res.append(not_inplace_transform(curve, self.transform))
            return res
        else:
            return curves

    def generate_curves_with_transform(self, transform):
        self.compute_entity()
        for curve in self.generate_curves():
            yield not_inplace_transform(curve, transform)

    _font = None
    _plane = rh.Plane.WorldXY
    _size = 11
    _constrains = None
    _text = "foo"
    _transform = None

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def constrains(self):
        return self._constrains

    @constrains.setter
    def constrains(self, value):
        self._constrains = value

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    @property
    def plane(self):
        return self._plane

    @plane.setter
    def plane(self, value):
        self._plane = value

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        self._font = value


class TagOne(Tag):
    @property
    def transform(self):
        return Rhino.Geometry.Transform.Scale(self.plane.Origin, self.hight)

    def generate_curves(self):
        shpindel = ['4.58410865736586,0,0', '0,-4.451242716713182,0', '-19.853477782260782,-4.451242716713182,0',
                    '-19.853477782260782,4.451242716713182,0', '0,4.451242716713182,0', '4.58410865736586,0,0']
        shpindel_curve = rh.Polyline([rh.Point3d.TryParse(shp)[1] for shp in shpindel]).ToPolylineCurve()
        shpindel_curve.Transform(rh.Transform.Translation(self.plane.Origin.X, self.plane.Origin.Y + 164, 0.0))
        self.text = "  " + self.text
        mxf = Rhino.Geometry.Transform.Mirror(
            Rhino.Geometry.Plane(self.plane.Origin, self.plane.ZAxis, self.plane.YAxis))
        res = [shpindel_curve]
        for curve in list(Tag.generate_curves(self)):
            res.extend([curve, not_inplace_transform(curve, mxf)])
        return res


class TagTwo(Tag):
    @property
    def transform(self):
        trx1 = rh.Transform.Rotation(90, self.plane.ZAxis)
        trx2 = Rhino.Geometry.Transform.Scale(self.plane.Origin, self.hight)
        #vec = Rhino.Geometry.Vector3D(self.plane.Origin, rh.Point3d(self.plane.Origin[0], self.plane.Origin[1]+150, 0))
        #trx3 = Rhino.Geometry.Transform.Translation(vec)

        return rh.Transform.Multiply(trx2, trx1)


class TagThree(Tag):
    @property
    def transform(self):
        trx2 = Rhino.Geometry.Transform.Scale(self.plane.Origin, self.hight)
        return trx2


class MiniFramer():
    def __init__(self, cls):
        self._cls = cls
        self._cls.text_geometry = [[], [], [], [], [], []]
        self.rect = self._cls.panel.bound_frame
        self.spec_center = [self._cls.panel.hole_one, self._cls.panel.hole_two]
        # Rhino.Display.CustomDisplay.AddLine(
        #   rh.Line(self._cls.panel.edges[1].PointAtEnd, self._cls.panel.edges[1].PointAtStart))

        # edge2_vector.Unitize()

    def __call__(self, u, v, tagobj, layer, spec=False, p=1, *args, **kwargs):
        rH, rW = 1 / self.rect.Height, 1 / self.rect.Width
        tagobj.plane = copy.deepcopy(self._cls.panel.plane)
        if spec is False:
            # center = self.rect.PointAt(u * rW, v * rH)
            center = rh.Point3d(tagobj.plane.Origin[0] - u, tagobj.plane.Origin[1] - v, 0)
            tagobj.plane.Origin = center
        else:
            pp = self.spec_center[p]
            center = rh.Point3d(pp[0] + u, pp[1] + v, 0)
            tagobj.plane.Origin = center

        # tagobj.plane.Origin = center

        self._cls.text_geometry[layer].extend(list(itertools.chain(tagobj.generate_curves())))
        return self._cls


class Framer:
    def __init__(self, cls):
        self._cls = cls
        self._cls.text_geometry = [[], [], [], [], []]

        _, vv = self._cls.unroll_dict_f["frame"].TryGetPolyline()

        self.rect = rh.Rectangle3d.CreateFromPolyline(vv)
        self.spec =  self._cls.panel.marker_curve
    def __call__(self, u, v, tagobj, layer, side=None,  *args, **kwargs):

        if side is None:
            rH, rW = 1 / self.rect.Height, 1 / self.rect.Width

            center = self.rect.PointAt(u * rW, v * rH)
            tagobj.plane = rh.Plane(center, self.rect.Plane.YAxis, self.rect.Plane.XAxis)
            tagobj.text = self._cls.unroll_dict_f["tag"]

            # mw = r.Width / 4.0
            # mh = r.Height / 4.0
            # mark_a, mark_b = rh.Plane(rh.Point3d(400, mh * 3, 0.0), rh.Vector3d(0, 0, 1)), rh.Plane(
            # rh.Point3d(mw * 3, mh, 0.0), rh.Vector3d(0, 0, 1))
            # r = Rhino.DocObjects.DimensionStyle()
            # r.TextHeight = s
            # ee = rh.TextEntity()
            # self.tag = xxx.unroll_dict_f["tag"]
            # ee.Text = xxx.unroll_dict_f["tag"]
            # ee.TextHeight = s

            # ee.Plane = self.pln
            # ee.Font = Rhino.DocObjects.Font("TC_LaserSans")
            # t = rh.Transform.Scale(ee.Plane, 1, 1, 1.0)
            # self.text = ee

            # mxf = Rhino.Geometry.Transform.Mirror(Rhino.Geometry.Plane(center, tag.plane.ZAxis))

            # m2 = Rhino.Geometry.Transform.Mirror(Rhino.Geometry.Plane.WorldXY)
            # curves = list(tag.generate_curves()) + list(tag.generate_curves_with_transform(mxf))

            self._cls.text_geometry[layer].extend(list(itertools.chain(tagobj.generate_curves())))

            return self._cls

        else:
            crv = rh.Curve.Offset(self.spec[side], rh.Plane.WorldXY, -80+u, 0.01,
                                  rh.CurveOffsetCornerStyle.__dict__['None'])[0]
            self.pl = [crv, self.spec[side]]

            center = crv.PointAtNormalizedLength(0.5)

            crv_check = rh.Curve.Offset(self.spec[side], rh.Plane.WorldXY, -150, 0.01,
                                  rh.CurveOffsetCornerStyle.__dict__['None'])[0]

            center_check = crv_check.PointAtNormalizedLength(0.5)
            vec = Rhino.Geometry.Vector3d(center_check-center)
            param = crv.NormalizedLengthParameter(0.5)[1]
            # tagobj.plane = rh.Plane(center, self.rect.Plane.YAxis, self.rect.Plane.XAxis)
            plane = crv.FrameAt(param)[1]
            tagobj.plane = Rhino.Geometry.Plane(plane.Origin, plane.XAxis, vec)
            tagobj.text = self._cls.unroll_dict_f["tag"]

            #self.pl = tagobj.plane

            self._cls.text_geometry[layer].extend(list(itertools.chain(tagobj.generate_curves())))
            return self._cls
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
