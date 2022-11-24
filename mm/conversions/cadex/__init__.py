import rhino3dm
from rhino3dm import _rhino3dm as rh

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExRhino as rhino
import cadexchanger.CadExDXF as dxf

aKey = license.Value()

if not cadex.LicenseManager.Activate(aKey):
    print("Failed to activate CAD Exchanger license.")


def convert_to_cadex_viewer():
    aModel = cadex.ModelData_Model()


aReader = rhino.Rhino_Reader()
import json
import json
