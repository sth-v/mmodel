
__author__ = "sofyadobycina"

import os
import types

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import Rhino.Geometry as rh
import math
import sys
import imp
import ghpythonlib.treehelpers as th

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_panels"])
else:
    PWD = os.getenv("MMODEL_DIR") + "/panels_gh"
    sys.path.extend(
        [os.getenv("MMODEL_DIR") + "/panels_gh", os.getenv("MMODEL_DIR") + "/panels_gh/cogs"])

cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype) = imp.find_module("cogs", path=[PWD])
cogs = imp.load_module("cogs", cogsfile, cogsfilename, (cogssuffix, cogsmode, cogstype))
from functools import wraps

cogs.__init__("cogs", "generic nodule")
from cogs import Pattern, TT

reload(cogs)

pfile, pfilename, (psuffix, pmode, ptype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", pfile, pfilename, (psuffix, pmode, ptype))

main_panels.__init__("main_panels", "generic nodule")
from main_panels import N_4

reload(main_panels)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("panel_types", path=[PWD])
panel_types = imp.load_module("panel_types", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

panel_types.__init__("panel_types", "generic nodule")
from panel_types import P_1, P_2, N_1, N_3, N_2

reload(panel_types)

framelfile, framefilename, (framesuffix, framemode, frametype) = imp.find_module("main_framing", path=[PWD])
main_framing = imp.load_module("main_framing", framelfile, framefilename, (framesuffix, framemode, frametype))

main_framing.__init__("main_framing", "generic nodule")
from main_framing import MainFrame

reload(main_framing)




class UnrollPackage:
    panels_dict = {'P_1': P_1, 'P_2': P_2, 'N_1': N_1, 'N_2': N_2, 'N_3': N_3, 'N_4': N_4}

    def __init__(self, x, y, circle, elements):

        self.cog = TT(x, y, circle)

        self.data = []

        for key, value in elements.items():
            new = self.panels_dict[key](value)

            if key != 'N_4':
                setattr(self, key, MainFrame(71, 1200, 21, new))
                det = getattr(self, key)
                self.data.append(det.all_elems)
            else:
                setattr(self, key, new)









print(crv.__dict__)

a = UnrollPackage(x, y, circle, crv.__dict__)


# cog = TT(x, y, circle)
# a.niche.cg = cog
# a.niche.generate_cogs()

#side = b.all_offset()
side = a.data
side = th.list_to_tree(side)

#side = a.bound_plane
