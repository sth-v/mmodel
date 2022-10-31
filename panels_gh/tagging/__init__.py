__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import ast
import os
from pprint import pprint

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
import main_frame

reload(main_frame)
MMODEL_DIR = os.getenv("MMODEL_DIR")
HOME = os.getenv("HOME")
BOTTOM = 45
TOP = 35
N_NICHE = 45
P_NICHE = 43.53

import Rhino

encode = Rhino.Geometry.GeometryBase.FromJSON


class RhIterArgParser(dict):

    def __init__(self, kwargs):
        dict.__init__(self, **kwargs)

        for k, v in dict.items(self):
            if hasattr(v, "ToJSON"):
                dict.__setitem__(self, k, RhIterArgParser(ast.literal_eval(v.ToJSON(None))))
                print("yess")
                continue
            else:
                try:
                    iter(v)
                    datas = []
                    print('iteration will probably work')
                    if isinstance(v,dict):
                        dict.__setitem__(self, k, RhIterArgParser(v))


                    else:

                        for vv in v:

                            datas.append( RhIterArgParser(vv))


                    dict.__setitem__(self, k, datas)

                except TypeError:
                    print('not iterable')




                    dict.__setitem__(self, k, v)
class Tagger:

    def __init__(self, cls):
        self._cls = cls


    def __call__(self, *args):
        self.inst = self._cls(*args)

        #FramePanel.bottom = BOTTOM
        #FramePanel.top = TOP

        self.ap=RhIterArgParser(self.inst.unroll_dict)
        #self.panels = FramePanel(self.inst.panel_r, 0, P_NICHE), FramePanel(self.inst.panel_l, 1, P_NICHE)
        #self.niches = FramePanel(self.inst.niche_r, 0, N_NICHE), FramePanel(self.inst.niche_l, 1, N_NICHE)
        #with open(HOME+"/mmodel/panels_gh/dump{}.json".format(id(self)),"w") as pkl:
            #json.dump(self.ap, pkl, indent=3)
        #with open("Picklefile","w") as pklf:
        #    pklf.writelines(["PROTOCOL={}".format(pickle.HIGHEST_PROTOCOL)])
        #    pickle.dump(self, pklf, pickle.HIGHEST_PROTOCOL)

        pprint(dict(self.ap))

        return self.inst
