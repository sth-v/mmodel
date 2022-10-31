__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import ast
import copy
import os
import sys
from pprint import pprint

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
# import main_frame
if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

#reload(main_frame)
MMODEL_DIR = os.getenv("MMODEL_DIR")
HOME = os.getenv("HOME")
BOTTOM = 45
TOP = 35
N_NICHE = 45
P_NICHE = 43.53

import json
import Rhino

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
                    print('iteration will probably work')
                    if isinstance(v, dict):
                        dict.__setitem__(self, k, RhIterArgParser(v))


                    else:

                        for vv in v:
                            datas.append(RhIterArgParser(vv))

                    dict.__setitem__(self, k, datas)

                except TypeError:
                    print('not iterable')

                    dict.__setitem__(self, k, v)


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
        print "\n\n{}\n\n".format(dct)
        inst.stable_dct = copy.deepcopy(dct)
        ap = RhIterArgParser(dct)
        # self.panels = FramePanel(self.inst.panel_r, 0, P_NICHE), FramePanel(self.inst.panel_l, 1, P_NICHE)
        # self.niches = FramePanel(self.inst.niche_r, 0, N_NICHE), FramePanel(self.inst.niche_l, 1, N_NICHE)
        with open("{}/dump{}.json".format(PWD, id(self)), "w") as pkl:
            json.dump(ap, pkl, indent=3)
        # with open("Picklefile","w") as pklf:
        #    pklf.writelines(["PROTOCOL={}".format(pickle.HIGHEST_PROTOCOL)])
        #    pickle.dump(self, pklf, pickle.HIGHEST_PROTOCOL)

        pprint(dict(ap))

        return inst
