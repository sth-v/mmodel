__author__ = "sofyadobycina"

import os

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

import sys
import imp
import ghpythonlib.treehelpers as th
import math
import Rhino.Geometry as rh

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

cogs.__init__("cogs", "generic nodule")
from cogs import TT

reload(cogs)

sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype) = imp.find_module("main_sides", path=[PWD])
main_sides = imp.load_module("main_sides", sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype))

main_sides.__init__("main_sides", "generic nodule")

pfile, pfilename, (psuffix, pmode, ptype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", pfile, pfilename, (psuffix, pmode, ptype))

main_panels.__init__("main_panels", "generic nodule")
from main_panels import N_4

reload(main_panels)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("panel_types", path=[PWD])
panel_types = imp.load_module("panel_types", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

panel_types.__init__("panel_types", "generic nodule")
from panel_types import P_1, P_2, N_1, N_3, N_2, P_3

reload(panel_types)

framelfile, framefilename, (framesuffix, framemode, frametype) = imp.find_module("main_framing", path=[PWD])
main_framing = imp.load_module("main_framing", framelfile, framefilename, (framesuffix, framemode, frametype))

main_framing.__init__("main_framing", "generic nodule")

reload(main_framing)

from main_framing import MainFrame
import random


class UnrollPackage:
    panels_dict = {'P_1': P_1, 'P_2': P_2, 'P_3': P_3, 'N_1': N_1, 'N_2': N_2, 'N_3': N_3, 'N_4': N_4}

    def __init__(self, x, y, circle, pins_hole, bend_hole, elements):
        self.cog = TT(x, y, circle)
        tr = rh.Transform.Rotation(math.pi / 2, rh.Point3d(0, 0, 0))
        self.hls = bend_hole
        self.hls.Transform(tr)

        self.hls_rot = pins_hole
        self.hls_rot.Transform(tr)

        self.data = []
        self.fr = []

        self.cogs_bend = random.choice([True, False])
        for key, value in elements.items():

            if key != 'N_4' and key != 'N_2' and key != 'P_3':

                new = self.panels_dict[key](cogs_bend=self.cogs_bend, **value)
                new.hls = self.hls_rot

                new.niche.cg = self.cog
                new.niche.generate_cogs()

                try:
                    for i in new.side:
                        i.hls = self.hls
                except AttributeError:
                    pass

                setattr(self, key, MainFrame(new))
                det = getattr(self, key)
                self.data.append(det.all_elems)
                self.fr.append(det.unroll_dict_f)

            elif key == 'N_2':
                new = self.panels_dict[key](**value)
                setattr(self, key, MainFrame(new))
                det = getattr(self, key)
                self.data.append(det.all_elems)

            elif key == 'P_3':
                new = self.panels_dict[key](cogs_bend=False, **value)
                new.hls = self.hls_rot

                setattr(self, key, new)
                det = getattr(self, key)
                self.data.append(det.all_elems)


            else:
                new = self.panels_dict[key](**value)
                setattr(self, key, new)
                det = getattr(self, key)
                # self.data.append(det.all_elems)


def main():
    global x, y, circle, pins_hole, bend_hole, crv

    a = UnrollPackage(x, y, circle, pins_hole, bend_hole, crv.__dict__)
    side = th.list_to_tree(a.data)
    # a.P_2.niche.bend_surf
    return a, side


if __name__ == "__main__":
    a, side = main()
