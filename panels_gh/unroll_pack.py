"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

import gh_redis_api

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

import cogs

reload(cogs)
TT = cogs.TT
Pattern = cogs.Pattern
Panel = panel
N_1 = niche_side[0]
N_3 = niche_side[1]
BackNiche = back_niche
Ribs = ribs


class UnrollPack:

    @gh_redis_api.GhRedisProperty
    def unroll_dict(self):
        self._unroll_dict = {'P-'+ self.tag: [self.panel_r.unroll_dict, self.panel_l.unroll_dict],
                       'N-'+ self.tag: [self.niche_r.unroll_dict, self.niche_l.unroll_dict, self.niche_b.unroll_dict]}
        return self._unroll_dict

    def __init__(self, x, y, circle, panel_r, panel_l, niche_r, niche_l, r, n_b, cog_type, tag):
        self.tag = tag

        self.panel_r = Panel(panel_r, 0, cog_type, +self.tag+'-1')
        self.panel_l = Panel(panel_l, 1, cog_type, 'P-'+self.tag+'-2')
        cog = TT(x, y, circle)

        self.panel_r.niche.cg = cog
        self.panel_r.niche.generate_cogs()

        self.panel_l.niche.cg = cog
        self.panel_l.niche.generate_cogs()

        self.ribs = Ribs(r)
        self.niche_b = BackNiche(n_b, self.ribs, 'N-'+self.tag+'-2')


        self.niche_r = N_1(niche_r, self.ribs, self.niche_b, cog_type, 'N-'+self.tag+'-1')
        self.niche_l = N_3(niche_l, self.ribs, self.niche_b, cog_type, 'N-'+self.tag+'-3')

        self.niche_l.niche.cg = cog
        self.niche_l.niche.generate_cogs()

        self.niche_r.niche.cg = cog
        self.niche_r.niche.generate_cogs()


class MUP(UnrollPack):
    def __init__(self, *args, **kwargs):
        UnrollPack.__init__(self, *args, **kwargs)

    @property
    def unroll_dict(self):
        _unroll_dict = {'P': {'R': self.panel_r.unroll_dict, 'L': self.panel_l.unroll_dict},
                        'N': {'R': self.niche_r.unroll_dict, 'L': self.niche_l.unroll_dict,
                              'B': self.niche_b.unroll_dict},
                        'tag': self.tag
                        }
        return _unroll_dict

class MarkerDict:
    def __init__(self, input_dict):
        self.__dict__.update(input_dict)

    def GetString(self):
        return self.__dict__.__str__()


packs = []
pack_unrolls = []
a = []
b = []
c=[]
import ghpythonlib.treehelpers as th

for i in unroll_elems:
    p = UnrollPack(x, y, circle, *i)
    packs.append(p)
    pack_unrolls.append(p.unroll_dict)
    a.append(p.niche_l.niche.fres.FrameAt(p.niche_l.niche.fres.Domain[0])[1])
    c.append([[p.panel_r.cut, p.panel_r.fres], [p.panel_l.cut, p.panel_l.fres],
              [p.niche_r.cut, p.niche_r.fres, p.niche_r.grav], [p.niche_l.cut, p.niche_l.fres, p.niche_l.grav],
              [p.niche_b.cut, p.niche_b.fres, p.niche_b.grav]])

c = th.list_to_tree(c)

a = th.list_to_tree(a)
packs_ = []
pack_unrolls_ = []
a_ = []
b_ = []

for i in unroll_elems:
    pp = MUP(x, y, circle, *i)
    packs_.append(pp)
    pack_unrolls_.append(pp.unroll_dict)

