__author__ = "sofyadobycina"

import os

try:
    rs = __import__("rhinoscriptsyntax")
except:
    import rhinoscript as rs

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

cogs.__init__("cogs", "generic nodule")
from cogs import TT

reload(cogs)

sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype) = imp.find_module("main_sides", path=[PWD])
main_sides = imp.load_module("main_sides", sidesfile, sidesfilename, (sidessuffix, sidesmode, sidestype))

main_sides.__init__("main_sides", "generic nodule")
from main_sides import HolesSideTwo

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

reload(main_framing)

from main_framing import MainFrame




class UnrollPackage:
    panels_dict = {'P_1': P_1, 'P_2': P_2, 'N_1': N_1, 'N_2': N_2, 'N_3': N_3, 'N_4': N_4}

    def __init__(self, x, y, circle, bend_hole, elements):
        self.cog = TT(x, y, circle)
        self.hls = bend_hole

        self.data = []
        self.fr = []

        for key, value in elements.items():
            if key != 'N_4' and key != 'N_2':
                new = self.panels_dict[key](value, cogs_bend=True, tag=key)
                new.niche.cg = self.cog
                new.niche.generate_cogs()

                try:
                    for i in new.side:
                        i.hls = self.hls
                except AttributeError:
                    pass

                setattr(self, key, MainFrame(71, 1200, 21, new))
                det = getattr(self, key)
                self.data.append(det.all_elems)
                self.fr.append(det.unroll_dict_f)

            elif key == 'N_2':
                new = self.panels_dict[key](value)
                setattr(self, key, MainFrame(71, 1200, 21, new))
                new = self.panels_dict[key](value)

            else:
                new = self.panels_dict[key](value)
                setattr(self, key, new)


def main():
    global x, y, circle, crv
    print(crv.__dict__)
    a = UnrollPackage(x, y, circle, crv.__dict__)
    side = th.list_to_tree(a.data)
    return a, side


if __name__ == "__main__":
    a, side = main()
