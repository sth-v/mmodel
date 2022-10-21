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
    PWD = os.getenv("HOME") + "/mmodel/panels_gh"
    sys.path.extend(
        [os.getenv("HOME") + "/mmodel/panels_gh", os.getenv("HOME") + "/mmodel/panels_gh/cogs"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
cogs = imp.load_module("cogs", cogsfile, PWD, (cogssuffix, cogsmode, cogstype))
# sys.path.extend(["/Users/sofyadobycina/Documents/GitHub/mmodel/panels_gh"])
import ghpythonlib.treehelpers as th

TT = cogs.TT
Pattern = cogs.Pattern
Panel = panel
NicheSide = niche_side
BackNiche = back_niche
Ribs = ribs


class UnrollPack:

    @property
    def panel_r_cut(self):
        return self.panel_r.cut

    @property
    def panel_r_fres(self):
        return self.panel_r.fres

    @property
    def panel_l_cut(self):
        return self.panel_l.cut

    @property
    def panel_l_fres(self):
        return self.panel_l.fres

    @property
    def niche_r_cut(self):
        return self.niche_r.cut

    @property
    def niche_r_fres(self):
        return self.niche_r.fres

    @property
    def niche_r_grav(self):
        return self.niche_r.grav

    @property
    def niche_l_cut(self):
        return self.niche_l.cut

    @property
    def niche_l_fres(self):
        return self.niche_l.fres

    @property
    def niche_l_grav(self):
        return self.niche_l.grav

    @property
    def niche_b_cut(self):
        return self.niche_b.cut

    @property
    def niche_b_fres(self):
        return self.niche_b.fres

    @property
    def all(self):
        return [[self.panel_r_cut, self.panel_r_fres], [self.panel_l_cut, self.panel_l_fres],
                [self.niche_r_cut, self.niche_r_fres, self.niche_r_grav],
                [self.niche_l_cut, self.niche_l_fres, self.niche_l_grav], [self.niche_b_cut, self.niche_b_fres]]





    def __init__(self, x, y, circle, panel_r, panel_l, niche_r, niche_l, r, n_b):

        self.panel_r = Panel(panel_r, 0)
        self.panel_l = Panel(panel_l, 1)
        cog = TT(x, y, circle)

        self.panel_r.niche.cg = cog
        self.panel_r.niche.generate_cogs()

        self.panel_l.niche.cg = cog
        self.panel_l.niche.generate_cogs()

        self.niche_r = NicheSide(niche_r, 0, r, n_b)
        self.niche_l = NicheSide(niche_l, 1, r, n_b)
        
        self.niche_l.niche.cg=cog
        self.niche_l.niche.generate_cogs()

        self.niche_r.niche.cg = cog
        self.niche_r.niche.generate_cogs()
        
        self.niche_b = BackNiche(n_b)

        self.niche_b = BackNiche(n_b)
        self.ribs = Ribs(r)


packs = []
pack_unrolls = []
a = []
b = []
for i in unroll_elems:
    p = UnrollPack(x, y, circle, *i)
    packs.append(p)
    pack_unrolls.append(p.all)
    a.append(p.niche_r)

pack_unrolls = th.list_to_tree(pack_unrolls)
