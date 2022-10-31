"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs
#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

import imp
import os
import sys

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

TT = cogs.TT
Pattern = cogs.Pattern
Panel = panel
NicheSide = niche_side
BackNiche = back_niche
Ribs = ribs


class UnrollPack:

    @property
    def unroll_dict(self):
        unroll_dict = {'P-'+ self.tag: [self.panel_r.unroll_dict, self.panel_l.unroll_dict],
                       'N-'+ self.tag: [self.niche_r.unroll_dict, self.niche_l.unroll_dict, self.niche_b.unroll_dict]}
        return unroll_dict

    def __init__(self, x, y, circle, panel_r, panel_l, niche_r, niche_l, r, n_b, cog_type, tag):
        self.tag = tag

        self.panel_r = Panel(panel_r, 0, cog_type, 'P-'+self.tag+'-1')
        self.panel_l = Panel(panel_l, 1, cog_type, 'P-'+self.tag+'-2')
        cog = TT(x, y, circle)

        self.panel_r.niche.cg = cog
        self.panel_r.niche.generate_cogs()

        self.panel_l.niche.cg = cog
        self.panel_l.niche.generate_cogs()

        self.ribs = Ribs(r)
        self.niche_b = BackNiche(n_b, self.ribs, 'N-'+self.tag+'-2')


        self.niche_r = NicheSide(niche_r, 1, self.ribs, self.niche_b, cog_type, 'N-'+self.tag+'-1')
        self.niche_l = NicheSide(niche_l, 0, self.ribs, self.niche_b, cog_type, 'N-'+self.tag+'-3')

        self.niche_l.niche.cg = cog
        self.niche_l.niche.generate_cogs()

        self.niche_r.niche.cg = cog
        self.niche_r.niche.generate_cogs()




class MarkerDict:
    def __init__(self, input_dict):
        self.__dict__.update(input_dict)

    def GetString(self):
        return self.__dict__.__str__()


packs = []
pack_unrolls = []
a = []
b = []
import ghpythonlib.treehelpers as th

for i in unroll_elems:
    p = UnrollPack(x, y, circle, *i)
    packs.append(p)
    pack_unrolls.append(p.unroll_dict)
    a.append(p.niche_b.grav)

a = th.list_to_tree(a)