"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sofyadobycina"

#  Copyright (c) 2022. Computational Geometry, Digital Engineering and Optimizing your construction processe"

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

a = N_2(crv)
b = MainFrame(71, 1200, 21, a)

# cog = TT(x, y, circle)
# a.niche.cg = cog
# a.niche.generate_cogs()

#side = b.all_offset()
side = b.all_elems
side = th.list_to_tree(side)
niche = a.cut
bottom = a.fres
#side = a.bound_plane
