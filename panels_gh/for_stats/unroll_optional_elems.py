"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

import json

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import imp
import os
import sys
import Rhino.Geometry as rh

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
cogs = imp.load_module("cogs", cogsfile, PWD, (cogssuffix, cogsmode, cogstype))
# sys.path.extend(["/Users/sofyadobycina/Documents/GitHub/mmodel/panels_gh"])

import cogs

reload(cogs)
TT = cogs.TT
Pattern = cogs.Pattern
Panel = panel
NicheSide = niche_side
BackNiche = back_niche
Ribs = ribs
FramePanel = frame


class UnrollPack:

    def __init__(self, x, y, circle, elements, cog_type=False):

        self.cog_type = cog_type
        self.cog = TT(x, y, circle)


        self.panels = []
        self.data = []
        self.bound = []

        self.sizes = {}

        for key, value in elements.items():
            try:
                iter(value)
                for i, v in enumerate(value):
                    elem = self.args_test(key, v[1], n=i)

                    self.panels.append(elem)
                    self.data.append(elem.all_elems)

                    self.bound.append(elem.bound_frame_r)
                    self.sizes[v[0]] = {'width': round(elem.bound_frame_r.Width), 'height': round(elem.bound_frame_r.Height)}

            except TypeError:
                elem = self.args_test(key, value)

                self.panels.append(elem)
                self.data.append(elem.all_elems)

                self.bound.append(elem.bound_frame_r)


    def args_test(self, key, value, n=None):

        try:
            cog_type = self.cog_type[n]
        except TypeError:
            cog_type = self.cog_type

        if key == 'P-0':
            p_r = Panel(value, 0, cog_type, 'P-0')
            p_r.niche.cg = self.cog
            p_r.niche.generate_cogs()

            r = FramePanel(p_r, FramePanel.p_niche)
            return r

        elif key == 'P-1':
            p_l = Panel(value, 1, cog_type, 'P-1')
            p_l.niche.cg = self.cog
            p_l.niche.generate_cogs()

            r = FramePanel(p_l, FramePanel.p_niche)
            return r

        elif key == 'N-4':
            r = Ribs(value)
            return r

        elif key == 'N-1':
            n_r = NicheSide(value, 1)
            r = FramePanel(n_r, FramePanel.n_niche)
            return r

        elif key == 'N-3':
            n_l = NicheSide(value, 0)
            r = FramePanel(n_l, FramePanel.n_niche)
            return r

        else:
            pass



class MarkerDict:
    def __init__(self, input_dict):
        self.__dict__.update(input_dict)

    def GetString(self):
        return self.__dict__.__str__()


#packs = []
pack_unrolls = []


import ghpythonlib.treehelpers as th


a = UnrollPack(x, y, circle, unroll_elems.__dict__)

print(a.panels)
packs = th.list_to_tree(a.panels)
geom = th.list_to_tree(a.data)
bound = a.bound

json_object = json.dumps(a.sizes, indent=3)

with open('/Users/sofyadobycina/Documents/GitHub/mmodel/panels_gh/for_stats/niche_sizes.json', 'w') as out_file:
    out_file.write(json_object)


