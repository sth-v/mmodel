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

pfile, pfilename, (psuffix, pmode, ptype) = imp.find_module("main_panels", path=[PWD])
main_panels = imp.load_module("main_panels", pfile, pfilename, (psuffix, pmode, ptype))

main_panels.__init__("main_panels", "generic nodule")

reload(main_panels)

panelfile, panelfilename, (panelsuffix, panelmode, paneltype) = imp.find_module("panel_types", path=[PWD])
panel_types = imp.load_module("panel_types", panelfile, panelfilename, (panelsuffix, panelmode, paneltype))

panel_types.__init__("panel_types", "generic nodule")
from panel_types import NC_1, NC_2, B_1, B_2,PC_1,PC_2, B_3, B_1_T, PC_3, PC_4, NC_R_1, NC_R_2, NC_3, NC_R_3, B_2_1_rev, \
    B_2_1, B_2_rev

reload(panel_types)

panelfiletwo, panelfilenametwo, (panelsuffixtwo, panelmodetwo, paneltypetwo) = imp.find_module("panel_types_two", path=[PWD])
panel_typestwo = imp.load_module("panel_types_two", panelfiletwo, panelfilenametwo, (panelsuffixtwo, panelmodetwo, paneltypetwo))

panel_typestwo.__init__("panel_types_two", "generic nodule")
from panel_types_two import BC_2, BC_1, PB_1

reload(panel_typestwo)

framelfile, framefilename, (framesuffix, framemode, frametype) = imp.find_module("main_framing", path=[PWD])
main_framing = imp.load_module("main_framing", framelfile, framefilename, (framesuffix, framemode, frametype))

main_framing.__init__("main_framing", "generic nodule")

reload(main_framing)

from main_framing import MainFrame, MiniFrame,BoardFrame, ConeFrame

import main_tagging

reload(main_tagging)


class UnrollPackage:
    panels_dict = {'PC_1': PC_1, 'PC_2': PC_2, 'B_1': B_1, 'B_2': B_2, 'B_3':B_3, 'B_1_T':B_1_T, 'NC_3':NC_3,
                   'NC_R_3': NC_R_3, 'PC_3':PC_3, 'PC_4':PC_4, 'NC_1':NC_1, 'NC_2':NC_2, 'NC_R_1': NC_R_1, 'NC_R_2':NC_R_2,
                   "BC_2":BC_2, "BC_1":BC_1, "B_2_1_rev":B_2_1_rev, "B_2_1":B_2_1, "B_2_rev":B_2_rev, 'PB_1':PB_1}

    def __init__(self, x, y, circle, bend_hole, p3_hole, cog_hole, elements):
        self.cog = TT(x, y, circle)

        self.bend_hole = bend_hole
        self.p3_hole = p3_hole
        self.cog_hole = cog_hole

        self.data = []
        self.m = []

        for key, value in elements.items():

            if key =='B_1' or key=='B_1_T':
                new = self.panels_dict[key](**value)
                new.niche.cg = self.cog
                new.niche.cog_hole = self.cog_hole
                new.niche.generate_cogs()

                try:
                    for i in new.side:
                        i.hls = self.bend_hole
                    for i in new.extra_panel.side:
                        i.hls = self.bend_hole
                except AttributeError:
                    pass
                setattr(self, key, BoardFrame(new))

            elif key == "NC_1" or key == "NC_2" or key == "NC_R_1" or key == "NC_R_2":
                new = self.panels_dict[key](**value)

                new.niche.cg = self.cog
                new.niche.cog_hole = self.cog_hole
                new.niche.generate_cogs()

                try:
                    for i in new.side:
                        i.hls = self.bend_hole
                except AttributeError:
                    pass
                setattr(self, key, MainFrame(new))


            elif key == "NC_3" or key == "NC_R_3" or key == "BC_2" or key == "BC_1":
                new = self.panels_dict[key](**value)

                try:
                    new.niche.cg = self.cog
                    new.niche.cog_hole = self.cog_hole
                    new.niche.generate_cogs()
                except AttributeError:
                    pass


                try:
                    for i in new.side:
                        i.hls = self.bend_hole
                except AttributeError:
                    pass
                setattr(self, key, MainFrame(new))

                det = getattr(self, key)
                self.data.append(det.all_elems)

            elif key == "PB_1" or key =="PC_2":
                new = self.panels_dict[key](**value)

                #new.niche.cg = self.cog
                #new.niche.cog_hole = self.cog_hole
                #new.niche.generate_cogs()

                for i in new.side:
                    try:
                        i.hls = self.bend_hole
                    except AttributeError:
                        pass

                setattr(self, key, MainFrame(new))



            elif key == "PC_1" or key =="PC_2":
                new = self.panels_dict[key](**value)

                new.niche.cg = self.cog
                new.niche.cog_hole = self.cog_hole
                new.niche.generate_cogs()

                try:
                    for i in new.side:
                        i.hls = self.bend_hole
                except AttributeError:
                    pass
                setattr(self, key, ConeFrame(new))
                #setattr(self, key, MainFrame(new))



            elif key in ['B_2','B_3', 'B_2_1', 'B_2_1_rev', 'B_2_rev']:
                new = self.panels_dict[key](**value)

                setattr(self, key, MiniFrame(new))
                det = getattr(self, key)


            elif key == 'PC_3':
                new = self.panels_dict[key](**value)
                new.hls = self.p3_hole
                setattr(self, key, MainFrame(new))
                det = getattr(self, key)
                self.data.append(det.all_elems)


            elif key == 'PC_4':
                new = self.panels_dict[key](**value)
                new.hls = self.p3_hole
                setattr(self, key, MiniFrame(new))
                det = getattr(self, key)
                self.data.append(det.all_elems)


            else:
                pass

def main():
    global x, y, circle, bend_hole, p3_hole, cog_hole, crv

    a = UnrollPackage(x, y, circle, bend_hole, p3_hole, cog_hole, crv.__dict__)
    side = th.list_to_tree(a.data)
    #m = th.list_to_tree(a.m)
    #m=a.m

    return a, side


if __name__ == "__main__":
    a, side = main()




