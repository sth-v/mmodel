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

if os.getenv("USER") == "sofyadobycina":
    PWD = os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh"
    sys.path.extend([os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh",
                     os.getenv("HOME") + "Documents/GitHub/mmodel/panels_gh/cogs",
                     os.getenv("HOME") + "/Documents/GitHub/mmodel/panels_gh/main_sides"])
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

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("panel_unrolls", path=[PWD])
panel_unrolls= imp.load_module("panel_unrolls", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

panel_unrolls.__init__("panel_unrolls", "generic nodule")
from panel_unrolls import MainPanel
reload(panel_unrolls)

a = MainPanel(crv, False)

cog = TT(x, y, circle)
a.niche.cg = cog
a.niche.generate_cogs()

side = a.unrol_surf
niche = a.cut
bottom = a.fres